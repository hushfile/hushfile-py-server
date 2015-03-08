from base64 import b64encode
from datetime import datetime, timedelta
from flask import Flask, g, make_response, request, jsonify
from functools import wraps
import json
import os
import shutil
import tempfile
import time
from werkzeug.exceptions import (
    BadRequest,
    Conflict,
    NotFound,
    RequestedRangeNotSatisfiable,
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


@app.route('/api/file', methods=['POST'])
def post_file():
    payload = g.payload

    filepath = tempfile.mkdtemp(dir=g.config['data_path'])
    file_id = os.path.basename(filepath)
    upload_key = generate_password()
    delete_key = generate_password()

    expires = payload.get('expires', None)

    if not expires:
        dt_expires = (
            datetime.utcnow() + timedelta(seconds=DEFAULT_FILE_EXPIRATION))

        expires = int(time.mktime(dt_expires.timetuple()))

    properties = {
        'upload_key': upload_key,
        'delete_key': delete_key,
        'expires': expires,
        'chunks': 0,
    }

    if 'limit' in payload:
        properties.update({
            'limit': payload['limit'],
            'downloads': 0,
        })

    write_properties_file(file_id, properties)

    return jsonify({'id': file_id})


def file_exists(file_id):
    file = os.path.join(g.config['data_path'], file_id)
    return os.path.exists(file) and os.path.isdir(file)


def chunk_exists(file_id, index):
    chunk_file = os.path.join(g.config['data_path'], file_id, index)
    return os.path.exists(chunk_file)


def require_file_exists(f):
    app.logger.debug("require_file_exists invoked")

    @wraps(f)
    def check_file_exists(*args, **kwargs):
        if not file_exists(kwargs['id']):
            raise NotFound("The requested file could not be found")
        app.logger.info("Found file %s", kwargs['id'])
        return f(*args, **kwargs)
    return check_file_exists


def require_uploadpassword(f):
    @require_file_exists
    @wraps(f)
    def check_uploadpassword(*args, **kwargs):
        properties = read_properties_file(kwargs['id'])
        comparison = safe_str_cmp(
            request.args.get('key'),
            properties['upload_key'])

        if not comparison:
            raise Unauthorized()
        return f(*args, **kwargs)
    return check_uploadpassword


@app.route('/api/file/<string:id>/metadata', methods=['PUT'])
@require_uploadpassword
def put_file_metadata(id):
    payload = g.payload

    metadata_file = os.path.join(
        g.config['data_path'],
        id,
        metadata_filename)

    metadata = payload.copy()

    uploaded_file = request.files['metadata']
    if uploaded_file:
        metadata.update({
            'metadata': uploaded_file.read()
        })
    app.logger.debug("Writing metadata to %s", metadata_file)
    with open(metadata_file, 'wb') as f:
        json.dump(metadata, f)

    return jsonify({'id': id})


@app.route('/api/file/<id>/exists', methods=['GET'])
@require_file_exists
def get_file_exists(id):
    return jsonify({'id': id})


@app.route('/api/file/<id>/info', methods=['GET'])
@require_file_exists
def get_file_info(id):
    '''Return public information about the file'''

    properties = read_properties_file(id)

    info = {
        'id': id,
        'chunks': properties['chunks'],
        'size_total': properties['size_total'],
        'complete': properties['complete'],
        'expires': properties['expires'],
    }

    if 'limit' in properties:
        info.update({
            'limit': properties['limit'],
            'downloads': properties.get('downloads', 0),
        })

    return jsonify(info)


@app.route('/api/file/<id>/metadata', methods=['GET'])
@require_file_exists
def get_file_metadata(id):
    '''Return the metadata file along with its mac'''
    metadata_file = os.path.join(g.config)
    with open(metadata_file) as f:
        return jsonify(f.read())


@app.route('/api/file/<id>/<index>', methods=['PUT'])
@require_uploadpassword
def put_file(id, index):
    file = request.files['file']
    chunk_file = os.path.join(g.config['data_path'], id, '%d.chunk' % index)

    properties = read_properties_file(id)

    if chunk_exists(id, index):
        existing_size = os.path.getsize(chunk_file)
        properties['total_size'] -= existing_size
        file.save(chunk_file)
        properties['total_size'] += os.path.getsize(chunk_file)
    else:
        file.save(chunk_file)
        properties['chunks'] += 1

    write_properties_file(id, properties)

    return jsonify({
        'id': id,
        'index': index,
        'size': os.path.getsize(chunk_file)
    })


@app.route('/api/file/<id>/<index>', methods=['GET'])
@require_file_exists
def get_file(id, index):
    chunk_file = os.path.join(g.config['data_path'], id, index)

    if not chunk_exists(chunk_file):
        raise RequestedRangeNotSatisfiable()

    with open(chunk_file) as f:
        return make_response(f.read())


def remove_file(id):
    shutil.rmtree(os.path.join(g.config['data_path'], id))
    return jsonify({
        'id': id
    })


@app.route('/api/file/<string:id>/complete', methods=['DELETE', 'POST'])
@require_uploadpassword
def post_file_complete(id):
    properties = read_properties_file(id)

    cmp_chunks = g.payload.get('chunks') == properties['chunks']
    if request.method == 'POST' and not cmp_chunks:
        raise RequestedRangeNotSatisfiable()

    if properties['complete']:
        raise Conflict()

    if 'DELETE' == request.method:
        delete_file(id)
    else:
        properties['complete'] = True
        write_properties_file(id)


@app.route('/api/file/<id>', methods=['DELETE'])
@require_file_exists
def delete_file(id):
    properties = read_properties_file(id)
    if not safe_str_cmp(request.args.get('key'), properties['delete_key']):
        raise Unauthorized()
    remove_file(id)


@app.route('/api/info', methods=['GET'])
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
