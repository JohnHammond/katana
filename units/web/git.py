#!/usr/bin/env python3
from pwn import *
import requests
from units import NotApplicable
from web import WebUnit

#!/usr/bin/env python3
from contextlib import closing
import argparse
import multiprocessing
import os
import os.path
import re
import socket
import subprocess
import sys
import urllib.parse

import bs4
import dulwich.index
import dulwich.objects
import dulwich.pack
import requests
import socks
from hashlib import md5
import tempfile
import shutil

DEPENDENCIES = ['git']

def printf(a):
	# print(a)
	pass

# JOHN: The code below is shamelessly ripped from 
# https://github.com/arthaud/git-dumper

def is_html(response):
	''' Return True if the response is a HTML webpage '''
	return '<html>' in response.text


def get_indexed_files(response):
	''' Return all the files in the directory index webpage '''
	html = bs4.BeautifulSoup(response.text, 'html.parser')
	files = []

	for link in html.find_all('a'):
		url = urllib.parse.urlparse(link.get('href'))

		if (url.path and
				url.path != '.' and
				url.path != '..' and
				not url.path.startswith('/') and
				not url.scheme and
				not url.netloc):
			files.append(url.path)

	return files


def create_intermediate_dirs(path):
	''' Create intermediate directories, if necessary '''

	dirname, basename = os.path.split(path)

	if dirname and not os.path.exists(dirname):
		try:
			os.makedirs(dirname)
		except FileExistsError:
			pass # race condition


def get_referenced_sha1(obj_file):
	''' Return all the referenced SHA1 in the given object file '''
	objs = []

	if isinstance(obj_file, dulwich.objects.Commit):
		objs.append(obj_file.tree.decode())

		for parent in obj_file.parents:
			objs.append(parent.decode())
	elif isinstance(obj_file, dulwich.objects.Tree):
		for item in obj_file.iteritems():
			objs.append(item.sha.decode())
	elif isinstance(obj_file, dulwich.objects.Blob):
		pass
	else:
		pass
		# JOHN: Don't break. Just ignore.
		# printf('error: unexpected object type: %r\n' % obj_file, file=sys.stderr)
		# sys.exit(1)

	return objs


class Worker(multiprocessing.Process):
	''' Worker for process_tasks '''

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

			if task is None: # end signal
				return

			result = self.do_task(task, *self.args)

			assert isinstance(result, list), 'do_task() should return a list of tasks'

			self.tasks_done.put(result)

	def init(self, *args):
		raise NotImplementedError

	def do_task(self, task, *args):
		raise NotImplementedError


def process_tasks(initial_tasks, worker, jobs, args=(), tasks_done=None):
	''' Process tasks in parallel '''

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
		task_result = tasks_done.get(block=True)
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
	''' Download a list of files '''

	def init(self, url, directory, retry, timeout, unit, katana):
		self.unit = unit
		self.session = requests.Session()
		self.session.verify = False
		self.session.mount(url, requests.adapters.HTTPAdapter(max_retries=retry))

	def do_task(self, filepath, url, directory, retry, timeout, unit, katana):
		with closing(self.session.get('%s/%s' % (url, filepath),
									  allow_redirects=False,
									  stream=True,
									  timeout=timeout)) as response:
			# printf('[-] Fetching %s/%s [%d]\n', url, filepath, response.status_code)

			if response.status_code != 200:
				return []

			abspath = os.path.abspath(os.path.join(directory, filepath))
			create_intermediate_dirs(abspath)

			# write file
			with open(abspath, 'wb') as f:
				for chunk in response.iter_content(4096):
					f.write(chunk)

			return []


class RecursiveDownloadWorker(DownloadWorker):
	''' Download a directory recursively '''

	def do_task(self, filepath, url, directory, retry, timeout, unit, katana):
		with closing(self.session.get('%s/%s' % (url, filepath),
									  allow_redirects=False,
									  stream=True,
									  timeout=timeout)) as response:
			# printf('[-] Fetching %s/%s [%d]\n', url, filepath, response.status_code)

			if (response.status_code in (301, 302) and
					'Location' in response.headers and
					response.headers['Location'].endswith(filepath + '/')):
				return [filepath + '/']

			if response.status_code != 200:
				return []

			if filepath.endswith('/'): # directory index
				assert is_html(response)

				return [filepath + filename for filename in get_indexed_files(response)]
			else: # file
				abspath = os.path.abspath(os.path.join(directory, filepath))
				create_intermediate_dirs(abspath)

				# write file
				with open(abspath, 'wb') as f:
					for chunk in response.iter_content(4096):
						f.write(chunk)

				return []


