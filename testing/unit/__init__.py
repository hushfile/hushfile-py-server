import main
import os
import shutil
import tempfile

app = main.app.test_client()
here = os.path.abspath(os.path.dirname(__file__))
files = os.path.join(here, 'files')


def default_setup_module():
    main.app.config['DEBUG'] = True
    app.tmpdir = tempfile.mkdtemp()

    class MockContext():
        def __init__(self):
            self.config = {
                'data_path': os.path.join(app.tmpdir, 'files'),
            }
    main.app.app_ctx_globals_class = MockContext
    shutil.copytree(
        os.path.join(files, 'fixtures'),
        os.path.join(app.tmpdir, 'files'))


def default_teardown_module():
    shutil.rmtree(app.tmpdir)
