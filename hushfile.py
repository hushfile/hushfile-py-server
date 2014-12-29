from flask import Flask
import os

app = Flask(__name__)

abspath = os.path.abspath(os.path.basename(__file__))
DATA_PATH = os.environ.get('HUSHFILE_DATA_PATH',
                           os.path.join(abspath, 'files'))


def not_implemented():
    return "Coming soon, to a browser near you."


@app.route('/api/file', methods=['POST'])
def post_file():
    return not_implemented()


def assert_file_exists(id):
    return not_implemented()


@app.route('/api/file/<id>', methods=['PUT'])
def put_file(id):
    return not_implemented()


@app.route('/api/file/<id>/exists', methods=['GET'])
def get_file_exists(id):
    assert_file_exists()
    return ""


@app.route('/api/file/<id>/info', methods=['GET'])
def get_file_info(id):
    '''Return public information about the file'''
    return not_implemented()


@app.route('/api/file/<id>/metadata', methods=['GET'])
def get_file_metadata(id):
    '''Return the metadata file along with its mac'''
    return not_implemented()


@app.route('/api/file/<id>/<index>', methods=['GET'])
def get_file(id, index):
    return not_implemented()


@app.route('/api/file/<id>/<deletepassword>', methods=['DELETE'])
def delete_file(id, deletepassword):
    return not_implemented()


@app.route('/api/serverinfo', methods=['GET'])
def get_serverinfo():
    return not_implemented()

if __name__ == "__main__":
    assert os.path.exists(DATA_PATH) and os.path.isdir(DATA_PATH)
    app.debug = True
    app.run()
