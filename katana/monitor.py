#!/usr/bin/env python3
from __future__ import annotations
from typing import BinaryIO, Any
import logging
import json
import os
from PIL import Image

logger = logging.getLogger(__name__)


class Monitor(object):
    """ A monitor object recieves notifications from units whenever data,
    artifacts or flags are found while processing a target. The default monitor
    simply saves all artifacts to the artifact directory, and recurses on all
    data. It will also print flags to the console via it's logger. """

    def __init__(self):
        self.flags = []
        self.data = []
        self.artifacts = []
        self.exceptions = []
        self.thread_status = {}
        return

    def on_work(
        self,
        manager: katana.manager.Manager,
        threadid: int,
        unit: katana.unit.Unit,
        case: Any,
    ):
        """ Keep track of the thread statuses for asynchronous status updates
        """
        self.thread_status[threadid] = (unit, case)

    def on_depth_limit(
        self,
        manager: katana.manager.Manager,
        target: katana.target.Target,
        unit: katana.unit.Unit,
    ) -> None:
        """ This means we reached the manager['manager']['max-depth'] limit
        during recursion. """
        return

    def on_data(
        self, manager: katana.manager.Manager, unit: katana.unit.Unit, data: Any
    ) -> None:
        """ Notify the monitor of arbitrary data returned by a unit. The data
        could be of any type, but is likely `bytes` and should never be `str`
        (for complient units). The return value should indicate whether the
        given data should be recursed on (or re-evaluated for further unit
        processing). By default, all data is recursed on """
        self.data.append((unit, data))

    def on_artifact(
        self, manager: katana.manager.Manager, unit: katana.unit.Unit, path: str = None
    ) -> None:
        """ Notify the monitor that an artifact was found and may be of
        interest to store in a file. This may be a temporary file already open
        (which will be lost after the unit ends) or some data which appears
        to be a file. By default, this file is saved under the `outdir`
        directory of the Manager. The return value indicates whether a new
        target should be queued for recursion with this artifact as an upstream
        """

        self.artifacts.append((unit, path))

    def on_flag(
        self, manager: katana.manager.Manager, unit: katana.unit.Unit, flag: str
    ) -> None:
        """ Notify the monitor that a flag was found """
        self.flags.append((unit, flag))

    def on_exception(
        self, manager: katana.manager.Manager, unit: katana.unit.Unit, exc: Exception
    ) -> None:
        """ Notify the monitor that an exception occurred while processing a
        given unit. The exception is passed as the `exc` parameter """
        self.exceptions.append((unit, exc))

    def on_manager_exception(
        self, manager: katana.manager.Manager, exc: Exception
    ) -> None:
        """ Called when the manager catches an exception. By default, we do nothing.
        This is most likely a KeyboardInterrupt or some other signal that was sent to
        the main thread. """

    def on_completion(self, manager: katana.manager.Manager, timed_out: bool) -> None:
        """ This is called upon completion of evaluation (after manager.join()
        is complete). `timed_out` indicates if we reached a timeout. """


class LoggingMonitor(Monitor):
    logger = logging.getLogger("monitor")

    def __init__(self, *args, **kwargs):
        super(LoggingMonitor, self).__init__(*args, **kwargs)

    def on_flag(
        self, manager: katana.manager.Manager, unit: katana.unit.Unit, flag: str
    ):
        """ Log the solution chain of units which resulted in the given flag
        """
        super(LoggingMonitor, self).on_flag(manager, unit, flag)

        log_entry = " new target solution:\n"

        chain = []

        # Build chain in reverse direction
        link = unit
        while link is not None:
            chain.append(link)
            link = link.target.parent

        # Reverse the chain
        chain = chain[::-1]

        # Print the chain
        for n in range(len(chain)):
            log_entry += "  {0}{1}({2})->\n".format(
                " " * n, chain[n], str(chain[n].target)
            )
        log_entry += "  {0}{1}".format(" " * len(chain), flag)

        # Log the solution chain
        logger.info(log_entry)

    def on_artifact(
        self, manager: katana.manager.Manager, unit: katana.unit.Unit, path: str = None
    ) -> None:
        """ Log a new artifact """
        super(LoggingMonitor, self).on_artifact(manager, unit, path)
        logger.info(f" {unit}({unit.target}): new artifact: {path}")

    def on_exception(
        self,
        manager: katana.manager.Manager,
        unit: katana.unit.Unit,
        exception: Exception,
    ) -> None:
        super(LoggingMonitor, self).on_exception(manager, unit, exception)
        logger.warning(f" {unit}({unit.target}): exception: {exception}")


