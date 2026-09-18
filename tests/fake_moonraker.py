# -*- coding: utf-8 -*-
"""A small in-memory Moonraker for end-to-end tests (no printer needed).

    server = FakeMoonraker(config_files={"printer.cfg": "..."}); server.start()
    ... Moonraker("127.0.0.1", server.port) ...
    server.stop()
"""
import json
import re
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class FakeMoonraker:
    def __init__(self, config_files=None, klippy_log="", state="ready", print_state="standby", mcu="stm32f446xx",
                 gcodes=None, printing="", queued=None, thumbs=None):
        self.files = dict(config_files or {})
        self.klippy_log = klippy_log
        self.state = state
        self.print_state = print_state
        self.mcu = mcu
        self.gcodes = dict(gcodes or {})      # path -> contents
        self.printing = printing              # the file being printed right now
        self.queued = list(queued or [])      # files waiting in Moonraker's job queue
        self.thumbs = dict(thumbs or {})      # gcode path -> png bytes
        self.deleted = []
        self.calls = []
        self.warnings = []
        self.serials = ["/dev/serial/by-id/usb-Klipper_%s_FAKE123-if00" % mcu, "/dev/ttyAMA0"]
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), self._handler())
        self.port = self.httpd.server_address[1]

    def start(self):
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        return self

    def stop(self):
        self.httpd.shutdown()
        self.httpd.server_close()

    def _handler(self):
        fake = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def _send(self, code, body, raw=False):
                data = body if raw else json.dumps(body).encode()
                self.send_response(code)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def _ok(self, result):
                self._send(200, {"result": result})

            def do_GET(self):
                u = urllib.parse.urlparse(self.path)
                path = urllib.parse.unquote(u.path)
                fake.calls.append(("GET", path))
                if path == "/printer/info":
                    return self._ok({"state": fake.state, "state_message": "Printer is ready" if fake.state == "ready"
                                     else fake.klippy_log.strip().splitlines()[-1] if fake.klippy_log else "error",
                                     "hostname": "fakepi", "software_version": "v0.13.0-fake"})
                if path == "/server/info":
                    return self._ok({"moonraker_version": "v0.10.0-fake"})
                if path == "/printer/objects/query":
                    status = {}
                    for obj in urllib.parse.parse_qs(u.query, keep_blank_values=True):
                        if obj == "print_stats":
                            status[obj] = {"state": fake.print_state, "filename": fake.printing}
                        elif obj == "mcu":
                            status[obj] = {"mcu_constants": {"MCU": fake.mcu}}
                        elif obj == "configfile":
                            status[obj] = {"warnings": fake.warnings}
                    return self._ok({"status": status})
                if path == "/server/files/list":
                    if "gcodes" in urllib.parse.parse_qs(u.query).get("root", []):
                        return self._ok([{"path": p, "size": len(t)} for p, t in fake.gcodes.items()])
                    return self._ok([{"path": p, "size": len(t)} for p, t in fake.files.items()])
                if path == "/server/files/directory":
                    root = (urllib.parse.parse_qs(u.query).get("path") or ["gcodes"])[0]
                    root = root[len("gcodes"):].strip("/")
                    dirs, files = set(), []
                    for p, t in fake.gcodes.items():
                        if root and not p.startswith(root + "/"):
                            continue
                        rest = p[len(root) + 1:] if root else p
                        if "/" in rest:
                            dirs.add(rest.split("/")[0])
                        else:
                            files.append({"filename": rest, "size": len(t), "modified": 0})
                    return self._ok({"dirs": [{"dirname": d} for d in sorted(dirs)], "files": files})
                if path == "/server/files/metadata":
                    name = (urllib.parse.parse_qs(u.query).get("filename") or [""])[0]
                    if name not in fake.gcodes:
                        return self._send(404, {"error": {"message": "Metadata not available"}})
                    thumbs = ([{"width": 300, "height": 300, "size": 900,
                                "relative_path": ".thumbs/%s-300x300.png" % name.rpartition("/")[2][:-6]}]
                              if name in fake.thumbs else [])
                    return self._ok({"filename": name, "size": len(fake.gcodes[name]), "thumbnails": thumbs})
                if path == "/server/job_queue/status":
                    return self._ok({"queued_jobs": [{"filename": f} for f in fake.queued], "queue_state": "ready"})
                if path.startswith("/server/files/gcodes/"):
                    name = path[len("/server/files/gcodes/"):]
                    for gcode, png in fake.thumbs.items():
                        if name.endswith(".png") and gcode.rpartition("/")[2][:-6] in name:
                            return self._send(200, png, raw=True)
                    if name not in fake.gcodes:
                        return self._send(404, {"error": {"message": "File not found"}})
                    return self._send(200, fake.gcodes[name].encode(), raw=True)
                if path.startswith("/server/files/config/"):
                    name = path[len("/server/files/config/"):]
                    if name not in fake.files:
                        return self._send(404, {"error": {"message": "File not found"}})
                    return self._send(200, fake.files[name].encode(), raw=True)
                if path == "/server/files/logs/klippy.log":
                    return self._send(200, fake.klippy_log.encode(), raw=True)
                if path == "/machine/peripherals/serial":
                    return self._ok({"serial_devices": [{"path_by_id": s if "by-id" in s else None, "device_path": s}
                                                        for s in fake.serials]})
                return self._send(404, {"error": {"message": "Not found: " + path}})

            def do_POST(self):
                u = urllib.parse.urlparse(self.path)
                path = urllib.parse.unquote(u.path)
                length = int(self.headers.get("Content-Length") or 0)
                body = self.rfile.read(length)
                fake.calls.append(("POST", path))
                if path == "/server/files/upload":
                    b = re.search(r"boundary=(.+)", self.headers["Content-Type"]).group(1).encode()
                    fields, fname, content = {}, None, None
                    for part in body.split(b"--" + b):
                        if b"Content-Disposition" not in part:
                            continue
                        head, _, data = part.partition(b"\r\n\r\n")
                        data = data[:-2] if data.endswith(b"\r\n") else data
                        name = re.search(rb'name="([^"]+)"', head).group(1).decode()
                        fn = re.search(rb'filename="([^"]+)"', head)
                        if fn:
                            fname, content = fn.group(1).decode(), data.decode()
                        else:
                            fields[name] = data.decode()
                    full = (fields.get("path", "").strip("/") + "/" + fname).lstrip("/")
                    if fields.get("root") == "gcodes":
                        fake.gcodes[full] = content
                    else:
                        fake.files[full] = content
                    fake.calls.append(("UPLOAD", full))
                    return self._ok({"item": {"path": full, "root": fields.get("root")}})
                if path == "/printer/firmware_restart":
                    return self._ok("ok")
                if path == "/machine/services/restart":
                    return self._ok("ok")
                return self._send(404, {"error": {"message": "Not found: " + path}})

            def do_DELETE(self):
                u = urllib.parse.urlparse(self.path)
                path = urllib.parse.unquote(u.path)
                fake.calls.append(("DELETE", path))
                if path.startswith("/server/files/gcodes/"):
                    name = path[len("/server/files/gcodes/"):]
                    if name not in fake.gcodes:
                        return self._send(404, {"error": {"message": "File not found"}})
                    del fake.gcodes[name]
                    fake.deleted.append(name)
                    return self._ok({"item": {"path": name, "root": "gcodes"}})
                if path == "/server/files/directory":
                    q = urllib.parse.parse_qs(u.query)
                    folder = (q.get("path") or ["gcodes"])[0]
                    folder = folder[len("gcodes"):].strip("/")
                    inside = [p for p in fake.gcodes if folder and p.startswith(folder + "/")]
                    if inside and (q.get("force") or ["false"])[0] != "true":
                        return self._send(400, {"error": {"message": "Directory is not empty"}})
                    for p in inside:
                        del fake.gcodes[p]
                        fake.deleted.append(p)
                    return self._ok({"item": {"path": folder, "root": "gcodes"}})
                return self._send(404, {"error": {"message": "Not found: " + path}})

        return H
