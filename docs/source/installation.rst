Installation Instructions
=========================

.. toctree::
    :maxdepth: -1

Katana is designed first and foremost as a Python module. A ``setup.py`` script is provided to install via
``setuptools``. There are a number of binary dependencies which individual units depend on. When running Katana, you
will be notified of these dependencies if they are missing. A short list is provided below, but may not be up to date
depending on the units currently installed.

Binary Dependencies
-------------------

Depending on your distribution, installation methods will differ. In general, you will require the following packages:

- Python3.7+
- Python3 setuptools
- Python3 pip
- Python3 virtualenv (for development)
- libffi-dev
- libssl-dev
- pandoc
- libgmp3-dev
- libzbar-dev
- tesseract-ocr
- xsel
- libpoppler-cpp-dev
- libmpc-dev

If you are using Ubuntu, these requirements can be installed with the following ``apt`` command::

    sudo apt install -y python3.7-tk tk-dev python3.7 python3-pip python3-setuptools python3.7-dev \
        python3.7-venv libffi-dev libssl-dev pandoc libgmp3-dev libzbar-dev tesseract-ocr xsel \
        libpoppler-cpp-dev libmpc-dev

Installation on other distributions may differ (e.g. ``yum`` for CentOS, ``pacman`` for Arch, etc). Also, the names
of individual packages may differ. Consult your distribution package manager for locating these dependencies.

Installing Katana
-----------------

To install both the Katana module and Read-Evaluate-Print-Loop (REPL) interpreter, use setup tools::

    python setup.py install

This will install Katana and all of it's Python dependencies in your current environment.

External Unit Dependencies
--------------------------

On your first few runs of Katana, you may find that you receive dependency errors related to binaries not present
on your system. These dependencies are specific to the units you have installed. The default units used by Katana have
the following system dependencies. Installation of these packages varies by package and distribution. Consult your
distribution documentation for further assistance in installing them.

- exiftool
- steghide
- stegsnow
- zsteg
- jsteg
- node
- binwalk
- foremost
- unzip
- npiet
- tcpflow
- git
- apktool
- tesseract
- qpdf
- pdfinfo
- pdfimages
- strings
