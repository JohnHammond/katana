Katana
==============

> John Hammond | Caleb Stewart | February 18th, 2019

-----------------

This repository attempts to offer code and material to automate "running through the check-list" or hitting the "low-hanging fruit" in a Capture the Flag challenge. It is meant to act as a utility to help an individual _do things they might __otherwise forget to do__._

A lot of the context and ideas from this stem from the living document at [https://github.com/JohnHammond/ctf-katana](https://github.com/JohnHammond/ctf-katana)

**Katana is written in Python 3.**

DISCLAIMER
----------

**Katana will _automatically_ run code and do _potentially_ "malicious" things to its target.** It may throw SQL injection, it may try test for local file inclusion, uploading web shells or finding a means of remote code execution. **DO NOT, by any means, run this utility against ANYTHING that you do not have explicit permission and authorization to test.**

We do not claim responsibility or involvement for anything you break or any trouble you may get into by using this tool.

Getting Started
-------------

We recommend running this with the latest version of Python and inside of a virtual environment. If you need a hand getting the latest version of Python, I've found some help [here](https://tecadmin.net/install-python-3-7-on-ubuntu-linuxmint/).

```
sudo apt-get install -y python3.7-tk tk-dev python3.7 python3-pip python3-setuptools python3.7-dev python3.7-venv libffi-dev libssl-dev pandoc libgmp3-dev libzbar-dev tesseract-ocr xsel libpoppler-cpp-dev
python3.7 -m venv env
source env/bin/activate
```

From there, you can safely install dependencies with the environment's `pip` (as in, **do not** use sudo).

Dependencies 
---------------

```
pip install -r requirements.txt
```

Framework Methodology
---------------------

Katana works with a "boss -> worker" topology. One thread (the boss) spins off other threads (the workers) and returns the results once they have all completed. Each worker is called a "unit". The unit is what actually goes about and accomplishes the task.

To add functionality to Katana, you simply need to create units. The boss will then handle them appropriately.

You can read more about it in the `docs` directory.

-------

Support for Flag Formats
-------------

Katana offers support to hunt for a flag, if a flag format is supplied. You can supply `--flag-format` (or shorthand `-ff`) with a regular expression to return a flag if there was one in Katana's findings.

Examples:

```
$ ./katana --unit raw --unit stego pierre.png --flag-format USCGA{.*}
```

`results` Directory
-----------

Whenever Katana runs, it creates a `results` directory where it stores its findings and **artifacts** (files et. al.) that may be generated from any units.

**Katana will not run if the `results` directory already exists.**

If you are running Katana multiple times and just want to see the output, you may want to prepend a `rm -r results;` before your Katana command. **ENSURE THAT THE SEMI-COLON IS IN PLACE SO YOU DO NOT REMOVE KATANA AND YOUR FILES.**

Contributing
------------

If you would like to contribute to Katana, please see [`CONTRIBUTING.md`](CONTRIBUTING.md)

Thank You and Credits
-------------------------

As we got further along in development, we asked members of my Discord server if they would like to assist in creating units. The following is a list of units that were contributions from these members and their names, to offer our kudos and thank you. This project would not be what it is without your help!

```
crypto.dna - voidUpdate, Zwedgy
crypto.t9 - Zwedgy, r4j
esoteric.ook - Liikt
esoteric.cow - Drnkn
stego.audio_spectrogram - Zwedgy
stego.dtmf_decoder - Zwedgy
stego.whitespace - l14ck3r0x01
hash.md5 - John Kazantzis
esoteric.jsfuck - Zwedgy
crypto.playfair - voidUpdate
crypto.nato_phonetic - voidUpdate
```
