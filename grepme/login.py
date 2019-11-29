"""Authentication to GroupMe. Mostly a wrapper around keyring."""
from __future__ import print_function

import os
import sys

from getpass import getpass

from .constants import HOMEPAGE

ACCESS_TOKEN = None


def get_login():
    """Get the access token using various fallbacks"""
    import keyring

    global ACCESS_TOKEN
    if ACCESS_TOKEN is None:
        ACCESS_TOKEN = keyring.get_password("system", "grepme")
    if ACCESS_TOKEN is None:
        if sys.stdin.isatty():
            print(
                "This is the first time logging in (or you have deleted cached credentials)."
            )
            print(
                "You can retrieve your access token from https://dev.groupme.com/applications."
            )
            print("See %s#installing for further instructions." % HOMEPAGE)
            ACCESS_TOKEN = getpass("Groupme Access token: ")
        else:
            print(
                "WARNING: reading credentials from environment. "
                "This is insecure and intended only for testing, "
                "if you see this during normal use please file a bug report.",
                file=sys.stderr,
            )
            ACCESS_TOKEN = os.environ.get("GREPME_API_KEY")
        if ACCESS_TOKEN is None:
            sys.exit("Failed to read credentials")
        keyring.set_password("system", "grepme", ACCESS_TOKEN)
    return ACCESS_TOKEN


def delete_cached():
    """Remove a cached access token"""
    import keyring

    global ACCESS_TOKEN
    try:
        keyring.delete_password("system", "grepme")
    except keyring.errors.PasswordDeleteError:
        pass
    ACCESS_TOKEN = None
