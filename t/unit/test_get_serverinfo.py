from __future__ import division, print_function, unicode_literals

from t.unit import app, default_setup_module, default_teardown_module
from t.utils import status_code


def setup_module():
    default_setup_module()


def teardown_module():
    default_teardown_module()


def test_get_serverinfo():
    resp = app.get('/api/serverinfo')
    status_code(resp, 200)

    serverinfo = resp.get_data()

    assert 'max_retention_hours' in serverinfo
    assert 'max_filesize_bytes' in serverinfo
    assert 'max_chunksize_bytes' in serverinfo