class FindRefsWorker(DownloadWorker):
	''' Find refs/ '''

	def do_task(self, filepath, url, directory, retry, timeout, unit, katana):
		response = self.session.get('%s/%s' % (url, filepath),
									allow_redirects=False,
									timeout=timeout)
		# printf('[-] Fetching %s/%s [%d]\n', url, filepath, response.status_code)

		if response.status_code != 200:
			return []

		abspath = os.path.abspath(os.path.join(directory, filepath))
		create_intermediate_dirs(abspath)

		# write file
		with open(abspath, 'w') as f:
			f.write(response.text)


		# find refs
		tasks = []

		for ref in re.findall(r'(refs(/[a-zA-Z0-9\-\.\_\*]+)+)', response.text):
			ref = ref[0]
			if not ref.endswith('*'):
				tasks.append('.git/%s' % ref)
				tasks.append('.git/logs/%s' % ref)

		return tasks


class FindObjectsWorker(DownloadWorker):
	''' Find objects '''

	def do_task(self, obj, url, directory, retry, timeout, unit, katana):
		filepath = '.git/objects/%s/%s' % (obj[:2], obj[2:])
		response = self.session.get('%s/%s' % (url, filepath),
									allow_redirects=False,
									timeout=timeout)
		# printf('[-] Fetching %s/%s [%d]\n', url, filepath, response.status_code)

		if response.status_code != 200:
			return []

		abspath = os.path.abspath(os.path.join(directory, filepath))
		create_intermediate_dirs(abspath)

		# write file
		with open(abspath, 'wb') as f:
			f.write(response.content)
		

		# parse object file to find other objects
		obj_file = dulwich.objects.ShaFile.from_path(abspath)
		return get_referenced_sha1(obj_file)


