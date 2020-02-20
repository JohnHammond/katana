Getting Started
===============

.. toctree::
    :maxdepth: -1

Katana can be used in a number of different ways. It was designed first as a framework which is importable into other
projects, however it provides a built-in interface in the form of a REPL.

Using the REPL
--------------

The Katana REPL is available by simply running the Katana module or through the ``setuptools`` script::

    # Run as a python module
    python -m katana ...
    # Or using the bundled setuptools script
    katana ...

The REPL provides all the features of the Katana module plus some extras, and is implemented using the ``cmd2`` Python
module. All commands are documented within the REPL itself, and the you can find the most up to date help by running
the ``help`` command from within the interpreter. At the time of writing, the following runtime arguments may be
supplied::

    usage: katana [-h] [--config CONFIG] [--manager MANAGER] [--timeout TIMEOUT]
              [--auto] [--unit UNIT] [--exclude EXCLUDE] [--flag FLAG]
              [--force] [--apktool APKTOOL] [--md5 MD5] [--affine AFFINE]
              [--atbash ATBASH] [--caesar CAESAR] [--caesar255 CAESAR255]
              [--dna DNA] [--phonetic PHONETIC] [--polybius POLYBIUS]
              [--quipqiup QUIPQIUP] [--railfence RAILFENCE]
              [--reverse REVERSE] [--rot47 ROT47] [--rsa RSA] [--t9 T9]
              [--vigenere VIGENERE] [--xor XOR] [--brainfuck BRAINFUCK]
              [--cow COW] [--jsfuck JSFUCK] [--malbolge MALBOLGE] [--ook OOK]
              [--piet PIET] [--pikalang PIKALANG] [--binwalk BINWALK]
              [--foremost FOREMOST] [--gunzip GUNZIP] [--tesseract TESSERACT]
              [--tcpflow TCPFLOW] [--pdf2text PDF2TEXT] [--pdfcrack PDFCRACK]
              [--pdfimages PDFIMAGES] [--pdfinfo PDFINFO] [--ascii85 ASCII85]
              [--base32 BASE32] [--base58 BASE58] [--base64 BASE64]
              [--base85 BASE85] [--exiftool EXIFTOOL] [--morsecode MORSECODE]
              [--qrcode QRCODE] [--strings STRINGS] [--unbinary UNBINARY]
              [--undecimal UNDECIMAL] [--unhexlify UNHEXLIFY]
              [--urldecode URLDECODE] [--audio_spectrogram AUDIO_SPECTROGRAM]
              [--dtmf_decode DTMF_DECODE] [--jsteg JSTEG] [--snow SNOW]
              [--steghide STEGHIDE] [--stegsnow STEGSNOW]
              [--stegsolve STEGSOLVE] [--whitespace WHITESPACE]
              [--zsteg ZSTEG] [--extract EXTRACT]
              [--basic_img_shell BASIC_IMG_SHELL]
              [--basic_nosqli BASIC_NOSQLI] [--basic_sqli BASIC_SQLI]
              [--cookies COOKIES] [--form_submit FORM_SUBMIT] [--git GIT]
              [--logon_cookies LOGON_COOKIES] [--robots ROBOTS]
              [--spider SPIDER] [--unzip UNZIP]
              [targets [targets ...]]

    Automatically identify and solve basic Capture the Flag challenges

    positional arguments:
      targets               targets to evaluate

    optional arguments:
      -h, --help            show this help message and exit
      --config CONFIG, -c CONFIG
                            configuration file
      --manager MANAGER, -m MANAGER
                            comma separated manager configurations (e.g. flag-
                            format=FLAG{.*?})
      --timeout TIMEOUT, -t TIMEOUT
                            timeout for all unit evaluations in seconds
      --auto, -a            shorthand for `-m auto=True`
      --unit UNIT, -u UNIT  explicitly run a unit on target
      --exclude EXCLUDE, -e EXCLUDE
                            exclude a unit from running
      --flag FLAG, -f FLAG  set the flag format
      --force               Force execution even if results directory exists
      --apktool APKTOOL     comma separated unit configuration
      --md5 MD5             comma separated unit configuration
      --affine AFFINE       comma separated unit configuration
      --atbash ATBASH       comma separated unit configuration
      --caesar CAESAR       comma separated unit configuration
      --caesar255 CAESAR255
                            comma separated unit configuration
      --dna DNA             comma separated unit configuration
      --phonetic PHONETIC   comma separated unit configuration
      --polybius POLYBIUS   comma separated unit configuration
      --quipqiup QUIPQIUP   comma separated unit configuration
      --railfence RAILFENCE
                            comma separated unit configuration
      --reverse REVERSE     comma separated unit configuration
      --rot47 ROT47         comma separated unit configuration
      --rsa RSA             comma separated unit configuration
      --t9 T9               comma separated unit configuration
      --vigenere VIGENERE   comma separated unit configuration
      --xor XOR             comma separated unit configuration
      --brainfuck BRAINFUCK
                            comma separated unit configuration
      --cow COW             comma separated unit configuration
      --jsfuck JSFUCK       comma separated unit configuration
      --malbolge MALBOLGE   comma separated unit configuration
      --ook OOK             comma separated unit configuration
      --piet PIET           comma separated unit configuration
      --pikalang PIKALANG   comma separated unit configuration
      --binwalk BINWALK     comma separated unit configuration
      --foremost FOREMOST   comma separated unit configuration
      --gunzip GUNZIP       comma separated unit configuration
      --tesseract TESSERACT
                            comma separated unit configuration
      --tcpflow TCPFLOW     comma separated unit configuration
      --pdf2text PDF2TEXT   comma separated unit configuration
      --pdfcrack PDFCRACK   comma separated unit configuration
      --pdfimages PDFIMAGES
                            comma separated unit configuration
      --pdfinfo PDFINFO     comma separated unit configuration
      --ascii85 ASCII85     comma separated unit configuration
      --base32 BASE32       comma separated unit configuration
      --base58 BASE58       comma separated unit configuration
      --base64 BASE64       comma separated unit configuration
      --base85 BASE85       comma separated unit configuration
      --exiftool EXIFTOOL   comma separated unit configuration
      --morsecode MORSECODE
                            comma separated unit configuration
      --qrcode QRCODE       comma separated unit configuration
      --strings STRINGS     comma separated unit configuration
      --unbinary UNBINARY   comma separated unit configuration
      --undecimal UNDECIMAL
                            comma separated unit configuration
      --unhexlify UNHEXLIFY
                            comma separated unit configuration
      --urldecode URLDECODE
                            comma separated unit configuration
      --audio_spectrogram AUDIO_SPECTROGRAM
                            comma separated unit configuration
      --dtmf_decode DTMF_DECODE
                            comma separated unit configuration
      --jsteg JSTEG         comma separated unit configuration
      --snow SNOW           comma separated unit configuration
      --steghide STEGHIDE   comma separated unit configuration
      --stegsnow STEGSNOW   comma separated unit configuration
      --stegsolve STEGSOLVE
                            comma separated unit configuration
      --whitespace WHITESPACE
                            comma separated unit configuration
      --zsteg ZSTEG         comma separated unit configuration
      --extract EXTRACT     comma separated unit configuration
      --basic_img_shell BASIC_IMG_SHELL
                            comma separated unit configuration
      --basic_nosqli BASIC_NOSQLI
                            comma separated unit configuration
      --basic_sqli BASIC_SQLI
                            comma separated unit configuration
      --cookies COOKIES     comma separated unit configuration
      --form_submit FORM_SUBMIT
                            comma separated unit configuration
      --git GIT             comma separated unit configuration
      --logon_cookies LOGON_COOKIES
                            comma separated unit configuration
      --robots ROBOTS       comma separated unit configuration
      --spider SPIDER       comma separated unit configuration
      --unzip UNZIP         comma separated unit configuration


