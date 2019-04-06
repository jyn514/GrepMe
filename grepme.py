#!/usr/bin/env python3
'''Grepme: grep for GroupMe

Copyright (c) 2019 Joshua Nelson
Licensed under BSD 3-Clause license.
See LICENSE for details.
'''
# python2 compat
from __future__ import print_function
try:
    BrokenPipeError
except NameError:
    from socket import error as BrokenPipeError

import re
from os import isatty
from datetime import datetime

import requests

VERSION = "1.0.0"

GROUPME_API = 'https://api.groupme.com/v3'
GREEN = '\x1b[32m'
RED = '\x1b[31m'
PURPLE = '\x1b[35m'
RESET = '\x1b[0m'

def get(url, **params):
    '''Get a GroupMe API url using requests.
    Can have arbitrary string parameters which will be part of the GET query string.'''
    params['token'] = access_token
    response = requests.get(GROUPME_API + url, params=params)
    if 200 <= response.status_code < 300:
        return response.json()['response']
    if response.status_code == 304:
        return None
    raise RuntimeError(response, "Got bad status code")

def get_logged_in_user():
    response = get('/users/me')
    return response['id']

def get_messages(group, before_id=None, limit=100):
    '''Get messages from a group.
    before_id: int: id of the message to start at, going backwards
    limit: int: number of messages to fetch at once'''
    query = '/groups/' + group + '/messages'
    response = get(query, before_id=before_id, limit=limit)
    if response is not None:
        return response['messages']
    return []

def get_dm(user_id, before_id=None, limit=100):
    '''Get direct messages from a user.
    user_id: int: id of user. use get_group(text, dm=True) to convert text to id.
    before_id: int: id of message to start at, going backwards
    limit: int: number of messages to fetch at once
    '''
    query = '/direct_messages'
    response = get(query, other_user_id=user_id, before_id=before_id, limit=limit)
    if response is not None:
        return response['direct_messages']
    return []

def search_messages(regex, group, dm=False, interactive=False, users=None,
        liked=None, not_liked=None, only_matching=False, reverse_matching=False):
    '''Generator. Given some regex, search a group for messages matching that regex.
    regex: _sre.SRE_Pattern: regex created using `re.compile`
    group: _sre.SRE_Pattern: regex created using `re.compile`
    dm: bool: whether the group is a direct message or not
    '''
    get_function = get_dm if dm else get_messages
    last = None
    buffer = get_function(group)
    while len(buffer):
        for i, message in enumerate(buffer):
            # uploads don't always have text
            if (message['text'] is None
                or users and not re.search(users, message['name'])
                or liked and liked.isdisjoint(message['favorited_by'])
                or not_liked and not_liked.intersection(message['favorited_by'])):
                continue
            result = regex.search(message['text'])
            if bool(result) == reverse_matching:
                continue
            if not reverse_matching:
                if only_matching:
                    message['text'] = result.group()
                    start, end = 0, len(result.group())
                else:
                    start, end = result.span()
                if interactive:
                    message['text'] = message['text'][:start] + RED \
                            + message['text'][start:end] + RESET + message['text'][end:]
            # note this may break if the text comes right at the end of a page,
            # this has not been tested
            yield buffer, i
        last = buffer[-1]['id']
        buffer = get_function(group, before_id=last)

def get_all_groups(dm=False):
    '''Generator. Yield all groups available.
    dm: bool: whether to get direct messages or groups
    '''
    if not dm:
        def get_f(page=None):
            'return groups, paginated'
            return get('/groups', omit='memberships', per_page=100, page=page)
        data = lambda group: group
    else:
        def get_f(page=None):
            'return direct messages, paginated'
            return get('/chats', page=page, per_page=100)
        data = lambda group: group['other_user']
    page = 1
    response = get_f()
    while response != []:
        for group in response:
            yield data(group)
        page += 1
        response = get_f(page)

def get_group(regex, dm=False):
    '''Generator. Yield all groups matching `regex`.
    regex: _sre.SRE_Pattern: regex created using `re.compile`
    dm: bool: whether the group should be a direct message or not
    '''
    for group in get_all_groups(dm):
        if regex.search(group['name']):
            yield group['id']

