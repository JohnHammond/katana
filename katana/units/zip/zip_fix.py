"""
ZIP corrupted file fix

This unit looks for ZIP files magic bytes and tries to fix the file.

The unit inherits from :class:`katana.unit.FileUnit` to ensure the target
is some kind of archive (zip,gz,jar,apk,docx). Actually we are going to run
on any file.
"""
import os
import re
import subprocess
import hashlib

from katana.unit import FileUnit

def md5sum(path: str) -> hashlib.md5:
    """
    Quick convenience function to get the MD5 hash of a file
    """
    md5 = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            md5.update(chunk)
    return md5

ok_pattern = re.compile(b"test of .+ OK")
def valid_zip_file(path: str) -> bool:
  """
  Use zip -T to test the integrity of a zip file
  """
  p = subprocess.Popen(
      ["zip", "-T", path],
      stdout=subprocess.PIPE,
      stdin=subprocess.PIPE,
      stderr=subprocess.PIPE,
  )
  p.wait()
  output = b"".join(p.communicate())
  return ok_pattern.match(output)

class Unit(FileUnit):
  RECURSE_SELF = False
  """
  This unit can recurse into itself because ZIP file can be very cursed.
  """
  PRIORITY = 35
  """
  Priority works with 0 being the highest priority, and 100 being the 
  lowest priority. 50 is the default priorty. This unit has a moderately
  high priority due to speed and broadness of applicability
  """

  """
  This matches some of the most known magic bytes of compressed archives.
  """
  MAGIC_PATTERN = b"PK(\1\2|\3\4|\5\6|\7\x08)"

  """
  If we find this amount or more magic patterns we will process the file.
  If we get too many false possitives increase it.
  """
  MAGIC_THRESHOLD = 3

  def evaluate(self, case: str):
    """
    Evaluate the target. Fix any corrupted magic if found.

    :param case: A case returned by ``enumerate``. For this unit,\
    the ``enumerate`` function is not used.
    :return: None. This function should not return any data.
    """
    file_content = self.file_content()
    # Search for magic headers
    magics_count = len(re.findall(self.MAGIC_PATTERN, file_content))

    # Looks like a zip but it's not valid, lets try to fix it
    if magics_count >= self.MAGIC_THRESHOLD and not valid_zip_file(self.target.path):
      name, f = self.generate_artifact("fix_zip_data.zip")
      f.close()
      name = os.path.abspath(name)

      p = subprocess.Popen(
          ['echo "y" | ', "zip", "-FF", "--out", name, self.target.path],
          shell=True,
          stdout=subprocess.PIPE,
          stdin=subprocess.PIPE,
          stderr=subprocess.PIPE,
      )
      p.wait()
      
      # If the fixed file is different we register it
      if md5sum(name) != md5sum(self.target.path):
        self.manager.register_artifact(self, name)
      
      # Else we delete it to avoid collecting garbage
      else:
        os.remove(name)