Configuration
-------------

Configuration parameters can either be set in an ``.ini`` file or at runtime via the ``set`` command.
Configuration files are parsed using the built-in Python ``configparser`` module. The most important section is the
``manager`` section, which defines a few key parameters::

    [manager]
    # Flag format REGEX
    flag-format=FLAG{.*?}
    # Output directory
    outdir=./results

Other parameters can be seen by running `set manager` at the katana prompt to receive a listing of the values currently
set at runtime. When using the `set` command, parameters are specified with their fully qualified section/parameter
name like so::

    set manager[flag-format] NEWFLAG{.*?}

If the section name is not specified, a default value is added which will be used for any subsequent sections which
request that value. This is particularly useful for a configuration such as ``dict``, which can be specified once and
will then apply to all units which require a dictionary like so::

    set dict /path/to/rockyou.txt

You can also override the dictionary of a specific unit by specifying the unit as the section name::

    set steghide[dict] /path/to/different/dict.txt

Evaluating Targets
------------------

The ``target`` command is used to view, start, and stop target evaluation. The ``target add`` sub-command will queue a
target to begin analysis. The target specified can be a path name, URL, or raw data. Katana will create an abstract
``Target`` object and deduce the type of data passed to in intelligently::

    katana - waiting - 0 units queued
    ➜ target add --help
    Usage: target add [-h] target [...]

    positional arguments:
      target      the target to evaluate

    optional arguments:
      -h, --help  show this help message and exit

    katana - waiting - 0 units queued
    ➜ target add ./tests/cases/orchestra
    [+] ./tests/cases/orchestra: queuing target

