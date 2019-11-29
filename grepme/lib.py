#!/usr/bin/env python
"""Grepme: grep for GroupMe

Copyright (c) 2019 Joshua Nelson
Licensed under BSD 3-Clause license.
See LICENSE for details.
"""
# python2 compat
from __future__ import print_function

import re
import json
from argparse import ArgumentParser
from datetime import datetime
from sys import stdin

from .http import get
from .constants import VERSION

# ANSI terminal color codes
RED = "\x1b[31m"
GREEN = "\x1b[32m"
YELLOW = "\x1b[33m"
PURPLE = "\x1b[35m"
RESET = "\x1b[0m"

EMPTY_MATCH = re.match("^", "")


def get_logged_in_user():
    "return the user id of the user whose credentials we're using"
    # static variable: https://stackoverflow.com/questions/279561/
    if "cache" not in get_logged_in_user.__dict__:
        response = get("/users/me")
        if response is None:
            raise RuntimeError(response, "Could not get current user")
        get_logged_in_user.cache = response["id"]
    return get_logged_in_user.cache


def add_attachments(message):
    if "attachments" not in message:
        return
    pictures = list(filter(lambda a: a["type"] == "image", message["attachments"]))
    if not pictures:
        return
    if message["text"] is None:
        message["text"] = ""
    else:
        message["text"] += "\n"
    for attachment in pictures:
        message["text"] += "\nimage: " + attachment["url"]


def get_messages(group, before_id=None, limit=100):
    """Get messages from a group.
    group: str: id of the group to get messages for
    before_id: int: id of the message to start at, going backwards
    limit: int: number of messages to fetch at once"""
    query = "/groups/" + group + "/messages"
    response = get(
        query, allow_cache=before_id is not None, before_id=before_id, limit=limit
    )
    if response is not None:
        return response["messages"]
    return []


def get_dm(user_id, before_id=None, limit=100):
    """Get direct messages from a user.
    user_id: int: id of user. use get_group(dm=True) to convert username to id.
    before_id: int: id of message to start at, going backwards
    limit: int: number of messages to fetch at once
    """
    query = "/direct_messages"
    response = get(
        query,
        other_user_id=user_id,
        limit=limit,
        allow_cache=before_id is not None,
        before_id=before_id,
    )
    if response is not None:
        return response["direct_messages"]
    return []


def search_messages(group, config, dm=False):
    """Generator. Find all messages which are matched by `filter_message`
    filter_message: a function taking a dictionary and returning a boolean
    group: _sre.SRE_Pattern: regex created using `re.compile`
    config: an object with the boolean properties
            'reverse_matching', 'only_matching', and 'color'
    dm: bool: whether the group is a direct message or not

    Note below that the while loop comes right before a for loop.
    Note also the yield instead of a return.
    This is a common pattern for grepme: GroupMe returns an arbitrarily large amount
    of data (sometimes gigabytes!) and it would far too expensive to process it
    all at once. Instead, we process a fixed amount at a time (usually 100 messages)
    and yield it one message at a time so it's evaluated lazily.
    """
    get_function = get_dm if dm else get_messages
    last = None
    buffer = get_function(group)
    while buffer:
        for i, message in enumerate(buffer):
            result = filter_message(message, config)
            if result is None:
                continue
            if not config.reverse_matching:
                if config.only_matching:
                    message["text"] = result.group()
                    start, end = 0, len(result.group())
                else:
                    start, end = result.span()
                if config.color:
                    message["text"] = (
                        message["text"][:start]
                        + RED
                        + message["text"][start:end]
                        + RESET
                        + message["text"][end:]
                    )
            # TODO: this may not show all context if the text comes right at the end of a page
            yield buffer, i
        last = buffer[-1]["id"]
        buffer = get_function(group, before_id=last)


def get_all_groups(dm=False):
    """Generator. Yield all groups available.
    dm: bool: whether to get direct messages or groups
    """
    if dm:

        def get_f(page=1):
            "return direct messages, paginated"
            return get("/chats", allow_cache=False, page=page, per_page=100)

        def data(group):
            "return the username of the person messaged"
            return group["other_user"]

    else:

        def get_f(page=1):
            "return groups, paginated"
            return get(
                "/groups",
                allow_cache=False,
                omit="memberships",
                per_page=100,
                page=page,
            )

        def data(group):
            "the identity function"
            return group

    page = 1
    response = get_f()
    # see search_messages for description of while/for/yield pattern
    while response:
        for group in response:
            yield data(group)
        page += 1
        response = get_f(page)


def get_group(regex, dm=False):
    """Generator. Yield all groups matching `regex` in the format (name, id).
    regex: _sre.SRE_Pattern: regex created using `re.compile`
    dm: bool: whether the group should be a direct message or not
    """
    for group in get_all_groups(dm):
        if regex.search(group["name"]):
            yield group["name"], group["id"]


