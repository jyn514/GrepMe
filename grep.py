import re
import requests
from sys import stderr

from login import access_token

groupme = 'https://api.groupme.com/v3'

def get(url, **params):
    params['token'] = access_token
    response = requests.get(groupme + url, params=params)
    if 200 <= response.status_code < 300:
        return response.json()['response']
    raise RuntimeError(response, "Got bad status code")

def get_messages(group, before_id=None, limit=100):
    query = '/groups/' + group + '/messages'
    return get(query, before_id=before_id)

def search_messages(text, group):
    last = None
    buffer = get_messages(group)
    while last != buffer['messages'][-1]['id']:
        for message in buffer['messages']:
            # uploads don't need text
            if message['text'] is not None:
                for t in text:
                    if re.search(t, message['text']):
                        yield message
        last = buffer['messages'][-1]['id']
        try:
            buffer = get_messages(group, before_id=last)
        except RuntimeError as e:
            if e.args[0].status_code == 304:
                raise StopIteration() from e
            raise

def get_group(name):
    page = 1
    response = get('/groups', omit='memberships', per_page=100)
    while response != []:
        for group in response:
            if re.search(name, group['name']):
                yield group['id']
        page += 1
        response = get('/groups', omit='memberships', page=page, per_page=100)

def main(text, group_names):
    for group_name in group_names:
        try:
            group = next(get_group(group_name))
        except StopIteration:
            print("ERROR: Group", group_name, "not found", file=stderr)
            continue
        for message in search_messages(text, group):
            print(message['text'])

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("text", nargs='+', help='text to search')
    parser.add_argument('--group', action='append',
                        help='group to search')
    args = parser.parse_args()
    # https://bugs.python.org/issue16399
    if args.group is None:
        args.group = ['ACM']
    main(args.text, args.group)