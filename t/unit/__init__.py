import main
import shutil
import tempfile

app = main.app.test_client()


def default_setup_module(mockcontext=None):
    main.app.config['DEBUG'] = True
    app.tmpdir = tempfile.mkdtemp()

    class MockContext():
        def __init__(self):

            self.config = {
                'data_path': app.tmpdir,
            }

    main.app.app_ctx_globals_class = MockContext


def default_teardown_module():
    shutil.rmtree(app.tmpdir)
