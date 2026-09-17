# -*- coding: utf-8 -*-
"""Troubleshooter page: reads Klipper's state and klippy.log, explains problems and how to fix them."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QMessageBox, QPlainTextEdit, QPushButton,
                               QVBoxLayout, QWidget)

from .. import APP_NAME
from ..doctor import card, diagnose, last_session
from ..i18n import tr
from ..moonraker import MoonrakerError


class DoctorMixin:
    def page_doctor(self):
        w, v = self._page(tr("doctor.title"), tr("doctor.hint"))
        row = QHBoxLayout()
        b = QPushButton(tr("doctor.check_printer"), objectName="primary")
        b.clicked.connect(self.act_doctor_printer)
        row.addWidget(b)
        self.doctor_state = QLabel(objectName="hint")
        self.doctor_state.setWordWrap(True)
        row.addWidget(self.doctor_state, 1)
        v.addLayout(row)

        self.doctor_input = QPlainTextEdit()
        self.doctor_input.setPlaceholderText(tr("doctor.paste"))
        self.doctor_input.setLayoutDirection(Qt.LeftToRight)
        self.doctor_input.setMaximumHeight(110)
        v.addWidget(self.doctor_input)
        row2 = QHBoxLayout()
        b2 = QPushButton(tr("doctor.diagnose"))
        b2.clicked.connect(lambda: self._doctor_show(self.doctor_input.toPlainText(), tr("doctor.source_pasted")))
        row2.addWidget(b2)
        row2.addStretch(1)
        v.addLayout(row2)

        self.doctor_results = QVBoxLayout()
        self.doctor_results.setSpacing(10)
        holder = QWidget(objectName="page")
        holder.setLayout(self.doctor_results)
        v.addWidget(holder)
        v.addStretch(1)
        return w

    def act_doctor_printer(self):
        try:
            m = self.mr()
        except MoonrakerError as e:
            QMessageBox.critical(self, APP_NAME, str(e))
            return

        def work():
            info = m.info()
            warnings = m.config_warnings()
            try:
                log = last_session(m.download_log("klippy.log"))
            except MoonrakerError:
                log = ""
            return info, warnings, log

        def done(r, e):
            if e:
                QMessageBox.critical(self, APP_NAME, str(e))
                return
            info, warnings, log = r
            state = info.get("state", "?")
            msg = (info.get("state_message") or "").strip()
            self.doctor_state.setText(tr("doctor.state", state=state, msg=msg.splitlines()[0] if msg else ""))
            text = "\n".join([msg, log] + [w.get("message", "") for w in warnings if isinstance(w, dict)])
            self._doctor_show(text, tr("doctor.source_printer"), warnings)
        self.bg(work, done)

    def _doctor_show(self, text, source, warnings=None):
        lay = self.doctor_results
        while lay.count():
            item = lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        hits = diagnose(text)
        head = QLabel(tr("doctor.found", count=len(hits), source=source) if hits else tr("doctor.nothing"))
        head.setStyleSheet("font-weight:600; color:%s;" % ("#d29922" if hits else "#3fb950"))
        lay.addWidget(head)
        for rid, line, page in hits:
            title, cause, fix = card(rid)
            box = QFrame()
            box.setStyleSheet("QFrame { background:#161b22; border:1px solid #2b3441; border-radius:10px; }"
                              "QLabel { border:none; background:transparent; }")
            bl = QVBoxLayout(box)
            t = QLabel("<b>%s</b>" % title)
            t.setStyleSheet("font-size:15px; color:#ffa198;")
            bl.addWidget(t)
            ln = QLabel(line)
            ln.setStyleSheet("font-family:Consolas,monospace; color:#8b949e;")
            ln.setWordWrap(True)
            ln.setLayoutDirection(Qt.LeftToRight)
            ln.setTextInteractionFlags(Qt.TextSelectableByMouse)
            bl.addWidget(ln)
            c = QLabel("<b>%s</b> %s" % (tr("doctor.cause"), cause))
            c.setWordWrap(True)
            bl.addWidget(c)
            f = QLabel("<b>%s</b><br>%s" % (tr("doctor.fix"), fix.replace("\n", "<br>")))
            f.setWordWrap(True)
            bl.addWidget(f)
            if page:
                b = QPushButton(tr("doctor.open_page"))
                b.clicked.connect(lambda _=False, p=page: self.goto_page(p))
                r = QHBoxLayout()
                r.addWidget(b)
                r.addStretch(1)
                bl.addLayout(r)
            lay.addWidget(box)
