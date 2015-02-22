from base64 import b64encode
from flask import Flask, request, jsonify
import json
import os
import tempfile
from werkzeug.exceptions import (BadRequest,
                                 NotFound)

app = Flask(__name__)

abspath = os.path.abspath(os.path.dirname(__file__))
CONFIGURATION_LOCATION = os.environ.get(
    'HUSHFILE_CONFIGURATION_LOCATION',
    os.path.join(abspath, 'config.json')
)
DATA_PATH = os.environ.get('HUSHFILE_DATA_PATH',
                           os.path.join(abspath, 'files'))
DEFAULT_FILE_EXPIRATION = os.environ.get('HUSHFILE_DEFAULT_FILE_EXPIRATION',
                                         60*60*24*30)  # 30 days
FILEID_LENGTH = 15

metadata_filename = 'metadata.json'
properties_filename = 'properties.json'


def generate_password(length=40):
    return b64encode(os.urandom(42))[:40]


def create_new_file(filepath):
    filepath = tempfile.mkdtemp(dir=DATA_PATH)

    fileid = os.path.basename(filepath)

    app.logger.info("Creating new upload at %s" % filepath)

    return fileid, filepath


def read_metadata_file(filepath):
    with open(os.path.join(filepath, metadata_filename), 'rb') as f:
        content = f.read()
    return json.loads(content)


def write_metadata_file(filepath, metadata):
    metadata_file = os.path.join(filepath, metadata_filename)

    with open(metadata_file, 'wb') as f:
        f.write(json.dumps(metadata))


def read_properties_file(filepath):
    with open(os.path.join(filepath, properties_filename), 'r') as f:
        content = f.read()
    return json.loads(content)


def write_properties_file(filepath, properties):
    properties_file = os.path.join(filepath, properties_filename)

    with open(properties_file, 'w') as f:
        f.write(json.dumps(properties))


def parse_request_data(request):
    return request.get_json() or request.form


def not_implemented():
    return "Coming soon, to a browser near you."


@app.route('/api/file', methods=['POST'])
def post_file():
    payload = parse_request_data(request)

    if not payload['metadata']:
        app.logger.error("Parsing of request failed")
        raise BadRequest()

    fileid, filepath = create_new_file(DATA_PATH)

    write_metadata_file(filepath,
                        {
                            'metadata': payload['metadata'],
                            'mac': payload['mac']
                        })

    uploadpassword = generate_password()
    properties = {
        'uploadpassword': uploadpassword,
        'deletepassword': payload.get('deletepassword', ''),
        'expire': payload.get('expire', DEFAULT_FILE_EXPIRATION),
        'limit': payload.get('limit', None),
        'chunks': payload.get('chunks', None),
    }

    write_properties_file(filepath, properties)

    return jsonify({
        'id': fileid,
        'uploadpassword': uploadpassword,
    })


def assert_file_exists(id):
    if not os.path.isdir(os.path.join(DATA_PATH, id)):
        raise NotFound("The requested file could not be found")


@app.route('/api/file/<id>', methods=['PUT'])
def put_file(id):
    return not_implemented()


@app.route('/api/file/<id>/exists', methods=['GET'])
def get_file_exists(id):
    assert_file_exists(id)
    return ""


@app.route('/api/file/<id>/info', methods=['GET'])
def get_file_info(id):
    assert_file_exists(id)
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
    return jsonify(json.load(open(CONFIGURATION_LOCATION)))

if __name__ == "__main__":
    app.debug = True
    app.logger.debug("Starting with DATA_PATH=%s", DATA_PATH)
    assert os.path.exists(DATA_PATH) and os.path.isdir(DATA_PATH)

    app.run()
