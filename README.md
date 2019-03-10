# GrepMe
Grep for GroupMe

## Installing
1. Download or clone the repo
2. Find your login token on https://dev.groupme.com/applications -> Terminal Application
3. Run `echo "access_token = '$ACCESS_TOKEN'" > login.py`

## Usage
```
usage: grepme.py [-h] [--group GROUP] [-l] [-q] [-d] [-i] text [text ...]

positional arguments:
  text               text to search

optional arguments:
  -h, --help         show this help message and exit
  --group GROUP      group to search. can be specified multiple times
  -l, --list         show all available groups and exit
  -q, --quiet        don't show who said something
  -d, --date         show the date a message was sent
  -i, --ignore-case  ignore case distinctions in both text and groups
```

Note that `group` defaults to 'ACM'.
Unicode is handled fine, see below.

## Example
```
$ ./grepme.py -i swear --group 'ACM$'
Huиter Damroи: I work in the IBM building but I can meet you at Swearingen or anywhere.
Matthew Clapp: Is anybody in Swearingen?
ℬℜΔƉѰ: Can someone confirm that the Airport monitors in Swearingen have a Code-a-thon announcement?
Justin Baum: Hey does anyone know who I should email so my Carolina Card can get me into Swearingen?
^C
```
