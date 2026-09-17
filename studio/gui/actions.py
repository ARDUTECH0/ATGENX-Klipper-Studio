# -*- coding: utf-8 -*-
"""User actions: projects, printer connection, board, generate, upload."""
import difflib
import io
import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QFileDialog, QListWidgetItem, QMessageBox

from .. import APP_NAME
from ..appdata import write_backup
from ..boards import (apply_board, board_label, boards_for_mcu, build_hint, get_board,
                      load_boards, slots)
from ..cfgtools import fmt as n
from ..configset import ConfigSet
from ..generator import mesh_bounds
from ..i18n import tr
from ..importer import import_config
from ..merge import build
from ..model import load_project, new_params, save_project
from ..moonraker import Moonraker, MoonrakerError, safe_upload
from ..validate import validate

KLIPPER_FLASH_DOCS = "https://www.klipper3d.org/Installation.html#building-and-flashing-the-micro-controller"


class ActionsMixin:
    # ---------- helpers ----------
    def mr(self):
        self.collect()
        return Moonraker(self.P["host"], self.P["port"], self.api_key.text())

    def board(self):
        return get_board(self.P.get("board", ""))

    def _board_changed(self):
        if not hasattr(self, "board_info"):
            return
        i = self.board_cb.currentIndex()
        bid = self.board_ids[i] if 0 <= i < len(self.board_ids) else ""
        b = get_board(bid)
        if not b:
            self.board_info.setText(tr("board.custom_info"))
            return
        rows = "".join("<tr><td style='color:#8b949e;padding-right:14px'>%s</td><td>%s</td></tr>" % (k, v)
                       for k, v in build_hint(b))
        extras = ", ".join(e["name"] for e in b.get("extra_sections", [])) or "-"
        self.board_info.setText(
            "<b>%s</b><br><br>"
            "<span style='color:#8b949e'>make menuconfig</span><table>%s</table><br>"
            "%s: %d &nbsp;·&nbsp; TMC: %s<br>%s: %s<br><br>"
            "<a style='color:#58a6ff' href='%s'>%s</a> &nbsp;·&nbsp; <a style='color:#58a6ff' href='%s'>%s</a>" % (
                board_label(b), rows, tr("board.driver_slots"), len(b["drivers"]),
                ", ".join(b.get("tmc_types") or ["-"]), tr("board.required_sections"), extras,
                b["source"], tr("board.source_link"), KLIPPER_FLASH_DOCS, tr("board.flash_link")))

    def _log(self, msg):
        if hasattr(self, "log_box"):
            from datetime import datetime
            self.log_box.appendPlainText("[%s]  %s" % (datetime.now().strftime("%H:%M:%S"), msg))
        self.statusBar().showMessage(msg, 8000)

    def _notes(self, notes):
        for key, kw in notes:
            self._log("• " + tr(key, **kw))

    # ---------- generate ----------
    def do_generate(self):
        if not hasattr(self, "out_box"):
            return
        self.collect()
        x0, y0, x1, y1 = mesh_bounds(self.P)
        self.mesh_lbl.setText("X %s → %s    Y %s → %s" % (n(x0), n(x1), n(y0), n(y1)))
        mode = "merge" if self.rb_merge.isChecked() else "full"
        self.cb_keep.setEnabled(mode == "full")
        board = self.board()
        try:
            self.generated = build(self.P, self.current_text, mode, self.cb_keep.isChecked(), board)
        except Exception as e:  # show any generator bug instead of crashing the UI
            self.generated = ""
            self.out_box.setPlainText(tr("preview.gen_error", err=e))
            return
        self.out_box.setPlainText(self.generated)
        if self.current_text:
            d = list(difflib.unified_diff(self.current_text.splitlines(), self.generated.splitlines(),
                                          tr("preview.current"), tr("preview.new"), lineterm="", n=2))
            add = sum(1 for l in d if l.startswith("+") and not l.startswith("+++"))
            rem = sum(1 for l in d if l.startswith("-") and not l.startswith("---"))
            self.diff_box.setPlainText("\n".join(d) if d else tr("preview.no_diff"))
            self.tabs.setTabText(1, "%s  (+%d  −%d)" % (tr("preview.diff"), add, rem))
            self.src_lbl.setText(tr("preview.based_on", src=self.current_src))
        else:
            self.diff_box.setPlainText(tr("preview.no_current"))
            self.tabs.setTabText(1, tr("preview.diff"))
            self.src_lbl.setText(tr("preview.no_current_full"))
        cs = getattr(self, "cs", None)
        self.results = validate(self.P, self.generated, board,
                                elsewhere=cs.section_files() if cs else None,
                                klipper_warnings=cs.warnings if cs else None)
        self.val_list.clear()
        icons = {"error": ("✖", "#f85149"), "warn": ("▲", "#d29922"), "ok": ("✔", "#3fb950")}
        errs = 0
        order = {"error": 0, "warn": 1, "ok": 2}
        for kind, msg, page in sorted(self.results, key=lambda r: order[r[0]]):
            ic, col = icons[kind]
            it = QListWidgetItem("%s   %s" % (ic, msg))
            it.setForeground(QColor(col))
            it.setData(Qt.UserRole, page)
            if kind != "ok" and page != "page_preview":
                it.setToolTip(tr("preview.check_click"))
            self.val_list.addItem(it)
            errs += kind == "error"
        self.tabs.setTabText(0, tr("preview.checks_errors", count=errs) if errs else tr("preview.checks") + "  ✔")
        self.update_nav_status()

    # ---------- projects ----------
    def act_new(self):
        if QMessageBox.question(self, APP_NAME, tr("msg.confirm_new")) == QMessageBox.Yes:
            host, port = self.P["host"], self.P["port"]
            self.P = new_params()
            self.P["host"], self.P["port"] = host, port
            self.current_text = self.current_src = None
            self.refresh()
            self.do_generate()

    def act_open_project(self):
        path, _ = QFileDialog.getOpenFileName(self, tr("tb.open_project"), os.path.expanduser("~"),
                                              "Studio project (*.studio.json *.json)")
        if not path:
            return
        try:
            self.P = load_project(path)
            self.refresh()
            self._log(tr("msg.project_opened", name=os.path.basename(path)))
        except Exception as e:
            QMessageBox.critical(self, APP_NAME, tr("msg.project_open_failed", err=e))

    def act_save_project(self):
        self.collect()
        name = (self.P.get("printer_name") or "printer").strip().replace(" ", "-").lower()
        path, _ = QFileDialog.getSaveFileName(self, tr("tb.save_project"),
                                              os.path.join(os.path.expanduser("~"), name + ".studio.json"),
                                              "Studio project (*.studio.json)")
        if path:
            save_project(self.P, path)
            self._log(tr("msg.project_saved", name=os.path.basename(path)))

    def act_open_cfg(self):
        path, _ = QFileDialog.getOpenFileName(self, tr("tb.open_cfg"), os.path.expanduser("~"), "Klipper config (*.cfg)")
        if not path:
            return
        try:
            with io.open(path, encoding="utf-8") as f:
                text = f.read()
            cs = None
            if os.path.basename(path) == "printer.cfg":
                from .files_page import local_configset
                cs = local_configset(os.path.dirname(path))
                self.set_configset(cs, ("local", os.path.dirname(path)))
            self._load_text(text, tr("msg.local_file", name=os.path.basename(path)),
                            cs.includes_text() if cs else "")
        except Exception as e:
            QMessageBox.critical(self, APP_NAME, str(e))

    def _load_text(self, text, src, includes_text=""):
        host, port = self.P["host"], self.P["port"]
        P, notes = import_config(text, includes_text=includes_text)
        P["host"], P["port"] = host, port
        self.P = P
        self.current_text = text.replace("\r\n", "\n")
        self.current_src = src
        self.refresh()
        self._log(tr("msg.loaded", src=src, lines=text.count("\n")))
        self._notes(notes)
        self.do_generate()

    # ---------- printer ----------
    def act_test(self):
        try:
            m = self.mr()
        except MoonrakerError as e:
            self.info_box.setPlainText("✖  %s" % e)
            return
        self.info_box.setPlainText(tr("msg.connecting", url=m.base))

        def work():
            return m.info(), m.server_info(), m.print_state(), m.mcu_chip(), m.list_config()

        def done(r, e):
            if e:
                self.info_box.setPlainText("✖  %s" % e)
                self._set_conn(False)
                return
            info, srv, st, chip, files = r
            matches = boards_for_mcu(chip) if chip else []
            boards = load_boards()
            lines = [
                "✔  " + tr("msg.connected"),
                "Klipper    : %s  |  %s" % (info.get("state"), info.get("software_version", "")),
                "Moonraker  : %s" % srv.get("moonraker_version", ""),
                "Host       : %s" % info.get("hostname", ""),
                "Print      : %s" % st,
                "MCU        : %s" % (chip or "?"),
                "Config     : %d files" % len(files),
            ]
            if matches:
                lines += ["", tr("msg.boards_for_mcu", count=len(matches))]
                lines += ["   • " + board_label(boards[b]) for b in matches[:12]]
            msg = (info.get("state_message") or "").strip()
            if msg:
                lines += ["", msg]
            self.info_box.setPlainText("\n".join(lines))
            self._set_conn(True, st)
        self.bg(work, done)

    def _set_conn(self, ok, state=""):
        if ok:
            col = "#d29922" if state in ("printing", "paused") else "#3fb950"
            txt = "●  " + tr("conn.connected", state=tr("state." + state) if state in ("printing", "paused") else state)
        else:
            col, txt = "#f85149", "●  " + tr("conn.offline")
        self.conn_lbl.setText(txt)
        self.conn_lbl.setStyleSheet("color:%s;padding:12px 18px;" % col)

    def act_import_printer(self):
        try:
            m = self.mr()
        except MoonrakerError as e:
            QMessageBox.critical(self, APP_NAME, str(e))
            return

        def work():
            cs = ConfigSet.load(m.download_config, m.list_config_sizes())
            cs.warnings = m.config_warnings()
            if "printer.cfg" not in cs.files:
                raise MoonrakerError(tr("msg.no_printer_cfg"))
            return cs

        def done(cs, e):
            if e:
                QMessageBox.critical(self, APP_NAME, tr("msg.download_failed", err=e))
                return
            try:
                self.set_configset(cs, ("printer", self.P["host"]))
                self._load_text(cs.files["printer.cfg"], tr("msg.printer_file", host=self.P["host"]), cs.includes_text())
                self._set_conn(True)
                QMessageBox.information(self, APP_NAME, tr("msg.imported_all", files=len(cs.files)))
            except ValueError as ex:
                QMessageBox.critical(self, APP_NAME, tr("msg.import_failed", err=ex))
        self.bg(work, done)

    def act_detect_serial(self):
        try:
            m = self.mr()
        except MoonrakerError as e:
            QMessageBox.critical(self, APP_NAME, str(e))
            return

        def done(r, e):
            if e:
                QMessageBox.critical(self, APP_NAME, str(e))
                return
            self.serial_cb.clear()
            ports = [p for p in r if "by-id" in p] or r
            if not ports:
                QMessageBox.information(self, APP_NAME, tr("msg.no_serial"))
                return
            self.serial_cb.addItems(ports)
            klipper = [p for p in ports if "Klipper" in p]
            if len(klipper) == 1:
                self.binds_by_key["mcu_serial"].setText(klipper[0])
            self._log(tr("msg.serial_found", count=len(ports)))
        self.bg(m.serial_devices, done)

    def act_apply_board(self):
        self.collect()
        b = self.board()
        if not b:
            QMessageBox.information(self, APP_NAME, tr("msg.choose_board"))
            return
        notes = apply_board(self.P, b, self.keep_inv.isChecked())
        self.refresh()
        self._log(tr("msg.board_applied", name=b["name"]))
        self._notes(notes)
        QMessageBox.information(self, APP_NAME, tr("msg.board_applied", name=b["name"]) +
                                ("\n\n" + "\n".join("• " + tr(k, **kw) for k, kw in notes) if notes else ""))

    def act_save_cfg(self):
        self.do_generate()
        path, _ = QFileDialog.getSaveFileName(self, tr("preview.save_local"),
                                              os.path.join(os.path.expanduser("~"), "printer.cfg"),
                                              "Klipper config (*.cfg)")
        if path:
            with io.open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(self.generated)
            self._log(tr("msg.saved", path=path))

    def act_upload(self):
        self.do_generate()
        errs = [r[1] for r in self.results if r[0] == "error"]
        if errs:
            QMessageBox.critical(self, APP_NAME, tr("msg.fix_errors") + "\n\n• " + "\n• ".join(errs))
            self.tabs.setCurrentIndex(0)
            return
        if not self.current_text:
            if QMessageBox.warning(self, APP_NAME, tr("msg.no_current_upload"),
                                   QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
                return
        warns = [r[1] for r in self.results if r[0] == "warn"]
        msg = tr("msg.upload_steps")
        if warns:
            msg += "\n\n" + tr("msg.warnings") + "\n• " + "\n• ".join(warns)
        if QMessageBox.question(self, tr("preview.upload"), msg) != QMessageBox.Yes:
            return
        try:
            m = self.mr()
        except MoonrakerError as e:
            QMessageBox.critical(self, APP_NAME, str(e))
            return
        new_text, base = self.generated, self.current_text

        def work():
            return safe_upload(m, new_text, base, log=self.bridge.log.emit, backup_writer=write_backup)

        def done(r, e):
            if e:
                self._log("✖ " + str(e))
                QMessageBox.critical(self, APP_NAME, str(e))
                return
            bname, fresh, info = r
            self.last_backup = (bname, fresh)
            self.btn_restore.setEnabled(True)
            state = info.get("state")
            self._log("Klipper: %s" % state)
            self.tabs.setCurrentIndex(3)
            if state == "ready":
                self.current_text = new_text
                self.current_src = tr("msg.printer_file", host=self.P["host"])
                self._set_conn(True, "ready")
                self.do_generate()
                QMessageBox.information(self, APP_NAME, tr("msg.upload_ok"))
            else:
                QMessageBox.warning(self, APP_NAME, tr("msg.upload_not_ready", state=state,
                                                       msg=(info.get("state_message") or "")[:600]))
        self.bg(work, done)

    def act_restore(self):
        if not self.last_backup:
            return
        bname, text = self.last_backup
        if QMessageBox.question(self, APP_NAME, tr("msg.confirm_restore", name=bname)) != QMessageBox.Yes:
            return
        try:
            m = self.mr()
        except MoonrakerError as e:
            QMessageBox.critical(self, APP_NAME, str(e))
            return

        def work():
            st = m.print_state()
            if st in ("printing", "paused"):
                raise MoonrakerError(tr("up.busy_" + st))
            m.upload_config("printer.cfg", text)
            m.firmware_restart()
            return m.wait_ready()

        def done(r, e):
            if e:
                QMessageBox.critical(self, APP_NAME, str(e))
                return
            self.current_text = text
            self._log(tr("msg.restored", name=bname, state=r.get("state")))
            self.do_generate()
            QMessageBox.information(self, APP_NAME, tr("msg.restored", name=bname, state=r.get("state")))
        self.bg(work, done)