class JsonMonitor(Monitor):
    def get_result(self, results, unit):
        if unit.target.parent:
            parent_results = self.get_result(results, unit.target.parent)
        else:
            parent_results = results
        if repr(unit.target) not in parent_results["children"]:
            parent_results["children"][repr(unit.target)] = {
                str(unit): {"children": {}},
                "target_id": unit.target.hash.hexdigest(),
            }
        elif str(unit) not in parent_results["children"][repr(unit.target)]:
            parent_results["children"][repr(unit.target)][str(unit)] = {"children": {}}
        return parent_results["children"][repr(unit.target)][str(unit)]

    def build_results(self, target=None) -> Dict[str, Any]:

        results = {"children": {}}

        for datum in self.data:
            # Only look at units with the given root target
            if target is not None and datum[0].origin is not target:
                continue

            # Grab the result hash from the results object
            result = self.get_result(results, datum[0])

            # Ensure we have a data array
            if "data" not in result:
                result["data"] = []

            # Remove the annoying quotes and "b" from strings and bytes objects
            # respectively
            if isinstance(datum[1], str):
                datum = repr(datum[1])[1:-1]
            elif isinstance(datum[1], bytes):
                datum = repr(datum[1])[2:-1]
            else:
                datum = datum[1]

            # Add the data
            result["data"].append(datum)

        for flag in self.flags:

            # Only look at units with the given root target
            if target is not None and flag[0].origin is not target:
                continue

            # Grab the result hash from the results object
            result = self.get_result(results, flag[0])

            # Ensure we have a data array
            if "flags" not in result:
                result["flags"] = []

            # Remove the annoying quotes and "b" from strings and bytes objects
            # respectively
            if isinstance(flag[1], str):
                flag = repr(flag[1])[1:-1]
            elif isinstance(flag[1], bytes):
                flag = repr(flag[1])[2:-1]
            else:
                flag = flag[1]

            # Add the data
            result["flags"].append(flag)

        for artifact in self.artifacts:

            # Only look at units with the given root target
            if target is not None and artifact[0].origin is not target:
                continue

            # Grab the result hash from the results object
            result = self.get_result(results, artifact[0])

            # Ensure we have an artifact array
            if "artifacts" not in result:
                result["artifacts"] = []

            # Save the artifact name
            result["artifacts"].append(artifact[1])

            for flag in self.flags:
                # Grab the result hash from the results object
                result = self.get_result(results, flag[0])

                # Ensure we have an artifact array
                if "flags" not in result:
                    result["flags"] = []

                # Save the artifact name
                result["flags"].append(flag[1])

        for exception in self.exceptions:

            # Only look at units with the given root target
            if target is not None and exception[0].origin is not target:
                continue

            # Grab the result hash from the results object
            result = self.get_result(results, exception[0])

            # Ensure we have an artifact array
            if "exceptions" not in result:
                result["exceptions"] = []

            # Save the artifact name
            result["exceptions"].append(str(exception[1]))

        if target is not None:
            if repr(target) not in results["children"]:
                return {}
            else:
                return results["children"][repr(target)]
        else:
            return results["children"]

    def on_completion(self, manager: katana.manager.Manager, timed_out: bool) -> None:
        super(JsonMonitor, self).on_completion(manager, timed_out)

        results = {"children": {}}

        for datum in self.data:
            # Grab the result hash from the results object
            result = self.get_result(results, datum[0])

            # Ensure we have a data array
            if "data" not in result:
                result["data"] = []

            # Remove the annoying quotes and "b" from strings and bytes objects
            # respectively
            if isinstance(datum[1], str):
                datum = repr(datum[1])[1:-1]
            elif isinstance(datum[1], bytes):
                datum = repr(datum[1])[2:-1]
            else:
                datum = datum[1]

            # Add the data
            result["data"].append(datum)

        for flag in self.flags:
            # Grab the result hash from the results object
            result = self.get_result(results, flag[0])

            # Ensure we have a data array
            if "flags" not in result:
                result["flags"] = []

            # Remove the annoying quotes and "b" from strings and bytes objects
            # respectively
            if isinstance(flag[1], str):
                flag = repr(flag[1])[1:-1]
            elif isinstance(flag[1], bytes):
                flag = repr(flag[1])[2:-1]
            else:
                flag = flag[1]

            # Add the data
            result["flags"].append(flag)

        for artifact in self.artifacts:
            # Grab the result hash from the results object
            result = self.get_result(results, artifact[0])

            # Ensure we have an artifact array
            if "artifacts" not in result:
                result["artifacts"] = []

            # Save the artifact name
            result["artifacts"].append(artifact[1])

            for flag in self.flags:
                # Grab the result hash from the results object
                result = self.get_result(results, flag[0])

                # Ensure we have an artifact array
                if "flags" not in result:
                    result["flags"] = []

                # Save the artifact name
                result["flags"].append(flag[1])

        for exception in self.exceptions:
            # Grab the result hash from the results object
            result = self.get_result(results, exception[0])

            # Ensure we have an artifact array
            if "exceptions" not in result:
                result["exceptions"] = []

            # Save the artifact name
            result["exceptions"].append(exception[1])

        result_path = os.path.join(manager["manager"]["outdir"], "results.json")
        with open(result_path, "w") as fh:
            json.dump(results["children"], fh, indent=" ")
