import re
from argparse import Namespace

import pytest
from hypothesis import example, given, strategies

import grepme

# cache this for later
grepme.get_logged_in_user()


def config(*args):
    return grepme.make_config(grepme.make_parser().parse_args(args=args))


def match_anything(message, *config_args):
    return grepme.filter_message(message, config(".*", *config_args))


@given(strategies.text())
def test_nothing_matches(text):
    assert match_anything({"text": text}, "-v") is None


@given(strategies.text())
@example("\n")
def test_everything_matches(text):
    assert match_anything({"text": text}).group() is text


@given(strategies.text())
def test_favorited(text):
    assert (
        match_anything(
            {"text": text, "favorited_by": [grepme.get_logged_in_user()]}, "-f"
        ).group()
        is text
    )
    assert match_anything({"text": text, "favorited_by": []}, "-f") is None
    assert (
        match_anything(
            {"text": text, "favorited_by": [grepme.get_logged_in_user()]}, "-F"
        )
        is None
    )
    assert match_anything({"text": text, "favorited_by": []}, "-F").group() is text


@given(strategies.text())
def test_user(text):
    assert match_anything({"text": "blah", "name": text}, "-u", ".*").group() is "blah"
    # a^: don't match any user
    assert match_anything({"text": "blah", "name": text}, "-u", "a^") is None


def test_illegal_arguments():
    with pytest.raises(SystemExit):
        config("-f", "-F")
