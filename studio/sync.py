# -*- coding: utf-8 -*-
"""Sending files to several printers at once - the part that does the work.

No Qt in here on purpose: the window subscribes to events, and the tests drive the same code
against a fake Moonraker.

Safety rules that are not optional:
  * a file that is printing right now, or waiting in the printer's queue, is never overwritten
    and never deleted - it is skipped and reported;
  * a dry run performs every check and every comparison, and sends nothing.
"""
import os
import threading
import time

from .moonraker import Aborted, MoonrakerError
from .printers import client

UPLOAD, REPLACE, SAME, BUSY, FAILED = "upload", "replace", "same", "busy", "failed"


class Options(object):
    def __init__(self, remote_dir="", dry_run=False, skip_same=True, workers=4):
        self.remote_dir = (remote_dir or "").strip("/")
        self.dry_run = bool(dry_run)
        self.skip_same = bool(skip_same)   # a file of the same size that is already there
        self.workers = max(1, int(workers))


def local_files(paths):
    """Turns files and folders into [(absolute path, name on the printer, size)]."""
    out = []
    for p in paths:
        p = os.path.abspath(p)
        if os.path.isdir(p):
            for root, _, names in os.walk(p):
                for n in sorted(names):
                    if n.lower().endswith((".gcode", ".gco", ".g", ".ufp", ".3mf")):
                        full = os.path.join(root, n)
                        rel = os.path.relpath(full, p).replace("\\", "/")
                        out.append((full, rel, os.path.getsize(full)))
        elif os.path.isfile(p):
            out.append((p, os.path.basename(p), os.path.getsize(p)))
    return out


def remote_name(opts, rel):
    return "%s/%s" % (opts.remote_dir, rel) if opts.remote_dir else rel


def plan(m, files, opts):
    """What would happen to each file, without touching anything."""
    try:
        existing = m.list_gcodes()
    except MoonrakerError:
        existing = {}
    busy = m.busy_files()
    actions = []
    for path, rel, size in files:
        name = remote_name(opts, rel)
        if name in busy:
            actions.append((BUSY, path, name, size))
        elif name in existing:
            same = opts.skip_same and existing.get(name) == size
            actions.append((SAME if same else REPLACE, path, name, size))
        else:
            actions.append((UPLOAD, path, name, size))
    return actions


def sync_one(printer, files, opts, emit, stop=None):
    """Sends `files` to one printer. Returns a summary dict; never raises."""
    pid = printer["id"]
    done = {"printer": pid, "sent": 0, "skipped": 0, "busy": 0, "failed": 0, "bytes": 0, "error": ""}
    opts_dir = opts.remote_dir or (printer.get("remote_path") or "")
    one = Options(opts_dir, opts.dry_run, opts.skip_same, opts.workers)
    try:
        m = client(printer, timeout=15)
        m.server_info()  # fail here, loudly, rather than look like a printer with nothing to do
        emit("start", pid, {"label": printer.get("name") or printer.get("host")})
        actions = plan(m, files, one)
    except MoonrakerError as e:
        done["error"] = str(e)
        emit("error", pid, {"text": str(e)})
        emit("done", pid, done)
        return done

    total_bytes = sum(a[3] for a in actions if a[0] in (UPLOAD, REPLACE)) or 1
    sent_bytes = [0]
    started = time.time()
    for kind, path, name, size in actions:
        if stop and stop():
            emit("log", pid, {"level": "warn", "text": "stopped"})
            break
        if kind == BUSY:
            done["busy"] += 1
            emit("skip", pid, {"name": name, "why": "busy"})
            continue
        if kind == SAME:
            done["skipped"] += 1
            emit("skip", pid, {"name": name, "why": "same"})
            continue
        if one.dry_run:
            done["sent"] += 1
            done["bytes"] += size
            emit("file", pid, {"name": name, "size": size, "dry": True,
                               "replace": kind == REPLACE, "progress": 1.0})
            continue

        def progress(got, tot, _n=name, _s=size):
            sent = sent_bytes[0] + got
            secs = max(0.001, time.time() - started)
            speed = sent / secs
            emit("progress", pid, {"name": _n, "sent": got, "total": tot, "speed": speed,
                                   "eta": max(0.0, (total_bytes - sent) / speed) if speed else 0.0,
                                   "overall": min(1.0, sent / float(total_bytes))})
        try:
            m.upload_gcode(path, one.remote_dir, progress=progress, stop=stop)
            sent_bytes[0] += size
            done["sent"] += 1
            done["bytes"] += size
            emit("file", pid, {"name": name, "size": size, "dry": False, "replace": kind == REPLACE,
                               "progress": min(1.0, sent_bytes[0] / float(total_bytes))})
        except Aborted:
            emit("log", pid, {"level": "warn", "text": "stopped"})
            break
        except (MoonrakerError, OSError) as e:
            done["failed"] += 1
            emit("fail", pid, {"name": name, "text": str(e)})
    emit("done", pid, done)
    return done


def sync(printers, files, opts, emit, stop=None):
    """Sends the same files to every printer at the same time, one thread each."""
    results = {}
    threads = []

    def work(p):
        results[p["id"]] = sync_one(p, files, opts, emit, stop)

    for p in printers:
        t = threading.Thread(target=work, args=(p,), daemon=True)
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    return results


def human_size(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return "%.0f %s" % (n, unit) if unit == "B" else "%.1f %s" % (n, unit)
        n /= 1024.0


def human_time(secs):
    secs = int(max(0, secs))
    if secs < 60:
        return "%ds" % secs
    if secs < 3600:
        return "%dm %02ds" % (secs // 60, secs % 60)
    return "%dh %02dm" % (secs // 3600, (secs % 3600) // 60)
