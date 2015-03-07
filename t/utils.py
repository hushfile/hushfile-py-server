from __future__ import division, print_function, unicode_literals

import json
from nose.tools import eq_ as assert_equal


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
