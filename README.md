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
sudo apt-get install -y python3.7 python3-pip python3-setuptools python3.7-dev python3-venv libffi-dev libssl-dev pandoc libgmp3-dev libzbar-dev tesseract-ocr
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

To add functionality to Katana, you simply need to create units. The boss will then handle them appropriately. Currently, the units we have defined are:

```
crypto/affine.py       pdf/pdfinfo.py        stego/steghide.py
crypto/atbash.py       pdf/pdftotext.py      stego/stegsolve.py
crypto/caesar.py       pwnage/stdin.py       stego/zsteg.py
crypto/polybius.py     raw/base64_decode.py  web/basic_img_shell.py
crypto/railfence.py    raw/exiftool.py       web/basic_nosqli.py
crypto/reverse.py      raw/file.py           web/basic_sqli.py
crypto/rot47.py        raw/morsecode.py      web/cookies.py
crypto/vigenere.py     raw/qrcode.py         web/git.py
crypto/xor.py          raw/strings.py        web/logon_cookies.py
esoteric/brainfuck.py  raw/unbinary.py       web/request.py
esoteric/malbolge.py   raw/undecimal.py      web/robots.py
esoteric/pikalang.py   raw/unhexlify.py      zip/crack.py
forensics/binwalk.py   stego/jsteg.py
forensics/foremost.py  stego/snow.py
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
rm -r results/ ; ./katana.py --unit raw ./tests/orchestra -ff USCGA{.*?}
```

__exiftool__

This detects the Base64 encoded flag.

```
rm -r results/ ; ./katana.py --unit raw ./tests/woof64.jpg --flag-format 'USCGA{.*?}'
```

__Morsecode__

This detects the hex encoded flag

```
rm -r results/ ; ./katana.py --unit raw ./tests/tamuctf_morsecode.txt --flag-format 'gigem{.*?}'
```

__QR code__

```
rm -r results/ ; ./katana.py --unit raw ./tests/qrcode.png --flag-format 'USCGA{.*}'
```


__steghide__

Without a password: 

```
rm -r results/; ./katana.py --unit raw --unit stego ./tests/rubber_ducky.jpg -ff "USCGA{.*?}"
```

With a password:

```
rm -r results/; ./katana.py --unit raw --unit stego ./tests/evil_ducky.jpg --dict /opt/rockyou.txt -ff "USCGA{.*?}"
```

__snow__

```
rm -r results/; ./katana.py --unit raw --unit stego ./tests/let_it_snow.txt -ff "USCGA{.*?}"
```

__zsteg__

```
rm -r results/; ./katana.py --unit raw --unit stego ./tests/pierre.png -ff "USCGA{.*?}"
```

__robots.txt__

```
rm -r results/; ./katana.py --unit web.robots http://johnhammond.org -ff "FLAG{.*?}"
```

__Basic SQL Injection__

```
rm -r results/; ./katana.py --unit web http://2018shell.picoctf.com:53261/ -ff "picoCTF{.*}"
```

__Cookies__

```
rm -r results/; ./katana.py --unit web.cookies http://johnhammond.org -ff "FLAG{.*?}"
```

__Crypto__

```
rm -r results/ ; ./katana.py --unit raw --unit crypto ./tests/welcome_crypto.txt -ff sun{.*?}
```

__Brainfuck__

```
rm -r results/ ; ./katana.py --unit esoteric.brainfuck ./tests/brainmeat.txt -ff sun{.*?}
rm -r results/ ; ./katana.py -a ./tests/brainfuck.txt -ff USCGA{.*?}
```

__Pikalang__

```
rm -r results/ ; ./katana.py --unit esoteric ./tests/it.pokeball -ff "HELLO WORLD"
rm -r results/ ; ./katana.py --unit esoteric ./tests/pikalang.pokeball -ff USCGA{.*?}
```

__Malbolge__

```
rm -r results/ ; ./katana.py --unit esoteric ./tests/malbolge.txt -ff "Hello World"
```
