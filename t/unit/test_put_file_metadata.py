from __future__ import division, print_function, unicode_literals

import json
import os

from t.unit import app, default_setup_module, default_teardown_module
from t.utils import status_code


def setup_module():
    default_setup_module()


def teardown_module():
    default_teardown_module()


def setup_mockfile(file_id, uploadpassword='1234'):
    filepath = os.path.join(app.tmpdir, file_id)
    os.makedirs(filepath)
    with open(os.path.join(filepath, 'properties.json'), 'w') as f:
        json.dump({
            'uploadpassword': uploadpassword
        }, f)
    return filepath


def test_success():
    filepath = setup_mockfile('foobar')
    payload = {
        'uploadpassword': '1234',
        'metadata': 'encryptedtexthere'
    }
    resp = app.put('/api/file/foobar/metadata', data=payload)
    status_code(resp, 200)

    with open(os.path.join(filepath, 'metadata.json')) as f:
        j = json.load(f)
        assert 'uploadpassword' not in j


def test_not_found():
    resp = app.put('/api/file/fewfsadgsg/metadata', data={})
    status_code(resp, 404)


def test_put_file_no_meta():
    filepath = setup_mockfile('1234')
    payload = {
        'uploadpassword': '1234',
    }
    resp = app.put('/api/file/1234/metadata', data=payload)
    status_code(resp, 400)
    metadata_file = os.path.join(filepath, 'metadata.json')
    assert not os.path.exists(metadata_file)


def test_put_file_unauthorized():
    filepath = setup_mockfile('weggkgelg')
    payload = {
        'uploadpassword': '2wefegf',
        'metadata': 'encryptedtexthere'
    }

    resp = app.put('/api/file/weggkgelg/metadata', data=payload)
    status_code(resp, 401)

    metadata_file = os.path.join(filepath, 'metadata.json')
    assert not os.path.exists(metadata_file)
