from __future__ import division, print_function, unicode_literals
from nose.tools import eq_ as assert_equal


def status_code(resp, expect):
    assert_equal(resp.status_code, expect)
