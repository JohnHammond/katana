:mod:`katana.units.web` --- Web Application Testing
=========================================================

These units handle procedures that are often necessary for challenges in the Web category of CTFs.

.. note::

	These units are by default *aggressive*: they will automatically perform SQL injections, attempt LFI, bruteforce web pages and more. Ensure that you have *full authorization and permission* to point this at a website.


Admittedly, these should be organized into a framework so that once vulnerabilities are found for a website, they can be shared with sister units and leveraged as needed. This is a large undertaking that is still not completed.

.. toctree::
	web/basic_img_shell
	web/basic_nosqli
	web/basic_sqli
	web/cookies
	web/dir
	web/form_submit
	web/git
	web/logon_cookies
	web/robots
	web/spider