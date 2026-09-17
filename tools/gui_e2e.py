# -*- coding: utf-8 -*-
"""End-to-end test of the real app window against a fake Moonraker (no printer needed).

    QT_QPA_PLATFORM=offscreen python tools/gui_e2e.py [printer.cfg]

Clicks through every page and action: connect, import (with includes), detect serial, board,
motors & drivers, pins, generate, upload (+ printing / changed-file guards), restore,
config file editing, troubleshooter, language switch, projects.
"""
import io
import os
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests"))
os.environ["ATGENX_STUDIO_HOME"] = tempfile.mkdtemp(prefix="studio_e2e_")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtWidgets import QApplication, QMessageBox  # noqa: E402

from fake_moonraker import FakeMoonraker  # noqa: E402
from studio import i18n  # noqa: E402
from studio.gui.app import Studio  # noqa: E402
from studio.gui.style import STYLE  # noqa: E402
from studio.model import load_project, save_project  # noqa: E402

MESSAGES = []
RESULTS = []


def patch_dialogs():
    def record(kind, answer=None):
        def f(parent, title, text, *a, **k):
            MESSAGES.append((kind, str(text)))
            return answer if answer is not None else QMessageBox.Ok
        return staticmethod(f)
    QMessageBox.question = record("question", QMessageBox.Yes)
    QMessageBox.warning = record("warning", QMessageBox.Yes)
    QMessageBox.information = record("information")
    QMessageBox.critical = record("critical")


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond)))
    print("%s  %s%s" % ("PASS" if cond else "FAIL", name, ("  -  " + detail) if detail and not cond else ""))


def wait(win, timeout=60):
    app = QApplication.instance()
    t0 = time.time()
    app.processEvents()
    while win.busy and time.time() - t0 < timeout:
        app.processEvents()
        time.sleep(0.02)
    for _ in range(5):
        app.processEvents()


def last(kind):
    return next((t for k, t in reversed(MESSAGES) if k == kind), "")


