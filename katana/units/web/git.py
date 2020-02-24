"""
Git Dumper

This unit will detect if a ``/.git/`` directory is found on a website.
If it is, it will pull down all the files and search for flags within
the commits and objects inside of the public facing git repository.

This process is threaded, alongside Katana already being threaded...
so your mileage may vary.

This unit inherits from :class:`katana.units.web.WebUnit` as that contains
lots of predefined variables that can be used throughout multiple web units.

.. note::  

    This code is shamelessly ripped from https://github.com/arthaud/git-dumper

"""


import multiprocessing
import os
import os.path
import re
import shutil
import socket
import subprocess
import tempfile
import urllib.parse

from contextlib import closing
from hashlib import md5

import bs4
import dulwich.index
import dulwich.objects
import dulwich.pack
import requests
import socks

from typing import Any

import re
from katana.units.web import WebUnit
from katana.unit import NotApplicable


def is_html(response):
    """ Return True if the response is a HTML webpage """
    return "<html>" in response.text


def get_indexed_files(response):
    """
    Part of the Git Dumper procedure.

    Return all the files in the directory index webpage.
    """
    html = bs4.BeautifulSoup(response.text, "html.parser")
    files = []

    for link in html.find_all("a"):
        url = urllib.parse.urlparse(link.get("href"))

        if (
            url.path
            and url.path != "."
            and url.path != ".."
            and not url.path.startswith("/")
            and not url.scheme
            and not url.netloc
        ):
            files.append(url.path)

    return files


def create_intermediate_dirs(path):
    """
    Part of the Git Dumper procedure.

    Create intermediate directories, if necessary
    """

    dirname, basename = os.path.split(path)

    if dirname and not os.path.exists(dirname):
        try:
            os.makedirs(dirname)
        except FileExistsError:
            pass  # race condition


def get_referenced_sha1(obj_file):
    """
    Part of the Git Dumper procedure.

    Return all the referenced SHA1 in the given object file
    """
    objs = []

    if isinstance(obj_file, dulwich.objects.Commit):
        objs.append(obj_file.tree.decode())

        for parent in obj_file.parents:
            objs.append(parent.decode())
    elif isinstance(obj_file, dulwich.objects.Tree):
        for item in obj_file.iteritems():
            objs.append(item.sha.decode())
    elif isinstance(obj_file, dulwich.objects.Blob):
        pass  # Ignore these.
    else:
        pass  # Ignore these.

    return objs


class Worker(multiprocessing.Process):
    """
    Part of the Git Dumper procedure.

    Worker for process_tasks 
    """

    def __init__(self, pending_tasks, tasks_done, args):
        super().__init__()
        self.daemon = True
        self.pending_tasks = pending_tasks
        self.tasks_done = tasks_done
        self.args = args

    def run(self):
        # initialize process
        self.init(*self.args)

        # fetch and do tasks
        while True:
            task = self.pending_tasks.get(block=True)

            if task is None:  # end signal
                return

            result = self.do_task(task, *self.args)

            assert isinstance(result, list), "do_task() should return a list of tasks"

            self.tasks_done.put(result)

    def init(self, *args):
        raise NotImplementedError

    def do_task(self, task, *args):
        raise NotImplementedError


def process_tasks(initial_tasks, worker, jobs, args=(), tasks_done=None):
    """
    Part of the Git Dumper procedure.

    Process tasks in parallel.
    """

    if not initial_tasks:
        return

    tasks_seen = set(tasks_done) if tasks_done else set()
    pending_tasks = multiprocessing.Queue()
    tasks_done = multiprocessing.Queue()
    num_pending_tasks = 0

    # add all initial tasks in the queue
    for task in initial_tasks:
        assert task is not None

        if task not in tasks_seen:
            pending_tasks.put(task)
            num_pending_tasks += 1
            tasks_seen.add(task)

    # initialize processes
    processes = [worker(pending_tasks, tasks_done, args) for _ in range(jobs)]

    # launch them all
    for p in processes:
        p.start()

    # collect task results
    while num_pending_tasks > 0:
        task_result = tasks_done.get()
        num_pending_tasks -= 1

        for task in task_result:
            assert task is not None

            if task not in tasks_seen:
                pending_tasks.put(task)
                num_pending_tasks += 1
                tasks_seen.add(task)

    # send termination signal (task=None)
    for _ in range(jobs):
        pending_tasks.put(None)

    # join all
    for p in processes:
        p.join()


