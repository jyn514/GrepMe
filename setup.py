from sys import stderr
from os.path import exists
from setuptools import setup

url = 'https://github.com/jyn514/GrepMe'
if not exists("login.py"):
    print("FATAL: login.py does not exist. "
          "Please see the readme locally or online at ' + url", file=stderr)
    quit(1)

setup(
    name='grepme',
    version='0.0.1',
    description='grep for GroupMe',
    author='Joshua Nelson',
    author_email='jyn514@gmail.com',
    python_requires='>=3',
    url=url,
    scripts=['grepme.py', 'login.py'],
    entry_points = {
        'console_scripts': ['grepme=grepme:main']
    },
    install_requires='requests'
)
