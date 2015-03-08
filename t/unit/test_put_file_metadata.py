from __future__ import division, print_function, unicode_literals

import json
import os

from t.unit import app, default_setup_module, default_teardown_module
from t.utils import assert_equal, status_code

here = os.path.abspath(os.path.dirname(__file__))
files = os.path.join(here, 'files')


def setup_module():
    default_setup_module()


def teardown_module():
    default_teardown_module()


def test_success():
    metadata_src = os.path.join(files, 'metadata')
    with open(metadata_src) as f:
        payload = {
            'metadata': f,
        }
        resp = app.put('/api/file/incomplete/metadata?key=1234', data=payload)
        status_code(resp, 200)

        metadata_file = os.path.join(
            app.tmpdir,
            'files',
            'incomplete',
            'metadata.json')

        assert os.path.exists(metadata_file)

    with open(metadata_src) as f:
        with open(metadata_file) as g:
            data = json.load(g)
            assert 'metadata' in data
            assert_equal(data['metadata'], f.read())


def test_not_found():
    payload = {
        'metadata': 'encryptedtexthere'
    }
    resp = app.put('/api/file/doesnotexist/metadata?key=1234', data=payload)
    status_code(resp, 404)


def test_put_file_no_meta():
    resp = app.put('/api/file/incomplete/metadata?key=1234', data={})
    status_code(resp, 400)
    metadata_file = os.path.join(app.tmpdir, 'metadata.json')
    assert not os.path.exists(metadata_file)


def test_put_file_unauthorized():
    payload = {
        'metadata': 'encryptedtexthere'
    }

    resp = app.put('/api/file/incomplete/metadata?key=wrong', data=payload)
    status_code(resp, 401)

    metadata_file = os.path.join(app.tmpdir, 'metadata.json')
    assert not os.path.exists(metadata_file)
