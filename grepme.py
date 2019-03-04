import re
import requests
from sys import stderr
from datetime import datetime

from login import access_token

groupme = 'https://api.groupme.com/v3'

class NotModified(RuntimeError):
    pass

def get(url, **params):
    params['token'] = access_token
    response = requests.get(groupme + url, params=params)
    if 200 <= response.status_code < 300:
        return response.json()['response']
    if response.status_code == 304:
        raise NotModified()
    raise RuntimeError(response, "Got bad status code")

def get_messages(group, before_id=None, limit=100):
    query = '/groups/' + group + '/messages'
    return get(query, before_id=before_id, limit=limit)['messages']

def get_dm(user_id, before_id=None, limit=100):
    query = '/direct_messages'
    return get(query, other_user_id=user_id, before_id=before_id, limit=limit)['direct_messages']

def search_messages(text, group, dm=False):
    get_function = get_dm if dm else get_messages
    last = None
    buffer = get_function(group)
    while len(buffer):
        for message in buffer:
            # uploads don't need text
            if message['text'] is not None:
                for t in text:
                    if re.search(t, message['text']):
                        yield message
        last = buffer[-1]['id']
        try:
            buffer = get_function(group, before_id=last)
        except NotModified:
            break

def get_all_groups(dm=False):
    if not dm:
        def get_f(page=None):
            return get('/groups', omit='memberships', per_page=100, page=page)
        data = lambda group: group
    else:
        def get_f(page=None):
             return get('/chats', page=page, per_page=100)
        data = lambda group: group['other_user']
    page = 1
    response = get_f()
    while response != []:
        for group in response:
            yield data(group)
        page += 1
        response = get_f(page)

def get_group(group_names, dm=False):
    for group in get_all_groups(dm):
        for group_name in group_names:
            if re.search(group_name, group['name']):
                yield group['id']

def print_message(message, show_users=True, show_date=True):
    if show_date:
        date = datetime.utcfromtimestamp(message['created_at'])
        print(date.strftime('%c'), end=': ')
    if show_users:
        print(message['name'], end=': ')
    print(message['text'])

def main():
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
                        help='group to search')
    parser.add_argument('-l', '--list', action='store_true',
                        help='show all available groups and exit')
    parser.add_argument('-q', '--quiet', action='store_false',
                        dest='show_users', help="don't show who said something")
    parser.add_argument('-d', '--date', action='store_true',
                        help='show the date a message was sent')
    args = parser.parse_args()
    # https://bugs.python.org/issue16399
    if args.group is None:
        args.group = ['ACM']
    for group in get_group(args.group):
        for message in search_messages(args.text, group):
            print_message(message, show_users=args.show_users, show_date=args.date)
    for user in get_group(args.group, dm=True):
        for message in search_messages(args.text, user, dm=True):
            print_message(message, show_users=args.show_users, show_date=args.date)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
