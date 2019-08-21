About Katana
==================================

Thus far, the best use of Katana is a quick check to see if a CTF challenge is so simple that it can be solved by this collection of automated procedures. 

Katana is not, by any means, *finished* or *complete*...  in fact it is very much intended to *never* be finished, as the user is encouraged to add new code and units to solve more and more CTF challenges. 

Usage
----------------

Katana can operate in ``auto`` mode -- as in, try every single unit applicable and throw the kitchen sink -- or it can run with individual units specified. No matter how you start Katana, you will always need to supply a *target*.

- Using auto mode:

.. code-block:: bash

	./katana.py -a ctf_image.png

- Using specific units:

.. code-block:: bash

	./katana.py --unit stego ctf_image.png
	./katana.py --unit stego.zsteg ctf_image.png

In these examples, the target supplied is the simple ``ctf_image.png`` file. You could instead supply a URL, or just given data like a ciphertext. **Note, if you supply a file that does not exist (perhaps after a typo!) Katana will treat it as data, and operate regardless of whether or not you realize your mistake.**

Arguably the best feature of Katana is the ability to hunt for a flag amongst the data it cuts through. You can supply ``--flag-format`` (or shorthand ``-ff``) with a regular expression to return a flag if there was one in Katana's findings.

.. code-block:: bash

	./katana.py --unit raw --unit stego pierre.png --flag-format FLAG{.*}

Framework Methodology
---------------------

Katana works with a "boss -> worker" topology. One thread (the boss) spins off other threads (the workers) and returns the results once they have all completed. Each worker is called a "unit". The unit is what actually goes about and accomplishes the task.

To add functionality to Katana, you simply need to create units. The boss will then handle them appropriately.

The Results Output
------------------

Whenever Katana runs, it creates a ``results`` directory where it stores its findings and artifacts (files et. al.) that may be generated from any units.

Katana will not run if the results directory already exists.

If you are running Katana multiple times and just want to see the output, you may want to prepend a ``rm -r results;`` before your Katana command. **Please ensure that semi-colon is in place so you do not remove Katana and your files.**

Contributions and Credits
-------------------------

As we got further along in development, we asked members of my Discord server if they would like to assist in creating units. The following is a list of units that were contributions from these members and their names, to offer our kudos and thank you. This project would not be what it is without your help!


- ``crypto.dna`` - voidUpdate, Zwedgy
- ``crypto.t9`` - Zwedgy, r4j
- ``esoteric.ook`` - Liikt
- ``esoteric.cow`` - Drnkn
- ``stego.audio_spectrogram`` - Zwedgy
- ``stego.dtmf_decoder`` - Zwedgy
- ``stego.whitespace`` - l14ck3r0x01
- ``hash.md5`` - John Kazantzis
- ``esoteric.jsfuck`` - Zwedgy
- ``crypto.playfair`` - voidUpdate
- ``crypto.nato_phonetic`` - voidUpdate

