# -*- coding: utf-8 -*-
"""Renders README screenshots from the test fixtures (no printer needed).

    python tools/screenshots.py [en|ar]
"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("ATGENX_STUDIO_HOME", os.path.join(ROOT, "tests", ".studio_home"))

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from studio import i18n  # noqa: E402
from studio.gui.app import Studio  # noqa: E402
from studio.gui.files_page import local_configset  # noqa: E402
from studio.gui.style import STYLE  # noqa: E402


def main(lang="en"):
    i18n.set_lang(lang)
    app = QApplication.instance() or QApplication(sys.argv)
    app.setLayoutDirection(Qt.RightToLeft if i18n.is_rtl() else Qt.LeftToRight)
    app.setStyleSheet(STYLE)
    fix = os.path.join(ROOT, "tests", "fixtures")
    win = Studio()
    win.resize(1360, 900)
    win.P["host"] = "mainsailos.local"
    win.refresh()
    with io.open(os.path.join(fix, "simple_printer.cfg"), encoding="utf-8") as f:
        text = f.read()
    win._load_text(text, "printer.cfg on mainsailos.local")
    win.set_configset(local_configset(os.path.join(fix, "modular")), ("local", "mainsailos.local"))
    win.show()
    out = os.path.join(ROOT, "docs", "screenshots")
    os.makedirs(out, exist_ok=True)
    shots = {"page_start": "start", "page_board": "board", "page_probe": "probe", "page_preview": "review", "page_files": "files"}

    def shot(builder, name):
        win.goto_page(builder)
        if builder == "page_preview":
            win.tabs.setCurrentIndex(1)
        app.processEvents()
        path = os.path.join(out, "%s-%s.png" % (name, lang))
        win.grab().save(path)
        print(path)

    for builder, name in shots.items():
        shot(builder, name)

    # a Voron 2.4 style machine for the motors page: 4 Z, sensorless X/Y, TMC Autotune
    from studio.boards import apply_board, get_board
    P = win.P
    board = get_board("bigtreetech-octopus-v1.1")
    P["kinematics"], P["bed_x"], P["bed_y"], P["probe"], P["z_leveling"] = "corexy", 350.0, 350.0, "inductive", "quad_gantry_level"
    for mid in ("z1", "z2", "z3"):
        P["motors"][mid]["enabled"] = True
    apply_board(P, board, keep_inversion=False)
    for mid in ("x", "y"):
        m = P["motors"][mid]
        m.update(run_current=1.4, microsteps=32, sensorless=True, sg=80, autotune="ldo-42sth48-2504ac")
    for mid in ("z", "z1", "z2", "z3"):
        P["motors"][mid].update(run_current=0.8, rotation_distance=40.0, autotune="ldo-42sth48-2004ac")
    P["motors"]["e"].update(run_current=0.5, rotation_distance=22.679, stealthchop=999999)
    win.sel_motor = "x"
    win.refresh()
    shot("page_motors", "motors")

    win._doctor_show("MCU 'mcu' shutdown: Timer too close\n"
                     "Unable to read tmc uart 'stepper_x' register IFCNT", "klippy.log")
    shot("page_doctor", "doctor")
    win.close()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "en")
