# -*- coding: utf-8 -*-
"""Two pages for working with more than one printer.

Printers      the list of machines, and sending the same files to all of them at once
Printer files what is on a printer now: folders, thumbnails, and deleting safely

The work happens in studio/sync.py on background threads. They only put events on a queue;
a timer drains it and touches the widgets, so nothing but the main thread draws.
"""
import os
import queue

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QColor, QIcon, QPixmap
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout,
                               QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListWidget, QListWidgetItem,
                               QMessageBox, QPlainTextEdit, QProgressBar, QPushButton, QSpinBox,
                               QStyle, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from .. import printers as PR
from .. import sync as SY
from ..i18n import tr
from ..moonraker import MoonrakerError

LOG_COLOR = {"info": "#9aa7b4", "ok": "#2ea043", "warn": "#d29922", "error": "#f85149", "busy": "#d29922"}


class PrinterDialog(QDialog):
    """Add or edit one printer, including the ports and folder it overrides."""

    def __init__(self, parent, printer=None):
        QDialog.__init__(self, parent)
        self.setWindowTitle(tr("fleet.edit_title"))
        p = printer or PR.new_printer()
        f = QFormLayout(self)
        self.name = QLineEdit(p["name"])
        self.host = QLineEdit(p["host"])
        self.port = QSpinBox()
        self.port.setRange(1, 65535)
        self.port.setValue(int(p["port"] or PR.DEFAULT_PORT))
        self.ssh = QSpinBox()
        self.ssh.setRange(1, 65535)
        self.ssh.setValue(int(p["ssh_port"] or PR.DEFAULT_SSH_PORT))
        self.folder = QLineEdit(p["remote_path"])
        self.folder.setPlaceholderText(tr("fleet.folder_hint"))
        self.key = QLineEdit(p["api_key"])
        f.addRow(tr("fleet.name"), self.name)
        f.addRow(tr("fleet.host"), self.host)
        f.addRow(tr("fleet.port"), self.port)
        f.addRow(tr("fleet.ssh_port"), self.ssh)
        f.addRow(tr("fleet.folder"), self.folder)
        f.addRow(tr("connection.api_key"), self.key)
        box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        box.accepted.connect(self.accept)
        box.rejected.connect(self.reject)
        f.addRow(box)
        self.printer = dict(p)

    def value(self):
        p = dict(self.printer)
        p.update(name=self.name.text().strip(), host=self.host.text().strip(), port=self.port.value(),
                 ssh_port=self.ssh.value(), remote_path=self.folder.text().strip(), api_key=self.key.text().strip())
        return p


