from getpass import getpass
import keyring

def get_login():
    access_token = keyring.get_password("system", "grepme")
    if access_token is None:
        access_token = getpass("Groupme Access token: ")
        keyring.set_password("system", "grepme", access_token)
    return access_token

def delete_cached():
    keyring.delete_password("system", "grepme")
    return get_login()
