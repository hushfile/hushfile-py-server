import main
import shutil
import tempfile
import unittest


class TestHushfile(unittest.TestCase):
    tmp_dir = None

    def setUp(self):
        main.app.config['DEBUG'] = True
        self.app = main.app.test_client()
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_success(self):
        pass
