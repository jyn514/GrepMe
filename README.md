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

## Example
```
$ python3 grep.py --group 'CSCE 518' text
Namespace(group=['CSCE 518'], text=['text'])
hey guys i will be mising class next tuesday and looking at the slides there is a lot pf context and information that is missing from the lecture slides that ronni will be talking about in class. would anyone be kind enough to take detailed and copious notes? i would really appreciate it - thanks a lot!
$ # regex supported (anything you can put in `re.search`)
$ python3 grep.py --group 'CSCE 518' '.*re.*'
It started off great and then I turned the page and it was downhill from there
i'm at tcoop, lemme walk down to 2A22 real quick
Can you explain what that means a bit more?
is that one of those christmas tree packets where all the flags are open?
Anyone want to meet in Swearingen to go over the TCP dumps in Lecture 16?
No worries, hey guys if any of you have the quiz on commands, could you send me a pic? I wasn't there that day, sadly �
i just finished the commands as well but since you put yours here, i guess i dont need to haha
...
```
