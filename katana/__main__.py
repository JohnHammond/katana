#!/usr/bin/env python3
from types import FrameType
import argparse
import logging
import signal
import sys

from katana.manager import Manager
from katana.monitor import LoggingMonitor, JsonMonitor
from katana.repl import Repl, ReplMonitor
import katana.util
import os


def main():

    # Setup basic logging
    logging.basicConfig(level=logging.INFO)

    # Build the argument parse object
    parser = argparse.ArgumentParser(
        prog="katana",
        description="Automatically identify and solve basic Capture the Flag challenges",
        add_help=False,
    )

    # Parse config option first
    parser.add_argument("--config", "-c", help="configuration file", default=None)
    args, remaining_args = parser.parse_known_args()

    # Build our katana monitor
    monitor = ReplMonitor()

    # Create our katana manager
    manager = Manager(monitor=monitor, config_path=args.config)

    # Build final parser
    parser = argparse.ArgumentParser(
        prog="katana",
        description="Automatically identify and solve basic Capture the Flag challenges",
    )

    # Add global arguments
    parser.add_argument("--config", "-c", help="configuration file", default=None)
    parser.add_argument(
        "--manager",
        "-m",
        default=None,
        help="comma separated manager configurations (e.g. flag-format=FLAG{.*?})",
    )
    parser.add_argument(
        "--timeout",
        "-t",
        type=float,
        help="timeout for all unit evaluations in seconds",
    )
    parser.add_argument("targets", nargs="*", default=[], help="targets to evaluate")
    parser.add_argument(
        "--auto", "-a", help="shorthand for `-m auto=True`", action="store_true"
    )
    parser.add_argument(
        "--unit",
        "-u",
        help="explicitly run a unit on target",
        action="append",
        default=[],
    )
    parser.add_argument(
        "--exclude",
        "-e",
        help="exclude a unit from running",
        action="append",
        default=[],
    )
    parser.add_argument("--flag", "-f", help="set the flag format")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force execution even if results directory exists",
    )

    # Add options for all the unit specific configurations
    for unit in manager.finder.units:
        parser.add_argument(
            "--" + unit.get_name(),
            default=None,
            help="comma separated unit configuration",
        )

    # Parse arguments
    args = parser.parse_args(remaining_args)

    # Load configuration file
    if args.config is not None:
        result = manager.read(args.config)
        if len(result) == 0:
            logging.error(" {0}: no such file or directory".format(args.config))
            sys.exit(1)

    # Apply configurations
    if args.manager is not None:
        params = args.manager.split(",")
        for param in params:
            name, value = param.split("=")
            manager["manager"][name] = value

    # Apply auto shorthand
    if args.auto is not None:
        manager["manager"]["auto"] = "yes"

    # Apply flag format
    if args.flag is not None:
        manager["manager"]["flag-format"] = args.flag

    # Apply requested units
    units = [u for u in manager["manager"]["units"].split(",") if u] + args.unit
    manager["manager"]["units"] = ",".join(units)

    # Apply excluded units
    excluded = manager["manager"]["exclude"].split(",") + args.exclude
    manager["manager"]["exclude"] = ",".join(excluded)

    # Enable results removal if requested
    if args.force:
        manager["manager"]["force"] = "yes"
    else:
        manager["manager"]["force"] = "no"

    # Apply unit configurations
    args_dict = vars(args)  # We need this because configs have '.'
    for unit in manager.finder.units:
        # Ignore if nothing was specified
        if args_dict[unit.get_name()] is None:
            continue

        # Initialize the unit if needed
        if unit.get_name() not in manager:
            manager[unit.get_name()] = {}

        # Parse params
        params = args_dict[unit.get_name()].split(",")
        for param in params:
            name, value = param.split("=")
            manager[unit.get_name()][name] = value

    # Queue the specified targets
    for target in args.targets:

        manager.queue_target(target)

    # Build the REPL and execute it
    sys.argv = sys.argv[:1]
    repl = Repl(manager)
    sys.exit(repl.cmdloop())


if __name__ == "__main__":
    main()
