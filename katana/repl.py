#!/usr/bin/env python3
from watchdog.events import FileSystemEventHandler, FileSystemEvent, FileCreatedEvent
from watchdog.observers.api import ObservedWatch
from watchdog.observers import Observer
from colorama import Fore, Back, Style
from typing import Any, Dict, List
from cmd2 import clipboard
import cmd2.plugin
import argparse
import queue
import cmd2
import re
import os

from katana.monitor import JsonMonitor, LoggingMonitor
from katana.unit import Unit
from katana.manager import Manager
from katana.target import Target
import katana.util


class MonitoringEventHandler(FileSystemEventHandler):
    """ Receives events from watchdog for newly created files to queue """

    def __init__(self, repl: "katana.repl.Repl", *args, **kwargs):
        super(MonitoringEventHandler, self).__init__(*args, **kwargs)

        # Save the manager
        self.repl = repl

    def on_created(self, event: FileSystemEvent):
        """ Called when a new file is created """

        # We only care about files
        if not isinstance(event, FileCreatedEvent):
            return

        # Queue the event
        self.repl.manager.queue_target(event.src_path)

        # Notify the user
        with self.repl.terminal_lock:
            self.repl.async_alert(
                f"[{Fore.GREEN}!{Style.RESET_ALL}] "
                f"new target queued: {event.src_path}"
            )


class ReplMonitor(JsonMonitor):
    """ A monitor which will save important information needed to run
    the Repl katana shell. """

    def __init__(self):
        super(ReplMonitor, self).__init__()

        # The repl will assign this for us
        self.repl: Repl = None

    def on_flag(self, manager: Manager, unit: Unit, flag: str):
        super(ReplMonitor, self).on_flag(manager, unit, flag)

        chain = []

        # Build chain in reverse direction
        link = unit
        while link is not None:
            chain.append(link)
            link = link.target.parent

        # Reverse the chain
        chain = chain[::-1]

        # First entry is special
        log_entry = (
            f"{Fore.MAGENTA}{chain[0]}{Style.RESET_ALL}("
            f"{Fore.RED}{chain[0].target}{Style.RESET_ALL}) - "
            f"{Fore.GREEN}completed{Style.RESET_ALL}!\n"
        )

        # Print the chain
        for n in range(1, len(chain)):
            log_entry += (
                f" {' '*n}{Fore.MAGENTA}{chain[n]}{Style.RESET_ALL}("
                f"{Fore.RED}{chain[n].target}{Style.RESET_ALL}) "
                f"{Fore.YELLOW}➜ {Style.RESET_ALL}\n"
            )
        log_entry += (
            f" {' ' * len(chain)}{Fore.GREEN}{Style.BRIGHT}{flag}{Style.RESET_ALL} - "
            f"(copied)"
        )

        # Put the flag on the clipboard
        clipboard.write_to_paste_buffer(flag)

        # Notify the user
        with self.repl.terminal_lock:
            self.repl.async_alert(log_entry)

    def on_exception(
        self, manager: katana.manager.Manager, unit: katana.unit.Unit, exc: Exception
    ) -> None:
        super(ReplMonitor, self).on_flag(manager, unit, exc)

        # Notify the user
        with self.repl.terminal_lock:
            self.repl.pexcept(exc)


