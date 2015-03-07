from base64 import b64encode
import json
from mock import patch
import os

from t.unit import app, default_setup_module, default_teardown_module
from t.utils import status_code

json_header = {
    'Content-type': 'application/json',
}


def setup_module():
    default_setup_module()


def teardown_module():
    default_teardown_module()


def api_upload_success(wrap_func=lambda x: x, headers={}):
    payload = {
        'metadata': b64encode(os.urandom(42)),
        'mac': '12345'
    }
    with patch('main.generate_password') as p:
        p.return_value = '1234567890'

        resp = app.post(
            '/api/file',
            data=wrap_func(payload),
            headers=headers)
        status_code(resp, 200)
        data = json.loads(resp.get_data())

        file = os.path.join(app.tmpdir, data['id'])
        assert os.path.isdir(file)

        # TODO: Test file contents


def test_post_file_json():
    api_upload_success(wrap_func=json.dumps, headers=json_header)


def test_post_file_multipart():
    api_upload_success()