class DownloadWorker(Worker):
    """
    Part of the Git Dumper procedure.

    Download a list of files
    """

    def __init__(self, pending_tasks, tasks_done, args):
        super().__init__(pending_tasks, tasks_done, args)
        # self.unit = unit
        self.session = requests.Session()

    def init(self, url, directory, retry, timeout, unit, katana):
        self.session.verify = False
        self.session.mount(url, requests.adapters.HTTPAdapter(max_retries=retry))

    def do_task(self, filepath, url, directory, retry, timeout, unit, katana):
        with closing(
            self.session.get(
                "%s/%s" % (url, filepath),
                allow_redirects=False,
                stream=True,
                timeout=timeout,
            )
        ) as response:

            if response.status_code != 200:
                return []

            abspath = os.path.abspath(os.path.join(directory, filepath))
            create_intermediate_dirs(abspath)

            # write file
            with open(abspath, "wb") as f:
                for chunk in response.iter_content(4096):
                    f.write(chunk)

            return []


class RecursiveDownloadWorker(DownloadWorker):
    """
    Part of the Git Dumper procedure.

    Download a directory recursively.
    """

    def do_task(self, filepath, url, directory, retry, timeout, unit, katana):
        with closing(
            self.session.get(
                "%s/%s" % (url, filepath),
                allow_redirects=False,
                stream=True,
                timeout=timeout,
            )
        ) as response:

            if (
                response.status_code in (301, 302)
                and "Location" in response.headers
                and response.headers["Location"].endswith(filepath + "/")
            ):
                return [filepath + "/"]

            if response.status_code != 200:
                return []

            if filepath.endswith("/"):  # directory index
                assert is_html(response)

                return [filepath + filename for filename in get_indexed_files(response)]
            else:  # file
                abspath = os.path.abspath(os.path.join(directory, filepath))
                create_intermediate_dirs(abspath)

                # write file
                with open(abspath, "wb") as f:
                    for chunk in response.iter_content(4096):
                        f.write(chunk)

                return []


class FindRefsWorker(DownloadWorker):
    """
    Part of the Git Dumper procedure.

    Find refs/
    """

    def do_task(self, filepath, url, directory, retry, timeout, unit, katana):
        response = self.session.get(
            "%s/%s" % (url, filepath), allow_redirects=False, timeout=timeout
        )

        if response.status_code != 200:
            return []

        abspath = os.path.abspath(os.path.join(directory, filepath))
        create_intermediate_dirs(abspath)

        # write file
        with open(abspath, "w") as f:
            f.write(response.text)

        # find refs
        tasks = []

        for ref in re.findall(r"(refs(/[a-zA-Z0-9\-\.\_\*]+)+)", response.text):
            ref = ref[0]
            if not ref.endswith("*"):
                tasks.append(".git/%s" % ref)
                tasks.append(".git/logs/%s" % ref)

        return tasks


class FindObjectsWorker(DownloadWorker):
    """
    Part of the Git Dumper procedure.

    Find objects.
    """

    def do_task(self, obj, url, directory, retry, timeout, unit, katana):
        filepath = ".git/objects/%s/%s" % (obj[:2], obj[2:])
        response = self.session.get(
            "%s/%s" % (url, filepath), allow_redirects=False, timeout=timeout
        )
        # Fetching %s/%s [%d]\n', url, filepath, response.status_code

        if response.status_code != 200:
            return []

        abspath = os.path.abspath(os.path.join(directory, filepath))
        create_intermediate_dirs(abspath)

        # write file
        with open(abspath, "wb") as f:
            f.write(response.content)

        # parse object file to find other objects
        obj_file = dulwich.objects.ShaFile.from_path(abspath)
        return get_referenced_sha1(obj_file)


