#!/usr/bin/env python
"""Grepme: grep for GroupMe

Copyright (c) 2019 Joshua Nelson
Licensed under BSD 3-Clause license.
See LICENSE for details.
"""
# python2 compat
from __future__ import print_function

try:
    BrokenPipeError
except NameError:
    from socket import error as BrokenPipeError

import sys
from . import login
from .lib import make_config, make_parser, search_all, get_all_groups


def main():
    "parse arguments and convert text to regular expressions"
    # the hacky stuff, this you really don't want in a library probably
    # text not required when --list passed
    for i, arg in enumerate(sys.argv):
        if arg == "--":
            pass
        elif arg in ["--list", "-l"] and (i == 0 or sys.argv[i - 1] != "--group"):
            for group in get_all_groups():
                print(group["name"])
            sys.exit()
        elif arg in ["-D", "--delete-cached"]:
            login.delete_cached()

    config = make_config(make_parser().parse_args())

    # main program
    try:
        search_all(config)
    except KeyboardInterrupt:
        print()  # so it looks nice and we don't have ^C<prompt>
    except BrokenPipeError:
        pass


if __name__ == "__main__":
    main()
