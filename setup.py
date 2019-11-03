#!/usr/bin/env python

from setuptools import find_packages
from setuptools import setup

dependencies = [
    "wheel",
    "requests",
    "argparse",
    "python-magic",
    "pyzbar",
    "pillow",
    "clipboard",
    "jinja2",
    "pyenchant",
    "pycrypto",
    "pytesseract",
    "dulwich",
    "bs4",
    "base58",
    "pysocks",
    "scipy",
    "pydub",
    "matplotlib",
    "pdftotext",
    "PyPDF2",
    "pyopenssl",
    "primefac @ https://github.com/elliptic-shiho/primefac-fork",
    "sphinx",
    "sphinx-rtd-theme",
    "gmpy",
    "cmd2",
    "watchdog",
    "pygments",
]
dependency_links = [
    "git+https://github.com/elliptic-shiho/primefac-fork#egg=primefac-1.0.0"
]

# Setup
setup(
    name="katana",
    version="2.0",
    description="Automatic Capture the Flag Problem Solver",
    author="John Hammond/Caleb Stewart",
    url="https://github.com/JohnHammond/katana",
    packages=find_packages(),
    package_data={"katana": ["templates/*"]},
    entry_points={"console_scripts": ["katana=katana.__main__:main"]},
    install_requires=dependencies,
    dependency_links=dependency_links,
)
