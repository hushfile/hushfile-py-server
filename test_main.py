from base64 import b64encode
import json
import main
from mock import patch
import os
import shutil
import tempfile
import unittest

json_header = {
    'Content-type': 'application/json',
}

here = abspath = os.path.abspath(os.path.dirname(__file__))
files = os.path.join(here, 'files')


class TestMain(unittest.TestCase):
    tmp_dir = None

    def status_code(self, resp, expect):
        self.assertEqual(resp.status_code, expect)

    def setUp(self):
        main.app.config['DEBUG'] = True
        self.app = main.app.test_client()
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def api_upload_success(self, wrap_func=lambda x: x, headers={}):
        payload = {
            'metadata': b64encode(os.urandom(42)),
            'mac': '12345'
        }

        with patch('main.generate_password') as p:
            with patch('main.DATA_PATH', self.tmp_dir):
                p.return_value = '1234567890'

                resp = self.app.post('/api/file',
                                     data=wrap_func(payload),
                                     headers=headers)
                self.assertEqual(resp.status_code, 200)
                data = json.loads(resp.get_data())

                assert os.path.isdir(os.path.join(self.tmp_dir,
                                                  data['id']))

                # TODO: Test file contents

    def test_api_upload_json(self):
        self.api_upload_success(wrap_func=json.dumps, headers=json_header)

    def test_api_upload_multipart(self):
        self.api_upload_success()

    def test_api_upload_no_meta(self):
        payload = {
            'mac': '1234'
        }
        resp = self.app.post('/api/file', data=payload)
        self.assertEqual(resp.status_code, 400)

    def test_api_get_serverinfo(self):
        config_location = os.path.join(files, 'config.json')

        expected = json.load(open(config_location))
        with patch('main.CONFIGURATION_LOCATION', config_location):
            resp = self.app.get('/api/serverinfo')
        self.status_code(resp, 200)

        assert json.loads(resp.get_data()) == expected
