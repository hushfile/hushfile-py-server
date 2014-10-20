#!/usr/bin/env python3.3
import cherrypy
from cherrypy.lib.static import serve_file
import os.path
import json
import shutil
import re
import glob

def natural_sort_key(s, _nsre=re.compile('([0-9]+)')):
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(_nsre, s)]

abspath = os.path.abspath(os.path.dirname(__file__))

def generate_password():
    length = 40
    return hex(int.from_bytes(os.urandom(length), byteorder="big"))[2:].zfill(length * 2)

def generate_uniqid():
    uniqid = generate_password()
    while os.path.exists(uniqid):
        uniqid = gen()
    return uniqid

def write(srcfile, dstpath):
    with open(dstpath, "w" + ("b" if isinstance(srcfile, bytes) else "")) as f:
        if isinstance(srcfile, (bytes, str)):
            f.write(srcfile)
        else:
            shutil.copyfileobj(srcfile.file, f)

def get_serverdata(directory):
    try:
        with open(os.path.join(directory, "serverdata.json")) as f:
            return json.loads(f.read())
    except FileNotFoundError:
        raise cherrypy.NotFound()

def get_dir_from_fileid(fileid):
    if not os.path.abspath(os.path.join(config["data_path"], fileid)).startswith(os.path.abspath(config["data_path"])): raise cherrypy.NotFound()
    return os.path.abspath(os.path.join(config["data_path"], fileid))

def files_and_totalsize(directory):
     files = glob.glob(os.path.join(directory, "cryptofile.*"))
     return (files, sum(map(os.path.getsize, files)))

