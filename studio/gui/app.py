# -*- coding: utf-8 -*-
"""Main window."""
import os
import sys
import threading

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QAction, QDesktopServices, QIcon
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox,
                               QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow,
                               QMessageBox, QPushButton, QScrollArea, QSizePolicy, QSpinBox, QStackedWidget,
                               QTableWidgetItem, QToolBar, QVBoxLayout, QWidget)

from .. import APP_NAME, ASSETS_DIR, LICENSE_NAME, REPO_URL, SUPPORT_URL, __version__
from .. import i18n
from ..appdata import load_settings, save_settings
from ..i18n import tr
from ..model import MOTOR_LABEL, PIN_ROLES, bus_keys, enabled_motors, new_params
from .actions import ActionsMixin
from .doctor_page import DoctorMixin
from .features_page import FeaturesMixin
from .files_page import FilesMixin
from .map_page import MapMixin
from .help_panel import HelpMixin
from .motors_page import MotorsMixin
from .pages import PagesMixin
from .style import STYLE
from .widgets import Bridge


class Studio(PagesMixin, FeaturesMixin, MotorsMixin, MapMixin, FilesMixin, DoctorMixin, HelpMixin, ActionsMixin, QMainWindow):
    def __init__(self, P=None, current_text=None, current_src=None):
        super().__init__()
        self.P = P or new_params()
        self.binds, self.binds_by_key = [], {}
        self.current_text, self.current_src = current_text, current_src
        self.generated, self.results, self.busy = "", [], False
        self.bridge = Bridge()
        self.bridge.done.connect(lambda cb, r, e: cb(r, e))
        self.bridge.log.connect(self._log)

        self.setWindowTitle("%s  %s" % (APP_NAME, __version__))
        self.resize(1440, 900)
        root = QWidget(objectName="root")
        self.setCentralWidget(root)
        lay = QHBoxLayout(root)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        side = QWidget(objectName="side")
        side.setFixedWidth(240)
        sl = QVBoxLayout(side)
        sl.setContentsMargins(0, 0, 0, 0)
        brand = QHBoxLayout()
        brand.setContentsMargins(16, 14, 12, 2)
        logo = QLabel()
        logo.setPixmap(QIcon(os.path.join(ASSETS_DIR, "icon.svg")).pixmap(40, 40))
        brand.addWidget(logo)
        name = QLabel("Klipper Studio", objectName="brand")
        brand.addWidget(name, 1)
        sl.addLayout(brand)
        sl.addWidget(QLabel(tr("app.tagline"), objectName="sub"))
        self.nav = QListWidget(objectName="nav")
        self.nav.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        sl.addWidget(self.nav, 1)
        self.conn_lbl = QLabel("●  " + tr("conn.offline"))
        self.conn_lbl.setStyleSheet("color:#6e7681;padding:12px 18px;")
        sl.addWidget(self.conn_lbl)
        lay.addWidget(side)

        main = QWidget()
        ml = QVBoxLayout(main)
        ml.setContentsMargins(22, 14, 22, 12)
        self.stack = QStackedWidget()
        ml.addWidget(self.stack, 1)
        navrow = QHBoxLayout()
        self.btn_prev = QPushButton(tr("nav.prev"))
        self.btn_next = QPushButton(tr("nav.next"), objectName="primary")
        navrow.addWidget(self.btn_prev)
        navrow.addStretch(1)
        navrow.addWidget(self.btn_next)
        ml.addLayout(navrow)
        lay.addWidget(main, 1)
        lay.addWidget(self.build_help_panel())

        for key, builder in self.PAGES:
            self.nav.addItem(QListWidgetItem(tr(key)))
            sc = QScrollArea()
            sc.setWidgetResizable(True)
            sc.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            sc.setWidget(getattr(self, builder)())
            self.stack.addWidget(sc)
        self.nav.currentRowChanged.connect(self._go)
        self.btn_prev.clicked.connect(lambda: self.nav.setCurrentRow(max(0, self.nav.currentRow() - 1)))
        self.btn_next.clicked.connect(lambda: self.nav.setCurrentRow(min(self.nav.count() - 1, self.nav.currentRow() + 1)))
        self._toolbar()
        self.register_bound_help()
        self.statusBar().showMessage(tr("app.ready"))
        self.refresh()
        self.nav.setCurrentRow(0)
        self.show_page_help(0)

    # ---------- chrome ----------
    def _toolbar(self):
        tb = QToolBar()
        tb.setMovable(False)
        self.addToolBar(tb)
        for key, fn in (("tb.new", self.act_new), ("tb.open_project", self.act_open_project),
                        ("tb.save_project", self.act_save_project), ("tb.open_cfg", self.act_open_cfg)):
            a = QAction(tr(key), self)
            a.triggered.connect(fn)
            tb.addAction(a)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        tb.addWidget(spacer)
        a = QAction(tr("tb.help_panel"), self)
        a.setCheckable(True)
        a.setChecked(True)
        a.toggled.connect(self.act_toggle_help)
        tb.addAction(a)
        a = QAction(tr("tb.guide"), self)
        a.triggered.connect(self.act_guide)
        tb.addAction(a)
        a = QAction(tr("tb.language"), self)
        a.triggered.connect(self.act_language)
        tb.addAction(a)
        a = QAction("☕  " + tr("tb.support"), self)
        a.triggered.connect(lambda: QDesktopServices.openUrl(QUrl(SUPPORT_URL)))
        tb.addAction(a)
        a = QAction(tr("tb.about"), self)
        a.triggered.connect(self.act_about)
        tb.addAction(a)

    def _page(self, title, hint):
        w = QWidget(objectName="page")
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 8, 0)
        v.addWidget(QLabel(title, objectName="title"))
        h = QLabel(hint, objectName="hint")
        h.setWordWrap(True)
        v.addWidget(h)
        return w, v

    def _group(self, v, title):
        g = QGroupBox(title)
        f = QFormLayout(g)
        f.setRowWrapPolicy(QFormLayout.WrapLongRows)
        f.setHorizontalSpacing(18)
        f.setVerticalSpacing(8)
        v.addWidget(g)
        return f

    # ---------- bindings ----------
    def _bind(self, key, w, setter, getter):
        self.binds.append((key, setter, getter))
        self.binds_by_key[key] = w
        return w

    def spin(self, key, lo, hi, dec=0, step=1.0, suffix=""):
        w = QDoubleSpinBox() if dec else QSpinBox()
        if dec:
            w.setDecimals(dec)
        w.setRange(lo, hi)
        w.setSingleStep(step)
        if suffix:
            w.setSuffix("  " + suffix)
        w.setMinimumWidth(170)
        conv = (lambda: float(w.value())) if dec else (lambda: int(w.value()))
        return self._bind(key, w, lambda val: w.setValue(val), conv)

    def check(self, key, text):
        w = QCheckBox(text)
        return self._bind(key, w, lambda val: w.setChecked(bool(val)), w.isChecked)

    def combo(self, key, items):
        w = QComboBox()
        data = []
        for it in items:
            if isinstance(it, tuple):
                w.addItem(str(it[1]))
                data.append(it[0])
            else:
                w.addItem(str(it))
                data.append(it)
        w.setMinimumWidth(240)

        def setter(val):
            if val not in data:
                w.addItem(str(val))
                data.append(val)
            w.setCurrentIndex(data.index(val))
        return self._bind(key, w, setter, lambda: data[w.currentIndex()])

    def line(self, key):
        w = QLineEdit()
        w.setMinimumWidth(300)
        w.setLayoutDirection(Qt.LeftToRight)
        return self._bind(key, w, lambda val: w.setText(str(val)), lambda: w.text().strip())

    def collect(self):
        for key, _, getter in self.binds:
            self.P[key] = getter()
        self._collect_pins()

    def refresh(self):
        for key, setter, _ in self.binds:
            if key in self.P:
                setter(self.P[key])
        self._fill_pins()
        self._fill_motors()
        self._fill_features()
        self._fill_map()

    def page_index(self, builder):
        return [b for _, b in self.PAGES].index(builder)

    def goto_page(self, builder):
        self.nav.setCurrentRow(self.page_index(builder))

    # ---------- pin table ----------
    def _pin_rows(self):
        rows = []
        for mid in enabled_motors(self.P):
            m = self.P["motors"][mid]
            lab = MOTOR_LABEL[mid]
            keys = ["step_pin", "dir_pin", "enable_pin"]
            if mid in ("x", "y", "z"):
                keys.append("endstop_pin")
            if m["sensorless"] or m["keep_diag"]:
                keys.append("diag_pin")
            rows += [(("motor", mid, k), "%s  ·  %s" % (lab, k)) for k in keys]
            rows += [(("bus", mid, k), "%s  ·  %s" % (lab, k)) for k in bus_keys(m["driver"], m["bus"])]
        rows += [(("pin", role), tr(label)) for role, label in PIN_ROLES.items()]
        return rows

    def _pin_value(self, data):
        if data[0] == "pin":
            return self.P["pins"].get(data[1], "")
        if data[0] == "motor":
            return self.P["motors"][data[1]][data[2]]
        return self.P["motors"][data[1]]["bus"].get(data[2], "")

    def _fill_pins(self):
        if not hasattr(self, "pin_table"):
            return
        self.pin_table.setRowCount(0)
        for data, label in self._pin_rows():
            r = self.pin_table.rowCount()
            self.pin_table.insertRow(r)
            it = QTableWidgetItem(label)
            it.setData(Qt.UserRole, data)
            it.setFlags(it.flags() & ~Qt.ItemIsEditable)
            self.pin_table.setItem(r, 0, it)
            pv = QTableWidgetItem(self._pin_value(data))
            pv.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.pin_table.setItem(r, 1, pv)

    def _collect_pins(self):
        # only while the pins page is open - other pages edit pins directly
        if not hasattr(self, "pin_table") or self.stack.currentIndex() != self.page_index("page_pins"):
            return
        for r in range(self.pin_table.rowCount()):
            data = self.pin_table.item(r, 0).data(Qt.UserRole)
            val = self.pin_table.item(r, 1).text().strip()
            if data[0] == "pin":
                self.P["pins"][data[1]] = val
            elif data[0] == "motor":
                if data[2] == "dir_pin":
                    val = val.lstrip("!")
                self.P["motors"][data[1]][data[2]] = val
            elif val:
                self.P["motors"][data[1]]["bus"][data[2]] = val
            else:
                self.P["motors"][data[1]]["bus"].pop(data[2], None)

    def _go(self, idx):
        self.collect()
        self.stack.setCurrentIndex(idx)
        self.btn_prev.setEnabled(idx > 0)
        self.btn_next.setEnabled(idx < self.nav.count() - 1)
        key = self.PAGES[idx][1]
        if key == "page_pins":
            self._fill_pins()
        if key == "page_motors":
            self._fill_motors()
        if key == "page_features":
            self._fill_features()
        if key == "page_map":
            self._fill_map()
        self.do_generate()  # keeps checks and the sidebar badges up to date
        self.show_page_help(idx)

    def bg(self, fn, done):
        if self.busy:
            QMessageBox.information(self, APP_NAME, tr("msg.busy"))
            return
        self.busy = True
        QApplication.setOverrideCursor(Qt.WaitCursor)

        def wrap(r, e):
            self.busy = False
            QApplication.restoreOverrideCursor()
            done(r, e)

        def work():
            try:
                r, e = fn(), None
            except Exception as ex:  # reported to the user in `done`
                r, e = None, ex
            self.bridge.done.emit(wrap, r, e)
        threading.Thread(target=work, daemon=True).start()

    # ---------- language / about ----------
    def act_language(self):
        self.collect()
        new = "en" if i18n.get_lang() == "ar" else "ar"
        s = load_settings()
        s["lang"] = new
        save_settings(s)
        i18n.set_lang(new)
        app = QApplication.instance()
        app.setLayoutDirection(Qt.RightToLeft if i18n.is_rtl() else Qt.LeftToRight)
        win = Studio(self.P, self.current_text, self.current_src)
        win.api_key.setText(self.api_key.text())
        win.show()
        app._studio_window = win
        self.close()

    def act_about(self):
        box = QMessageBox(self)
        box.setWindowTitle(tr("tb.about"))
        box.setTextFormat(Qt.RichText)
        box.setText(tr("about.text", app=APP_NAME, ver=__version__, license=LICENSE_NAME,
                       repo=REPO_URL, support=SUPPORT_URL))
        box.exec()

    def closeEvent(self, ev):
        s = load_settings()
        s["host"], s["port"] = self.P.get("host", ""), self.P.get("port", 7125)
        save_settings(s)
        super().closeEvent(ev)


def run(smoke=False):
    settings = load_settings()
    i18n.set_lang(settings.get("lang") or i18n.system_lang())
    if os.name == "nt":  # own taskbar icon instead of Python's
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ATGENX.KlipperStudio")
        except (AttributeError, OSError):
            pass
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setWindowIcon(QIcon(os.path.join(ASSETS_DIR, "icon.svg")))
    app.setLayoutDirection(Qt.RightToLeft if i18n.is_rtl() else Qt.LeftToRight)
    app.setStyleSheet(STYLE)
    P = new_params()
    P["host"] = settings.get("host", "")
    P["port"] = int(settings.get("port", 7125) or 7125)
    win = Studio(P)
    if smoke:
        for i in range(win.nav.count()):
            win.nav.setCurrentRow(i)
        win.do_generate()
        print("SMOKE OK  lang=%s pages=%d binds=%d gen=%d chars checks=%d" % (
            i18n.get_lang(), win.nav.count(), len(win.binds), len(win.generated), len(win.results)))
        return 0
    app._studio_window = win
    win.show()
    return app.exec()
