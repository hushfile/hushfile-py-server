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

    def setup_mockfile(self, file_id, uploadpassword='1234'):
        filepath = os.path.join(self.tmp_dir, file_id)
        os.makedirs(filepath)
        with open(os.path.join(filepath, 'properties.json'), 'w') as f:
            json.dump({
                'uploadpassword': uploadpassword
            }, f)
        return filepath

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

    def test_post_file_json(self):
        self.api_upload_success(wrap_func=json.dumps, headers=json_header)

    def test_post_file_multipart(self):
        self.api_upload_success()

    def test_get_serverinfo(self):
        config_location = os.path.join(files, 'config.json')

        expected = json.load(open(config_location))
        with patch('main.CONFIGURATION_LOCATION', config_location):
            resp = self.app.get('/api/serverinfo')
        self.status_code(resp, 200)

        assert json.loads(resp.get_data()) == expected

    def test_put_metadata_success(self):
        with patch('main.DATA_PATH', self.tmp_dir):
            filepath = self.setup_mockfile('foobar')
            payload = {
                'uploadpassword': '1234',
                'metadata': 'encryptedtexthere'
            }
            resp = self.app.put('/api/file/foobar/metadata', data=payload)
            self.status_code(resp, 200)

            with open(os.path.join(filepath, 'metadata.json')) as f:
                j = json.load(f)
                assert 'uploadpassword' not in j

    def test_put_metadata_not_exists(self):
        resp = self.app.put('/api/file/fewfsadgsg/metadata', data={})
        self.status_code(resp, 404)

    def test_put_file_no_meta(self):
        with patch('main.DATA_PATH', self.tmp_dir):
            filepath = self.setup_mockfile('1234')
            payload = {
                'uploadpassword': '1234',
            }
            resp = self.app.put('/api/file/1234/metadata', data=payload)
            self.assertEqual(resp.status_code, 400)
            metadata_file = os.path.join(filepath, 'metadata.json')
            assert not os.path.exists(metadata_file)

    def test_put_file_unauthorized(self):
        with patch('main.DATA_PATH', self.tmp_dir):
            filepath = self.setup_mockfile('weggkgelg')
            payload = {
                'uploadpassword': '2wefegf',
                'metadata': 'encryptedtexthere'
            }

            resp = self.app.put('/api/file/weggkgelg/metadata', data=payload)
            self.status_code(resp, 401)

            metadata_file = os.path.join(filepath, 'metadata.json')
            assert not os.path.exists(metadata_file)
