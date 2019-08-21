Installation
==================================

Katana was originally developed on Ubuntu and Arch Linux, but the tool should work on any Posix-like distribution.

Considering Katana takes advantage of multiple tools that are often used in CTF competitions, there are a fair number of dependencies. Those are typically expected to be installed system-wide and available within your ``PATH`` environment variable.

Python 3.7
----------

We recommend running this with the latest version of Python and inside of virtual environment. If you need a hand getting the latest version of Python, these commands should bring you up to speed:

- Download pre-requisites

.. code-block:: bash

	sudo apt-get install build-essential checkinstall
	sudo apt-get install libreadline-gplv2-dev libncursesw5-dev libssl-dev \
	    libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev libffi-dev zlib1g-dev

- Download and extract Python 3.7

.. code-block:: bash

	cd /usr/src
	sudo wget https://www.python.org/ftp/python/3.7.4/Python-3.7.4.tgz

- Compile Python source

.. code-block:: bash

	cd Python-3.7.4
	sudo ./configure --enable-optimizations
	sudo make altinstall

``make altinstall`` is used to prevent replacing the default Python binary file ``/usr/bin/python``, so you do not clobber the version you may use currently.

Dependencies and Virtual Environment
------------------------------------

Using a virtual environment, you can safely install the needed Python modules with the environment's ``pip``. You should *not* need to use ``sudo``, other than the initial system-wide packages you may need.

.. code-block:: bash

	sudo apt-get install -y python3.7-tk tk-dev python3.7 python3-pip python3-setuptools python3.7-dev python3-venv libffi-dev libssl-dev pandoc libgmp3-dev libzbar-dev tesseract-ocr xsel libpoppler-cpp-dev
	python3.7 -m venv env
	source env/bin/activate

	pip install -r requirements.txt

At this point, you should be able to run Katana as a script, with the ``./katana.py`` syntax.

If you would like Katana installed to be used alongside its sister project, **Scimitar**, you can take advantage of the standard ``setup.py`` script.

.. code-block:: bash

	python3.7 setup.py install