def fetch_git( unit, url, directory, jobs, retry, timeout, katana):
	''' Dump a git repository into the output directory '''

	assert os.path.isdir(directory), '%s is not a directory' % directory
	assert not os.listdir(directory), '%s is not empty' % directory
	assert jobs >= 1, 'invalid number of jobs'
	assert retry >= 1, 'invalid number of retries'
	assert timeout >= 1, 'invalid timeout'

	# find base url
	url = url.rstrip('/')
	if url.endswith('HEAD'):
		url = url[:-4]
	url = url.rstrip('/')
	if url.endswith('.git'):
		url = url[:-4]
	url = url.rstrip('/')

	# check for /.git/HEAD
	# printf('[-] Testing %s/.git/HEAD ', url)
	response = requests.get('%s/.git/HEAD' % url, verify=False, allow_redirects=False)
	# printf('[%d]\n', response.status_code)

	if response.status_code != 200:
		# printf('error: %s/.git/HEAD does not exist\n', url, file=sys.stderr)
		return 1
	elif not response.text.startswith('ref:'):
		# printf('error: %s/.git/HEAD is not a git HEAD file\n', url, file=sys.stderr)
		return 1

	# check for directory listing
	# printf('[-] Testing %s/.git/ ', url)
	response = requests.get('%s/.git/' % url, verify=False, allow_redirects=False)
	# printf('[%d]\n', response.status_code)

	if response.status_code == 200 and is_html(response) and 'HEAD' in get_indexed_files(response):
		printf('[-] Fetching .git recursively\n')
		process_tasks(['.git/', '.gitignore'],
					  RecursiveDownloadWorker,
					  jobs,
					  args=(url, directory, retry, timeout, unit, katana))

		printf('[-] Running git checkout .\n')
		# os.chdir(directory)
		subprocess.check_call(['git', 'checkout', '.'], cwd = directory)
		return 0

	# no directory listing
	printf('[-] Fetching common files\n')
	tasks = [
		'.gitignore',
		'.git/COMMIT_EDITMSG',
		'.git/description',
		'.git/hooks/applypatch-msg.sample',
		'.git/hooks/applypatch-msg.sample',
		'.git/hooks/applypatch-msg.sample',
		'.git/hooks/commit-msg.sample',
		'.git/hooks/post-commit.sample',
		'.git/hooks/post-receive.sample',
		'.git/hooks/post-update.sample',
		'.git/hooks/pre-applypatch.sample',
		'.git/hooks/pre-commit.sample',
		'.git/hooks/pre-push.sample',
		'.git/hooks/pre-rebase.sample',
		'.git/hooks/pre-receive.sample',
		'.git/hooks/prepare-commit-msg.sample',
		'.git/hooks/update.sample',
		'.git/index',
		'.git/info/exclude',
		'.git/objects/info/packs',
	]
	process_tasks(tasks,
				  DownloadWorker,
				  jobs,
				  args=(url, directory, retry, timeout, unit, katana))

	# find refs
	printf('[-] Finding refs/\n')
	tasks = [
		'.git/FETCH_HEAD',
		'.git/HEAD',
		'.git/ORIG_HEAD',
		'.git/config',
		'.git/info/refs',
		'.git/logs/HEAD',
		'.git/logs/refs/heads/master',
		'.git/logs/refs/remotes/origin/HEAD',
		'.git/logs/refs/remotes/origin/master',
		'.git/logs/refs/stash',
		'.git/packed-refs',
		'.git/refs/heads/master',
		'.git/refs/remotes/origin/HEAD',
		'.git/refs/remotes/origin/master',
		'.git/refs/stash',
	]

	process_tasks(tasks,
				  FindRefsWorker,
				  jobs,
				  args=(url, directory, retry, timeout, unit, katana))

	# find packs
	printf('[-] Finding packs\n')
	tasks = []

	# use .git/objects/info/packs to find packs
	info_packs_path = os.path.join(directory, '.git', 'objects', 'info', 'packs')
	if os.path.exists(info_packs_path):
		with open(info_packs_path, 'r') as f:
			info_packs = f.read()

		for sha1 in re.findall(r'pack-([a-f0-9]{40})\.pack', info_packs):
			tasks.append('.git/objects/pack/pack-%s.idx' % sha1)
			tasks.append('.git/objects/pack/pack-%s.pack' % sha1)

	process_tasks(tasks,
				  DownloadWorker,
				  jobs,
				  args=(url, directory, retry, timeout, unit, katana))

	# find objects
	printf('[-] Finding objects\n')
	objs = set()
	packed_objs = set()
	
	# .git/packed-refs, .git/info/refs, .git/refs/*, .git/logs/*
	files = [
		os.path.join(directory, '.git', 'packed-refs'),
		os.path.join(directory, '.git', 'info', 'refs'),
		os.path.join(directory, '.git', 'FETCH_HEAD'),
		os.path.join(directory, '.git', 'ORIG_HEAD'),
	]
	for dirpath, _, filenames in os.walk(os.path.join(directory, '.git', 'refs')):
		for filename in filenames:
			files.append(os.path.join(dirpath, filename))
	for dirpath, _, filenames in os.walk(os.path.join(directory, '.git', 'logs')):
		for filename in filenames:
			files.append(os.path.join(dirpath, filename))

	for filepath in files:
		if not os.path.exists(filepath):
			continue

		with open(filepath, 'r') as f:
			content = f.read()

		for obj in re.findall(r'(^|\s)([a-f0-9]{40})($|\s)', content):
			obj = obj[1]
			objs.add(obj)

	# use .git/index to find objects
	index_path = os.path.join(directory, '.git', 'index')
	if os.path.exists(index_path):
		index = dulwich.index.Index(index_path)

		for entry in index.iterblobs():
			objs.add(entry[1].decode())

	# use packs to find more objects to fetch, and objects that are packed
	pack_file_dir = os.path.join(directory, '.git', 'objects', 'pack')
	if os.path.isdir(pack_file_dir):
		for filename in os.listdir(pack_file_dir):
			if filename.startswith('pack-') and filename.endswith('.pack'):
				pack_data_path = os.path.join(pack_file_dir, filename)
				pack_idx_path = os.path.join(pack_file_dir, filename[:-5] + '.idx')
				pack_data = dulwich.pack.PackData(pack_data_path)
				pack_idx = dulwich.pack.load_pack_index(pack_idx_path)
				pack = dulwich.pack.Pack.from_objects(pack_data, pack_idx)

				for obj_file in pack.iterobjects():
					packed_objs.add(obj_file.sha().hexdigest())
					objs |= set(get_referenced_sha1(obj_file))

	# fetch all objects
	printf('[-] Fetching objects\n')
	process_tasks(objs,
				  FindObjectsWorker,
				  jobs,
				  args=(url, directory, retry, timeout, unit, katana),
				  tasks_done=packed_objs)

	# git checkout
	printf('[-] Running git checkout .\n')
	# os.chdir(directory)

	# ignore errors

	subprocess.call(['git', 'checkout', '.'], stderr=open(os.devnull, 'wb'), cwd = directory)
	return 0


# JOHN: March 24th
# I'm not going to finish implementing the actual download
# of a github repo right now -- but will check to see if
# one exists
# Code ideas come from: https://github.com/internetwache/GitTools/