class Api(object):
    @cherrypy.expose
    @cherrypy.tools.allow(methods=['POST'])
    @cherrypy.tools.json_out()
    def finishupload(self, fileid, uploadpassword):
        directory = get_dir_from_fileid(fileid)
        if not os.path.exists(directory): raise cherrypy.NotFound()
        try:
            with open(os.path.join(directory, "uploadpassword"), "r") as f:
                if uploadpassword != f.read():
                    return {"status": "wrong uploadpassword"}
        except OSError:
            return {"status": "already finished"}
        files, totalsize = files_and_totalsize(directory)
        in_order = sort(files, key=natural_order_key)
        missing_a_chunk = len(in_order)-1 != int(in_order[-1].rpartition("."))
        if not missing_a_chunk:
            try:
                os.remove(os.path.join(directory, "uploadpassword"))
                is_now_finished = True
            except OSError as e:
                assert e.errno != errno.ENOENT
                is_now_finished = False
        return {"status": "missing a chunk" if missing_a_chunk else "OK", "chunks": len(in_order), "totalsize": totalsize, "fileid": fileid, "finished": is_now_finished, "uploadpassword": "" if is_now_finished else uploadpassword}

    @cherrypy.expose
    @cherrypy.tools.allow(methods=['POST'])
    @cherrypy.tools.json_out()
    def upload(self, cryptofile, finishupload, chunknumber, fileid=None, uploadpassword=None, metadata=None, deletepassword=None):
        if fileid is None:
            if metadata is None:
                print("2")
                return {"status": "metadata must be set when starting a new upload"}
            if deletepassword is None:
                print("3")
                return {"status": "deletepassword must be set when starting a new upload"}
            fileid = generate_uniqid()
            uploadpassword = generate_password()
            new = True
        else:
            new = False
        
        directory = get_dir_from_fileid(fileid)
        cryptofilepath = os.path.join(directory, "cryptofile")
        metadatapath = os.path.join(directory, "metadata")
        serverdatapath = os.path.join(directory, "serverdata.json")
        uploadpasswordpath = os.path.join(directory, "uploadpassword")

        if not new:
            if not os.path.exists(directory):
                return {"status": "invalid fileid"}
            if not os.path.exists(uploadpasswordpath):
                return {"status": "can't upload to finished file"}

        if new:
            os.mkdir(directory)
            with open(metadatapath, "w") as f:
                f.write(metadata)
            pairs = [("deletepassword", deletepassword), ("clientip", cherrypy.request.remote.ip)]
            dic = dict(pairs)
            with open(serverdatapath, "w") as f:
                f.write(json.dumps(dic))
            if not json.loads(finishupload.lower()): # TODO fjern lower()
                with open(uploadpasswordpath, "w") as f:
                    f.write(uploadpassword)
        else:
            with open(os.path.join(directory, "uploadpassword"), "r") as f:
                if uploadpassword != f.read():
                    return {"status": "wrong uploadpassword"}
            if json.loads(finishupload.lower()):
                try:
                    os.remove(uploadpasswordpath)
                except OSError:
                    return {"status": "couldn't remove uploadpassword"}

        dstpath = os.path.join(directory, "cryptofile." + str(int(chunknumber)))
        if os.path.exists(dstpath):
            print("7")
            return {"status": "chunk already exists"}
        write(cryptofile, dstpath)
        print("wrote " + dstpath)

        files, totalsize = files_and_totalsize(directory)
        ret = {"status": "OK", "fileid": fileid, "chunks": len(files), "totalsize": totalsize, "finished": not os.path.exists(uploadpasswordpath)}
        if new: ret["uploadpassword"] = "" if json.loads(finishupload.lower()) else uploadpassword
        return ret

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def exists(self, fileid):
        directory = get_dir_from_fileid(fileid)
        files, totalsize = files_and_totalsize(directory)
        return {"fileid": fileid, "exists": os.path.exists(get_dir_from_fileid(fileid)), "chunks": len(files), "totalsize": totalsize, "finished": not os.path.exists(os.path.join(directory, "uploadpassword"))}

    @cherrypy.expose
    def file(self, fileid, chunknumber):
        directory = get_dir_from_fileid(fileid)
        path = os.path.join(directory, "cryptofile." + str(int(chunknumber)))
        if not os.path.exists(path): raise cherrypy.NotFound()
        if os.path.exists(os.path.join(directory, "uploadpassword")): raise HTTPError("412 Precondition Failed") # TODO json response with HTTP error
        return serve_file(path, content_type="text/plain")

    @cherrypy.expose
    def metadata(self, fileid):
        directory = get_dir_from_fileid(fileid)
        path = os.path.join(directory, "metadata")
        if not os.path.exists(path): raise cherrypy.NotFound()
        if os.path.exists(os.path.join(directory, "uploadpassword")): raise HTTPError("412 Precondition Failed")
        return serve_file(path, content_type="text/plain")

    @cherrypy.expose
    @cherrypy.tools.allow(methods=['POST'])
    @cherrypy.tools.json_out()
    def delete(self, fileid, deletepassword):
        di = get_dir_from_fileid(fileid)
        if get_serverdata(di)["deletepassword"] != deletepassword:
            raise cherrypy.HTTPError("401 Unauthorized")

        os.remove(os.path.join(di, "cryptofile"))
        os.remove(os.path.join(di, "metadata"))
        os.remove(os.path.join(di, "serverdata.json"))
        try:
            os.remove(os.path.join(di, "uploadpassword"))
        except OSError:
            pass
        os.rmdir(di)
        return {"fileid": fileid, "deleted": True}

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def ip(self, fileid):
        return {"fileid": fileid, "uploadip": get_serverdata(get_dir_from_fileid(fileid))["clientip"]}

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def serverinfo(self):
        return {k: v for (k, v) in config.items() if k in ("server_operator_email", "max_retention_hours", "max_chunksize_bytes", "max_filesize_bytes")}

def error_page_404(status, message, traceback, version):
    return json.dumps({"fileid":"", "status": "bad request"})

class App(object):
    _cp_config = {'error_page.404': error_page_404}
    def error_page_404(status, message, traceback, version):
        return "lol"

    api = Api()

def http_methods_allowed(methods=['GET', 'HEAD']):
    method = cherrypy.request.method.upper()
    if method not in methods:
        cherrypy.response.headers['Allow'] = ", ".join(methods)
        raise cherrypy.HTTPError(405)

cherrypy.tools.allow = cherrypy.Tool('on_start_resource', http_methods_allowed)

conf = {
    'global': {
       'server.socket_host': '0.0.0.0',
       'server.socket_port': 8801,
       'request.error_response': lambda: "loldog"
    },
}

with open(os.path.join(abspath, "config.json")) as f:
    config = json.loads(f.read())

if __name__ == "__main__":
    cherrypy.quickstart(App(), '/', conf)
