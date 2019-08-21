:mod:`katana.units.stego` --- Steganography
=========================================================

These units handle procedures that are often necessary for challenges in the Steganography category of CTFs.

.. note::

	Often times, these units can take a long amount of time and bottleneck Katana's operations. If you know you do not need these checks, include ``--exclude stego`` in your command. 

.. toctree::
	stego/audio_spectrogram
	stego/dtmf_decode
	stego/jsteg
	stego/snow
	stego/steghide
	stego/stegsolve
	stego/whitespace
	stego/zsteg