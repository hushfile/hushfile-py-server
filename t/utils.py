from __future__ import division, print_function, unicode_literals
from nose.tools import eq_ as assert_equal


def status_code(resp, expect):
    assert_equal(resp.status_code, expect)


def setup_mockfile(file_id, uploadpassword='1234'):
    filepath = os.path.join(app.tmpdir, file_id)
    os.makedirs(filepath)
    with open(os.path.join(filepath, 'properties.json'), 'w') as f:
        json.dump({
            'uploadpassword': uploadpassword
        }, f)
    return filepath
