from base64 import b64encode
import json
import main
from mock import patch
from nose.tools import eq_ as assert_equal
import os
import shutil
import tempfile

json_header = {
    'Content-type': 'application/json',
}

here = abspath = os.path.abspath(os.path.dirname(__file__))
files = os.path.join(here, 'files')

app = None
tmpdir = None


def status_code(resp, expect):
    assert_equal(resp.status_code, expect)


def setup_module():
    global app, tmpdir
    tmpdir = tempfile.mkdtemp()
    main.app.config['DEBUG'] = True
    app = main.app.test_client()


def teardown_module():
    shutil.rmtree(tmpdir)


def setup_mockfile(file_id, uploadpassword='1234'):
    filepath = os.path.join(tmpdir, file_id)
    os.makedirs(filepath)
    with open(os.path.join(filepath, 'properties.json'), 'w') as f:
        json.dump({
            'uploadpassword': uploadpassword
        }, f)
    return filepath


def api_upload_success(wrap_func=lambda x: x, headers={}):
    payload = {
        'metadata': b64encode(os.urandom(42)),
        'mac': '12345'
    }

    with patch('main.generate_password') as p:
        with patch('main.DATA_PATH', tmpdir):
            p.return_value = '1234567890'

            resp = app.post(
                '/api/file',
                data=wrap_func(payload),
                headers=headers)
            status_code(resp, 200)
            data = json.loads(resp.get_data())

            assert os.path.isdir(os.path.join(tmpdir, data['id']))

            # TODO: Test file contents


def test_post_file_json():
    api_upload_success(wrap_func=json.dumps, headers=json_header)


def test_post_file_multipart():
    api_upload_success()


def test_get_serverinfo():
    config_location = os.path.join(files, 'config.json')

    expected = json.load(open(config_location))
    with patch('main.CONFIGURATION_LOCATION', config_location):
        resp = app.get('/api/serverinfo')
    status_code(resp, 200)

    assert json.loads(resp.get_data()) == expected


def test_put_metadata_success():
    with patch('main.DATA_PATH', tmpdir):
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


def test_put_metadata_not_exists():
    resp = app.put('/api/file/fewfsadgsg/metadata', data={})
    status_code(resp, 404)


def test_put_file_no_meta():
    with patch('main.DATA_PATH', tmpdir):
        filepath = setup_mockfile('1234')
        payload = {
            'uploadpassword': '1234',
        }
        resp = app.put('/api/file/1234/metadata', data=payload)
        status_code(resp, 400)
        metadata_file = os.path.join(filepath, 'metadata.json')
        assert not os.path.exists(metadata_file)


def test_put_file_unauthorized():
    with patch('main.DATA_PATH', tmpdir):
        filepath = setup_mockfile('weggkgelg')
        payload = {
            'uploadpassword': '2wefegf',
            'metadata': 'encryptedtexthere'
        }

        resp = app.put('/api/file/weggkgelg/metadata', data=payload)
        status_code(resp, 401)

        metadata_file = os.path.join(filepath, 'metadata.json')
        assert not os.path.exists(metadata_file)