def fetch_git(unit, url, directory, jobs, retry, timeout, katana):
    """ 
    Dump a .git repository into the output directory. 

    This is the core function of the https://github.com/arthaud/git-dumper
    code.
    """

    assert os.path.isdir(directory), "%s is not a directory" % directory
    assert not os.listdir(directory), "%s is not empty" % directory
    assert jobs >= 1, "invalid number of jobs"
    assert retry >= 1, "invalid number of retries"
    assert timeout >= 1, "invalid timeout"
    # find base url
    url = url.rstrip("/")
    if url.endswith("HEAD"):
        url = url[:-4]
    url = url.rstrip("/")
    if url.endswith(".git"):
        url = url[:-4]
    url = url.rstrip("/")

    # check for /.git/HEAD
    response = requests.get("%s/.git/HEAD" % url, verify=False, allow_redirects=False)

    if response.status_code != 200:
        # error: %s/.git/HEAD does not exist\n', url, file=sys.stderr
        return 1
    elif not response.text.startswith("ref:"):
        # error: %s/.git/HEAD is not a git HEAD file\n', url, file=sys.stderr
        return 1

    # check for directory listing
    # Testing /.git/
    response = requests.get("%s/.git/" % url, verify=False, allow_redirects=False)

    if (
        response.status_code == 200
        and is_html(response)
        and "HEAD" in get_indexed_files(response)
    ):
        # Fetching .git recursively
        process_tasks(
            [".git/", ".gitignore"],
            RecursiveDownloadWorker,
            jobs,
            args=(url, directory, retry, timeout, unit, katana),
        )

        # run git checkout
        subprocess.check_call(["git", "checkout", "."], cwd=directory)
        return 0

    # no directory listing
    # Fetching common files
    tasks = [
        ".gitignore",
        ".git/COMMIT_EDITMSG",
        ".git/description",
        ".git/hooks/applypatch-msg.sample",
        ".git/hooks/applypatch-msg.sample",
        ".git/hooks/applypatch-msg.sample",
        ".git/hooks/commit-msg.sample",
        ".git/hooks/post-commit.sample",
        ".git/hooks/post-receive.sample",
        ".git/hooks/post-update.sample",
        ".git/hooks/pre-applypatch.sample",
        ".git/hooks/pre-commit.sample",
        ".git/hooks/pre-push.sample",
        ".git/hooks/pre-rebase.sample",
        ".git/hooks/pre-receive.sample",
        ".git/hooks/prepare-commit-msg.sample",
        ".git/hooks/update.sample",
        ".git/index",
        ".git/info/exclude",
        ".git/objects/info/packs",
    ]
    process_tasks(
        tasks, DownloadWorker, jobs, args=(url, directory, retry, timeout, unit, katana)
    )

    # find refs
    tasks = [
        ".git/FETCH_HEAD",
        ".git/HEAD",
        ".git/ORIG_HEAD",
        ".git/config",
        ".git/info/refs",
        ".git/logs/HEAD",
        ".git/logs/refs/heads/master",
        ".git/logs/refs/remotes/origin/HEAD",
        ".git/logs/refs/remotes/origin/master",
        ".git/logs/refs/stash",
        ".git/packed-refs",
        ".git/refs/heads/master",
        ".git/refs/remotes/origin/HEAD",
        ".git/refs/remotes/origin/master",
        ".git/refs/stash",
    ]

    process_tasks(
        tasks, FindRefsWorker, jobs, args=(url, directory, retry, timeout, unit, katana)
    )

    # find packs
    tasks = []

    # use .git/objects/info/packs to find packs
    info_packs_path = os.path.join(directory, ".git", "objects", "info", "packs")
    if os.path.exists(info_packs_path):
        with open(info_packs_path) as f:
            info_packs = f.read()

        for sha1 in re.findall(r"pack-([a-f0-9]{40})\.pack", info_packs):
            tasks.append(".git/objects/pack/pack-%s.idx" % sha1)
            tasks.append(".git/objects/pack/pack-%s.pack" % sha1)

    process_tasks(
        tasks, DownloadWorker, jobs, args=(url, directory, retry, timeout, unit, katana)
    )

    # find objects
    objs = set()
    packed_objs = set()

    # .git/packed-refs, .git/info/refs, .git/refs/*, .git/logs/*
    files = [
        os.path.join(directory, ".git", "packed-refs"),
        os.path.join(directory, ".git", "info", "refs"),
        os.path.join(directory, ".git", "FETCH_HEAD"),
        os.path.join(directory, ".git", "ORIG_HEAD"),
    ]
    for dirpath, _, filenames in os.walk(os.path.join(directory, ".git", "refs")):
        for filename in filenames:
            files.append(os.path.join(dirpath, filename))
    for dirpath, _, filenames in os.walk(os.path.join(directory, ".git", "logs")):
        for filename in filenames:
            files.append(os.path.join(dirpath, filename))

    for filepath in files:
        if not os.path.exists(filepath):
            continue

        with open(filepath) as f:
            content = f.read()

        for obj in re.findall(r"(^|\s)([a-f0-9]{40})($|\s)", content):
            obj = obj[1]
            objs.add(obj)

    # use .git/index to find objects
    index_path = os.path.join(directory, ".git", "index")
    if os.path.exists(index_path):
        index = dulwich.index.Index(index_path)

        for entry in index.iterblobs():
            objs.add(entry[1].decode())

    # use packs to find more objects to fetch, and objects that are packed
    pack_file_dir = os.path.join(directory, ".git", "objects", "pack")
    if os.path.isdir(pack_file_dir):
        for filename in os.listdir(pack_file_dir):
            if filename.startswith("pack-") and filename.endswith(".pack"):
                pack_data_path = os.path.join(pack_file_dir, filename)
                pack_idx_path = os.path.join(pack_file_dir, filename[:-5] + ".idx")
                pack_data = dulwich.pack.PackData(pack_data_path)
                pack_idx = dulwich.pack.load_pack_index(pack_idx_path)
                pack = dulwich.pack.Pack.from_objects(pack_data, pack_idx)

                for obj_file in pack.iterobjects():
                    packed_objs.add(obj_file.sha().hexdigest())
                    objs |= set(get_referenced_sha1(obj_file))

    # fetch all objects
    process_tasks(
        objs,
        FindObjectsWorker,
        jobs,
        args=(url, directory, retry, timeout, unit, katana),
        tasks_done=packed_objs,
    )

    # ignore errors

    subprocess.call(
        ["git", "checkout", "."], stderr=open(os.devnull, "wb"), cwd=directory
    )
    return 0