After adding a target, you can view the progress of all targets with the ``target list`` command::

    katana - waiting - 0 units queued
    ➜ target list --help
    Usage: __main__.py list [-h] [--completed] [--running] [--all] [--flags]

    optional arguments:
      -h, --help       show this help message and exit
      --completed, -c  Display only completed targets
      --running, -r    Display only running targets
      --all, -a        Display all targets (running/completed)
      --flags, -f      D`

    ➜ katana - running - 0 units queued
    ➜ target list

    ./tests/cases/orchestra - completed
     hash: 2f0a02add67b58de837c7be054ae9e77
     flag: JHDCTF{strings}

When a target locates a flag, it will produce an asynchronous message to the screen identifying the unit and the flag
which was found. The flag will also be copied to the primary clipboard::

    katana - waiting - 0 units queued
    ➜ target ad
    strings(./tests/cases/orchestra) - completed!
      JHDCTF{strings} - (copied)
    katana - running - 0 units queued
    ➜ target ad

After a target has located flag(s), you can view the solution path for a target using the ``target solution`` command::

    katana - waiting - 0 units queued
    ➜ target solution -r ./tests/cases/evil_ducky.jpg
    steghide(./tests/cases/evil_ducky.jpg) ➜
      strings(./results/60959e0ca0e4a202fd928c50f49a34fb/steghide/dGlua2Vy) ➜
       JHDCTF{we_finally_found_the_the_flag} - (copied)


Monitoring Directories
----------------------

The Katana REPL has the ability to utilize the ``watchdog`` Python module to monitor a directory or list of directories
for new files and queue them for evaluation automatically. The allows you to start a Katana for a CTF, and then simply
download interesting targets to a directory, checking periodically for flags or hung targets. The ``monitor`` command
can be used to add, remove, and list monitored directories::

    katana - waiting - 0 units queued
    ➜ monitor --help
    Usage: monitor [-h] {list, ls, l, remove, rm, r, add, a} ...

    Begin monitoring the given directory and automatically queue new targets as they are created.

    optional arguments:
      -h, --help            show this help message and exit

    subcommands:
      {list, ls, l, remove, rm, r, add, a}
                            Actions
        list
        remove (rm, r)      remove a monitored directory
        add (a)             begin monitoring a new directory


CTFd Integration
----------------

The Katana REPL has support to integrate with CTFd platforms. This integration includes the following:

- List challenges
- View challenge details (including solve state)
- Queue challenge (attached files and/or description)
- Automatically submit flags

This functionality is exposed through the ``ctfd`` command. All ``ctfd`` functions depend on a new configuration section
named ``ctfd``::

    [ctfd]
    url=http://ctfd.yourdomain.com
    username=YourUserName
    password=YourPassword

After you specify these configuration items, you can use the ``ctfd list`` command to list available challenges. The list
is ordered from lowest-to-highest value, with solved challenges placed at the bottom. If your terminal supports
extended escape sequences, solved challenges will be "dim" and struck-through::

    katana - waiting - 0 units queued
    ➜ set ctfd
    [ctfd]
    url = http://192.168.1.37:8000
    username = User01
    password = password

    katana - waiting - 0 units queued
    ➜ ctfd list
    ID Title      Points
    1  Orchestra  25

The ``ctfd show`` command will show the details of a given challenge ID::

    katana - waiting - 0 units queued
    ➜ ctfd show 1
    Orchestra - 25 points - solved

     It's music to my ears!

     Files:
      - orchestra

To queue a challenge for evaluation, you can use the `ctfd queue` command. By default, this command only queues attached
files. To also queue the description of the challenge for evaluation, use the ``--description/-d`` flag. It will also
check that the given challenge is not already solved (although this can be bypassed with the ``--force`` flag)::

    katana - waiting - 0 units queued
    ➜ ctfd queue --force 1
    [+] ctfd: queuing http://192.168.1.37:8000/files/f36fce4574bed199beb8170ac5b9bc1e/orchestra?token=eyJ0ZWFtX2lkIjpudWxsLCJ1c2VyX2lkIjozLCJmaWxlX2lkIjoxfQ.Xbd3yA.cKg9KcdqjStAQNAtHY5LP_m5uCw

    strings(http://192.168.1.37:8000/files/f36fce4574bed199beb8170ac5b9bc...) - completed!
      JHDCTF{there_is_no_orchestra_without_the_strings} - (copied)

    [+] ctfd: correct flag for challenge 1

In this case, automatic flag submission was turned on, and the flag was automatically submitted upon completion to CTFd.
The updated ``solved`` state will be visible immediately in both ``ctfd list`` and ``ctfd show``.