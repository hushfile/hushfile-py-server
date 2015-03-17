from __future__ import division, print_function, unicode_literals

from testing.unit import app, default_setup_module, default_teardown_module
from testing.tools import status_code


def setup_module():
    default_setup_module()


def teardown_module():
    default_teardown_module()


def test_get_serverinfo():
    resp = app.get('/api/info')
    status_code(resp, 200)

    info = resp.get_data()

    assert 'max_retention_hours' in info
    assert 'max_filesize_bytes' in info
    assert 'max_chunksize_bytes' in info
