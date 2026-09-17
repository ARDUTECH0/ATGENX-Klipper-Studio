# -*- coding: utf-8 -*-
"""Minimal Moonraker HTTP client (standard library only)."""
import json
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

from .i18n import tr


class MoonrakerError(Exception):
    pass


class Moonraker:
    def __init__(self, host, port=7125, api_key="", timeout=10):
        host = (host or "").strip().rstrip("/")
        for pre in ("http://", "https://"):
            if host.startswith(pre):
                host = host[len(pre):]
        if not host:
            raise MoonrakerError(tr("mr.no_host"))
        self.base = "http://%s:%d" % (host, int(port))
        self.api_key = (api_key or "").strip()
        self.timeout = timeout

    def _req(self, method, path, data=None, headers=None, raw=False, timeout=None):
        headers = dict(headers or {})
        if self.api_key:
            headers["X-Api-Key"] = self.api_key
        req = urllib.request.Request(self.base + path, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout or self.timeout) as r:
                body = r.read()
        except urllib.error.HTTPError as e:
            msg = e.read().decode("utf-8", "replace")
            try:
                msg = json.loads(msg)["error"]["message"]
            except (ValueError, KeyError, TypeError):
                pass
            if e.code in (401, 403):
                raise MoonrakerError(tr("mr.unauthorized"))
            raise MoonrakerError("HTTP %d: %s" % (e.code, str(msg)[:300]))
        except urllib.error.URLError as e:
            raise MoonrakerError(tr("mr.no_connection", url=self.base, reason=e.reason))
        except OSError as e:
            raise MoonrakerError(tr("mr.network", err=e))
        if raw:
            return body
        try:
            return json.loads(body.decode("utf-8"))
        except ValueError:
            raise MoonrakerError(tr("mr.bad_reply"))

    def get(self, path):
        return self._req("GET", path)["result"]

    def post(self, path):
        return self._req("POST", path)["result"]

    # ---- info ----
    def info(self):
        return self.get("/printer/info")

    def server_info(self):
        return self.get("/server/info")

    def query(self, *objs):
        q = "&".join(urllib.parse.quote(o) for o in objs)
        return self.get("/printer/objects/query?" + q)["status"]

    def print_state(self):
        try:
            return self.query("print_stats")["print_stats"]["state"]
        except (MoonrakerError, KeyError):
            return "unknown"

    def mcu_chip(self):
        """Processor reported by the main MCU, e.g. 'lpc1769' or 'stm32f446xx' ('' if unknown)."""
        try:
            m = self.query("mcu")["mcu"]
            return (m.get("mcu_constants", {}).get("MCU") or "").lower()
        except (MoonrakerError, KeyError, AttributeError):
            return ""

    def serial_devices(self):
        """Serial ports on the host (Moonraker >= 0.8). [] when unsupported."""
        try:
            devs = self.get("/machine/peripherals/serial").get("serial_devices", [])
        except MoonrakerError:
            return []
        out = []
        for d in devs:
            p = d.get("path_by_id") or d.get("device_path")
            if p:
                out.append(p)
        return out

    # ---- files ----
    def download_config(self, name="printer.cfg"):
        body = self._req("GET", "/server/files/config/" + urllib.parse.quote(name), raw=True)
        return body.decode("utf-8")

    def list_config(self):
        return [f["path"] for f in self.get("/server/files/list?root=config")]

    def list_config_sizes(self):
        return [(f["path"], f.get("size", 0)) for f in self.get("/server/files/list?root=config")]

    def config_warnings(self):
        """Klipper's own config warnings (deprecated options, ...)."""
        try:
            return self.query("configfile")["configfile"].get("warnings", [])
        except (MoonrakerError, KeyError):
            return []

    def upload_config(self, name, text):
        """Uploads to the config root. `name` may contain sub folders (a/b.cfg)."""
        b = "----studio" + uuid.uuid4().hex
        folder, _, base = name.rpartition("/")
        path_field = ("--%s\r\nContent-Disposition: form-data; name=\"path\"\r\n\r\n%s\r\n" % (b, folder)) if folder else ""
        data = (("--%s\r\nContent-Disposition: form-data; name=\"root\"\r\n\r\nconfig\r\n" % b) + path_field +
                ("--%s\r\nContent-Disposition: form-data; name=\"file\"; filename=\"%s\"\r\n"
                 "Content-Type: text/plain\r\n\r\n" % (b, base))).encode("utf-8")
        data += text.encode("utf-8") + ("\r\n--%s--\r\n" % b).encode("utf-8")
        return self._req("POST", "/server/files/upload", data=data, timeout=30,
                         headers={"Content-Type": "multipart/form-data; boundary=" + b})

    # ---- control ----
    def firmware_restart(self):
        return self.post("/printer/firmware_restart")

    def restart_service(self, service):
        return self.post("/machine/services/restart?service=" + urllib.parse.quote(service))

    def wait_ready(self, seconds=45):
        t0 = time.time()
        last = None
        time.sleep(3)
        while time.time() - t0 < seconds:
            try:
                last = self.info()
                if last.get("state") in ("ready", "error", "shutdown"):
                    return last
            except MoonrakerError:
                pass
            time.sleep(2)
        return last or {"state": "timeout", "state_message": tr("mr.timeout")}


