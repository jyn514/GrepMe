import json
import os
import sys
from warnings import warn

import certifi
import urllib3
from diskcache import Cache

from . import login
from .constants import HOMEPAGE

GROUPME_API = "https://api.groupme.com/v3"

# keeps connections alive for a while so that you don't waste
# time on an SSL handshake for every request
HTTP = urllib3.PoolManager(cert_reqs="CERT_REQUIRED", ca_certs=certifi.where())

# cache directory for saved files
_cache_dir = os.environ.get(
    "XDG_CACHE_HOME", os.path.join(os.path.expanduser("~"), ".cache")
)
CACHE_DIR = os.path.join(_cache_dir, "grepme")
CACHE = Cache(CACHE_DIR)


def get(url, allow_cache=True, **fields):
    # remove None entries
    fields = {k: v for k, v in fields.items() if v is not None}

    if not allow_cache:
        return _get(url, **fields)

    key = (url, fields)
    val = CACHE.get(key)
    if val is None:
        val = _get(url, **fields)
        CACHE.set(key, val)
    return val


def _get(url, **fields):
    """Get a GroupMe API url using urllib3.
    Can have arbitrary string parameters
    which will be part of the GET query string."""
    fields["token"] = login.get_login()
    response = HTTP.request("GET", GROUPME_API + url, fields=fields)

    # 2XX Success
    if 200 <= response.status < 300:
        if response.status != 200:
            warn(
                "Unexpected status code %d when querying %s. "
                "Please open an issue at %s/issues/new"
                % (response.status, response.geturl(), HOMEPAGE)
            )
        data = response.data.decode("utf-8")
        return json.loads(data)["response"]

    # 304 Not Modified: we reached the end of the data
    if response.status == 304:
        return None

    # 401 Not Authorized
    if response.status == 401:
        sys.exit(
            "Permission denied. Maybe you typed your password wrong? "
            "Try changing it with -D."
        )

    # Unknown status code
    raise RuntimeError(
        response,
        "Got bad status code %d when querying %s: %s"
        % (response.status, response.geturl(), response.data.decode("utf-8")),
    )
