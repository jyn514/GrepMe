#!/usr/bin/env python3
import os.path
from sys import stderr
from setuptools import setup

URL = 'https://github.com/jyn514/GrepMe'
if not os.path.exists("login.py"):
    print("FATAL: login.py does not exist. "
          "Please see the readme locally or online at '" + URL + "'", file=stderr)
    quit(1)

DESCRIPTION = 'grep for GroupMe',
here = os.path.abspath(os.path.dirname(__file__))
try:
    with open(os.path.join(here, 'README.md')) as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = DESCRIPTION

setup(
    name='grepme',
    version='0.0.1',
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Joshua Nelson',
    author_email='jyn514@gmail.com',
    python_requires='>=3',
    url=URL,
    py_modules=["grepme", "login"],
    entry_points = {
        'console_scripts': ['grepme=grepme:main']
    },
    install_requires='requests'
)
