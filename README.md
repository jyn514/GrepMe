# GrepMe
Grep for GroupMe

## For Users
### Installing
1. `pip install grepme`
2. Create your login token on https://dev.groupme.com/applications -> Create Application
  None of the info there is used in grepme, you can give garbage values.
3. Run grepme. You should be prompted for your login token.

If you type your token wrong, you can use `-D` and grepme will prompt you again,
e.g. `grepme -D some_text`

### Examples
- Search case-insensitive for 'school': `grepme -i school`
- Search in a different group: `grepme --group USCCyber api`
- Show the entire history of a group: `grepme '.*'`
- Filter by date: `grepme -d '.*' | grep 2018`
- Search by user: `grepme -u Joshua '.*'`
- Show all available groups: `grepme -l`
- Show version: `grepme -V`

### See it in action
```
$ ./grepme.py -i swear --group 'ACM$'
Huиter Damroи: I work in the IBM building but I can meet you at Swearingen or anywhere.
Matthew Clapp: Is anybody in Swearingen?
ℬℜΔƉѰ: Can someone confirm that the Airport monitors in Swearingen have a Code-a-thon announcement?
Justin Baum: Hey does anyone know who I should email so my Carolina Card can get me into Swearingen?
^C
```

### Full usage
```
usage: grepme.py [-h] [-g GROUP] [-l] [-q] [-d] [-i] [-a AFTER_CONTEXT]
                 [-b BEFORE_CONTEXT] [-c CONTEXT] [--color] [--no-color]
                 [-u USER] [-f] [-F] [-o] [-v] [-V] [-D]
                 text [text ...]

grep for groupme, version 1.0.0

positional arguments:
  text                  text to search

optional arguments:
  -h, --help            show this help message and exit
  -g GROUP, --group GROUP
                        group to search. can be specified multiple times
  -l, --list            show all available groups and exit
  -q, --quiet           don't show who said something
  -d, --date            show the date a message was sent
  -i, --ignore-case     ignore case distinctions in both text and groups
  -a AFTER_CONTEXT, -A AFTER_CONTEXT, --after-context AFTER_CONTEXT
                        show the following n messages after a match
  -b BEFORE_CONTEXT, -B BEFORE_CONTEXT, --before-context BEFORE_CONTEXT
                        show the previous n messages before a match
  -c CONTEXT, -C CONTEXT, --context CONTEXT
                        show n messages around a match. overrides -A and -B.
  --color               always color output
  --no-color            never color output
  -u USER, --user USER  search by username. can be specified multiple times
  -f, --favorited, --liked
                        only show liked messages
  -F, --not-favorited, --not-liked
                        never show liked messages
  -o, --only-matching   only show text that matched, not the whole message
  -v, --reverse-matching
                        only show messages that didn't match
  -V, --version         show version
  -D, --delete-cached   delete cached credentials. useful if you mistype in
                        the inital login prompt
```

Note that `group` defaults to '^ACM$'.
Unicode is handled fine, see below.

## For Developers
### Testing
1. `pip install -r dev-requirements.txt`
2. `pytest`

If you see any test failures, it's a bug! Please let me know: https://github.com/jyn514/GrepMe/issues
If you have suggestions for more tests, those are also welcome.

### Contributing
Fork the repository, make some changes, make a pull request.
Note: the script `test/pre-commit` will be run on any commit.
You may want to run it automatically yourself: `ln -s ../test/pre-commit .git/hooks`
