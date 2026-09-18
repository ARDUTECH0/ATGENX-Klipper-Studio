# -*- coding: utf-8 -*-
"""Command line interface.

  python -m studio                          start the app
  python -m studio boards [--mcu lpc1769]   list supported boards
  python -m studio check  printer.cfg       import + merge + validate (writes nothing on the printer)
  python -m studio generate project.json [-o printer.cfg] [--base existing.cfg] [--full]
  python -m studio --smoke                  build the UI and exit (for CI)
"""
import argparse
import difflib
import io
import os
import re
import sys

from . import APP_NAME, __version__, i18n
from .boards import board_label, boards_for_mcu, get_board, load_boards
from .cfgtools import split_save
from .i18n import tr
from .importer import import_config
from .merge import build
from .model import MOTOR_LABEL, enabled_motors, load_project
from .validate import validate

ICONS = {"error": "✖", "warn": "▲", "ok": "✔"}


def _utf8():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass


def cmd_boards(a):
    boards = load_boards()
    ids = boards_for_mcu(a.mcu, boards) if a.mcu else list(boards)
    for bid in ids:
        b = boards[bid]
        m = b.get("mcu", {})
        print("%-34s %-44s %-8s %s" % (bid, board_label(b), m.get("family") or "", ",".join(m.get("processors") or [])))
    print("\n%d boards" % len(ids))
    return 0


def _report(P, text, out, board):
    R = validate(P, out, board)
    old_main, _ = split_save(text or "")
    new_main, new_save = split_save(out)
    d = list(difflib.unified_diff((text or "").splitlines(), out.splitlines(), lineterm=""))
    print("  lines      %d -> %d   diff +%d -%d" % ((text or "").count("\n"), out.count("\n"),
          sum(1 for l in d if l[:1] == "+" and l[:3] != "+++"), sum(1 for l in d if l[:1] == "-" and l[:3] != "---")))
    print("  macros     %d -> %d" % (len(re.findall(r"^\[gcode_macro ", old_main, re.M)),
                                      len(re.findall(r"^\[gcode_macro ", new_main, re.M))))
    print("  SAVE_CONFIG %s" % re.findall(r"^#\*# \[([^\]]+)\]", new_save, re.M))
    for kind, msg, _page in R:
        if kind != "ok" or msg.startswith(("Mesh", "منطقة")):
            print("  %s %s" % (ICONS[kind], msg))
    return sum(1 for r in R if r[0] == "error")


def cmd_check(a):
    with io.open(a.file, encoding="utf-8") as f:
        text = f.read().replace("\r\n", "\n")
    P, notes = import_config(text)
    if a.board:
        P["board"] = a.board
    board = get_board(P["board"])
    print("== import ==")
    for k in ("board", "kinematics", "probe", "probe_z", "z_leveling", "pid_e_kp", "pid_b_kp", "pa",
              "shaper_x", "shaper_y", "shaper_z", "leds", "led_effects", "fil_sensor", "max_accel", "max_z_accel"):
        print("  %-12s %s" % (k, P[k]))
    for mid in enabled_motors(P):
        m = P["motors"][mid]
        print("  motor %-3s slot=%-11s %-8s %sA ms=%s rd=%s%s%s" % (
            MOTOR_LABEL[mid], m["slot"] or "-", m["driver"], m["run_current"], m["microsteps"], m["rotation_distance"],
            " sensorless" if m["sensorless"] else "", " z=" + m["z_position"] if m["z_position"] else ""))
    for key, kw in notes:
        print("  • " + tr(key, **kw))
    errors = 0
    for mode in ("merge", "full"):
        out = build(P, text, mode, True, board)
        print("\n== %s ==" % mode)
        errors += _report(P, text, out, board)
        if a.out:
            os.makedirs(a.out, exist_ok=True)
            path = os.path.join(a.out, "printer.%s.cfg" % mode)
            with io.open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(out)
            print("  -> %s" % path)
    return 1 if errors else 0


def cmd_generate(a):
    P = load_project(a.project)
    base = None
    if a.base:
        with io.open(a.base, encoding="utf-8") as f:
            base = f.read().replace("\r\n", "\n")
    board = get_board(P["board"])
    out = build(P, base, "full" if a.full else "merge", True, board)
    errors = _report(P, base, out, board)
    with io.open(a.output, "w", encoding="utf-8", newline="\n") as f:
        f.write(out)
    print("-> %s" % a.output)
    return 1 if errors else 0


def cmd_doctor(a):
    from .doctor import card, diagnose, last_session
    with io.open(a.file, encoding="utf-8", errors="replace") as f:
        text = f.read()
    hits = diagnose(last_session(text) if a.file.endswith(".log") else text)
    if not hits:
        print(tr("doctor.nothing"))
        return 0
    for rid, line, _page in hits:
        title, cause, fix = card(rid)
        print("\n## %s\n   > %s\n   %s\n   %s" % (title, line, cause, fix.replace("\n", "\n   ")))
    return 0


def main(argv=None):
    _utf8()
    argv = sys.argv[1:] if argv is None else argv
    p = argparse.ArgumentParser(prog="python -m studio", description="%s %s" % (APP_NAME, __version__))
    p.add_argument("--lang", choices=i18n.LANGS)
    p.add_argument("--version", action="version", version="%s %s" % (APP_NAME, __version__))
    p.add_argument("--smoke", action="store_true", help=argparse.SUPPRESS)
    sub = p.add_subparsers(dest="cmd")
    b = sub.add_parser("boards", help="list supported boards")
    b.add_argument("--mcu", default="")
    c = sub.add_parser("check", help="import, merge and validate a printer.cfg")
    c.add_argument("file")
    c.add_argument("--board", default="")
    c.add_argument("--out", default="")
    d = sub.add_parser("doctor", help="explain Klipper errors from klippy.log or a pasted message file")
    d.add_argument("file")
    g = sub.add_parser("generate", help="generate printer.cfg from a project file")
    g.add_argument("project")
    g.add_argument("-o", "--output", default="printer.cfg")
    g.add_argument("--base", default="")
    g.add_argument("--full", action="store_true")
    a = p.parse_args(argv)

    i18n.set_lang(a.lang or i18n.system_lang())
    if a.cmd == "boards":
        return cmd_boards(a)
    if a.cmd == "check":
        return cmd_check(a)
    if a.cmd == "doctor":
        return cmd_doctor(a)
    if a.cmd == "generate":
        return cmd_generate(a)
    try:
        from .gui.app import run
    except ImportError as e:
        print("PySide6 is required for the app:  pip install -r requirements.txt\n(%s)" % e)
        return 2
    return run(smoke=a.smoke, lang=a.lang or "")
