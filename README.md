Katana
==============

> John Hammond | Caleb Stewart | February 18th, 2019

-----------------

This repository attempts to offer code and material to automate "running through the check-list" or hitting the "low-hanging fruit" in a Capture the Flag challenge. It is meant to act as a utility to help an individual _do things they might __otherwise forget to do__._

A lot of the context and ideas from this stem from the living document at [https://github.com/JohnHammond/ctf-katana](https://github.com/JohnHammond/ctf-katana)

**Katana is written in Python3.**

Dependencies 
---------------

```
sudo apt install -y python3-pip libffi-dev libssl-dev pandoc
sudo pip3 install -r requirements.txt
sudo pip3 install git+https://github.com/arthaud/python3-pwntools.git
```

Framework Methodology
---------------------

Katana works with a "boss -> worker" topology. One thread (the boss) spins off other threads (the workers) and returns the results once they have all completed. Each worker is called a "unit". The unit is what actually goes about and accomplishes the task.

To add functionality to Katana, you simply need to create units. The boss will then handle them appropriately. Currently, the units we have defined are:

```
raw
	- file
	- strings
	- exiftool
	- morsecode
	- qrcode

stego
	- steghide 
	- snow
	- qrcode
	- zsteg
	- jsteg

web
	- robots
	- git
	- cookies
	- basic_sqli

forensics
	- foremost
	- binwalk

pdf
	- pdfinfo

esoteric
	- brainfuck
	- malbolge
	- pikalang

```

-------

Support for Flag Formats
-------------

Katana offers support to hunt for a flag, if a flag format is supplied. You can supply `--flag-format` (or shorthand `-f`) with a regular expression to return a flag if there was one in Katana's findings.

Examples:

```
$ ./katana --unit raw --unit stego pierre.png --flag-format USCGA{.*}
```

```
$ ./katana --unit raw --unit stego pierre.png --flag-format USCGA{.*}
```

`results` Directory
-----------

Whenever Katana runs, it creates a `results` directory where it stores its findings and **artifacts** (files et. al.) that may be generated from any units.

**Katana will not run if the `results` directory already exists.**

If you are running Katana multiple times and just want to see the output, you may want to prepend a `rm -r results;` before your Katana command. **ENSURE THAT THE SEMI-COLON IS IN PLACE SO YOU DO NOT REMOVE KATANA AND YOUR FILES.**

Cookbooks
----------

When you are given a file, in most cases you will want to include the `raw` unit, in addition to the category you are working with.

