import subprocess
from hashlib import md5

from katana import units
from katana import utilities
from katana.units import NotApplicable

DEPENDENCIES = ['snow']


class Unit(units.FileUnit):
	PRIORITY = 30

	def __init__(self, katana, target, keywords=None):
		super(Unit, self).__init__(katana, target)

		if target.is_url:
			raise NotApplicable('target is a URL')

	def evaluate(self, katana, case):

		p = subprocess.Popen(['snow', self.target.path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

		# Look for flags, if we found them...
		try:
			response = utilities.process_output(p)
		except UnicodeDecodeError:

			# This probably isn't plain text....
			p.stdout.seek(0)
			response = p.stdout.read()

			# So consider it is some binary output and try and handle it.
			artifact_path, artifact = katana.artifact(self, 'output_%s' % md5(self.target).hexdigest())
			artifact.write(response)
			artifact.close()

			katana.recurse(self, artifact_path)

		if response is not None:
			if 'stdout' in response:

				# If we see anything interesting in here... scan it again!
				for line in response['stdout']:
					katana.recurse(self, line)

			if 'stderr' in response:
				return

			katana.add_results(self, response)
