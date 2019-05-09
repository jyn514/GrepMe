from __future__ import print_function

import os
import sys

from getpass import getpass
import keyring

access_token = None

def get_login():
    global access_token
    if access_token is None:
        access_token = keyring.get_password("system", "grepme")
    if access_token is None:
        if sys.stdin.isatty():
            access_token = getpass("Groupme Access token: ")
        else:
            print("WARNING: reading credentials from environment. "
                  "This is insecure and intended only for testing, "
                  "if you see this during normal use please file a bug report.",
                  file=sys.stderr)
            access_token = os.environ.get("GREPME_API_KEY")
        if access_token is None:
            exit("Failed to read credentials")
        keyring.set_password("system", "grepme", access_token)
    return access_token

def delete_cached():
    global access_token
    try:
        keyring.delete_password("system", "grepme")
    except keyring.errors.PasswordDeleteError:
        pass
    access_token = None
