from __future__ import division, print_function, unicode_literals

from t.unit import app, default_setup_module, default_teardown_module
from t.utils import expect_not_found, expect_response


def setup_module():
    default_setup_module()


def teardown_module():
    default_teardown_module()


def test_success():
    expect_response(
        app.get('/api/file/singleton/info'),
        payload={
            'chunks': 1,
            'size_total': 473831,
            'complete': True,
            'expires': 12345678,
        })


def test_not_found():
    expect_not_found(app.get('/api/file/foobar/info'))
