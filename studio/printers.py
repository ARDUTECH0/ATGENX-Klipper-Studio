# -*- coding: utf-8 -*-
"""The list of printers the app knows about, and where each one keeps its files.

Stored in the user's settings file, so it survives updates and is never part of a project.
Each printer may override the ports and the folder its gcode goes into; anything left empty
falls back to the default.
"""
import uuid

from .appdata import load_settings, save_settings

DEFAULT_PORT = 7125
DEFAULT_SSH_PORT = 22
FIELDS = ("id", "name", "host", "port", "ssh_port", "remote_path", "api_key", "enabled")


def new_printer(name="", host="", port=DEFAULT_PORT, ssh_port=DEFAULT_SSH_PORT,
                remote_path="", api_key="", enabled=True):
    return {"id": uuid.uuid4().hex[:12], "name": name or host or "printer", "host": host,
            "port": int(port or DEFAULT_PORT), "ssh_port": int(ssh_port or DEFAULT_SSH_PORT),
            "remote_path": remote_path or "", "api_key": api_key or "", "enabled": bool(enabled)}


def _clean(p):
    out = new_printer()
    out.update(dict((k, p[k]) for k in FIELDS if k in p))
    out["id"] = str(out["id"] or uuid.uuid4().hex[:12])
    out["port"] = int(out["port"] or DEFAULT_PORT)
    out["ssh_port"] = int(out["ssh_port"] or DEFAULT_SSH_PORT)
    out["enabled"] = bool(out["enabled"])
    out["name"] = str(p.get("name") or out["host"] or "printer")  # unnamed printers go by their host
    return out


def load_printers():
    items = load_settings().get("printers")
    return [_clean(p) for p in items if isinstance(p, dict)] if isinstance(items, list) else []


def save_printers(printers):
    s = load_settings()
    s["printers"] = [_clean(p) for p in printers]
    save_settings(s)
    return s["printers"]


def add_printer(printers, printer):
    printers = list(printers) + [_clean(printer)]
    return save_printers(printers)


def update_printer(printers, pid, **changes):
    printers = [dict(p, **changes) if p["id"] == pid else p for p in printers]
    return save_printers(printers)


def delete_printer(printers, pid):
    return save_printers([p for p in printers if p["id"] != pid])


def move_printer(printers, pid, delta):
    """Reorder: delta -1 moves it up the list, +1 down."""
    items = list(printers)
    idx = next((i for i, p in enumerate(items) if p["id"] == pid), -1)
    new = idx + delta
    if idx < 0 or not (0 <= new < len(items)):
        return save_printers(items)
    items[idx], items[new] = items[new], items[idx]
    return save_printers(items)


def client(printer, timeout=10):
    """A Moonraker client for one printer, with its own port and key."""
    from .moonraker import Moonraker
    return Moonraker(printer["host"], printer.get("port") or DEFAULT_PORT,
                     printer.get("api_key") or "", timeout=timeout)


def label(printer):
    host = printer.get("host") or "?"
    port = int(printer.get("port") or DEFAULT_PORT)
    return "%s  (%s%s)" % (printer.get("name") or host, host, "" if port == DEFAULT_PORT else ":%d" % port)
