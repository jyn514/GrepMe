# GrepMe
Grep for GroupMe

## Installing
1. Download or clone the repo
2. Find your login token on https://dev.groupme.com/applications -> Terminal Application
3. Run `echo "access_token = \"$ACCESS_TOKEN\"" > login.py`

## Usage
```
usage: grep.py [-h] [--group GROUP] text [text ...]

positional arguments:
  text           text to search

optional arguments:
  -h, --help     show this help message and exit
  --group GROUP  group to search
```

Note that `group` defaults to 'ACM'.
