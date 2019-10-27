#!/usr/bin/env python3
import functools
import os
import re
from typing import Any, Dict, List, Tuple

import argparse
import cmd2.plugin
from cmd2 import clipboard
from cmd2.argparse_custom import Cmd2ArgumentParser, CompletionItem
from colorama import Fore, Style
from watchdog.events import FileSystemEventHandler, FileSystemEvent, FileCreatedEvent
from watchdog.observers import Observer
from watchdog.observers.api import ObservedWatch

import katana.util
from katana.manager import Manager
from katana.monitor import JsonMonitor
from katana.target import Target
from katana.unit import Unit
from katana.repl import ctfd


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


def get_target_choices(repl, uncomplete=False) -> List[CompletionItem]:
    """
    Get available targets for command completion

    :param repl: The Repl object
    :return: List of completion object referring to queued targets
    """
    repl: Repl

    # Grab root targets
    targets = [t for t in repl.manager.targets if t.parent is None]

    # Filter by uncompleted units
    if uncomplete:
        targets = [t for t in targets if not t.completed]

    result = [CompletionItem(t.hash.hexdigest(), repr(t)) for t in targets]

    return result


def get_monitor_choices(repl: "katana.repl.Repl") -> List[CompletionItem]:
    """
    Get available monitors for command completion
    
    :param repl: The Repl object
    :return: List of completion objects referring to monitored directories
    """

    return [d for d in repl.directories]


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

        # Setup argparse completers for commands

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
            state = f"{Fore.YELLOW}waiting{Style.RESET_ALL}"
        else:
            state = f"{Fore.GREEN}running{Style.RESET_ALL}"

        # update the prompt
        self.prompt = (
            f"{Fore.CYAN}katana{Style.RESET_ALL} - {state} - "
            f"{Fore.BLUE}{self.manager.work.qsize()} units queued{Style.RESET_ALL} "
            f"\n{Fore.GREEN}➜ {Style.RESET_ALL}"
        )

    status_parser = Cmd2ArgumentParser(
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

    exit_parser = Cmd2ArgumentParser(
        description="Cleanup currently running evaluation and exit"
    )
    exit_parser.add_argument(
        "--timeout",
        "-t",
        type=float,
        help="Timeout for waiting in outstanding evaluations",
    )
    exit_parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force exit prior to evaluation completion",
    )

    @cmd2.with_argparser(exit_parser)
    def do_exit(self, args: argparse.Namespace) -> bool:
        """
        Exit the katana REPL. Optionally, force current evaluation to complete immediately.
        
        :param args: argparse Namespace containing parameters
        :return: whether to exit or not (always True)
        """

        if args.force is not None and args.force:
            self.poutput(f"[{Fore.YELLOW}!{Style.RESET_ALL}] forcing thread exit")
            self.manager.abort()
        else:
            self.poutput(
                f"[{Fore.BLUE}-{Style.RESET_ALL}] waiting for thread completion (timeout={args.timeout})"
            )
            self.terminal_lock.release()
            result = self.manager.join(args.timeout)
            self.terminal_lock.acquire()
            if not result:
                self.poutput(f"[{Fore.YELLOW}!{Style.RESET_ALL}] evaluation timeout")

        self.poutput(f"[{Fore.GREEN}+{Style.RESET_ALL}] manager exited cleanly")

        return True

    @cmd2.with_argparser(exit_parser)
    def do_quit(self, args: argparse.Namespace) -> bool:
        """ Same as do_exit """
        return self.do_exit(args)

    # The main argument parser
    monitor_parser = Cmd2ArgumentParser(
        description=r"""Begin monitoring the given directory and automatically queue new targets """
        """as they are created."""
    )
    # Subparsers object to create sub-commands
    monitor_subparsers: argparse._SubParsersAction = monitor_parser.add_subparsers(
        help="Actions", required=True, dest="_action"
    )

    # `list` parser
    monitor_list_parser: Cmd2ArgumentParser = monitor_subparsers.add_parser(
        "list",
        aliases=["ls", "l"],
        help="list currently monitored directories",
        prog="monitor ls",
    )
    monitor_list_parser.set_defaults(action="list")

    # `remove` parser
    monitor_remove_parser: Cmd2ArgumentParser = monitor_subparsers.add_parser(
        "remove",
        aliases=["rm", "r"],
        help="remove a monitored directory",
        prog="monitor remove",
    )
    monitor_remove_parser.add_argument(
        "directory",
        nargs="+",
        help="The directories to stop monitoring",
        choices_method=get_monitor_choices,
    )
    monitor_remove_parser.set_defaults(action="remove")

    # `add` parser
    monitor_add_parser: Cmd2ArgumentParser = monitor_subparsers.add_parser(
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
        "directory",
        nargs="+",
        help="The directories to monitor",
        completer_method=functools.partial(
            cmd2.Cmd.path_complete, path_filter=lambda path: os.path.isdir(path)
        ),
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
    target_parser = Cmd2ArgumentParser(
        description="Add, remove, and view queued targets"
    )
    target_subparsers: argparse._SubParsersAction = target_parser.add_subparsers(
        help="Actions", required=True, dest="_action"
    )

    # Add a new target
    target_add_parser: Cmd2ArgumentParser = target_subparsers.add_parser(
        "add", aliases=["a"], help="Add a new target for processing"
    )
    target_add_parser.add_argument(
        "target",
        nargs="+",
        help="the target to evaluate",
        completer_method=cmd2.Cmd.path_complete,
    )
    target_add_parser.set_defaults(action="add")

    # Stop a running target
    target_stop_parser: Cmd2ArgumentParser = target_subparsers.add_parser(
        "stop", aliases=["s", "cancel", "c"], help="Stop evaluation of a queued target"
    )
    target_stop_parser.add_argument(
        "target",
        nargs="+",
        help="the target id (hash) to stop",
        choices_method=functools.partial(get_target_choices, uncomplete=True),
    )
    target_stop_parser.set_defaults(action="stop")

    # List queued targets
    target_list_parser: Cmd2ArgumentParser = target_subparsers.add_parser(
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

    # View target solutions (chain of units producing flags)
    target_solution_parser: Cmd2ArgumentParser = target_subparsers.add_parser(
        "solution", aliases=["flags"], help="List solution chains for all found flags"
    )
    target_solution_parser.add_argument(
        "--raw",
        "-r",
        action="store_true",
        help="Match the specified target by the target upstream string vice the hash",
    )
    target_solution_parser.add_argument(
        "target",
        help="The target hash or upstream (if --raw is specified)",
        choices_method=get_target_choices,
    )
    target_solution_parser.set_defaults(action="solution")

    @cmd2.with_argparser(target_parser)
    def do_target(self, args: argparse.Namespace) -> bool:
        """ Add/stop/list queued targets """
        actions = {
            "add": self._target_add,
            "stop": self._target_stop,
            "list": self._target_list,
            "solution": self._target_solution,
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
        for target in args.target:
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
            # In this context, we mean root targets only
            targets = [t for t in self.manager.targets if t.parent is None]
        elif args.which == "completed":
            targets = [
                t for t in self.manager.targets if t.completed and t.parent is None
            ]
        elif args.which == "running":
            targets = [
                t for t in self.manager.targets if not t.completed and t.parent is None
            ]
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

    def _target_solution(self, args: argparse.Namespace) -> None:
        """
        Display all found solutions for this target.
        
        :param args: argparse Namespace object with parsed parameters
        :return:
        """

        if args.raw is not None:
            # Match based on target upstream
            flags = [
                f
                for f in self.manager.monitor.flags
                if f[0].origin.upstream.startswith(bytes(args.target, "utf-8"))
            ]
        else:
            # Match based on target hash
            flags = [
                f
                for f in self.manager.monitor.flags
                if f[0].origin.hash.hexdigest() == bytes(args.target, "utf-8")
            ]

        # Ensure we found at least one target
        if len(flags) == 0:
            self.perror(f"[{Fore.RED}-{Style.RESET_ALL}] {args.target}: no flags found")
            return
        elif len(flags) > 1:
            # We found more than one, assume the first matching
            self.poutput(
                f"[{Fore.YELLOW}!{Style.RESET_ALL}] {args.target}: selecting "
                f"{Fore.RED}{flags[0][0].origin}{Style.RESET_ALL}"
            )

        # Either the first or only flag
        flag: Tuple[Unit, str] = flags[0]

        # The chain of units upward
        chain = []

        # Build chain in reverse direction
        link = flag[0]
        while link is not None:
            chain.append(link)
            link = link.target.parent

        # Reverse the chain
        chain = chain[::-1]

        # First entry is special
        log_entry = (
            f"{Fore.MAGENTA}{chain[0]}{Style.RESET_ALL}("
            f"{Fore.RED}{chain[0].target}{Style.RESET_ALL})\n"
        )

        # Print the chain
        for n in range(1, len(chain)):
            log_entry += (
                f" {' '*n}{Fore.MAGENTA}{chain[n]}{Style.RESET_ALL}("
                f"{Fore.RED}{chain[n].target}{Style.RESET_ALL}) "
                f"{Fore.YELLOW}➜ {Style.RESET_ALL}\n"
            )
        log_entry += (
            f" {' ' * len(chain)}{Fore.GREEN}{Style.BRIGHT}{flag[1]}{Style.RESET_ALL} - "
            f"(copied)"
        )

        # Print the entry
        self.poutput(log_entry)

    set_parser = Cmd2ArgumentParser(
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
            if section not in self.manager and not args.value:
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

    # ctfd command parser
    ctfd_parser = Cmd2ArgumentParser(
        description="Interact with a CTFd instance to easily queue targets"
    )
    ctfd_subparsers: argparse._SubParsersAction = ctfd_parser.add_subparsers(
        help="Actions", required=True, dest="_action"
    )

    # `ctfd list` parser
    ctfd_list_parser: argparse.ArgumentParser = ctfd_subparsers.add_parser(
        "list", help="List all challenges on the CTFd server"
    )
    ctfd_list_parser.set_defaults(action="list")

    # `ctfd queue` parser
    ctfd_queue_parser: argparse.ArgumentParser = ctfd_subparsers.add_parser(
        "queue", help="Queue a challenge for evaluation"
    )
    ctfd_queue_parser.add_argument(
        "--files",
        "-f",
        action="store_true",
        help="Only queue attached files for evaluation",
    )
    ctfd_queue_parser.add_argument(
        "challenge_id",
        type=int,
        help="Challenge ID to queue",
        choices_method=ctfd.get_challenge_choices,
    )
    ctfd_queue_parser.set_defaults(action="queue")

    @cmd2.with_argparser(ctfd_parser)
    def do_ctfd(self, args: argparse.Namespace) -> bool:
        """
        Interact with a CTFd instance.
        
        :param args: argparse Namespace object containing parameters
        :return: True
        """

        # Actions table
        actions = {"list": self._ctfd_list, "queue": self._ctfd_queue}

        # Execute specified action
        actions[args.action](args)

        # Do not exit
        return False

    def _ctfd_list(self, args: argparse.Namespace) -> None:
        """
        List all avaiable challenge IDs
        
        :param args: argparse Namespace object with parameters
        :return: None
        """

        challenges = ctfd.get_challenges(self)
        output = [f"{'ID':<8}{'Title':<40}Points"]

        for c in challenges:
            output.append(f"{c['id']:<8}{c['name']:<40}{c['value']}")

        self.poutput("\n".join(output))

    def _ctfd_queue(self, args: argparse.Namespace) -> None:
        """
        Queue a challenge for evaluation
        
        :param args:
        :return:
        """

        self.poutput("Not implemented")