class FleetMixin:
    # ------------------------------------------------------------------ printers page
    def page_printers(self):
        w, v = self._page(tr("fleet.title"), tr("fleet.hint"))
        self.fleet = PR.load_printers()
        self.sync_files = []
        self.sync_queue = queue.Queue()
        self.sync_stop = False
        self.sync_bars = {}

        self.printer_table = QTableWidget(0, 5)
        self.printer_table.setHorizontalHeaderLabels([tr("fleet.col.use"), tr("fleet.col.name"),
                                                      tr("fleet.col.host"), tr("fleet.col.port"),
                                                      tr("fleet.col.folder")])
        self.printer_table.verticalHeader().setVisible(False)
        self.printer_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.printer_table.setSelectionMode(QTableWidget.SingleSelection)
        hdr = self.printer_table.horizontalHeader()
        for i in range(5):
            hdr.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        self.printer_table.setMinimumHeight(170)
        self.printer_table.itemDoubleClicked.connect(lambda *_: self.act_printer_edit())
        self.printer_table.itemChanged.connect(self._printer_checked)
        v.addWidget(self.printer_table)

        row = QHBoxLayout()
        for key, fn in (("fleet.add", self.act_printer_add), ("fleet.edit", self.act_printer_edit),
                        ("fleet.remove", self.act_printer_remove), ("fleet.up", lambda: self.act_printer_move(-1)),
                        ("fleet.down", lambda: self.act_printer_move(1))):
            b = QPushButton(tr(key))
            b.clicked.connect(fn)
            row.addWidget(b)
        row.addStretch(1)
        v.addLayout(row)

        # ---- what to send
        f = self._group(v, tr("fleet.files_group"))
        self.file_list = QListWidget()
        self.file_list.setMaximumHeight(110)
        f.addRow(self.file_list)
        row = QHBoxLayout()
        for key, fn in (("fleet.add_files", self.act_add_files), ("fleet.add_folder", self.act_add_folder),
                        ("fleet.clear_files", self.act_clear_files)):
            b = QPushButton(tr(key))
            b.clicked.connect(fn)
            row.addWidget(b)
        row.addStretch(1)
        self.sync_folder = QLineEdit()
        self.sync_folder.setPlaceholderText(tr("fleet.folder_hint"))
        self.sync_folder.setMaximumWidth(220)
        row.addWidget(QLabel(tr("fleet.into")))
        row.addWidget(self.sync_folder)
        f.addRow(row)
        row = QHBoxLayout()
        row.setSpacing(24)
        self.cb_dry = QCheckBox(tr("fleet.dry_run"))
        self.cb_same = QCheckBox(tr("fleet.skip_same"))
        self.cb_same.setChecked(True)
        row.addWidget(self.cb_dry)
        row.addWidget(self.cb_same)
        row.addStretch(1)
        f.addRow(row)
        self.register_help(self.cb_dry, "fleet.dry_run", tr("fleet.dry_run"))
        self.register_help(self.cb_same, "fleet.skip_same", tr("fleet.skip_same"))

        row = QHBoxLayout()
        self.btn_sync = QPushButton(tr("fleet.sync"))
        self.btn_sync.setObjectName("primary")
        self.btn_sync.clicked.connect(self.act_sync)
        self.btn_sync_stop = QPushButton(tr("fleet.stop"))
        self.btn_sync_stop.setEnabled(False)
        self.btn_sync_stop.clicked.connect(self.act_sync_stop)
        row.addWidget(self.btn_sync)
        row.addWidget(self.btn_sync_stop)
        row.addStretch(1)
        v.addLayout(row)

        self.bars_box = QWidget()
        self.bars_lay = QVBoxLayout(self.bars_box)
        self.bars_lay.setContentsMargins(0, 0, 0, 0)
        v.addWidget(self.bars_box)

        self.sync_log = QPlainTextEdit(readOnly=True)
        self.sync_log.setMinimumHeight(150)
        self.sync_log.setLayoutDirection(Qt.LeftToRight)
        v.addWidget(self.sync_log, 1)

        self.sync_timer = QTimer(self)
        self.sync_timer.timeout.connect(self._drain_sync)
        self._fill_printers()
        return w

    # ---- printer list
    def _fill_printers(self):
        t = self.printer_table
        t.blockSignals(True)          # filling rows must not look like the user ticking boxes
        t.setRowCount(len(self.fleet))
        for r, p in enumerate(self.fleet):
            use = QTableWidgetItem()
            use.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            use.setCheckState(Qt.Checked if p.get("enabled", True) else Qt.Unchecked)
            use.setData(Qt.UserRole, p["id"])
            t.setItem(r, 0, use)
            for c, text in ((1, p["name"]), (2, p["host"]), (3, str(p["port"])), (4, p["remote_path"] or "-")):
                it = QTableWidgetItem(text)
                it.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                t.setItem(r, c, it)
        t.blockSignals(False)
        if hasattr(self, "remote_printer"):
            self._fill_remote_printers()

    def _printer_checked(self, item):
        if item.column() != 0:
            return
        pid = item.data(Qt.UserRole)
        self.fleet = PR.update_printer(self.fleet, pid, enabled=item.checkState() == Qt.Checked)

    def _selected_printer(self):
        r = self.printer_table.currentRow()
        return self.fleet[r] if 0 <= r < len(self.fleet) else None

    def act_printer_add(self):
        d = PrinterDialog(self)
        if d.exec() == QDialog.Accepted and d.value()["host"]:
            self.fleet = PR.add_printer(self.fleet, d.value())
            self._fill_printers()

    def act_printer_edit(self):
        p = self._selected_printer()
        if not p:
            return
        d = PrinterDialog(self, p)
        if d.exec() == QDialog.Accepted:
            self.fleet = PR.update_printer(self.fleet, p["id"], **d.value())
            self._fill_printers()

    def act_printer_remove(self):
        p = self._selected_printer()
        if not p:
            return
        if QMessageBox.question(self, tr("fleet.remove"), tr("fleet.remove_q", name=p["name"])) == QMessageBox.Yes:
            self.fleet = PR.delete_printer(self.fleet, p["id"])
            self._fill_printers()

    def act_printer_move(self, delta):
        p = self._selected_printer()
        if not p:
            return
        row = self.printer_table.currentRow()
        self.fleet = PR.move_printer(self.fleet, p["id"], delta)
        self._fill_printers()
        self.printer_table.setCurrentCell(max(0, min(len(self.fleet) - 1, row + delta)), 1)

    # ---- files to send
    def _add_paths(self, paths):
        known = set(f[0] for f in self.sync_files)
        for path, rel, size in SY.local_files(paths):
            if path not in known:
                self.sync_files.append((path, rel, size))
        self.file_list.clear()
        for _, rel, size in self.sync_files:
            self.file_list.addItem("%s   (%s)" % (rel, SY.human_size(size)))
        self.file_list.addItem(tr("fleet.files_total", count=len(self.sync_files),
                                  size=SY.human_size(sum(f[2] for f in self.sync_files))))

    def act_add_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, tr("fleet.add_files"), os.path.expanduser("~"),
                                                "G-code (*.gcode *.gco *.g *.ufp *.3mf);;All files (*)")
        if paths:
            self._add_paths(paths)

    def act_add_folder(self):
        path = QFileDialog.getExistingDirectory(self, tr("fleet.add_folder"), os.path.expanduser("~"))
        if path:
            self._add_paths([path])

    def act_clear_files(self):
        self.sync_files = []
        self.file_list.clear()

    # ---- the sync itself
    def _slog(self, level, text):
        color = LOG_COLOR.get(level, "#9aa7b4")
        self.sync_log.appendHtml('<span style="color:%s">%s</span>' % (color, text))

    def act_sync(self):
        chosen = [p for p in self.fleet if p.get("enabled", True) and p.get("host")]
        if not chosen:
            QMessageBox.information(self, tr("fleet.title"), tr("fleet.no_printers"))
            return
        if not self.sync_files:
            QMessageBox.information(self, tr("fleet.title"), tr("fleet.no_files"))
            return
        for i in reversed(range(self.bars_lay.count())):
            self.bars_lay.itemAt(i).widget().setParent(None)
        self.sync_bars = {}
        for p in chosen:
            box = QWidget()
            lay = QHBoxLayout(box)
            lay.setContentsMargins(0, 0, 0, 0)
            name = QLabel(PR.label(p))
            name.setMinimumWidth(230)
            bar = QProgressBar()
            bar.setRange(0, 1000)
            info = QLabel("-")
            info.setMinimumWidth(240)
            lay.addWidget(name)
            lay.addWidget(bar, 1)
            lay.addWidget(info)
            self.bars_lay.addWidget(box)
            self.sync_bars[p["id"]] = (bar, info)

        self.sync_log.clear()
        opts = SY.Options(self.sync_folder.text().strip(), self.cb_dry.isChecked(), self.cb_same.isChecked())
        self._slog("info", tr("fleet.log_start", count=len(self.sync_files), printers=len(chosen)) +
                  (("  " + tr("fleet.log_dry")) if opts.dry_run else ""))
        self.sync_stop = False
        self.btn_sync.setEnabled(False)
        self.btn_sync_stop.setEnabled(True)
        files = list(self.sync_files)

        def emit(kind, pid, data):
            self.sync_queue.put((kind, pid, data))

        self.bg(lambda: SY.sync(chosen, files, opts, emit, lambda: self.sync_stop), self._sync_finished)
        self.sync_timer.start(120)

    def act_sync_stop(self):
        self.sync_stop = True
        self._slog("warn", tr("fleet.log_stopping"))

    def _sync_finished(self, result, error):
        self.sync_timer.stop()
        self._drain_sync()
        self.btn_sync.setEnabled(True)
        self.btn_sync_stop.setEnabled(False)
        if error:
            self._slog("error", str(error))
            return
        sent = sum(r["sent"] for r in (result or {}).values())
        busy = sum(r["busy"] for r in (result or {}).values())
        failed = sum(r["failed"] for r in (result or {}).values())
        self._slog("ok" if not failed else "error",
                  tr("fleet.log_done", sent=sent, busy=busy, failed=failed))

    def _drain_sync(self):
        while True:
            try:
                kind, pid, data = self.sync_queue.get_nowait()
            except queue.Empty:
                return
            bar, info = self.sync_bars.get(pid, (None, None))
            name = next((PR.label(p) for p in self.fleet if p["id"] == pid), pid)
            if kind == "start":
                self._slog("info", tr("fleet.log_connected", name=name))
            elif kind == "progress" and bar:
                bar.setValue(int(data["overall"] * 1000))
                info.setText("%s/s   %s   %s" % (SY.human_size(data["speed"]),
                                                 tr("fleet.eta", time=SY.human_time(data["eta"])),
                                                 data["name"][:28]))
            elif kind == "file":
                if bar:
                    bar.setValue(int(data["progress"] * 1000))
                self._slog("ok", "%s  %s  %s" % (name, tr("fleet.log_dry_sent") if data.get("dry")
                                                else tr("fleet.log_sent"), data["name"]))
            elif kind == "skip":
                self._slog("busy" if data["why"] == "busy" else "info",
                          "%s  %s  %s" % (name, tr("fleet.log_busy") if data["why"] == "busy"
                                          else tr("fleet.log_same"), data["name"]))
            elif kind == "fail":
                self._slog("error", "%s  %s  %s" % (name, data["name"], data["text"]))
            elif kind == "error":
                self._slog("error", "%s  %s" % (name, data["text"]))
            elif kind == "done" and bar:
                bar.setValue(1000 if not data["failed"] else bar.value())
                info.setText(tr("fleet.done_line", sent=data["sent"], skipped=data["skipped"],
                                busy=data["busy"], failed=data["failed"]))

    # ------------------------------------------------------------------ printer files page
    def page_remote(self):
        w, v = self._page(tr("remote.title"), tr("remote.hint"))
        self.remote_path = ""
        self.remote_busy = set()
        self.remote_thumbs = {}
        self.preview_popup = None
        self.preview_timer = QTimer(self)
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self._hide_preview)
        row = QHBoxLayout()
        self.remote_printer = QComboBox()
        self.remote_printer.setMinimumWidth(260)
        self.remote_printer.currentIndexChanged.connect(lambda *_: self.act_remote_refresh())
        row.addWidget(self.remote_printer)
        for key, fn in (("remote.refresh", self.act_remote_refresh), ("remote.up", self.act_remote_up),
                        ("remote.delete", self.act_remote_delete)):
            b = QPushButton(tr(key))
            b.clicked.connect(fn)
            row.addWidget(b)
        row.addStretch(1)
        self.remote_status = QLabel("", objectName="hint")
        row.addWidget(self.remote_status)
        v.addLayout(row)

        self.remote_crumbs = QLabel("gcodes", objectName="hint")
        v.addWidget(self.remote_crumbs)

        self.remote_list = QListWidget()
        self.remote_list.setViewMode(QListWidget.IconMode)
        self.remote_list.setIconSize(QSize(120, 120))
        self.remote_list.setGridSize(QSize(160, 170))
        self.remote_list.setResizeMode(QListWidget.Adjust)
        self.remote_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.remote_list.setWordWrap(True)
        self.remote_list.itemDoubleClicked.connect(self._remote_open)
        self.remote_list.setMouseTracking(True)
        self.remote_list.itemEntered.connect(self._remote_preview)
        v.addWidget(self.remote_list, 1)
        self._fill_remote_printers()
        return w

    def _fill_remote_printers(self):
        if not hasattr(self, "remote_printer"):
            return
        current = self.remote_printer.currentData()
        self.remote_printer.blockSignals(True)
        self.remote_printer.clear()
        for p in self.fleet:
            self.remote_printer.addItem(PR.label(p), p["id"])
        i = self.remote_printer.findData(current)
        if i >= 0:
            self.remote_printer.setCurrentIndex(i)
        self.remote_printer.blockSignals(False)

    def _remote_client(self):
        pid = self.remote_printer.currentData()
        p = next((x for x in self.fleet if x["id"] == pid), None)
        return (PR.client(p), p) if p else (None, None)

    def act_remote_refresh(self):
        m, p = self._remote_client()
        if not m:
            return
        self._hide_preview()
        self.remote_list.clear()
        self.remote_crumbs.setText("gcodes" + ("/" + self.remote_path if self.remote_path else ""))
        path = "gcodes" + ("/" + self.remote_path if self.remote_path else "")

        def work():
            data = m.list_dir(path)
            busy = m.busy_files()
            thumbs = {}
            for f in data.get("files", []):
                name = (self.remote_path + "/" + f["filename"]).lstrip("/")
                if f["filename"].lower().endswith((".gcode", ".gco", ".g")):
                    png = m.thumbnail(name)
                    if png:
                        thumbs[f["filename"]] = png
            return data, busy, thumbs

        def done(result, error):
            if error:
                self.remote_status.setText(str(error))
                return
            data, busy, thumbs = result
            self.remote_busy = busy
            self.remote_thumbs = {}
            folder_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)
            file_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)
            for d in data.get("dirs", []):
                it = QListWidgetItem(folder_icon, d["dirname"])
                it.setData(Qt.UserRole, ("dir", d["dirname"]))
                self.remote_list.addItem(it)
            for f in data.get("files", []):
                name = (self.remote_path + "/" + f["filename"]).lstrip("/")
                protected = name in busy
                label = f["filename"] + ("\n" + tr("remote.protected") if protected else "")
                icon = file_icon
                png = thumbs.get(f["filename"])
                if png:
                    pm = QPixmap()
                    if pm.loadFromData(png):
                        icon = QIcon(pm)
                        self.remote_thumbs[f["filename"]] = pm
                it = QListWidgetItem(icon, label)
                it.setData(Qt.UserRole, ("file", f["filename"]))
                it.setToolTip("%s  ·  %s" % (name, SY.human_size(f.get("size", 0))))
                if protected:
                    it.setForeground(QColor("#d29922"))
                self.remote_list.addItem(it)
            self.remote_status.setText(tr("remote.count", dirs=len(data.get("dirs", [])),
                                          files=len(data.get("files", [])), busy=len(busy)))
        self.remote_status.setText(tr("remote.loading"))
        self.bg(work, done)

    def _remote_open(self, item):
        kind, name = item.data(Qt.UserRole)
        if kind == "dir":
            self.remote_path = (self.remote_path + "/" + name).strip("/")
            self.act_remote_refresh()

    def act_remote_up(self):
        if self.remote_path:
            self.remote_path = self.remote_path.rpartition("/")[0]
            self.act_remote_refresh()

    def _remote_preview(self, item):
        """Hovering a file with a thumbnail shows it big, next to the cursor."""
        kind, name = item.data(Qt.UserRole)
        pm = self.remote_thumbs.get(name) if kind == "file" else None
        if pm is None or pm.isNull():
            return self._hide_preview()
        if self.preview_popup is None:
            self.preview_popup = QLabel(self, Qt.ToolTip)
            self.preview_popup.setStyleSheet("background:#161b22; border:1px solid #30363d; padding:4px;")
        big = pm.scaled(320, 320, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.preview_popup.setPixmap(big)
        self.preview_popup.resize(big.size())
        pos = self.remote_list.mapToGlobal(self.remote_list.visualItemRect(item).topRight())
        self.preview_popup.move(pos.x() + 12, pos.y())
        self.preview_popup.show()
        self.preview_timer.start(2500)

    def _hide_preview(self):
        if self.preview_popup is not None:
            self.preview_popup.hide()

    def act_remote_delete(self):
        m, p = self._remote_client()
        items = self.remote_list.selectedItems()
        if not m or not items:
            return
        targets = [it.data(Qt.UserRole) for it in items]
        protected = [n for kind, n in targets
                     if kind == "file" and (self.remote_path + "/" + n).lstrip("/") in self.remote_busy]
        if protected:
            QMessageBox.warning(self, tr("remote.delete"), tr("remote.protected_q", names=", ".join(protected)))
            targets = [(k, n) for k, n in targets if n not in protected]
        if not targets:
            return
        names = ", ".join(n for _, n in targets)
        if QMessageBox.question(self, tr("remote.delete"), tr("remote.delete_q", names=names)) != QMessageBox.Yes:
            return

        def work():
            removed = 0
            for kind, name in targets:
                full = (self.remote_path + "/" + name).lstrip("/")
                if kind == "dir":
                    inside = [f for f in m.list_gcodes() if f.startswith(full + "/")]
                    if [f for f in inside if f in self.remote_busy]:
                        continue
                    m.delete_dir(full)
                else:
                    m.delete_gcode(full)
                removed += 1
            return removed

        def done(result, error):
            if error:
                QMessageBox.warning(self, tr("remote.delete"), str(error))
            self.act_remote_refresh()
        self.bg(work, done)
