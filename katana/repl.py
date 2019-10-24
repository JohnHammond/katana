#!/usr/bin/env python3
from typing import Any, Tuple
import argparse
import cmd2
import re

from katana.monitor import JsonMonitor, LoggingMonitor
from katana.unit import Unit
from katana.manager import Manager
import katana.util


class ReplMonitor(JsonMonitor):
    """ A monitor which will save important information needed to run
    the Repl katana shell. """

    def __init__(self):
        super(ReplMonitor, self).__init__()

        # The repl will assign this for us
        self.repl: Repl = None

    def on_flag(self, manager: Manager, unit: Unit, flag: str):
        with self.repl.terminal_lock:
            self.repl.async_alert(f"{repr(unit)}: flag: {flag}")

    def on_exception(
        self, manager: katana.manager.Manager, unit: katana.unit.Unit, exc: Exception
    ) -> None:
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

        # Default prompt
        self.prompt = "katana> "

    def preloop(self) -> None:
        """ Start the manager processing prior to command loop execution """
        self.manager.start()

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
