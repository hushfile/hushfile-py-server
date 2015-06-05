from __future__ import division, print_function, unicode_literals

from functools import wraps
import json
from nose.tools import eq_ as assert_equal, assert_raises
from werkzeug.exceptions import NotFound


def status_code(resp, expect):
    assert_equal(resp.status_code, expect)


def expect_response(resp, status=200, payload=None):
    status_code(resp, status)

    if payload:
        assert_equal(
            json.loads(resp.get_data()),
            payload)


def expect_not_found(resp):
    status_code(resp, 404)


def throws_not_found(f):
    @wraps
    def inner(*args, **kwargs):
        with assert_raises(NotFound):
            return f(*args, **kwargs)
    return inner