class Repl(cmd2.Cmd):
    """ A simple Katana REPL implemented using the cmd2 module.
    
    You should instantiate the manager prior to creating this object. It will
    then allow the user to modify configuration, load configuration files, and
    queue targets, however you are free to do this prior to creating the Repl.
    
    The manager _must_ be created using a ReplMonitor or subclass thereof! Further,
    you should not call `manager.start()` prior to creating this object. It will
    call `manager.start()` prior to execution of the main command loop. This is
    to ensure that the we can register the Monitor with our Repl object for
    bidirectional communication.
    """

    def __init__(self, manager: Manager):
        super(Repl, self).__init__()

        # Ensure we are using the correct monitor
        if not isinstance(manager.monitor, ReplMonitor):
            raise RuntimeError("Repl expects a subclass of ReplMonitor!")

        # Save a manager reference
        self.manager = manager

        # Ensure the monitor knows we exist
        self.manager.monitor.repl = self

        # Display full tracebacks for errors/exceptions
        self.debug = True

        # Create a filesystem monitor
        self.fseventhandler = MonitoringEventHandler(self)
        self.observer = Observer()
        self.directories: Dict[str, ObservedWatch] = {}

        # Start the observer
        self.observer.start()

        # Register hook to update prompt
        self.register_cmdfinalization_hook(self.finalization_hook)

        # Start the manager
        self.manager.start()

        # Update the prompt
        self.update_prompt()

    def finalization_hook(
        self, data: cmd2.plugin.CommandFinalizationData
    ) -> cmd2.plugin.CommandFinalizationData:
        """ Updated dynamic prompt """
        # Update the prompt
        self.update_prompt()
        self.poutput("")
        # Maintain exit status
        return data

    def update_prompt(self):
        """ Updates the prompt with the current state """

        # build a dynamic state
        if self.manager.barrier.n_waiting == len(self.manager.threads):
            state = f"{Fore.YELLOW}waiting{Style.RESET_ALL} - "
        else:
            state = f"{Fore.GREEN}running{Style.RESET_ALL} - "

        # update the prompt
        self.prompt = f"{Fore.CYAN}katana{Style.RESET_ALL} - " + state
        self.prompt += (
            f"{Fore.BLUE}{self.manager.work.qsize()} units queued{Style.RESET_ALL} "
            f"\n{Fore.GREEN}➜ {Style.RESET_ALL}"
        )

    status_parser = argparse.ArgumentParser(
        description="Display status message for all running threads"
    )
    status_parser.add_argument(
        "--flags",
        "-f",
        action="store_true",
        help="Show all flags as well as thread status",
    )

    @cmd2.with_argparser(status_parser)
    def do_status(self, args):
        for tid, status in self.manager.monitor.thread_status.items():
            unit: Unit = status[0]
            case: Any = status[1]
            if case is not None:
                self.poutput(
                    f"thread[{tid}]: {repr(unit)} -> {katana.util.ellipsize(case, 20)}"
                )
            else:
                self.poutput(f"thread[{tid}]: {repr(unit)}")

        if args.flags is not None:
            self.poutput("Flags found so far: ")
            for unit, flag in self.manager.monitor.flags:
                self.poutput(f"{repr(unit)}: {flag}")

    evaluate_parser = argparse.ArgumentParser(
        description="Queue a new target for evaluation"
    )
    evaluate_parser.add_argument("target", type=str, help="the target to evaluate")

    @cmd2.with_argparser(evaluate_parser)
    def do_evaluate(self, args):
        """ Queue a new target for evaluation """
        self.manager.queue_target(bytes(args.target, "utf-8"))

    join_parser = argparse.ArgumentParser(
        description="Wait for all currently evaluating targets to complete, then exit"
    )
    join_parser.add_argument(
        "--timeout", "-t", type=float, help="Set a maximum timeout for completion"
    )

    @cmd2.with_argparser(join_parser)
    def do_join(self, args):
        """ Wait for all targets to complete evaluation, then exit """

        self.poutput("manager: waiting for thread completion")

        if not self.manager.join():
            self.poutput("manager: evaluation timed out")

        self.poutput(f"manager: {self.manager.work.qsize()} items left in queue")

        try:
            while True:
                self.poutput(f"{self.manager.work.get(False)}")
        except queue.Empty:
            pass

        return True

    # The main argument parser
    monitor_parser = argparse.ArgumentParser(
        description=r"""Begin monitoring the given directory and automatically queue new targets """
        """as they are created."""
    )
    # Subparsers object to create sub-commands
    monitor_subparsers: argparse._SubParsersAction = monitor_parser.add_subparsers(
        help="Actions", required=True, dest="_action"
    )

    # `list` parser
    monitor_list_parser: argparse.ArgumentParser = monitor_subparsers.add_parser(
        "list",
        aliases=["ls", "l"],
        help="list currently monitored directories",
        prog="monitor ls",
    )
    monitor_list_parser.set_defaults(action="list")

    # `remove` parser
    monitor_remove_parser: argparse.ArgumentParser = monitor_subparsers.add_parser(
        "remove",
        aliases=["rm", "r"],
        help="remove a monitored directory",
        prog="monitor remove",
    )
    monitor_remove_parser.add_argument(
        "directory", nargs="+", help="The directories to stop monitoring"
    )
    monitor_remove_parser.set_defaults(action="remove")

    # `add` parser
    monitor_add_parser: argparse.ArgumentParser = monitor_subparsers.add_parser(
        "add",
        aliases=["a"],
        help="begin monitoring a new directory",
        prog="monitor add",
    )
    monitor_add_parser.add_argument(
        "--recursive",
        "-r",
        default=False,
        action="store_true",
        help="Monitor the directory recursively",
    )
    monitor_add_parser.add_argument(
        "directory", nargs="+", help="The directories to monitor"
    )
    monitor_add_parser.set_defaults(action="add")

    @cmd2.with_argparser(monitor_parser)
    def do_monitor(self, args: argparse.Namespace) -> bool:
        """ Add a directory to the fs observer """

        if args.action == "add":
            for dir in args.directory:
                if not os.path.isdir(dir):
                    self.perror(f"[{Fore.RED}!{Style.RESET}] {dir}: not a directory")
                    continue
                abs_dir = os.path.realpath(os.path.abspath(dir))
                if abs_dir in self.directories:
                    self.perror(
                        f"[{Fore.RED}!{Style.RESET_ALL}] {dir}: already monitored"
                    )
                    continue
                self.directories[abs_dir] = self.observer.schedule(
                    self.fseventhandler, dir, args.recursive
                )
        elif args.action == "remove":
            # Remove currently monitored directories
            for dir in args.directory:

                # Make sure it exists
                if not os.path.isdir(dir):
                    self.perror(f"[{Fore.RED}!{Style.RESET}] {dir}: not a directory")
                    continue

                # Get the full canonical path
                dir = os.path.realpath(os.path.abspath(dir))

                # Ensure we are actually monitoring it
                if dir not in self.directories:
                    self.perror(
                        f"[{Fore.RED}!{Style.RESET}] {dir}: not being monitored"
                    )
                    continue

                # Remove it from the observer
                handle = self.directories[dir]
                del self.directories[dir]
                self.observer.unschedule(handle)

        elif args.action == "list":
            # List all monitored directories
            output = ""
            for path, handle in self.directories.items():
                if handle.is_recursive:
                    output += f"\n{handle.path} - {Fore.CYAN}recursive{Style.RESET_ALL}"
                else:
                    output += (
                        f"\n{handle.path} - {Fore.BLUE}non-recursive{Style.RESET_ALL}"
                    )
            self.poutput(output[1:])

        # Don't exit
        return False

    # Main target argument parser
    target_parser = argparse.ArgumentParser(
        description="Add, remove, and view queued targets"
    )
    target_subparsers: argparse._SubParsersAction = target_parser.add_subparsers(
        help="Actions", required=True, dest="_action"
    )

    # Add a new target
    target_add_parser: argparse.ArgumentParser = target_subparsers.add_parser(
        "add", aliases=["a"], help="Add a new target for processing"
    )
    target_add_parser.add_argument("target", nargs="+", help="the target to evaluate")
    target_add_parser.set_defaults(action="add")

    # Stop a running target
    target_stop_parser: argparse.ArgumentParser = target_subparsers.add_parser(
        "stop", aliases=["s", "cancel", "c"], help="Stop evaluation of a queued target"
    )
    target_stop_parser.add_argument(
        "targetid", nargs="+", help="the target id (hash) to stop"
    )
    target_stop_parser.set_defaults(action="stop")

    # List queued targets
    target_list_parser: argparse.ArgumentParser = target_subparsers.add_parser(
        "list", aliases=["ls", "l", "show"], help="List all queued targets"
    )
    target_list_parser.add_argument(
        "--completed",
        "-c",
        action="store_const",
        const="completed",
        dest="which",
        help="Display only completed targets",
    )
    target_list_parser.add_argument(
        "--running",
        "-r",
        action="store_const",
        const="running",
        dest="which",
        help="Display only running targets",
    )
    target_list_parser.add_argument(
        "--all",
        "-a",
        action="store_const",
        const="all",
        dest="which",
        help="Display all targets (running/completed)",
    )
    target_list_parser.add_argument(
        "--flags",
        "-f",
        action="store_const",
        const="flags",
        dest="which",
        help="Display only targets with flags",
    )
    target_list_parser.set_defaults(action="list")

    @cmd2.with_argparser(target_parser)
    def do_target(self, args: argparse.Namespace) -> bool:
        """ Add/stop/list queued targets """
        actions = {
            "add": self._target_add,
            "stop": self._target_stop,
            "list": self._target_list,
        }
        actions[args.action](args)
        return False

    def _target_add(self, args: argparse.Namespace) -> None:
        """ Add a new target for evaluation """

        for target in args.target:
            self.poutput(f"[{Fore.GREEN}+{Style.RESET_ALL}] {target}: queuing target")
            self.manager.queue_target(target)

    def _target_stop(self, args: argparse.Namespace) -> None:
        """ Stop processing the given target """

        # Stop each target
        for target in args.targetid:
            # Look for a matching hash
            for other in self.manager.targets:
                if other.hash.hexdigest() == target:
                    # Notify the user if it's already completed
                    if other.completed:
                        self.poutput(
                            f"[{Fore.YELLOW}!{Style.RESET_ALL}] {target}: already completed"
                        )
                    else:
                        other.completed = True

    def _target_list(self, args: argparse.Namespace) -> None:
        """
        Display a list of completed and/or running targets that have been queued.
        
        :param args: The argparse Namespace
        :return: None
        """

        targets: List[Target] = []

        if args.which is None or args.which == "all":
            targets = self.manager.targets
        elif args.which == "completed":
            targets = [t for t in self.manager.targets if t.completed]
        elif args.which == "running":
            targets = [t for t in self.manager.targets if not t.completed]
        elif args.which == "flags":
            targets = [f[0].origin for f in self.manager.monitor.flags]

        output = ""

        for target in targets:
            # Grab the status
            if target.completed:
                status = f"{Fore.GREEN}completed{Style.RESET_ALL}"
            else:
                status = f"{Fore.YELLOW}running{Style.RESET_ALL}"

            # Grab first flag
            flags = [f[1] for f in self.manager.monitor.flags if f[0].origin == target]

            # Build initial output
            output += (
                f"\n{Fore.RED}{target}{Style.RESET_ALL} - {status}\n"
                f" hash: {Fore.CYAN}{target.hash.hexdigest()}{Style.RESET_ALL}\n"
            )

            # Add flags if there are any
            output += "\n".join(
                f" flag: {Fore.GREEN}{Style.BRIGHT}{f}{Style.RESET_ALL}" for f in flags
            )

        # Print the list
        if len(output) > 0:
            self.poutput(output)

    def do_quit(self, args):
        """ Ensure we wait on unit completion before exiting """

        # Wait for threads to exit
        self.poutput("manager: waiting for thread completion... ")
        self.manager.abort()

        return True

    set_parser = argparse.ArgumentParser(
        description=r"""Set or retreive a katana runtime parameter. Parameters may be specified as """
        r"""SECTION[NAME] or simply NAME. If no section is specified, 'DEFAULT' is assumed. """
        r"""If no value is specified, the value will be printed. If no parameter or value is """
        r"""specified, then all sections are displayed. """
    )
    set_parser.add_argument(
        "--section", "-s", action="store_true", help="Show entire section contents"
    )
    set_parser.add_argument(
        "--reset", "-r", action="store_true", help="remove/reset a parameter"
    )
    set_parser.add_argument(
        "parameter", nargs=argparse.OPTIONAL, help="The parameter to modify"
    )
    set_parser.add_argument("value", nargs=argparse.OPTIONAL, help="The value to set")

    @cmd2.with_argparser(set_parser)
    def do_set(self, args: argparse.Namespace):
        """ Set a runtime parameter """
        pattern = r"([a-zA-Z_\-0-9]*)\[([a-zA-Z_\-0-9]*)\]"

        if args.parameter is not None:
            # Check if we are specifying section[parameter]
            match = re.match(pattern, args.parameter)
            if match is not None:
                # Grab each piece
                section, name = match[1], match[2]
            else:
                # Otherwise, assume default
                section = "DEFAULT"
                name = args.parameter

            # Ensure the section exists
            if section not in self.manager:
                self.perror(f"{section}: no such configuration section")
                return False

        if args.value:
            # Ensure the section exists
            if section not in self.manager:
                self.manager[section] = {}
            # Set the value
            self.manager[section][name] = args.value
        elif args.parameter is None:
            # Display the entire configuration
            for section in ["DEFAULT"] + self.manager.sections():
                # Print section
                self.poutput(f"[{section}]")

                # Print each item in the section
                for name in self.manager[section]:
                    if section == "DEFAULT" or name not in self.manager["DEFAULT"]:
                        self.poutput(f"  {name} = {self.manager[section][name]}")

        elif args.section is None:
            if args.reset:
                self.poutput(f"removing {section}[{name}]")
                self.manager.remove_option(section, name)
            else:
                # Display a single value within a section
                self.poutput(f"[{section}]")
                self.poutput(f"{name} = {self.manager[section][name]}")
        else:
            # Display an entire section either specifying section[name] or section alone
            if match is None:
                # We specified section alone, but it was captured in name above
                section = name
            # Ensure this exists (may have slipped past above check in the name variable)
            if section not in self.manager:
                self.perror(f"{section}: no such configuration section")
            else:
                # Print the whole section
                self.poutput(f"[{section}]")
                for name in self.manager[section]:
                    self.poutput(f"{name} = {self.manager[section][name]}")

        # All done! Don't exit.
        return False
