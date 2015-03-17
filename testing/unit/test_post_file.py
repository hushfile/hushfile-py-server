import json
import os

from testing.unit import app, default_setup_module, default_teardown_module
from testing.tools import status_code

json_header = {
    'Content-type': 'application/json',
}


def setup_module():
    default_setup_module()


def teardown_module():
    default_teardown_module()


def api_upload_success(wrap_func=lambda x: x, headers={}):
    resp = app.post(
        '/api/file',
        data=wrap_func({}),
        headers=headers)
    status_code(resp, 200)
    data = json.loads(resp.get_data())

    assert 'id' in data

    file = os.path.join(app.tmpdir, 'files', data['id'])
    assert os.path.isdir(file)

    # TODO: Test file contents


def test_post_file_json():
    api_upload_success(wrap_func=json.dumps, headers=json_header)


def test_post_file_multipart():
    api_upload_success()
