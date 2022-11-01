"""
ZIP corrupted file fix CRC

This unit looks for ZIP files magic bytes that are corrupted and tries to fix them.

The unit inherits from :class:`katana.unit.FileUnit` to ensure the target
is some kind of archive (zip,gz,jar,apk,docx). Actually we are going to run
on any file.

4.3.7  Local file header:
  local file header signature     4 bytes  (0x04034b50)
  version needed to extract       2 bytes
  general purpose bit flag        2 bytes
  compression method              2 bytes
  last mod file time              2 bytes
  last mod file date              2 bytes
  crc-32                          4 bytes
  compressed size                 4 bytes
  uncompressed size               4 bytes
  file name length                2 bytes
  extra field length              2 bytes
  file name (variable size)
  extra field (variable size)

Source: https://pkware.cachefly.net/webdocs/casestudies/APPNOTE.TXT

00: no compression
01: shrunk
02: reduced with compression factor 1
03: reduced with compression factor 2
04: reduced with compression factor 3
05: reduced with compression factor 4
06: imploded
08: deflated
09: enhanced deflated
10: PKWare DCL imploded
12: compressed using BZIP2
14: LZMA
18: compressed using IBM TERSE
19: IBM LZ77 z
98: PPMd version I, Rev 1 

Source: https://users.cs.jmu.edu/buchhofp/forensics/formats/pkzip.html

"""
import os
import re
from pwn import p32
import subprocess

from katana.unit import FileUnit

def hamming(a, b):
  distance = abs(len(a) - len(b))
  for i in range(min(len(a), len(b))):
    if a[i] != b[i]:
      distance += 1
  return distance


bad_crc_pattern = re.compile(b"\sbad CRC\s+[0-9a-f]{8}\s+\(should be ([0-9a-f]{8})\)")
ok_pattern = re.compile(b"test of .+ OK")
def has_bad_crc(path: str) -> bool:
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
  match = bad_crc_pattern.search(output)
  if match is None:
    match = ok_pattern.search(output)
    if match is None:
      return (True, None)
    else:
      return (False, None)
  else:
    return (True, match.groups()[0])

class Unit(FileUnit):
  RECURSE_SELF = True
  """
  This unit can recurse into itself because ZIP file can be very cursed.
  """
  PRIORITY = 35
  """
  Priority works with 0 being the highest priority, and 100 being the 
  lowest priority. 50 is the default priorty. This unit has a moderately
  high priority due to speed and broadness of applicability
  """

  def evaluate(self, case: str):
    """
    Evaluate the target. Fix any corrupted magic if found.

    :param case: A case returned by ``enumerate``. For this unit,\
    the ``enumerate`` function is not used.
    :return: None. This function should not return any data.
    """

    broken, bad_crc = has_bad_crc(self.target.path)
    if not broken or bad_crc is None:
      return

    file_content = self.file_content()

    # Search for magic headers
    match = re.search(b"PK\3\4.{10}" + p32(int(bad_crc,16)), file_content)

    if match is None:
      raise RuntimeError(f"FixCRC could not find local file header with broken CRC {str(bad_crc)}. Check {str(self.target.path)}")

    # Posibly someone messed with the compression byte and just need to find the right one
    for compression_method in [b"\0",b"\5",b"\7",b"\x08",b"\x09",b"\x0a",b"\x0b",b"\x0d",b"\x12",b"\x13",b"\x62"]:
      new_file_content = file_content[:match.start() + 8] + compression_method + b"\0" + file_content[match.start() + 10:]
      name, f = self.generate_artifact("fixed_crc_data.zip", mode="wb")
      f.write(new_file_content)
      f.close()

      name = os.path.abspath(name)
      broken, current_bad_crc = has_bad_crc(name)

      if not broken or (current_bad_crc is not None and bad_crc != current_bad_crc):
        # Recurse on the new file
        self.manager.register_artifact(self, name)
        break
      else:
        os.remove(name)



