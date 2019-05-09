import re
from argparse import Namespace

import pytest
from hypothesis import example, given, strategies

import grepme

# cache this for later
grepme.get_logged_in_user()

def config(*args):
    return grepme.make_config(grepme.make_parser().parse_args(args=args))


def match_anything(*args):
    return grepme.make_filter(config(".*", *args))


@given(strategies.text())
def test_nothing_matches(text):
    assert match_anything("-v")({'text': text}) is None


@given(strategies.text())
@example('\n')
def test_everything_matches(text):
    assert match_anything()({'text': text}).group() is text


@given(strategies.text())
def test_favorited(text):
    assert match_anything("-f")({
        'text': text,
        'favorited_by': [grepme.get_logged_in_user()]
        }).group() is text
    assert match_anything("-f")({
        'text': text,
        'favorited_by': []
        }) is None
    assert match_anything("-F")({
        'text': text,
        'favorited_by': [grepme.get_logged_in_user()]
        }) is None
    assert match_anything("-F")({
        'text': text,
        'favorited_by': []
        }).group() is text


@given(strategies.text())
def test_user(text):
    assert match_anything("-u", '.*')({
        'text': "blah",
        'name': text
        }).group() is "blah"
    # a^: don't match any user
    assert match_anything("-u", 'a^')({
        'text': 'blah',
        'name': text
        }) is None


def test_illegal_arguments():
    with pytest.raises(SystemExit):
        match_anything("-f", "-F")
