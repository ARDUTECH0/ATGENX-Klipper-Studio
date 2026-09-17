# -*- coding: utf-8 -*-
"""Config files page: every file of the printer, include tree, sections, editor, safe save."""
import io
import os
import shutil
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QTextCursor
from PySide6.QtWidgets import (QCheckBox, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
                               QMessageBox, QPlainTextEdit, QPushButton, QSplitter, QTreeWidget,
                               QTreeWidgetItem, QVBoxLayout, QWidget)

from .. import APP_NAME
from ..appdata import write_backup
from ..configset import ConfigSet, restart_kind
from ..i18n import tr
from ..moonraker import MoonrakerError, safe_save_file
from .widgets import CfgHighlighter


def local_configset(folder, root="printer.cfg"):
    listing = []
    for dirpath, dirs, files in os.walk(folder):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "studio_backups"]
        for f in files:
            full = os.path.join(dirpath, f)
            rel = os.path.relpath(full, folder).replace(os.sep, "/")
            listing.append((rel, os.path.getsize(full)))

    def fetch(path):
        with io.open(os.path.join(folder, path), encoding="utf-8") as fh:
            return fh.read()
    return ConfigSet.load(fetch, listing, root)


class FilesMixin:
    def page_files(self):
        w, v = self._page(tr("files.title"), tr("files.hint"))
        self.cs, self.cs_source, self.cs_original, self.cs_edits, self.cs_path = None, None, {}, {}, None

        top = QHBoxLayout()
        b = QPushButton(tr("files.load_printer"), objectName="primary")
        b.clicked.connect(self.act_files_load_printer)
        top.addWidget(b)
        self.files_summary = QLabel(objectName="hint")
        top.addWidget(self.files_summary, 1)
        v.addLayout(top)

        split = QSplitter(Qt.Horizontal)
        self.files_tree = QTreeWidget()
        self.files_tree.setHeaderHidden(True)
        self.files_tree.setMinimumWidth(270)
        self.files_tree.setLayoutDirection(Qt.LeftToRight)
        self.files_tree.itemClicked.connect(self._files_tree_clicked)
        split.addWidget(self.files_tree)

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(8, 0, 0, 0)
        row = QHBoxLayout()
        self.file_lbl = QLabel("-")
        self.file_lbl.setStyleSheet("font-weight:600;")
        row.addWidget(self.file_lbl, 1)
        self.find_edit = QLineEdit()
        self.find_edit.setPlaceholderText(tr("files.find"))
        self.find_edit.setMaximumWidth(220)
        self.find_edit.setLayoutDirection(Qt.LeftToRight)
        self.find_edit.returnPressed.connect(self._files_find)
        row.addWidget(self.find_edit)
        rl.addLayout(row)

        self.file_editor = QPlainTextEdit()
        self.file_editor.setLayoutDirection(Qt.LeftToRight)
        self.file_editor.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.file_editor.setMinimumHeight(430)
        self.hl_files = CfgHighlighter(self.file_editor.document())
        rl.addWidget(self.file_editor, 1)

        row2 = QHBoxLayout()
        self.file_restart = QCheckBox(tr("files.restart_after"))
        self.file_restart.setChecked(True)
        row2.addWidget(self.file_restart)
        row2.addStretch(1)
        br = QPushButton(tr("files.revert"))
        br.clicked.connect(self._files_revert)
        row2.addWidget(br)
        bs = QPushButton(tr("files.save"), objectName="primary")
        bs.clicked.connect(self.act_files_save)
        row2.addWidget(bs)
        rl.addLayout(row2)
        split.addWidget(right)
        split.setStretchFactor(1, 1)
        v.addWidget(split, 1)

        self.files_issues = QListWidget()
        self.files_issues.setMaximumHeight(130)
        v.addWidget(self.files_issues)
        return w

    # ---------- loading ----------
    def act_files_load_printer(self):
        try:
            m = self.mr()
        except MoonrakerError as e:
            QMessageBox.critical(self, APP_NAME, str(e))
            return

        def work():
            cs = ConfigSet.load(m.download_config, m.list_config_sizes())
            cs.warnings = m.config_warnings()
            return cs

        def done(cs, e):
            if e:
                QMessageBox.critical(self, APP_NAME, str(e))
                return
            self.set_configset(cs, ("printer", self.P["host"]))
        self.bg(work, done)

    def set_configset(self, cs, source):
        self.cs, self.cs_source = cs, source
        self.cs_original = dict(cs.files)
        self.cs_edits, self.cs_path = {}, None
        self._files_fill_tree()
        self._files_fill_issues()
        self.files_summary.setText(tr("files.summary", files=len(cs.files), included=len(cs.included),
                                      source=source[1]))
        if "printer.cfg" in cs.files:
            self._files_open("printer.cfg")

    def _files_fill_tree(self):
        t = self.files_tree
        t.clear()
        cs = self.cs
        done = set()

        def add_file(parent, path):
            label = path + ("  ●" if path in self.cs_edits else "")
            it = QTreeWidgetItem([label])
            it.setData(0, Qt.UserRole, ("file", path, 1))
            if path in cs.missing:
                it.setForeground(0, QColor("#f85149"))
            parent.addChild(it) if isinstance(parent, QTreeWidgetItem) else parent.addTopLevelItem(it)
            for name, line in cs.sections(path):
                s = QTreeWidgetItem(["[%s]" % name])
                s.setData(0, Qt.UserRole, ("file", path, line))
                s.setForeground(0, QColor("#8b949e"))
                it.addChild(s)
            if path not in done:
                done.add(path)
                for kid in cs.tree.get(path, []):
                    if kid in cs.files:
                        add_file(it, kid)
            return it

        if "printer.cfg" in cs.files:
            root = add_file(t, "printer.cfg")
            root.setExpanded(True)
        others = [p for p in cs.files if p not in cs.included]
        if others:
            grp = QTreeWidgetItem([tr("files.other_files")])
            grp.setForeground(0, QColor("#58a6ff"))
            t.addTopLevelItem(grp)
            for p in others:
                add_file(grp, p)
            grp.setExpanded(True)

    def _files_fill_issues(self):
        self.files_issues.clear()
        for p in self.cs.missing:
            it = QListWidgetItem("✖   " + tr("files.missing_include", path=p))
            it.setForeground(QColor("#f85149"))
            self.files_issues.addItem(it)
        for w in self.cs.warnings:
            msg = w.get("message", str(w)) if isinstance(w, dict) else str(w)
            it = QListWidgetItem("▲   Klipper: " + msg)
            it.setForeground(QColor("#d29922"))
            self.files_issues.addItem(it)
        if not self.files_issues.count():
            it = QListWidgetItem("✔   " + tr("files.no_issues"))
            it.setForeground(QColor("#3fb950"))
            self.files_issues.addItem(it)

    # ---------- editor ----------
    def _files_stash(self):
        if self.cs_path is None:
            return
        text = self.file_editor.toPlainText()
        if text != self.cs_original.get(self.cs_path):
            self.cs_edits[self.cs_path] = text
        else:
            self.cs_edits.pop(self.cs_path, None)

    def _files_open(self, path, line=1):
        if path != self.cs_path:
            self._files_stash()
            self.cs_path = path
            self.file_editor.setPlainText(self.cs_edits.get(path, self.cs.files.get(path, "")))
            kind = restart_kind(path)
            self.file_restart.setEnabled(bool(kind))
            self.file_restart.setText(tr("files.restart_after") + ("  (%s)" % kind if kind else ""))
            self.file_lbl.setText(path)
        block = self.file_editor.document().findBlockByLineNumber(max(0, line - 1))
        cur = QTextCursor(block)
        self.file_editor.setTextCursor(cur)
        self.file_editor.centerCursor()
        self.file_editor.setFocus()

    def _files_tree_clicked(self, item, _col=0):
        data = item.data(0, Qt.UserRole)
        if data and data[0] == "file":
            self._files_open(data[1], data[2])

    def _files_find(self):
        text = self.find_edit.text()
        if text and not self.file_editor.find(text):
            self.file_editor.moveCursor(QTextCursor.Start)
            self.file_editor.find(text)

    def _files_revert(self):
        if self.cs_path is None:
            return
        self.cs_edits.pop(self.cs_path, None)
        self.file_editor.setPlainText(self.cs_original.get(self.cs_path, ""))

    # ---------- saving ----------
    def act_files_save(self):
        if self.cs_path is None:
            return
        path, text = self.cs_path, self.file_editor.toPlainText()
        original = self.cs_original.get(path)
        if text == original:
            self._log(tr("files.no_changes"))
            return
        kind = restart_kind(path) if self.file_restart.isChecked() else ""
        if QMessageBox.question(self, APP_NAME, tr("files.confirm_save", path=path,
                                                   restart=kind or tr("files.no_restart"))) != QMessageBox.Yes:
            return

        if self.cs_source and self.cs_source[0] == "local":
            full = os.path.join(self.cs_source[1], path)
            shutil.copy2(full, full + ".%s.bak" % datetime.now().strftime("%Y%m%d_%H%M%S"))
            with io.open(full, "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
            self._files_saved(path, text)
            return
        try:
            m = self.mr()
        except MoonrakerError as e:
            QMessageBox.critical(self, APP_NAME, str(e))
            return

        def work():
            return safe_save_file(m, path, text, original, kind, log=self.bridge.log.emit, backup_writer=write_backup)

        def done(r, e):
            if e:
                QMessageBox.critical(self, APP_NAME, str(e))
                return
            _, info = r
            self._files_saved(path, text)
            if info and info.get("state") != "ready":
                QMessageBox.warning(self, APP_NAME, tr("msg.upload_not_ready", state=info.get("state"),
                                                       msg=(info.get("state_message") or "")[:600]))
        self.bg(work, done)

    def _files_saved(self, path, text):
        self.cs.files[path] = text
        self.cs_original[path] = text
        self.cs_edits.pop(path, None)
        if path == "printer.cfg":
            self.current_text = text
        self._files_fill_tree()
        self._log(tr("files.saved", path=path))