def print_message(buffer, i, config):
    """Pretty-print one or more messages
    buffer: list[object]: [{
        created_at: str,
        name: str,
        text: str,
    }]: messages to print
    i: int: the index of the message to start at
    config: object: {
        date: bool: whether to print the date the message was sent
        show_users: bool: whether to print the user who said a message
        color: bool: whether to print in color
        before_context: int: the number of messages before the i'th to print
        after_context: int: the number of messages after the i'th to print
        json: bool: whether to print as JSON or text
    }"""
    # groupme api returns results in reverse order,
    # we do fancy indexing so we don't waste time reversing the whole buffer
    for message in reversed(
        buffer[i - config.after_context : i + config.before_context + 1]
    ):
        if config.json:
            # just dump the whole thing
            print(json.dumps(message))
            continue
        if config.date:
            date = datetime.utcfromtimestamp(message["created_at"])
            if config.color:
                print(GREEN, end="")
            print(date.strftime("%c"), end=": ")
        if config.show_users:
            if config.color:
                print(PURPLE, end="")
            print(message["name"], end=": ")
        if config.color:
            print(RESET, end="")
        add_attachments(message)
        print(message["text"])


def print_group(group, color=True):
    "pretty-print a group name"
    if color:
        print("%s--- %s ---%s" % (YELLOW, group, RESET))
    else:
        print("--- %s ---" % group)


def make_parser():
    "create a parser grepme. makes the main method easier to read"
    parser = ArgumentParser(description="grep for groupme, version " + VERSION)
    parser.add_argument("regex", nargs="+", help="text to search")
    parser.add_argument(
        "-g",
        "--group",
        action="append",
        help="group to search. can be specified multiple times",
    )
    parser.add_argument(
        "-l", "--list", action="store_true", help="show all available groups and exit"
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_false",
        dest="show_users",
        help="don't show who said something",
    )
    parser.add_argument(
        "-d", "--date", action="store_true", help="show the date a message was sent"
    )
    parser.add_argument(
        "-i",
        "--ignore-case",
        action="store_true",
        default=False,
        help="ignore case distinctions in both text and groups",
    )
    parser.add_argument(
        "-a",
        "-A",
        "--after-context",
        type=int,
        default=0,
        help="show the following n messages after a match",
    )
    parser.add_argument(
        "-b",
        "-B",
        "--before-context",
        type=int,
        default=0,
        help="show the previous n messages before a match",
    )
    parser.add_argument(
        "-c",
        "-C",
        "--context",
        type=int,
        help="show n messages around a match. overrides -A and -B.",
    )
    parser.add_argument(
        "-u",
        "--user",
        action="append",
        help="search by username. can be specified multiple times",
    )
    parser.add_argument(
        "-o",
        "--only-matching",
        action="store_true",
        help="only show text that matched, not the whole message",
    )
    parser.add_argument(
        "-v",
        "--reverse-matching",
        action="store_true",
        help="only show messages that didn't match",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version="%(prog)s " + VERSION,
        help="show version",
    )
    parser.add_argument(
        "-D",
        "--delete-cached",
        action="store_true",
        help="delete cached credentials. useful if you mistype "
        "in the inital login prompt",
    )
    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="delete cached message. you should very rarely have to use this option",
    )
    color = parser.add_mutually_exclusive_group()
    color.add_argument(
        "--color",
        action="store_true",
        default=stdin.isatty(),
        help="always color output",
    )
    color.add_argument(
        "--no-color", action="store_false", dest="color", help="never color output"
    )
    parser.add_argument(
        "--json", action="store_true", default=False, help="print messages as JSON"
    )
    # TODO: remove this check when we allow arbitrary entries for liked
    favorites = parser.add_mutually_exclusive_group()
    favorites.add_argument(
        "-f",
        "--favorited",
        "--liked",
        action="store_true",
        help="only show liked messages",
    )
    favorites.add_argument(
        "-F",
        "--not-favorited",
        "--not-liked",
        action="store_true",
        help="never show liked messages",
    )
    return parser


def make_config(args):
    "post process args in a helper function for library reuse"
    # default argument for list: https://bugs.python.org/issue16399
    if args.group is None:
        args.group = ["ACM"]
    if args.user is None:
        args.user = []
    # default arguments for set (so login isn't evaluated eagerly)
    if args.favorited:
        args.favorited = {get_logged_in_user()}
    if args.not_favorited:
        args.not_favorited = {get_logged_in_user()}

    flags = re.DOTALL
    if args.ignore_case:
        flags |= re.IGNORECASE

    if args.context is not None:
        args.after_context = args.before_context = args.context

    if args.json:
        args.color = False

    args.groups = re.compile("|".join(args.group), flags=flags)
    args.regex = re.compile("|".join(args.regex), flags=flags)
    args.users = re.compile("|".join(args.user), flags=flags)

    if args.clear_cache:
        import shutil
        from .http import CACHE_DIR

        shutil.rmtree(CACHE_DIR)

    return args


def filter_message(message, config):
    "a function which filters messages based on some config"
    if (
        message["text"] is None
        or config.users.pattern
        and not re.search(config.users, message["name"])
        or config.favorited
        and config.favorited.isdisjoint(message["favorited_by"])
        or config.not_favorited
        and config.not_favorited.intersection(message["favorited_by"])
    ):
        return None
    result = config.regex.search(message["text"])
    if bool(result) == config.reverse_matching:
        return None
    return result if result is not None else EMPTY_MATCH


def search_all(args):
    "the real main method. given some config, search for all matching messages"
    # search groups and dms
    for dm in [True, False]:
        for name, group in get_group(args.groups, dm=dm):
            if not args.json:
                print_group(name, color=args.color)
            for buffer, i in search_messages(group, args, dm=dm):
                print_message(buffer, i, args)
