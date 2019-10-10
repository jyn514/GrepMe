#!/bin/sh
case "$1" in
	test) REPO='--repository-url https://test.pypi.org/legacy/';;
esac
rm -rf dist
pip install --user --upgrade setuptools twine wheel
python setup.py bdist_wheel sdist
twine upload $REPO dist/*
