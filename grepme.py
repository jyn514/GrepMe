#!/usr/bin/env python3
'''Grepme: grep for GroupMe'''
import re
from datetime import datetime

import requests

from login import access_token

GROUPME_API = 'https://api.groupme.com/v3'

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

def search_messages(regex, group, dm=False):
    '''Generator. Given some regex, search a group for messages matching that regex.
    regex: _sre.SRE_Pattern: regex created using `re.compile`
    group: _sre.SRE_Pattern: regex created using `re.compile`
    dm: bool: whether the group is a direct message or not
    '''
    get_function = get_dm if dm else get_messages
    last = None
    buffer = get_function(group)
    while len(buffer):
        for message in buffer:
            # uploads don't need text
            if message['text'] is not None and regex.search(message['text']):
                yield message
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

def print_message(message, show_users=True, show_date=True):
    '''Pretty-print a dict with GroupMe API keys.'''
    if show_date:
        date = datetime.utcfromtimestamp(message['created_at'])
        print(date.strftime('%c'), end=': ')
    if show_users:
        print(message['name'], end=': ')
    print(message['text'])

def main():
    'parse arguments and convert text to regular expressions'
    from argparse import ArgumentParser
    from sys import argv
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
    parser.add_argument('--group', action='append',
                        help='group to search. can be specified multiple times')
    parser.add_argument('-l', '--list', action='store_true',
                        help='show all available groups and exit')
    parser.add_argument('-q', '--quiet', action='store_false',
                        dest='show_users', help="don't show who said something")
    parser.add_argument('-d', '--date', action='store_true',
                        help='show the date a message was sent')
    parser.add_argument('-i', '--ignore-case', action='store_true',
                        help='ignore case distinctions in both text and groups')
    args = parser.parse_args()
    # default argument for list: https://bugs.python.org/issue16399
    if args.group is None:
        args.group = ['ACM']

    flags = 0
    if args.ignore_case:
        flags |= re.IGNORECASE
    groups = re.compile('|'.join(args.group), flags=flags)
    regex = re.compile('|'.join(args.text), flags=flags)

    for group in get_group(groups):
        for message in search_messages(regex, group):
            print_message(message, show_users=args.show_users, show_date=args.date)
    for user in get_group(groups, dm=True):
        for message in search_messages(args.text, user, dm=True):
            print_message(message, show_users=args.show_users, show_date=args.date)

if __name__ == '__main__':
    main()
