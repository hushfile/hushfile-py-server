from __future__ import division, print_function, unicode_literals

from mock import patch

from t.unit import app, default_setup_module, default_teardown_module
from t.utils import expect_not_found, expect_response


def setup_module():
    default_setup_module()


def teardown_module():
    default_teardown_module()


def test_get_success():
    with patch('main.os.path.isdir', lambda x: True):
        expect_response(
            app.get('/api/file/singleton/exists'),
            payload={})


def test_get_not_found():
    expect_not_found(app.get('/api/file/foobar/exists'))