# -----------------------------------------------


bad_starting_links = [b"#", b"javascript:", b"https://", b"http://", b"//"]
"""
This is a blacklist to avoid inline JavaScript, anchors, and external links..
"""


def has_a_bad_start(link):
    """
    This is a convenience function just to avoid bad links above
    """
    for bad_start in bad_starting_links:
        if link.startswith(bad_start):
            return False
    else:
        return True


class Unit(WebUnit):

    PRIORITY = 40
    """
    Priority works with 0 being the highest priority, and 100 being the 
    lowest priority. 50 is the default priorty. This unit has a somewhat
    higher priority.
    """

    GROUPS = ["web", "git"]
    """
    These are "tags" for a unit. Considering it is a Web unit, "web"
    is included, as well as the name of the unit, "git".
    """

    RECURSE_SELF = False
    """
    This unit should not recurse into itself. It would make no sense.
    """

    # If find a downloadable file, uh, just leave it alone
    BAD_MIME_TYPES = ["application/octet-stream"]

    def __init__(self, *args, **kwargs):
        super(Unit, self).__init__(*args, **kwargs)

        # Grab the configuration data
        self.git_proxy = self.get("proxy", default="")
        self.git_jobs = self.geti("jobs", default=10)
        self.git_timeout = self.geti("git_timeout", default=3)
        self.git_retry = self.geti("git_retry", default=3)
        self.flag_format = self.manager.flag_pattern.pattern.decode("utf-8")

        # Validate these configs to ensure they make sense
        if self.git_jobs < 1:
            raise NotApplicable("invalid number of git-jobs")

        # retry validation
        if self.git_retry < 1:
            raise NotApplicable("invalid number of git-retries")

        # timeout validation
        if self.git_timeout < 1:
            raise NotApplicable("invalid git timeout")

        # proxy validation
        if self.git_proxy:
            proxy_valid = False

            for pattern, proxy_type in [
                (r"^socks5:(.*):(\d+)$", socks.PROXY_TYPE_SOCKS5),
                (r"^socks4:(.*):(\d+)$", socks.PROXY_TYPE_SOCKS4),
                (r"^http://(.*):(\d+)$", socks.PROXY_TYPE_HTTP),
                (r"^(.*):(\d+)$", socks.PROXY_TYPE_SOCKS5),
            ]:
                m = re.match(pattern, self.git_proxy)
                if m:
                    socks.setdefaultproxy(proxy_type, m.group(1), int(m.group(2)))
                    socket.socket = socks.socksocket
                    proxy_valid = True
                    break

            if not proxy_valid:
                raise NotApplicable("invalid git proxy")

        # Try to get see if there is a .git directory
        url = "{0}/{1}".format(self.target.url_root.rstrip("/"), ".git/HEAD")

        try:
            r = requests.get(url, allow_redirects=False)
        except (requests.exceptions.ConnectionError,):
            raise NotApplicable("cannot reach server")

        # If the response is anything other than a "Not Found",
        # we might have something here...
        if r.status_code == 404:
            raise NotApplicable("http response 404 at /.git/HEAD")
        else:
            self.response = r

    def evaluate(self, case: Any):
        """
        Evaluate the target. If a ``.git`` repository is found, download
        it and look through all of the objects for a flag.

        :param case: A case returned by ``enumerate``. For this unit,\
        the ``enumerate`` function is not used.

        :return: None. This function should not return any data.

        """

        # Keep track of seen files for the target
        self.target.seen_files = []

        temp_folder = tempfile.gettempdir()
        git_directory = tempfile.mkdtemp()

        # Download the repository
        try:
            fetch_git(
                self,
                self.target.url_root,
                git_directory,
                self.git_jobs,
                self.git_retry,
                self.git_timeout,
                self.manager,
            )
        except AssertionError as e:
            return  # something went wrong. stop.

        # Do a basic grep for flags
        grep = subprocess.run(
            "git grep -P {}".format(self.flag_format).split(),
            cwd=git_directory,
            stdout=subprocess.PIPE,
        )
        if self.manager.find_flag(self, grep.stdout):
            self.completed = True
            return

        # Start to look at the commit messages...
        grep = subprocess.run(
            "git log --pretty=oneline".split(),
            cwd=git_directory,
            stdout=subprocess.PIPE,
        )

        line_number = 0
        first_commit = ""

        for line in grep.stdout.decode("utf-8").split("\n"):
            commit, commit_message = line.split(" ")[0], " ".join(line.split(" ")[1:])
            if line_number == 0:
                first_commit = commit

            # Add the commit data
            self.manager.register_data(
                self, f"commit {commit[:6]}: {commit_message}", recurse=False
            )

            # If you find a flag in the commit message, STOP this unit!
            if self.manager.find_flag(self, commit_message):
                return

            # -----------------------------------------------------------------
            # JOHN: This next procedure is HEAVY
            #       It loops through every commit, grabs files and recurses
            #       on EVERY NEW FILE it finds.... soooooo
            #       I limit this to only run if a flag file is specified.
            if self.manager.flag_pattern:
                commit_data = subprocess.run(
                    f"git checkout {commit}".split(),
                    cwd=git_directory,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                # Look through all the files in the current commit
                for (directory, dirs, files) in os.walk(git_directory):
                    # Ignore the .git directory for god's sake
                    dirs[:] = [d for d in dirs if d not in [".git"]]

                    for filename in files:
                        file_path = os.path.join(directory, filename)

                        # Hash the file to make sure if we have not seen it before
                        path_hash = md5(open(file_path, "rb").read()).hexdigest()

                        if path_hash not in self.target.seen_files:
                            temp_path = os.path.join(temp_folder, path_hash)
                            shutil.move(file_path, temp_path)
                            self.manager.register_data(self, temp_path)
                            self.target.seen_files.append(path_hash)

                line_number += 1

            commit_data = subprocess.run(
                f"git checkout {first_commit}".split(),
                cwd=git_directory,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
