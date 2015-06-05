from __future__ import division, print_function, unicode_literals

from urllib import urlencode

from testing.unit import app, default_setup_module, default_teardown_module
from testing.tools import status_code


def setup_module():
    default_setup_module()


def teardown_module():
    default_teardown_module()


def check_throws_unauthorized(endpoint):
    resp = app.put(endpoint)
    status_code(resp, 401)

    resp = app.put(endpoint + '?' + urlencode('key='))
    assert not 401 == resp.status_code

    resp = app.put(endpoint + '?' + urlencode('key=1234'))
    assert not 401 == resp.status_code


def test_unauthorized():
    yield check_throws_unauthorized, '/api/file/singleton'
