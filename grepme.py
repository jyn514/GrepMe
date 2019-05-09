#!/usr/bin/env python
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
import sys
import warnings
from argparse import ArgumentParser
from datetime import datetime

import requests
import login

VERSION = "1.2.0"
HOMEPAGE = "https://github.com/jyn514/grepme"

GROUPME_API = 'https://api.groupme.com/v3'
RED = '\x1b[31m'
GREEN = '\x1b[32m'
YELLOW = '\x1b[33m'
PURPLE = '\x1b[35m'
RESET = '\x1b[0m'

EMPTY_MATCH = re.match('^', '')


def get(url, **params):
    '''Get a GroupMe API url using requests.
    Can have arbitrary string parameters
    which will be part of the GET query string.'''
    params['token'] = login.get_login()
    response = requests.get(GROUPME_API + url, params=params)
    if 200 <= response.status_code < 300:
        if response.status_code != 200:
            warnings.warn("Unexpected status code %d when querying %s. "
                          "Please open an issue at %s/issues/new"
                          % (response.status_code, response.request.url, HOMEPAGE))
        return response.json()['response']
    if response.status_code == 304:
        return None
    if response.status_code == 401:
        exit("Permission denied. Maybe you typed your password wrong? "
             "Try changing it with -D.")
    raise RuntimeError(response, "Got bad status code when querying "
                       + response.request.url)