def main():
    i18n.set_lang("en")
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyleSheet(STYLE)
    patch_dialogs()

    fix = os.path.join(ROOT, "tests", "fixtures")
    if len(sys.argv) > 1:
        printer_cfg = io.open(sys.argv[1], encoding="utf-8").read()
        files = {"printer.cfg": printer_cfg}
    else:
        printer_cfg = io.open(os.path.join(fix, "simple_printer.cfg"), encoding="utf-8").read()
        files = {"printer.cfg": printer_cfg, "macros.cfg": "[gcode_macro PARK]\ngcode:\n    G1 X10 F6000\n"}
    files["moonraker.conf"] = "[server]\nhost: 0.0.0.0\n"
    files["crowsnest.conf"] = "[cam 1]\nmode: ustreamer\n"
    fake = FakeMoonraker(files).start()

    win = Studio()
    win.P["host"], win.P["port"] = "127.0.0.1", fake.port
    win.refresh()

    # ---- connection
    win.act_test()
    wait(win)
    check("connect: test connection", "Connected" in win.info_box.toPlainText(), win.info_box.toPlainText()[:200])
    check("connect: MCU shown", "stm32f446xx" in win.info_box.toPlainText())

    win.act_import_printer()
    wait(win)
    check("import: printer.cfg loaded", win.current_text == printer_cfg.replace("\r\n", "\n"))
    check("import: all config files loaded", win.cs is not None and set(files) <= set(win.cs.files),
          str(win.cs and list(win.cs.files)))
    check("import: motors read", win.P["motors"]["x"]["step_pin"] != "")

    # ---- pages
    for i in range(win.nav.count()):
        win.nav.setCurrentRow(i)
        app.processEvents()
    check("pages: every page opens", win.stack.currentIndex() == win.nav.count() - 1)

    win.act_detect_serial()
    wait(win)
    check("board: serial detected", "FAKE123" in win.P["mcu_serial"] or
          "FAKE123" in win.binds_by_key["mcu_serial"].text())
    win.collect()

    # ---- motors & drivers
    win.goto_page("page_motors")
    app.processEvents()
    rows_before = win.motor_table.rowCount()
    board = win.board()
    extra = next(m for m in ("z1", "z2", "z3", "x1", "y1") if not win.P["motors"][m]["enabled"])
    free_before = board and len(board["drivers"]) > rows_before
    win.act_add_motor(extra)
    check("motors: add " + extra, win.P["motors"][extra]["enabled"] and win.motor_table.rowCount() == rows_before + 1)
    if free_before:
        check("motors: new motor got a free socket", win.P["motors"][extra]["slot"] != "")
    win._driver_changed("y", "tmc5160")
    check("motors: driver change y -> tmc5160", win.P["motors"]["y"]["driver"] == "tmc5160")
    win._driver_changed("y", win.P["motors"]["x"]["driver"])
    if win.P["motors"]["x"]["driver"] in ("tmc2209", "tmc2130", "tmc5160", "tmc2240"):
        win._sensorless_changed("x", True)
        check("motors: sensorless x on", win.P["motors"]["x"]["sensorless"] and win.P["motors"]["x"]["diag_pin"])
        win._sensorless_changed("x", False)
    win.sel_motor = extra
    win.act_remove_motor()
    check("motors: remove " + extra, not win.P["motors"][extra]["enabled"])

    # ---- features: built-in switch, section on/off, catalog
    win.goto_page("page_features")
    app.processEvents()
    win._toggle_builtin("retraction", True)
    win.do_generate()
    check("features: built-in switch adds its section", win.P["retraction"] and "[firmware_retraction]" in win.generated)
    macro = next((l[1:-1] for l in printer_cfg.splitlines() if l.startswith("[gcode_macro ")), None)
    if macro:
        win._toggle_section(macro, True, False)
        win.do_generate()
        check("features: section switched off is commented out", ("#[%s]" % macro) in win.generated)
        win._toggle_section(macro, True, True)
        win.do_generate()
        check("features: section switched back on", ("\n[%s]" % macro) in win.generated)
    from studio.features import CATALOG, section_names
    cid, sec = next((c, section_names(spec[3])[0]) for c, spec in CATALOG.items()
                    if c != "blank" and ("[%s]" % section_names(spec[3])[0]) not in printer_cfg)
    win._add_catalog(cid)
    win.do_generate()
    check("features: catalog item added (%s)" % cid, ("[%s]" % sec) in win.generated)
    win._remove_custom(len(win.P["custom_sections"]) - 1)
    win.do_generate()
    check("features: catalog item removed", ("[%s]" % sec) not in win.generated)
    check("features: sidebar badges and help panel", win.nav.item(0).text() and win.help_page_title.text())

    # ---- pins page edit survives navigation
    win.goto_page("page_pins")
    app.processEvents()
    for r in range(win.pin_table.rowCount()):
        if win.pin_table.item(r, 0).data(Qt.UserRole) == ("pin", "hotend_fan"):
            win.pin_table.item(r, 1).setText("PB15")
    win.goto_page("page_preview")
    app.processEvents()
    check("pins: edit kept", win.P["pins"]["hotend_fan"] == "PB15")

    # ---- generate & upload
    win.do_generate()
    errs = [r[1] for r in win.results if r[0] == "error"]
    check("preview: generated without errors", win.generated and not errs, " | ".join(errs))
    check("preview: macros kept", win.generated.count("[gcode_macro ") >= printer_cfg.count("[gcode_macro "))

    fake.print_state = "printing"
    MESSAGES.clear()
    win.act_upload()
    wait(win)
    check("upload: refused while printing", "printing" in last("critical").lower() and
          fake.files["printer.cfg"] == printer_cfg)
    fake.print_state = "standby"

    fake.files["printer.cfg"] = printer_cfg + "\n# changed by SAVE_CONFIG\n"
    MESSAGES.clear()
    win.act_upload()
    wait(win)
    check("upload: refused when file changed on printer", "changed on the printer" in last("critical"))
    fake.files["printer.cfg"] = printer_cfg

    MESSAGES.clear()
    new_text = win.generated
    win.act_upload()
    wait(win, 90)
    backups = [p for p in fake.files if p.startswith("studio_backups/")]
    check("upload: new printer.cfg on printer", fake.files["printer.cfg"] == new_text, last("critical"))
    check("upload: backup on printer", backups and fake.files[backups[-1]] == printer_cfg)
    check("upload: local backup", os.listdir(os.path.join(os.environ["ATGENX_STUDIO_HOME"], "backups")))
    check("upload: FIRMWARE_RESTART sent", ("POST", "/printer/firmware_restart") in fake.calls)
    check("upload: success message", "Klipper is ready" in last("information"))

    win.act_restore()
    wait(win, 90)
    check("restore: backup uploaded back", fake.files["printer.cfg"] == printer_cfg)

    # ---- config files page
    win.act_files_load_printer()
    wait(win)
    win._files_open("moonraker.conf")
    win.file_editor.setPlainText(files["moonraker.conf"] + "\n[octoprint_compat]\n")
    fake.calls.clear()
    win.act_files_save()
    wait(win)
    check("files: moonraker.conf saved", "[octoprint_compat]" in fake.files["moonraker.conf"])
    check("files: moonraker restarted", ("POST", "/machine/services/restart") in fake.calls)
    check("files: backup made", any(p.startswith("studio_backups/moonraker.conf") for p in fake.files))

    # ---- troubleshooter
    fake.state = "error"
    fake.klippy_log = ("old session\nADC out of range\nStart printer at Mon Sep 1\n===== Config file =====\n"
                       "# Timer too close in a comment\n=======================\n"
                       "Unable to read tmc uart 'stepper_x' register IFCNT\n")
    win.act_doctor_printer()
    wait(win)
    cards = win.doctor_results.count() - 1
    check("doctor: finds TMC problem from klippy.log", cards == 1, "cards=%d" % cards)
    win._doctor_show("Heater extruder not heating at expected rate", "test")
    check("doctor: pasted text", win.doctor_results.count() - 1 == 1)

    # ---- projects & language
    tmp = os.path.join(os.environ["ATGENX_STUDIO_HOME"], "p.studio.json")
    win.collect()
    save_project(win.P, tmp)
    P2 = load_project(tmp)
    check("project: save/load round trip", P2["motors"] == win.P["motors"] and P2["pins"] == win.P["pins"])

    win.act_language()
    app.processEvents()
    nw = app._studio_window
    check("language: switched to Arabic window", i18n.get_lang() == "ar" and nw is not win and nw.P is win.P)
    nw.do_generate()
    check("language: Arabic window generates", bool(nw.generated))

    fake.stop()
    failed = [n for n, ok in RESULTS if not ok]
    print("\n%d checks, %d failed" % (len(RESULTS), len(failed)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
