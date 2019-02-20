from pwn import *
import hashlib

class BaseUnit(object):

    # Unit constructor (saves the config)
    def __init__(self, config):
        self.config = config

    # The default unit supports all targets
    def check(self, target):
        return True

    @property
    def unit_name(self):
        return self.__class__.__module__

    def evaluate(self, target):
        log.error('{0}: no evaluate implemented: bad unit'.format(self.unit_name))

    # Create a new artifact for this target/unit and
    def artifact(self, target, name, mode='w'):
        path = os.path.join(self.get_output_dir(target), name)
        return open(path, mode), path

    def get_output_dir(self, target):
        # If there's only one target, we don't deal with sha256 sums.
        # Otherwise, the artifacts will be in:
        # $OUTDIR/artifacts/$SHA256(target)/module/unit/artifact_name
        outdir = os.path.join(
            self.config['outdir'],
            'artifacts',
            hashlib.sha256(target.encode('utf-8')).hexdigest(),
            *self.unit_name.split('.')
        )

        # If this directory doesn't exist, create it
        if not os.path.exists(outdir):
            try:
                os.makedirs(outdir)
            except:
                log.error('{0}: failed to create artifact directory'.format(
                    self.unit_name
                ))

        return outdir
        