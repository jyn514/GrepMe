from __future__ import print_function

import os
import sys

from getpass import getpass
import keyring

ACCESS_TOKEN = None


def get_login():
    global ACCESS_TOKEN
    if ACCESS_TOKEN is None:
        ACCESS_TOKEN = keyring.get_password("system", "grepme")
    if ACCESS_TOKEN is None:
        if sys.stdin.isatty():
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
            exit("Failed to read credentials")
        keyring.set_password("system", "grepme", ACCESS_TOKEN)
    return ACCESS_TOKEN


def delete_cached():
    global ACCESS_TOKEN
    try:
        keyring.delete_password("system", "grepme")
    except keyring.errors.PasswordDeleteError:
        pass
    ACCESS_TOKEN = None