class Unit(WebUnit):

	PRIORITY = 40

	@classmethod
	def add_arguments(cls, katana, parser):

			# parser.add_argument('url', metavar='URL',
			# 			help='url')
			# parser.add_argument('directory', metavar='DIR',
			# 					help='output directory')
			parser.add_argument('--git-proxy',
								help='use the specified proxy')
			parser.add_argument( '--git-jobs', type=int, default=10,
								help='number of simultaneous requests')
			parser.add_argument( '--git-retry', type=int, default=3,
								help='number of request attempts before giving up')
			parser.add_argument( '--git-timeout', type=int, default=3,
								help='maximum time in seconds before giving up')


	def __init__(self, katana, parent, target):

		# Run the parent constructor, to ensure this is a valid URL
		super(Unit, self).__init__(katana, parent, target)

		# jobs
		if katana.config['git_jobs'] < 1:
			raise NotApplicable('invalid number of git-jobs')

		# retry
		if katana.config['git_retry'] < 1:
			raise NotApplicable('invalid number of git-retries')

		# timeout
		if katana.config['git_timeout'] < 1:
			raise NotApplicable('invalid git timeout')

		# proxy
		if katana.config['git_proxy']:
			proxy_valid = False

			for pattern, proxy_type in [
					(r'^socks5:(.*):(\d+)$', socks.PROXY_TYPE_SOCKS5),
					(r'^socks4:(.*):(\d+)$', socks.PROXY_TYPE_SOCKS4),
					(r'^http://(.*):(\d+)$', socks.PROXY_TYPE_HTTP),
					(r'^(.*):(\d+)$', socks.PROXY_TYPE_SOCKS5)]:
				m = re.match(pattern, katana.config['git_proxy'])
				if m:
					socks.setdefaultproxy(proxy_type, m.group(1), int(m.group(2)))
					socket.socket = socks.socksocket
					proxy_valid = True
					break

			if not proxy_valid:
				raise NotApplicable('invalid git proxy')


		# Try to get see if there is a .git directory
		url = '{0}/{1}'.format(self.target.url_root.rstrip('/'), '.git/HEAD')

		try:
			r = requests.get(url, allow_redirects=False)
		except (requests.exceptions.ConnectionError,):
			raise NotApplicable('cannot reach server')

		# If the response is anything other than a "Not Found",
		# we might have something here...
		if r.status_code == 404:
			raise NotApplicable('http response 404 at /.git/HEAD')
		else:
			self.response = r
	
	def evaluate(self, katana, case):
		self.target.seen_files = []
		temp_folder = tempfile.gettempdir()

		# git_directory = katana.get_artifact_path(self)
		git_directory = tempfile.mkdtemp()
		# git_directory = git_directory.name
		
		# Download the repository
		try:
			fetch_git( self, self.target.url_root, git_directory, katana.config['git_jobs'], katana.config['git_retry'], katana.config['git_timeout'], katana)
		except AssertionError as e:
			return # something went wrong. stop.

		katana.add_artifact( self, git_directory )

		# Do a basic grep for flags
		grep = subprocess.run("git grep -P {}".format(katana.config['flag_format']).split(), cwd = git_directory, stdout = subprocess.PIPE)
		if katana.locate_flags(self, grep.stdout):
			self.completed = True
			return

		# Start to look at the commit messages...
		grep = subprocess.run("git log --pretty=oneline".split(), cwd = git_directory, stdout = subprocess.PIPE)
		
		line_number = 0
		first_commit = ""

		for line in grep.stdout.decode('utf-8').split('\n'):
			commit, commit_message = line.split(' ')[0], ' '.join(line.split(' ')[1:])
			if line_number == 0:
				first_commit = commit

			katana.add_results(self, f'commit {commit[:6]}: {commit_message}')
			# katana.recurse(self, message)
			
			if katana.locate_flags(self, commit_message):
				self.completed = True
				return 

			# -----------------------------------------------------------------
			# JOHN: This next procedure is HEAVY
			#       It loops through every commit, grabs files and recurses
			#       on EVERY NEW FILE it finds.... soooooo
			#       I limit this to only run if a flag file is specified.
			if katana.config['flag_format']:
				commit_data = subprocess.run(f"git checkout {commit}".split(), cwd = git_directory, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
				# Look through all the files in the current commit
				for (directory, dirs, files) in os.walk(git_directory, topdown=True):
					# Ignore the .git directory for god's sake
					dirs[:] = [d for d in dirs if d not in ['.git']]

					for filename in files:
						file_path = os.path.join(directory, filename)


						# Hash the file to make sure if we have not seen it before
						path_hash = md5(open(file_path, 'rb').read()).hexdigest()
						
						if path_hash not in self.target.seen_files:							
							temp_path = os.path.join(temp_folder, path_hash)
							shutil.move(file_path, temp_path)
							katana.recurse(self, temp_path)
							self.target.seen_files.append(path_hash)
				
				line_number += 1

			commit_data = subprocess.run(f"git checkout {first_commit}".split(), cwd = git_directory, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
