from getpass import getpass
import keyring

access_token = None

def get_login():
    global access_token
    if access_token is None:
        access_token = keyring.get_password("system", "grepme")
    if access_token is None:
        access_token = getpass("Groupme Access token: ")
        keyring.set_password("system", "grepme", access_token)
    return access_token

def delete_cached():
    global access_token
    try:
        keyring.delete_password("system", "grepme")
    except keyring.errors.PasswordDeleteError:
        pass
    access_token = None
