from base64 import b64encode
from flask import Flask, g, request, jsonify
from functools import wraps
import json
import os
import tempfile
from werkzeug.exceptions import (BadRequest,
                                 NotFound,
                                 Unauthorized)
from werkzeug.security import safe_str_cmp


class FlaskContext():
    def __init__(self):
        with open(CONFIGURATION_LOCATION) as f:
            self.config = json.load(f)


app = Flask(__name__)
app.app_ctx_globals_class = FlaskContext

abspath = os.path.abspath(os.path.dirname(__file__))
CONFIGURATION_LOCATION = os.environ.get(
    'HUSHFILE_CONFIGURATION_LOCATION',
    os.path.join(abspath, 'config.json')
)
DEFAULT_FILE_EXPIRATION = os.environ.get('HUSHFILE_DEFAULT_FILE_EXPIRATION',
                                         60*60*24*30)  # 30 days
FILEID_LENGTH = 15

metadata_filename = 'metadata.json'
properties_filename = 'properties.json'


def generate_password(length=40):
    return b64encode(os.urandom(42))[:40]


def create_new_file():
    print(g.config['data_path'])
    filepath = tempfile.mkdtemp(dir=g.config['data_path'])
    fileid = os.path.basename(filepath)

    app.logger.info("Creating new upload at %s" % filepath)

    return fileid, filepath


def read_metadata_file(file_id):
    metadata_file = os.path.join(
        g.config['data_path'],
        file_id,
        metadata_filename)

    with open(metadata_file, 'rb') as f:
        return json.load(f)


def read_properties_file(file_id):
    properties_file = os.path.join(
        g.config['data_path'],
        file_id,
        properties_filename)

    with open(properties_file, 'r') as f:
        return json.load(f)


def write_properties_file(file_id, properties):
    properties_file = os.path.join(
        g.config['data_path'],
        file_id,
        properties_filename)

    with open(properties_file, 'w') as f:
        json.dump(properties, f)


@app.before_request
def parse_request_data():
    if request.method in ['POST', 'PUT']:
        g.payload = request.get_json() or request.form


def not_implemented():
    return "Coming soon, to a browser near you."


@app.route('/api/file', methods=['POST'])
def post_file():
    payload = g.payload

    fileid, filepath = create_new_file()

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


def require_file_exists(f):
    @wraps(f)
    def check_file_exists(*args, **kwargs):
        dirname = os.path.join(g.config['data_path'], kwargs['id'])
        if not os.path.isdir(dirname):
            raise NotFound("The requested file could not be found")
        app.logger.info("Found file %s", kwargs['id'])
        return f(*args, **kwargs)
    return check_file_exists


def require_uploadpassword(f):
    @require_file_exists
    @wraps(f)
    def check_uploadpassword(*args, **kwargs):
        properties = read_properties_file(kwargs['id'])
        payload = g.payload
        comparison = safe_str_cmp(
            payload['uploadpassword'],
            properties['uploadpassword'])

        if not comparison:
            raise Unauthorized()
        return f(*args, **kwargs)
    return check_uploadpassword


@app.route('/api/file/<string:id>/metadata', methods=['PUT'])
@require_uploadpassword
def put_file_metadata(id):
    payload = g.payload

    if 'metadata' not in payload:
        app.logger.error("Parsing of request failed")
        raise BadRequest()

    metadata = payload.copy()
    del metadata['uploadpassword']

    metadata_file = os.path.join(
        g.config['data_path'],
        id,
        metadata_filename)

    app.logger.debug("Writing metadata to %s", metadata_file)
    with open(metadata_file, 'wb') as f:
        json.dump(metadata, f)

    return jsonify({})


@app.route('/api/file/<id>/exists', methods=['GET'])
@require_file_exists
def get_file_exists(id):
    return ""


@app.route('/api/file/<id>/info', methods=['GET'])
@require_file_exists
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
    c = g.config
    return jsonify({
        'max_retention_hours': c.get('max_retention_hours', 24),
        'max_filesize_bytes': c.get('max_filesize_bytes', 1073741824),
        'max_chunksize_bytes': c.get('max_chunksize_bytes', 104857600),
    })

if __name__ == "__main__":
    app.debug = True
    assert os.path.exists(CONFIGURATION_LOCATION) and \
        os.path.isfile(CONFIGURATION_LOCATION)

    app.run()
