Katana
==============

> John Hammond | Caleb Stewart | February 18th, 2019

-----------------

This repository attempts to offer code and material to automate "running through the check-list" or hitting the "low-hanging fruit" in a Capture the Flag challenge. It is meant to act as a utility to help an individual _do things they might __otherwise forget to do__._

A lot of the context and ideas from this stem from the living document at [https://github.com/JohnHammond/ctf-katana](https://github.com/JohnHammond/ctf-katana)

**Katana is written in Python3.**

Virtual Environment
-------------

We recommend running this with the latest version of Python and inside of virtual environment.

```
python -m venv <your_environment>
source <your_environment>/bin/activate
```

From there, you can safely install dependencies with the environment's `pip` (as in, **do not** use sudo).

Dependencies 
---------------

```
sudo apt install -y libffi-dev libssl-dev pandoc
pip install -r requirements.txt
pip install git+https://github.com/arthaud/python3-pwntools.git
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

crypto
	- caesar
	- reverse
	- atbash
	- rot47

forensics
	- foremost
	- binwalk

pdf
	- pdfinfo

esoteric
	- brainfuck
	- malbolge
	- pikalang

zip
	- crack

```

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

Cookbooks
----------

__strings__


```
rm -r results/ ; ./katana.py --unit raw  ./tests/orchestra
```

__exiftool__

This detects the Base64 encoded flag.

```
rm -r results/ ; ./katana.py --unit raw  ./tests/woof64.jpg --flag-format 'USCGA{.*?}'
```

__Morsecode__

This detects the hex encoded flag

```
rm -r results/ ; ./katana.py --unit raw  ./tests/tamuctf_morsecode.txt --flag-format 'gigem{.*?}'
```

__QR code__

```
rm -r results/ ; ./katana.py --unit raw  ./tests/qrcode.png --flag-format 'USCGA{.*}'
```


__steghide__

Without a password: 

```
rm -r results/; ./katana.py --unit raw --unit stego  ./tests/rubber_ducky.jpg -ff "USCGA{.*?}"
```

With a password:

```
rm -r results/; ./katana.py --unit raw --unit stego  ./tests/evil_ducky.jpg --dict /opt/rockyou.txt -ff "USCGA{.*?}"
```

__snow__

```
rm -r results/; ./katana.py --unit raw --unit stego  ./tests/let_it_snow.txt -ff "USCGA{.*?}"
```

__zsteg__

```
rm -r results/; ./katana.py --unit raw --unit stego  ./tests/pierre.png -ff "USCGA{.*?}"
```

__robots.txt__

```
rm -r results/; ./katana.py --unit web http://web5.tamuctf.com -ff "gigem{.*?}"
```


__Basic SQL Injection__

```
rm -r results/; ./katana.py --unit web http://web1.tamuctf.com -ff "gigem{.*?}"
rm -r results/; ./katana.py --unit web http://2018shell.picoctf.com:53261/ -ff "picoCTF{.*}"
```

__Cookies__

```
rm -r results/; ./katana.py --unit web.cookies "http://www.whatarecookies.com/"
```

__Crypto__

```
rm -r results/ ; ./katana.py --unit raw --unit crypto  ./tests/welcome_crypto.txt -ff sun{.*?}
```

__Brainfuck__

```
rm -r results/ ; ./katana.py --unit esoteric.brainfuck  ./tests/brainmeat.txt -ff sun{.*?}
rm -r results/ ; ./katana.py -a  ./tests/brainfuck.txt -ff USCGA{.*?}
```

__Pikalang__

```
rm -r results/ ; ./katana.py --unit esoteric  ./tests/it.pokeball 
rm -r results/ ; ./katana.py --unit esoteric  ./tests/pikalang.pokeball 
```

__Malbolge__

```
rm -r results/ ; ./katana.py --unit esoteric  ./tests/malbolge.txt 
```