def safe_upload(m, new_text, base_text, log=print, backup_writer=None):
    """Upload with every safety check. Returns (backup_name, previous_text, klipper_info).

    1. refuse while printing / paused
    2. refuse if printer.cfg changed since it was downloaded (e.g. SAVE_CONFIG)
    3. backup on the printer (and locally through backup_writer)
    4. upload, FIRMWARE_RESTART, wait for Klipper
    """
    st = m.print_state()
    log(tr("up.state", state=st))
    if st in ("printing", "paused"):
        raise MoonrakerError(tr("up.busy_" + st))
    fresh = m.download_config("printer.cfg").replace("\r\n", "\n")
    if base_text is not None and fresh != base_text:
        raise MoonrakerError(tr("up.changed_on_printer"))
    name = _backup(m, "printer.cfg", fresh, log, backup_writer)
    m.upload_config("printer.cfg", new_text)
    log(tr("up.uploaded", lines=new_text.count("\n")))
    m.firmware_restart()
    log(tr("up.restarting"))
    return name, fresh, m.wait_ready()


def backup_name(path):
    """studio_backups/<file>.<timestamp>.bak - a sub folder, so [include *.cfg] never picks it up."""
    from datetime import datetime
    return "studio_backups/%s.%s.bak" % (path.replace("/", "__"), datetime.now().strftime("%Y%m%d_%H%M%S"))


def _backup(m, path, text, log, backup_writer):
    name = backup_name(path)
    m.upload_config(name, text)
    log(tr("up.backup_remote", name=name))
    if backup_writer:
        log(tr("up.backup_local", path=backup_writer(name.split("/")[-1], text)))
    return name


def safe_save_file(m, path, new_text, original_text, restart="", log=print, backup_writer=None):
    """Saves any config file with the same safety rules as printer.cfg. Returns (backup name, klipper info)."""
    st = m.print_state()
    if st in ("printing", "paused"):
        raise MoonrakerError(tr("up.busy_" + st))
    fresh = m.download_config(path).replace("\r\n", "\n")
    if original_text is not None and fresh != original_text:
        raise MoonrakerError(tr("files.changed_on_printer", path=path))
    name = _backup(m, path, fresh, log, backup_writer)
    m.upload_config(path, new_text)
    log(tr("files.saved", path=path))
    info = None
    if restart == "klipper":
        m.firmware_restart()
        log(tr("up.restarting"))
        info = m.wait_ready()
    elif restart:
        m.restart_service(restart)
        log(tr("files.service_restarted", service=restart))
    return name, info
