:mod:`katana.units.crypto` --- Cryptography
=========================================================

These units handle procedures that are often necessary for challenges in the Cryptography category of CTFs.

.. note::

	Often times, these units can take a long amount of time and bottleneck Katana's operations. If you know you do not need these checks, include ``--exclude crypto`` in your command. 


.. toctree::
	crypto/affine
	crypto/atbash
	crypto/caesar255
	crypto/caesar
	crypto/dna
	crypto/nato_phonetic
	crypto/polybius
	crypto/quipqiup
	crypto/railfence
	crypto/rot47
	crypto/rsa
	crypto/t9
	crypto/vigenere
	crypto/xor