def get_logged_in_user():
    "return the user id of the user whose credentials we're using"
    # static variable: https://stackoverflow.com/questions/279561/
    if 'cache' not in get_logged_in_user.__dict__:
        response = get('/users/me')
        if response is None:
            raise RuntimeError(response, "Could not get current user")
        get_logged_in_user.cache = response['id']
    return get_logged_in_user.cache


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
    user_id: int: id of user. use get_group(dm=True) to convert username to id.
    before_id: int: id of message to start at, going backwards
    limit: int: number of messages to fetch at once
    '''
    query = '/direct_messages'
    response = get(query, other_user_id=user_id,
                   before_id=before_id, limit=limit)
    if response is not None:
        return response['direct_messages']
    return []


def search_messages(filter_message, group, config, dm=False):
    '''Generator. Given some regex, search a group for messages matching that regex.
    regex: _sre.SRE_Pattern: regex created using `re.compile`
    group: _sre.SRE_Pattern: regex created using `re.compile`
    dm: bool: whether the group is a direct message or not
    '''
    get_function = get_dm if dm else get_messages
    last = None
    buffer = get_function(group)
    while buffer:
        for i, message in enumerate(buffer):
            result = filter_message(message)
            if result is None:
                continue
            if not config.reverse_matching:
                if config.only_matching:
                    message['text'] = result.group()
                    start, end = 0, len(result.group())
                else:
                    start, end = result.span()
                if config.color:
                    message['text'] = message['text'][:start] + RED \
                        + message['text'][start:end] + RESET + message['text'][end:]
            # TODO: this may break if the text comes right at the end of a page
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
        def data(group):
            'the identity function'
            return group
    else:
        def get_f(page=None):
            'return direct messages, paginated'
            return get('/chats', page=page, per_page=100)
        def data(group):
            'return the username of the person messaged'
            return group['other_user']
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
            yield group['name'], group['id']


def print_message(buffer, i, config):
    '''Pretty-print a dict with GroupMe API keys.'''
    # groupme api returns results in reverse order,
    # we do fancy indexing so we don't waste time reversing the whole buffer
    for message in reversed(buffer[i - config.after_context:
                                   i + config.before_context + 1]):
        if config.date:
            date = datetime.utcfromtimestamp(message['created_at'])
            if config.color:
                print(GREEN, end='')
            print(date.strftime('%c'), end=': ')
        if config.show_users:
            if config.color:
                print(PURPLE, end='')
            print(message['name'], end=': ')
        if config.color:
            print(RESET, end='')
        print(message['text'])


def print_group(group, color=True):
    "pretty-print a group name"
    if color:
        print("%s--- %s ---%s" % (YELLOW, group, RESET))
    else:
        print("--- %s ---" % group)


def make_parser():
    "create a parser grepme. makes the main method easier to read"
    parser = ArgumentParser(description="grep for groupme, version " + VERSION)
    parser.add_argument("regex", nargs='+', help='text to search')
    parser.add_argument('-g', '--group', action='append',
                        help='group to search. can be specified multiple times')
    parser.add_argument('-l', '--list', action='store_true',
                        help='show all available groups and exit')
    parser.add_argument('-q', '--quiet', action='store_false',
                        dest='show_users', help="don't show who said something")
    parser.add_argument('-d', '--date', action='store_true',
                        help='show the date a message was sent')
    parser.add_argument('-i', '--ignore-case', action='store_true', default=False,
                        help='ignore case distinctions in both text and groups')
    parser.add_argument('-a', '-A', '--after-context', type=int, default=0,
                        help="show the following n messages after a match")
    parser.add_argument('-b', '-B', '--before-context', type=int, default=0,
                        help="show the previous n messages before a match")
    parser.add_argument('-c', '-C', '--context', type=int,
                        help="show n messages around a match. overrides -A and -B.")
    parser.add_argument('-u', '--user', action='append',
                        help='search by username. can be specified multiple times')
    parser.add_argument('-o', '--only-matching', action='store_true',
                        help="only show text that matched, not the whole message")
    parser.add_argument('-v', '--reverse-matching', action='store_true',
                        help="only show messages that didn't match")
    parser.add_argument("-V", '--version', action='version',
                        version='%(prog)s ' + VERSION, help="show version")
    parser.add_argument('-D', '--delete-cached', action='store_true',
                        help="delete cached credentials. useful if you mistype "
                             "in the inital login prompt")
    color = parser.add_mutually_exclusive_group()
    color.add_argument('--color', action='store_true', default=sys.stdin.isatty(),
                       help='always color output')
    color.add_argument('--no-color', action='store_false', dest='color',
                       help='never color output')
    # TODO: remove this check when we allow arbitrary entries for liked
    favorites = parser.add_mutually_exclusive_group()
    favorites.add_argument('-f', '--favorited', '--liked', action='store_true',
                           help="only show liked messages")
    favorites.add_argument('-F', '--not-favorited', '--not-liked',
                           action='store_true', help="never show liked messages")
    return parser


def make_config(args):
    'post process args in a helper function for library reuse'
    # default argument for list: https://bugs.python.org/issue16399
    if args.group is None:
        args.group = ['ACM']
    if args.user is None:
        args.user = []
    if args.favorited:
        args.favorited = {get_logged_in_user()}
    if args.not_favorited:
        args.not_favorited = {get_logged_in_user()}

    flags = re.DOTALL
    if args.ignore_case:
        flags |= re.IGNORECASE

    if args.context is not None:
        args.after_context = args.before_context = args.context

    args.groups = re.compile('|'.join(args.group), flags=flags)
    args.regex = re.compile('|'.join(args.regex), flags=flags)
    args.users = re.compile('|'.join(args.user), flags=flags)

    args.filter_message = make_filter(args)
    return args


def make_filter(config):
    """given a config namespace,
    return a function which filters messages appropriately.
    useful if you want to test `filter_message`"""
    def filter_message(message):
        if (message['text'] is None
                or config.users.pattern and not re.search(config.users, message['name'])
                or config.favorited and config.favorited.isdisjoint(message['favorited_by'])
                or config.not_favorited and
                   config.not_favorited.intersection(message['favorited_by'])):
            return None
        result = config.regex.search(message['text'])
        if bool(result) == config.reverse_matching:
            return None
        return result if result is not None else EMPTY_MATCH
    return filter_message


def search_all(args):
    "the real main method. given some config, search for all matching messages"
    for name, group in get_group(args.groups):
        print_group(name, color=args.color)
        for buffer, i in search_messages(args.filter_message, group, args):
            print_message(buffer, i, args)
    for name, user in get_group(args.groups, dm=True):
        print_group(name, color=args.color)
        for buffer, i in search_messages(args.filter_message, user, args, dm=True):
            print_message(buffer, i, args)


def main():
    'parse arguments and convert text to regular expressions'
    # the hacky stuff, this you really don't want in a library probably
    # text not required when --list passed
    for i, arg in enumerate(sys.argv):
        if arg == '--':
            break
        elif arg in ['--list', '-l'] and (i == 0 or sys.argv[i - 1] != '--group'):
            for group in get_all_groups():
                print(group['name'])
            exit()
        elif arg in ['-D', '--delete-cached']:
            login.delete_cached()

    config = make_config(make_parser().parse_args())

    # main program
    try:
        search_all(config)
    except KeyboardInterrupt:
        print()  # so it looks nice and we don't have ^C<prompt>
    except BrokenPipeError:
        pass


if __name__ == '__main__':
    main()
