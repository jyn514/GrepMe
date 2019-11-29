#!/usr/bin/env bash
set -ev

case "$1" in
	test) shift; REPO='--repository-url https://test.pypi.org/legacy/';;
esac
rm -rf dist

VERSION_REGEX="\([1-9]\d*\)\.\([1-9]\d*\)\.\([1-9]\d*\)"
read major minor patch < <(sed -n "s/VERSION = \"$VERSION_REGEX\"/\1 \2 \3/p" grepme/constants.py)
case "$1" in
	major) major=$(( major + 1 ));;
	minor) minor=$(( minor + 1 ));;
	patch|*) patch=$(( patch + 1 ));;
esac
sed -i "s/VERSION = \"$VERSION_REGEX\"/VERSION = \"$major.$minor.$patch\"/" grepme/constants.py

VERSION="$(grep VERSION grepme/constants.py | cut -d " " -f 3 | tr -d \")"
git diff grepme/constants.py
echo "does this diff changing the version to $VERSION look right?"
read -r REPLY
[ "$REPLY" = y ] || { echo "aborting"; exit 1; }

git add grepme/constants.py
git commit -m "bump version number to $VERSION"
git tag "$VERSION"
git push --tags && git push

pip install --user --upgrade setuptools twine wheel
python setup.py bdist_wheel sdist
twine upload $REPO dist/*
