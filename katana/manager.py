#!/usr/bin/env python3
""" A katana manager which is capable managing the evaluation of arbitrary
units against an arbitrary number of Targets of varying types in a
multithreaded manner and reporting results to a Monitor object """
from dataclasses import dataclass, field
from typing import List, Any, Generator, Dict, Callable, Tuple
import configparser
import threading
import queue
import time
import os
import sys
import regex as re
import shutil
import requests


# katana imports
from katana.target import Target, BadTarget
from katana.unit import Unit, Finder
from katana.monitor import Monitor
import katana.util


@dataclass
class Download(object):
    """ Tracks data about an active download """

    # The URL being downloaded
    url: str
    # The size of the download (if known, -1 otherwise)
    size: int
    # The number of bytes already transferred
    trans: int
    # Average speed (bytes/second)
    speed: float
    # Whether this download is completed
    completed: bool


class Manager(configparser.ConfigParser):
    """ Class to manage the threaded evaluation of applicable units against
    arbitrary targets. Facilitates work queue management and recursion within
    given units. It will also manage output file creation (such as artifacts).
    """

    @dataclass(order=True)
    class WorkItem(object):
        """ Defines the items that are actually placed in the work queue. The
        work queue maintains the state of the case generator and priority for
        the unit. Priority is taken directly from the unit. `generator` is the
        result of `unit.evaluate` and will be called when the first thread
        begins evaluating the unit. """

        priority: float
        action: str = field(compare=False)
        unit: Unit = field(compare=False)
        generator: Generator[Any, None, None] = field(compare=False)

    def __init__(self, monitor: Monitor = None, config_path=None, default_units=True):

        # This needs to exist before the ConfigParser is initialized
        self.running = False

        # Initialize ConfigParser
        super(Manager, self).__init__()

        # Default values for configuration items
        self["DEFAULT"] = {
            "units": "",
            "threads": 4,
            "outdir": "./results",
            "auto": False,
            "recurse": True,
            "force": False,
            "exclude": "",
            "min-data": 5,
            "download": True,
            "template": "default",
            "timeout": 0.1,
            "prioritize": True,
            "default-units": True,
            "max-depth": 10,
        }

        if "manager" not in self:
            self["manager"] = {}

        try:
            self["DEFAULT"]["threads"] = str(len(os.sched_getaffinity(0)))
        except AttributeError:
            # os.sched_getaffinity does not exist. We fallback to
            # multiprocessing
            import multiprocessing

            self["DEFAULT"]["threads"] = str(multiprocessing.cpu_count())

        # Load a configuration file if specified
        if config_path is not None and len(self.read(config_path)) == 0:
            raise RuntimeError("{0}: configuration file not found")

        # Create a default monitor if there is none
        if monitor is None:
            monitor = Monitor()

        # Create the unit finder for matching targets to units
        self.finder = Finder(self, use_default=default_units)
        # This is the work queue
        self.work = queue.PriorityQueue()
        # This is the barrier which signals wait on and signals completion of
        # evaluation. It is initialized in the `start` method
        self.barrier: threading.Barrier = None
        # Array of threads (also initialized in `start`)
        self.threads = []
        # Flag pattern will be compiled upon running `start`
        self.flag_pattern = None

        # This is dumb, and I don't know why we need it
        if "flag-format" in self["manager"]:
            self["manager"]["flag-format"] = self["manager"]["flag-format"]

        # Save the monitor
        self.monitor = monitor
        # Have we joined or aborted yet?
        self.running = False
        # List of root targets that have been queued
        self.targets: List[Target] = []
        self.target_hash: Dict[str, Target] = {}
        # Number of cases completed (for stats)
        self.cases_completed = 0
        # This might be a bad idea
        self.lock: threading.Lock = threading.Lock()
        # Downloads that are in progress
        self.downloads: List[Download] = []

    def set(self, section: str, option: str, value: Any = None) -> None:
        """ Wrapper around ConfigParser.set. We need to take into account some special
        configs which require other things to be accounted for (e.g. flag_format for
        RE compilation). """

        # We only specially handle manager and DEFAULT sections
        if section != "manager" and section != "DEFAULT":
            return super(Manager, self).set(section, option, value)

        # Flag Format needs to be compiled
        if option == "flag-format":
            self.flag_pattern = re.compile(
                bytes(value, "utf-8"), re.IGNORECASE | re.MULTILINE | re.DOTALL
            )
        elif option == "threads":
            if self.running:
                # We cannot modify the thread count after starting the manager
                return

        return super(Manager, self).set(section, option, value)

    def download(
        self,
        url: str,
        blocksize: int = 512,
        method: Callable = requests.get,
        *args,
        **kwargs,
    ) -> Tuple[requests.Request, Generator[bytes, None, None]]:
        """ Begin the streaming download of a URL.
        
        :param url: the URL to download
        :type url: str
        :param blocksize: The size of each block of data to return
        :type blocksize: int
        :param method: The method used to request the page, defaults to ``requests.get``
        :type method: Callable
        :returns: A tuple of the request object and a generator returning the chunks
        :rtype: Tuple[requests.Request, Generator[bytes, None, None]]
        """

        # Initiate the connection
        request: requests.Request = method(url, stream=True, *args, **kwargs)

        # extract the content length
        if "content-length" in request.headers:
            size = int(request.headers["content-length"])
        else:
            size = -1

        # Build the download object
        d = Download(url, size, 0, 0, False)

        # Track the download
        self.downloads.append(d)

        def _iterate_content():
            # We catch the first one to ensure we don't start reading data too early
            yield None

            start = time.time()
            last_update = 0

            # Iterate over the data
            for chunk in request.iter_content(chunk_size=blocksize):
                # Increment total transfer count
                d.trans += len(chunk)
                # Recalculate transfer speed
                d.speed = d.trans / (time.time() - start)

                if (time.time() - last_update) > 1:
                    self.monitor.on_download_update(self, d)
                    last_update = time.time()

                # Return the chunk
                yield chunk

            d.completed = True
            self.monitor.on_download_update(self, d)

        # Create the Generator and ignore the first result
        gen = _iterate_content()
        next(gen)

        # Return the
        return request, gen

    @property
    def active_downloads(self) -> List[Download]:
        """ Grab a list of active downloads. This also cleans the download list """
        self.downloads = [d for d in self.downloads if not d.completed]
        return self.downloads

    def register_artifact(self, unit: Unit, path: str, recurse: bool = True) -> None:
        """ Register an artifact result with the manager """

        # Notify the monitor of an artifact
        self.monitor.on_artifact(self, unit, path)

        # Recurse on this target
        if unit.target.config["manager"].getboolean("recurse") and recurse:
            self.queue_target(path, parent=unit)

    def register_data(self, unit: Unit, data: Any, recurse: bool = True) -> None:
        """ Register arbitrary data results with the manager """

        # Sometimes units do weird things
        if len(data) < int(self["manager"]["min-data"]):
            return

        # Notify the monitor of the data
        self.monitor.on_data(self, unit, data)

        # Look for flagsregister
        self.find_flag(unit, data)

        if unit.target.config["manager"].getboolean("recurse") and recurse:
            # Only do full recursion if requested
            self.queue_target(data, parent=unit)

    def register_flag(self, unit: Unit, flag: str) -> None:
        """ Register a flag that was found during processing and raise the
        FoundFlag exception. """

        # Mark this unit as completed
        if unit is not None:
            unit.origin.completed = True

        # Notify the monitor
        self.monitor.on_flag(self, unit, flag)

    def find_flag(self, unit: Unit, data: Any) -> bool:
        """ Search arbitrary data for flags matching the given flag format in
        the manager configuration """

        # Iterate over lists and tuples automatically
        if isinstance(data, list) or isinstance(data, tuple):
            found = 0
            for item in data:
                found += self.find_flag(unit, item)
            return found > 0

        # Iterate over dictionaries
        if isinstance(data, dict):
            found = 0
            for key, item in data.items():
                found += self.find_flag(unit, item)
            return found > 0

        # We deal with bytes here
        if isinstance(data, str):
            data = data.encode("utf-8")

        # CALEB: this is a hack to remove XML from flags, and check that as
        # well. It was observed to be needed for some weird XML challenges.
        no_xml = re.sub(b"<[^<]+>", b"", data)
        if no_xml != data:
            self.find_flag(unit, no_xml)

        # Search the data for flags
        match = re.search(
            bytes(unit.target.config["manager"]["flag-format"], "utf-8"),
            data,
            re.DOTALL | re.MULTILINE | re.IGNORECASE,
        )
        if match:
            # Flags should be printable
            try:
                found = match.group().decode("utf-8")
            except UnicodeDecodeError:
                pass
            else:
                if katana.util.isprintable(found):
                    # Strict flags means that the flag will be alone in the output
                    if (
                        unit is not None
                        and unit.STRICT_FLAGS
                        and len(found) == len(data)
                    ):
                        self.register_flag(unit, found)
                        return True
                    elif unit is None or not unit.STRICT_FLAGS:
                        self.register_flag(unit, found)
                        return True

        return False

    def target(
        self,
        upstream: bytes,
        parent: Unit = None,
        config: configparser.ConfigParser = None,
    ) -> Target:
        """ Build a new target in the context of this manager """
        t = Target(self, upstream, parent, config=config)
        return t

    def validate(self) -> None:
        """ Validate the configuration given this manager, a target, and a set
        of chosen units you are going to run. Not verify the validity could
        cause unexpected errors later when running your units """

        # Ensure the required global values are present in the configuration
        if "flag-format" not in self["manager"]:
            raise RuntimeError("manager: flag-format not specified")

        self.finder.validate()

    def queue_target(
        self,
        upstream: bytes,
        parent: Unit = None,
        scale: float = None,
        config: configparser.ConfigParser = None,
        background: bool = False,
    ) -> Target:
        """ Create a target, enumerate units, queue them, and return the target
        object """

        if isinstance(upstream, list) or isinstance(upstream, tuple):
            for item in upstream:
                self.queue_target(item, parent=parent)
            return None
        elif isinstance(upstream, dict):
            for key, item in upstream.items():
                self.queue_target(item, parent=parent)
            return None
        elif not isinstance(upstream, str) and not isinstance(upstream, bytes):
            upstream = repr(upstream)

        # That's silly...
        if upstream.strip() == b"" or upstream.strip() == "":
            return None

        # Don't recurse if the parent is already done
        if parent is not None:

            # Don't queue recursion for a completed target
            if parent.origin.completed:
                return None
            # Maximum depth reached!
            if (parent.depth + 1) >= parent.target.config["manager"].getint(
                "max-depth"
            ):
                self.monitor.on_depth_limit(self, parent.target, parent)
                return None

        # Scale linearly with our parent's priority
        if scale is None and parent is not None:
            scale = parent.PRIORITY / 100.0
        elif scale is None:
            # No scale defined, use 1.0
            scale = 1.0

        # Create the target object
        try:
            target = self.target(upstream, parent, config=config)
        except BadTarget:
            return None

        def _do_queue():

            # Build the target
            try:
                target.build_target()
            except BadTarget:
                target._completed = True
                return

            # Don't requeue targets with the same hash
            if target.hash.hexdigest() in self.target_hash:
                target._completed = True
                return
            else:
                self.target_hash[target.hash.hexdigest()] = target

            # Track the root targets
            # if parent is None:
            self.targets.append(target)

            # This indicates the flag was in plaintext in the content of the target
            # No need to queue units.
            if target.completed:
                return

            # Enumerate valid units
            for unit in self.finder.match(target, scale=scale):
                self.queue(unit)

            # Tell the unit we are done adding units
            target.building = False

            # If we missed this due to `building == True`, set it now
            if target.units_left <= 0:
                target.completed = True

        if background:
            # Queue the target at a later time, so we can continue (e.g. w/ REPL)
            t = threading.Thread(target=_do_queue, daemon=True).start()
        else:
            _do_queue()

        # Return the target object
        return target

    def queue(self, unit: Unit) -> None:
        """ Queue the given unit to be evaluated. This will add the unit to the
        queue given it's prioritization, and the unit will be evaluated once
        the manager is started. If the manager has already been started, the
        unit will be evaluated based on it's priority the next time a thread is
        free. """

        # Check if we are completed
        if unit.is_complete():
            return

        item = Manager.WorkItem(
            unit.PRIORITY,  # Unit priority
            "init",  # Initialization of work item
            unit,  # The unit itself
            unit.enumerate(),
        )  # The generator to get the next case

        # Increment unit count for target
        unit.origin.add_unit()

        # Queue the item for usage
        self.work.put(item)

        # Ensure sleeping threads wake up
        if self.barrier is not None:
            self.barrier.reset()

    def requeue(self, item: WorkItem) -> None:
        """ Requeue an item which has more cases left to evaluate """

        # Don't requeue completed items
        if item.unit.is_complete():
            return

        # We aren't initializing anymore
        # item.action = "evaluate"

        # Requeue the item
        self.work.put(item)

        if self.barrier is not None:
            self.barrier.reset()

    def start(self) -> None:
        """ Start the needed threads and begin evaluation of units. You can
        still add units to the queue for evaluation after start is called up
        until you call `Manager.join`.

        Targets can continue to be added up to the point that you call join.
        After that, any new target addition will generate an exception, unless
        there is a parent unit specified (aka, the target is due to recursion).
        """

        # Prepare the results directory
        self._prepare_results()

        # Validate the configuration items are valid and there will be no
        # issues moving forward
        self.validate()

        # Create the barrier object
        self.barrier = threading.Barrier(self["manager"].getint("threads") + 1)
        self.threads = [None] * self["manager"].getint("threads")
        self.running = True

        # Start the threads (will automatically begin processing units)
        for n in range(len(self.threads)):
            self.threads[n] = threading.Thread(target=self._thread, args=(n,))
            self.threads[n].start()

    def join(self, timeout=None) -> bool:
        """ Wait for all work to complete. Depending on your Finder and Target,
        this may take some time, and may time out before completion.

        After joining, no more root targets (those without parents) can be
        queued (this will result in an exception). One all targets have
        finished processing (including recursion/child targets), join will
        return.

        """

        # Ensure we are running
        if not self.running:
            return True

        # Record starting and expected ending time to comply with timeout
        if timeout is not None:
            join_time = time.time()
            stop_time = join_time + timeout
        # Indicates we have already requested threads to cleanly exit
        aborting = True
        # Timeout was hit
        did_timeout = False

        while True:

            try:
                # Wait for all threads to meet the barrier, which indicates all
                # unit/case pairs are processed
                if timeout is not None:
                    self.barrier.wait(stop_time - time.time())
                else:
                    self.barrier.wait()
            except threading.BrokenBarrierError:
                pass
            except KeyboardInterrupt:

                # If we have already signaled, and we catch another
                # Ctrl+C, just exit and let the user force quit at the
                # threading `join` call below
                if aborting is True:
                    break
                # Signal threads to exit cleanly after current unit/case pair
                # evaluation is completed.
                self._signal_complete()
                aborting = True
            else:
                # Just in case, we signal completion, but all threads should
                # exit when the barrier is reached successfully
                self._signal_complete()
                break

            # Signal completion if our timeout has expired
            if timeout is not None and time.time() >= stop_time:
                did_timeout = True
                self._signal_complete()
                break

        # Make sure no one calls abort
        self.running = False

        # Release all threads
        self._signal_complete()
        self.barrier.reset()

        # Wait on all threads to complete
        for thread in self.threads:
            thread.join()

        # Notify the monitor that we are done
        self.monitor.on_completion(self, did_timeout)

        return not did_timeout

    def abort(self) -> None:
        """ Signal completion to all threads, then wait for exit """

        # Ensure there is something to do
        if not self.running:
            return

        # Signal threads to exit, and then wait for it to happen
        self._signal_complete()
        for thread in self.threads:
            thread.join()

        self.monitor.on_completion(self, True)

    def _signal_complete(self) -> None:
        """ Send work items with high priority to signal closing down threads
        """

        for thread in self.threads:
            self.work.put(
                Manager.WorkItem(
                    -10000, "abort", None, None  # Priority  # Action  # Unit
                )
            )  # Generator

        # Make all the workers wake up and grab these events
        self.barrier.reset()

    def _thread(self, thread) -> None:
        """ This is the main method for each evaluator thread. It will monitor
        the work queue, and evaluate units as they become available. The
        threads are started by the ``Manager.start`` method. """

        while True:

            try:
                # Attempt to grab work from the queue
                work: Manager.WorkItem = self.work.get(False)
            except queue.Empty:
                try:
                    # Signal this thread is waiting for work
                    # check again every 0.2 seconds, just in case
                    self.monitor.on_work(self, thread, None, None)
                    self.barrier.wait()
                except threading.BrokenBarrierError:
                    # A new unit was queued or the timeout happened
                    # Check for new units
                    continue
                else:
                    # All threads hit the barrier, we are free to exit
                    break

            # The parent is asking nicely to exit
            if work.action == "abort":
                self.work.task_done()
                break

            # Ignore the unit if it is already completed
            if work.unit.is_complete():
                work.unit.origin.rem_unit()
                self.work.task_done()
                continue

            # if work.action == "init":
            # This is the first time the unit has run, so we need to
            # initialize the generator for cases
            #    work.generator = work.unit.enumerate()

            # We have a unit to process, grab the next case
            cases = []
            empty = False

            # This is a weird thing to do, since the queue is already protected by a lock...
            # However, this ensures when we pull items off the queue and re-insert them that
            # the priority will be maintained (otherwise another thread may grab a lower
            # unit off the queue while this one is gone)
            with self.lock:
                try:
                    for i in range(10):
                        try:
                            case = next(work.generator)
                        except StopIteration:
                            empty = True
                            break
                        cases.append(case)
                except Exception as e:
                    self.monitor.on_exception(self, work.unit, e)
                    self.work.task_done()
                    continue

                # Before we evaluate, place this case back on the queue in order to
                # allow parallel processing of the cases
                if not empty:
                    self.requeue(work)

            for case in cases:
                # Notify the monitor of thread status (this should be a very short
                # call because it can easily slow down processing!!!)
                self.monitor.on_work(self, thread, work.unit, case)

                try:
                    # Evaluate this case
                    work.unit.evaluate(case)
                except Exception as e:
                    # We got an exception, notify the monitor and continue
                    self.monitor.on_exception(self, work.unit, e)

                # Statistics
                work.unit.origin.units_evaluated += 1
                if work.unit.target is not work.unit.origin:
                    work.unit.target.units_evaluated += 1
                self.cases_completed += 1

            if empty:
                work.unit.origin.rem_unit()

            self.work.task_done()

    def _prepare_results(self) -> None:
        """ Prepare the results directory to house all artifacts and results
        from this run of katana. This is automatically called when `start` is
        executed, and will create the output directory.

        This function will raise an exception if the chosen output directory
        already exists. """

        if os.path.isdir(self["manager"]["outdir"]) and self["manager"].getboolean(
            "force"
        ):
            shutil.rmtree(self["manager"]["outdir"])
        elif os.path.isdir(self["manager"]["outdir"]):
            rm_outdir = input("Do you want to delete prior results [y/N]: ")
            if rm_outdir.lower() == "y" or rm_outdir.lower() == "yes":
                shutil.rmtree(self["manager"]["outdir"])
            else:
                sys.exit()

        # Create the directory tree for the output
        os.makedirs(self["manager"]["outdir"])
