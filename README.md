Katana
==============

> John Hammond | Caleb Stewart | February 18th, 2019

-----------------

This repository attempts to offer code and material to automate "running through the check-list" or hitting the "low-hanging fruit" in a Capture the Flag challenge. It is meant to act as a utility to help an individual _do things they might __otherwise forget to do__._

A lot of the context and ideas from this stem from the living document at [https://github.com/JohnHammond/ctf-katana](https://github.com/JohnHammond/ctf-katana)

**Katana is written in Python3.**

Virtual Environment
-------------

We recommend running this with the latest version of Python and inside of virtual environment. If you need a hand getting the latest version of Python, I've found some help [here](https://tecadmin.net/install-python-3-7-on-ubuntu-linuxmint/).

```
sudo apt-get install -y python3.7-tk tk-dev python3.7 python3-pip python3-setuptools python3.7-dev python3-venv libffi-dev libssl-dev pandoc libgmp3-dev libzbar-dev tesseract-ocr xsel libpoppler-cpp-dev
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
pdf/pdf2text.py	crypto/polybius.py	raw/base64_decode.py	stego/snow.py
pdf/pdfimages.py	crypto/railfence.py	raw/exiftool.py	stego/stegsolve.py
pdf/pdfinfo.py	crypto/dna.py		raw/qrcode.py		stego/zsteg.py
pdf/pdfcrack.py	zip/crack.py		raw/undecimal.py	stego/jsteg.py
pcap/tcpflow.py	pwnable/stdin.py	raw/unhexlify.py	ocr/tesseract.py
crypto/caesar.py	forensics/foremost.py	raw/ascii85_decode.py	web/dir.py
crypto/caesar255.py	forensics/binwalk.py	raw/base32_decode.py	web/cookies.py
crypto/atbash.py	esoteric/brainfuck.py	raw/urldecode.py	web/spider.py
crypto/vigenere.py	esoteric/cow.py	raw/base58_decode.py	web/git.py
crypto/rsa.py		esoteric/malbolge.py	raw/unbinary.py	web/basic_sqli.py
crypto/t9.py		esoteric/ook.py	raw/strings.py	web/logon_cookies.py
crypto/reverse.py	esoteric/piet.py	apk/apktool.py	web/basic_img_shell.py
crypto/xor.py		esoteric/pikalang.py	stego/audio_spectrogram.py	web/robots.py
crypto/rot47.py	raw/morsecode.py	stego/steghide.py	web/basic_nosqli.py
crypto/affine.py	raw/base85_decode.py	stego/whitespace.py	web/form_submit.py
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


Contributions and Credits
-------------------------

As we got further along in development, we asked members of my Discord server if they would like to assist in creating units. The following is a list of units that were contributions from these members and their names, to offer our kudos and thank you. This project would not be what it is without your help!

```
crypto.dna - voidUpdate, Zwedgy
crypto.t9 - Zwedgy, r4j
esoteric.ook - Liikt
esoteric.cow - Drnkn
stego.audio_spectrogram - Zwedgy
```

Cookbooks
----------

__strings__


```
rm -r results/ ; ./katana.py --unit raw ./tests/orchestra -ff 'USCGA{.*?}'
```

__exiftool__

This detects the Base64 encoded flag.

```
rm -r results/ ; ./katana.py --unit raw ./tests/woof64.jpg --flag-format 'USCGA{.*?}' --exclude crypto
```

__Morsecode__

This detects the hex encoded flag

```
rm -r results/ ; ./katana.py --unit raw ./tests/tamuctf_morsecode.txt --flag-format 'gigem{.*?}' --exclude crypto
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

__ROT47__

```
rm -r results/ ; ./katana.py --unit raw --unit crypto ./tests/welcome_crypto.txt -ff 'sun{.*?}'
```

__Brainfuck__

```
rm -r results/ ; ./katana.py --unit esoteric.brainfuck ./tests/brainmeat.txt -ff 'sun{.*?}'
rm -r results/ ; ./katana.py -a ./tests/brainfuck.txt -ff 'USCGA{.*?}'
```

__Pikalang__

```
rm -r results/ ; ./katana.py --unit esoteric ./tests/it.pokeball -ff "HELLO WORLD"
rm -r results/ ; ./katana.py --unit esoteric ./tests/pikalang.pokeball -ff 'USCGA{.*?}'
```

__Malbolge__

```
rm -r results/ ; ./katana.py --unit esoteric ./tests/malbolge.txt -ff "Hello World"
```

__DNA__

```
rm -r results/ ; ./katana.py -a "gtcactagacagttgagacagttgaaattgcatacacagcat" -ff 'This is a test'
```

__T9 Cipher__

```
rm -r results/ ; ./katana.py -a "8 44 444 7777 0 444 7777 0 2 0 8 33 7777 8 0 333 555 2 4 0" -ff 'this is a test flag'
```

__Whitespace Stego__

```
rm -r results/ ; ./katana.py --unit stego.whitespace "tests/whitespace.txt" -ff 'FLAG{.*?}'
```

__Piet__

```
rm -r results/ ; ./katana.py --unit esoteric.piet "tests/piet_hello_world.png" -ff 'Hello, World!'
```

PicoCTF Cookbook
================

__Resources__

```
rm -r results/ ; ./katana.py -a "https://picoctf.com/resources" -ff 'picoCTF{.*?}'
```

__Crypto Warmup 2__

```
rm -r results/ ; ./katana.py -a "cvpbPGS{guvf_vf_pelcgb!}" -ff 'picoCTF{.*?}'
```

__grep 1__

```
rm -r results/ ; ./katana.py -a -d "https://2018shell.picoctf.com/static/805ac70722810caa0b1c02bc88ef68d8/file" -ff 'picoCTF{.*?}'
```

__strings__

```
rm -r results/ ; ./katana.py -a -d "https://2018shell.picoctf.com/static/a3d311b507256d5d9299c0e94dfc4fc5/strings" -ff 'picoCTF{.*?}'
```

__Logon__

```
rm -r results/ ; ./katana.py -a "http://2018shell.picoctf.com:5477/" -ff 'picoCTF{.*?}'
```

__Reading Between the Eyes__

```
rm -r results/ ; ./katana.py -a -d "https://2018shell.picoctf.com/static/9129761dbc4bf494c47429f85ddf7434/husky.png" -ff 'picoCTF{.*?}'
```

__Recovering from the Snap__

```
rm -r results/ ; ./katana.py -a -i -d "https://2018shell.picoctf.com/static/b8561b04f5c7107ecb2f15c9a8c79fb8/animals.dd" -ff 'picoCTF{.*?}'
```

__admin panel__

```
rm -r results/ ; ./katana.py -a -d "https://2018shell.picoctf.com/static/1a6db339e11fa100ef52d944edaa9612/data.pcap" -ff 'picoCTF{.*?}'
```

__caesar cipher 1__

This does not solve as it should, because the file in fact already
has the picoCTF{} flag format inside. We cannot avoid this.

```
rm -r results/ ; ./katana.py -a -d "https://2018shell.picoctf.com/static/9c305b1460312c3bcfc6dd5741990c26/ciphertext" -ff 'picoCTF{.*?}'
```

__hex editor__

```
rm -r results/ ; ./katana.py -a -d "https://2018shell.picoctf.com/static/ccad03a151a0edac8bd01e665a595b7a/hex_editor.jpg" -ff 'picoCTF{.*?}'
```

__Irish Name Repo__

```
rm -r results/ ; ./katana.py --unit web.spider "http://2018shell.picoctf.com:52135/" -ff 'picoCTF{.*?}'
```

__Mr. Robots__

```
rm -r results/ ; ./katana.py -a "http://2018shell.picoctf.com:10157/" -ff 'picoCTF{.*?}'
```

__Truly an Artist__

```
rm -r results/ ; ./katana.py -a -d "https://2018shell.picoctf.com/static/69b2020b48082fb24714bf93707183e8/2018.png" -ff 'picoCTF{.*?}'
```


__now you don't__

```
rm -r results/ ; ./katana.py -a "https://2018shell.picoctf.com/static/eee00c8559a93bfde1241d5e00c2df37/nowYouDont.png" -d -ff 'picoCTF{.*?}'
```

__The Vault__

```
rm -r results/ ; ./katana.py -a "http://2018shell.picoctf.com:53261/" -ff 'picoCTF{.*?}'
```

__What's my Name?__

```
rm -r results/ ; ./katana.py -a "https://2018shell.picoctf.com/static/6ae91abb9e70e527e32729413103af90/myname.pcap" -d -ff 'picoCTF{.*?}'
```

__caesar cipher 2__

```
rm -r results/ ; ./katana.py -a "https://2018shell.picoctf.com/static/bed1fba9caa8aeda29580c36bf0d0276/ciphertext" -d -ff 'picoCTF{.*?}' -v
```