def print_message(buffer, i, show_users=True, show_date=True, before=0, after=0,
        interactive=False):
    '''Pretty-print a dict with GroupMe API keys.'''
    # groupme api returns results in reverse order,
    # we do fancy indexing so we don't waste time reversing the whole buffer
    for message in reversed(buffer[i - after:i + before + 1:]):
        if show_date:
            date = datetime.utcfromtimestamp(message['created_at'])
            if interactive:
                print(GREEN, end='')
            print(date.strftime('%c'), end=': ')
        if show_users:
            if interactive:
                print(PURPLE, end='')
            print(message['name'], end=': ')
        if interactive:
            print(RESET, end='')
        print(message['text'])

def main():
    'parse arguments and convert text to regular expressions'
    try:
        global access_token
        from login import access_token
    except ImportError:
        print("Failed to get login credentials. See README for details:\n",
            "https://github.com/jyn514/GrepMe/blob/%s/README.md" % VERSION)

    from argparse import ArgumentParser
    from sys import argv, stdin
    # text not required when --list passed
    for i, arg in enumerate(argv):
        if arg == '--':
            break
        elif arg in ['--list', '-l'] and (i == 0 or argv[i - 1] != '--group'):
            for group in get_all_groups():
                print(group['name'])
            exit()
    parser = ArgumentParser()
    parser.add_argument("text", nargs='+', help='text to search')
    parser.add_argument('-g', '--group', action='append',
                        help='group to search. can be specified multiple times')
    parser.add_argument('-l', '--list', action='store_true',
                        help='show all available groups and exit')
    parser.add_argument('-q', '--quiet', action='store_false',
                        dest='show_users', help="don't show who said something")
    parser.add_argument('-d', '--date', action='store_true',
                        help='show the date a message was sent')
    parser.add_argument('-i', '--ignore-case', action='store_true',
                        help='ignore case distinctions in both text and groups')
    parser.add_argument('-a', '-A', '--after-context', type=int, default=0,
                        help="show the following n messages after a match")
    parser.add_argument('-b', '-B', '--before-context', type=int, default=0,
                        help="show the previous n messages before a match")
    parser.add_argument('-c', '-C', '--context', type=int,
                        help="show n messages around a match. overrides -A and -B.")
    parser.add_argument('--color', action='store_true', default=None,
                        help='always color output')
    parser.add_argument('--no-color', action='store_false', dest='color', default=None,
                        help='never color output')
    parser.add_argument('-u', '--user', action='append',
                        help='search by username. can be specified multiple times')
    parser.add_argument('-f', '--favorited', '--liked', action='store_true',
                        help="only show liked messages")
    parser.add_argument('-F', '--not-favorited', '--not-liked',
        action='store_true', help="never show liked messages")
    parser.add_argument('-o', '--only-matching', action='store_true',
                        help="only show text that matched, not the whole message")
    parser.add_argument('-v', '--reverse-matching', action='store_true',
                        help="only show messages that didn't match")
    args = parser.parse_args()

    # post process args
    # default argument for list: https://bugs.python.org/issue16399
    if args.group is None:
        args.group = ['ACM']
    if args.user is None:
        args.user = []
    if args.favorited and args.not_favorited:
        print("Cannot specify both liked and not liked")
        parser.print_usage()
        exit(1)
    if args.favorited:
        args.favorited = {get_logged_in_user()}
    if args.not_favorited:
        args.not_favorited = {get_logged_in_user()}

    flags = 0
    if args.ignore_case:
        flags |= re.IGNORECASE

    if args.context is not None:
        args.after_context = args.before_context = args.context

    groups = re.compile('|'.join(args.group), flags=flags)
    regex = re.compile('|'.join(args.text), flags=flags)
    users = re.compile('|'.join(args.user), flags=flags)

    if args.color is None:
        args.color = isatty(stdin.fileno())

    # main program
    try:
        for group in get_group(groups):
            for buffer, i in search_messages(regex, group, interactive=args.color,
                    users=users, liked=args.favorited, not_liked=args.not_favorited,
                    only_matching=args.only_matching, reverse_matching=args.reverse_matching):
                print_message(buffer, i, show_users=args.show_users, show_date=args.date,
                              before=args.before_context, after=args.after_context,
                              interactive=args.color)
        for user in get_group(groups, dm=True):
            for buffer, i in search_messages(args.text, user, dm=True,
                    interactive=args.color, liked=args.favorited, not_liked=args.not_favorited, only_matching=args.only_matching, reverse_matching=args.reverse_matching):
                print_message(buffer, i, show_users=args.show_users, show_date=args.date,
                              before=args.before_context, after=args.after_context,
                              interactive=args.color)
    except KeyboardInterrupt:
        print()  # so it looks nice and we don't have ^C<prompt>
    except BrokenPipeError:
        pass

if __name__ == '__main__':
    main()
