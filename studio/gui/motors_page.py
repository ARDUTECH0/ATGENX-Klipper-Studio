# -*- coding: utf-8 -*-
"""Motors & drivers page: every motor on its own driver socket with its own driver features."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QGroupBox, QHBoxLayout,
                               QHeaderView, QLabel, QLineEdit, QMenu, QPlainTextEdit, QPushButton, QSpinBox,
                               QTableWidget, QTableWidgetItem, QToolButton, QWidget)

from ..boards import assign_slot, slot_label, slots, suggest_slot
from ..i18n import tr
from ..model import (DRIVER_INFO, MOTOR_IDS, MOTOR_LABEL, OPTIONAL_MOTORS, PRIMARY, SPI_KEYS, TUNING_GOALS, UART_KEYS,
                     Z_LEVELING, Z_MOTORS, autotune_motors, bus_keys, enabled_motors)
from .widgets import SearchCombo

MICROSTEPS = [1, 2, 4, 8, 16, 32, 64, 128]
COLS = ("motor", "socket", "driver", "current", "microsteps", "rotation", "invert", "stealth", "sensorless")
COPY_KEYS = ("driver", "run_current", "hold_current", "sense_resistor", "microsteps", "rotation_distance",
             "full_steps", "stealthchop", "interpolate", "invert", "autotune", "tuning_goal")


def _block(w, fn):
    w.blockSignals(True)
    try:
        fn()
    finally:
        w.blockSignals(False)


class MotorsMixin:
    def page_motors(self):
        w, v = self._page(tr("motors.title"), tr("motors.hint"))
        self.sel_motor = "x"

        row = QHBoxLayout()
        self.btn_add_motor = QToolButton()
        self.btn_add_motor.setText("＋  " + tr("motors.add"))
        self.btn_add_motor.setPopupMode(QToolButton.InstantPopup)
        self.add_menu = QMenu(self.btn_add_motor)
        self.btn_add_motor.setMenu(self.add_menu)
        self.add_menu.aboutToShow.connect(self._fill_add_menu)
        row.addWidget(self.btn_add_motor)
        b = QPushButton(tr("motors.remove"))
        b.clicked.connect(self.act_remove_motor)
        row.addWidget(b)
        b = QPushButton(tr("motors.copy_axis"))
        b.clicked.connect(self.act_copy_axis)
        row.addWidget(b)
        row.addStretch(1)
        v.addLayout(row)

        self.motor_table = QTableWidget(0, len(COLS))
        self.motor_table.setHorizontalHeaderLabels([tr("motors.col." + c) for c in COLS])
        self.motor_table.verticalHeader().setVisible(False)
        self.motor_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.motor_table.setSelectionMode(QTableWidget.SingleSelection)
        hdr = self.motor_table.horizontalHeader()
        for i in range(len(COLS)):
            hdr.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        self.motor_table.setMinimumHeight(300)
        self.motor_table.currentCellChanged.connect(lambda r, *_: self._select_motor_row(r))
        v.addWidget(self.motor_table)

        # ---- selected motor details
        self.detail_box = QGroupBox()
        grid = QHBoxLayout(self.detail_box)
        left, right = QFormLayout(), QFormLayout()
        for f in (left, right):
            f.setHorizontalSpacing(14)
            f.setVerticalSpacing(7)
        grid.addLayout(left, 1)
        grid.addSpacing(18)
        grid.addLayout(right, 1)

        self.caps_lbl = QLabel(objectName="hint")
        self.caps_lbl.setWordWrap(True)
        left.addRow(self.caps_lbl)
        self.d_hold = self._dspin(0, 3, 3, 0.05, "A", "hold_current", tr("motors.hold_default"))
        left.addRow(tr("motors.hold"), self.d_hold)
        self.d_sense = self._dspin(0, 1, 3, 0.005, "Ω", "sense_resistor", tr("motors.sense_default"))
        left.addRow(tr("motors.sense"), self.d_sense)
        self.d_full = QComboBox()
        self.d_full.addItem(tr("motors.full_200"), 200)
        self.d_full.addItem(tr("motors.full_400"), 400)
        self.d_full.currentIndexChanged.connect(lambda i: self._set_motor("full_steps", self.d_full.itemData(i)))
        left.addRow(tr("motors.full_steps"), self.d_full)
        self.d_interp = QCheckBox(tr("motors.interpolate"))
        self.d_interp.toggled.connect(lambda val: self._set_motor("interpolate", val))
        left.addRow("", self.d_interp)
        self.d_sg = QSpinBox()
        self.d_sg.valueChanged.connect(lambda val: self._set_motor("sg", val))
        left.addRow(tr("motors.sg"), self.d_sg)
        self.d_diag = self._motor_line("diag_pin")
        left.addRow(tr("motors.diag"), self.d_diag)
        self.d_zpos = self._motor_line("z_position")
        self.d_zpos.setPlaceholderText(tr("motors.zpos_auto"))
        left.addRow(tr("motors.zpos"), self.d_zpos)

        self.bus_edits = {}
        for key in UART_KEYS + SPI_KEYS:
            e = QLineEdit()
            e.setLayoutDirection(Qt.LeftToRight)
            e.textEdited.connect(lambda text, k=key: self._set_bus(k, text))
            self.bus_edits[key] = e
            right.addRow(key, e)
        self.d_autotune = SearchCombo()
        self.d_autotune.addItem("")
        self.d_autotune.addItems(autotune_motors())
        self.d_autotune.currentTextChanged.connect(lambda t: self._set_motor("autotune", t.strip()))
        right.addRow(tr("motors.autotune"), self.d_autotune)
        self.d_goal = QComboBox()
        for g in TUNING_GOALS:
            self.d_goal.addItem(tr("motors.goal." + g), g)
        self.d_goal.currentIndexChanged.connect(lambda i: self._set_motor("tuning_goal", self.d_goal.itemData(i)))
        right.addRow(tr("motors.tuning_goal"), self.d_goal)
        self.bus_form = right
        v.addWidget(self.detail_box)

        # ---- global
        f2 = self._group(v, tr("motors.leveling"))
        f2.addRow(tr("motors.leveling_method"), self.combo("z_leveling", [(z, tr("level." + z)) for z in Z_LEVELING]))
        self.lev_points = self._multi_line("z_tilt_points", tr("motors.points_auto"))
        f2.addRow(tr("motors.points"), self.lev_points)
        self.lev_corners = self._multi_line("qgl_corners", tr("motors.points_auto"))
        f2.addRow(tr("motors.gantry_corners"), self.lev_corners)
        f2.addRow(tr("motors.voltage"), self.spin("motor_voltage", 5, 60, 1, 1, "V"))
        v.addStretch(1)
        return w

    # ---------- helpers ----------
    def _dspin(self, lo, hi, dec, step, suffix, key, special):
        s = QDoubleSpinBox()
        s.setRange(lo, hi)
        s.setDecimals(dec)
        s.setSingleStep(step)
        s.setSuffix("  " + suffix)
        s.setSpecialValueText(special)
        s.valueChanged.connect(lambda val: self._set_motor(key, float(val)))
        return s

    def _motor_line(self, key):
        e = QLineEdit()
        e.setLayoutDirection(Qt.LeftToRight)
        e.textEdited.connect(lambda text: self._set_motor(key, text.strip()))
        return e

    def _multi_line(self, key, placeholder):
        e = QPlainTextEdit()
        e.setMaximumHeight(72)
        e.setLayoutDirection(Qt.LeftToRight)
        e.setPlaceholderText(placeholder)
        self._bind(key, e, lambda val: e.setPlainText(str(val)), lambda: e.toPlainText().strip())
        return e

    def _set_motor(self, key, val):
        if getattr(self, "_loading_motor", False):
            return
        self.P["motors"][self.sel_motor][key] = val

    def _set_bus(self, key, text):
        bus = self.P["motors"][self.sel_motor]["bus"]
        if text.strip():
            bus[key] = text.strip()
        else:
            bus.pop(key, None)

    # ---------- table ----------
    def _fill_motors(self):
        if not hasattr(self, "motor_table"):
            return
        board = self.board()
        t = self.motor_table
        mids = enabled_motors(self.P)
        _block(t, lambda: t.setRowCount(0))
        for r, mid in enumerate(mids):
            m = self.P["motors"][mid]
            _block(t, lambda: t.insertRow(r))
            it = QTableWidgetItem("  %s  " % MOTOR_LABEL[mid])
            it.setData(Qt.UserRole, mid)
            it.setFlags(it.flags() & ~Qt.ItemIsEditable)
            t.setItem(r, 0, it)

            sock = QComboBox()
            if board:
                sock.addItem("-", "")
                for s in slots(board):
                    sock.addItem(slot_label(s), s)
                i = sock.findData(m["slot"])
                sock.setCurrentIndex(max(i, 0))
                sock.currentIndexChanged.connect(lambda i, mid=mid, c=sock: self._socket_changed(mid, c.itemData(i)))
            else:
                sock.addItem(tr("motors.custom_pins"))
                sock.setEnabled(False)
            t.setCellWidget(r, 1, sock)

            drv = QComboBox()
            for d, info in DRIVER_INFO.items():
                drv.addItem(tr("driver.none") if d == "none" else info["label"], d)
            drv.setCurrentIndex(max(drv.findData(m["driver"]), 0))
            drv.currentIndexChanged.connect(lambda i, mid=mid, c=drv: self._driver_changed(mid, c.itemData(i)))
            t.setCellWidget(r, 2, drv)

            cur = QDoubleSpinBox()
            cur.setRange(0.05, 5.0)
            cur.setDecimals(2)
            cur.setSingleStep(0.05)
            cur.setValue(m["run_current"])
            cur.valueChanged.connect(lambda val, mid=mid: self._row_set(mid, "run_current", float(val)))
            t.setCellWidget(r, 3, cur)

            ms = QComboBox()
            for x in MICROSTEPS:
                ms.addItem(str(x), x)
            ms.setCurrentIndex(max(ms.findData(int(m["microsteps"])), 0))
            ms.currentIndexChanged.connect(lambda i, mid=mid, c=ms: self._row_set(mid, "microsteps", c.itemData(i)))
            t.setCellWidget(r, 4, ms)

            rd = QDoubleSpinBox()
            rd.setRange(0.1, 500)
            rd.setDecimals(3)
            rd.setValue(m["rotation_distance"])
            rd.valueChanged.connect(lambda val, mid=mid: self._row_set(mid, "rotation_distance", float(val)))
            t.setCellWidget(r, 5, rd)

            inv = QCheckBox()
            inv.setChecked(m["invert"])
            inv.toggled.connect(lambda val, mid=mid: self._row_set(mid, "invert", val))
            t.setCellWidget(r, 6, self._centered(inv))

            st = QSpinBox()
            st.setRange(0, 999999)
            st.setSpecialValueText("spreadCycle")
            st.setValue(int(m["stealthchop"]))
            st.setToolTip(tr("motors.stealth_tip"))
            st.valueChanged.connect(lambda val, mid=mid: self._row_set(mid, "stealthchop", int(val)))
            t.setCellWidget(r, 7, st)

            sl = QCheckBox()
            sl.setChecked(m["sensorless"])
            sl.setEnabled(mid in ("x", "y") and bool(DRIVER_INFO.get(m["driver"], {}).get("sg_key")))
            sl.toggled.connect(lambda val, mid=mid: self._sensorless_changed(mid, val))
            t.setCellWidget(r, 8, self._centered(sl))
        row = mids.index(self.sel_motor) if self.sel_motor in mids else 0
        t.setCurrentCell(row, 0)
        self._select_motor_row(row)

    def _centered(self, widget):
        box = QWidget()
        lay = QHBoxLayout(box)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setAlignment(Qt.AlignCenter)
        lay.addWidget(widget)
        return box

    def _row_set(self, mid, key, val):
        self.P["motors"][mid][key] = val

    def _select_motor_row(self, row):
        item = self.motor_table.item(row, 0) if row >= 0 else None
        if item is None:
            return
        self.sel_motor = item.data(Qt.UserRole)
        self._show_motor()

    def _show_motor(self):
        mid = self.sel_motor
        m = self.P["motors"][mid]
        info = DRIVER_INFO.get(m["driver"], DRIVER_INFO["none"])
        self._loading_motor = True
        try:
            self.detail_box.setTitle(tr("motors.details", motor=MOTOR_LABEL[mid]))
            caps = [info["label"]]
            if info["bus"]:
                caps.append(info["bus"].upper())
            caps.append(tr("motors.caps_sg") if info["sg_key"] else tr("motors.caps_no_sg"))
            if info["max_current"]:
                caps.append(tr("motors.caps_current", a=info["max_current"]))
            self.caps_lbl.setText("  ·  ".join(caps))
            self.d_hold.setValue(m["hold_current"])
            self.d_sense.setValue(m["sense_resistor"])
            self.d_full.setCurrentIndex(1 if int(m["full_steps"]) == 400 else 0)
            self.d_interp.setChecked(m["interpolate"])
            has_sg = bool(info["sg_key"]) and mid in ("x", "y")
            self.d_sg.setEnabled(has_sg and m["sensorless"])
            if info["sg_range"]:
                self.d_sg.setRange(*info["sg_range"])
                self.d_sg.setValue(m["sg"] if m["sg"] is not None else info["sg_default"])
            self.d_sg.setToolTip(tr("motors.sg_tip_" + ("sgthrs" if info["sg_key"] == "driver_SGTHRS" else "sgt")))
            self.d_diag.setText(m["diag_pin"])
            self.d_diag.setEnabled(has_sg and m["sensorless"])
            self.d_zpos.setText(m["z_position"])
            self.d_zpos.setEnabled(mid in Z_MOTORS)
            keys = bus_keys(m["driver"], m["bus"])
            for k, e in self.bus_edits.items():
                e.setText(m["bus"].get(k, ""))
                e.setVisible(k in keys)
                self.bus_form.labelForField(e).setVisible(k in keys)
            self.d_autotune.setCurrentText(m["autotune"])
            self.d_autotune.setEnabled(m["driver"] != "none")
            self.d_goal.setCurrentIndex(max(self.d_goal.findData(m["tuning_goal"]), 0))
        finally:
            self._loading_motor = False

    # ---------- changes ----------
    def _socket_changed(self, mid, slot):
        board = self.board()
        if not board:
            return
        if slot:
            assign_slot(self.P, mid, board, slot, keep_inversion=True)
            others = [MOTOR_LABEL[o] for o in enabled_motors(self.P) if o != mid and self.P["motors"][o]["slot"] == slot]
            if others:
                self._log(tr("motors.socket_taken", slot=slot, motors=", ".join(others)))
        else:
            self.P["motors"][mid]["slot"] = ""
        self.sel_motor = mid
        self._show_motor()

    def _driver_changed(self, mid, driver):
        m = self.P["motors"][mid]
        m["driver"] = driver
        info = DRIVER_INFO[driver]
        if not info["sg_key"]:
            m["sensorless"] = False
        if info["sg_range"] and m["sg"] is not None and not info["sg_range"][0] <= m["sg"] <= info["sg_range"][1]:
            m["sg"] = None
        self.sel_motor = mid
        self._fill_motors()

    def _sensorless_changed(self, mid, on):
        m = self.P["motors"][mid]
        m["sensorless"] = on
        if on:
            info = DRIVER_INFO[m["driver"]]
            if m["sg"] is None:
                m["sg"] = info["sg_default"]
            if not m["diag_pin"] and m["endstop_pin"]:
                m["diag_pin"] = "^" + m["endstop_pin"].lstrip("^~!")
            if info["bus"] == "spi" and m["diag_pin"] and "!" not in m["diag_pin"]:
                m["diag_pin"] = "^!" + m["diag_pin"].lstrip("^~!")
            if m["hold_current"] > 0:
                m["hold_current"] = 0.0
                self._log(tr("motors.hold_cleared", motor=MOTOR_LABEL[mid]))
        self.sel_motor = mid
        self._show_motor()

    def _fill_add_menu(self):
        self.add_menu.clear()
        for mid in OPTIONAL_MOTORS:
            if not self.P["motors"][mid]["enabled"]:
                a = self.add_menu.addAction(tr("motors.add_" + mid))
                a.triggered.connect(lambda _=False, mid=mid: self.act_add_motor(mid))

    def act_add_motor(self, mid):
        m = self.P["motors"][mid]
        prim = self.P["motors"][PRIMARY[mid]]
        m["enabled"] = True
        for k in COPY_KEYS:
            m[k] = prim[k]
        board = self.board()
        if board:
            slot = suggest_slot(self.P, mid, board)
            if slot:
                assign_slot(self.P, mid, board, slot, keep_inversion=True)
            else:
                self._log(tr("note.no_free_slot", motor=MOTOR_LABEL[mid]))
        self.sel_motor = mid
        self._fill_motors()
        self._log(tr("motors.added", motor=MOTOR_LABEL[mid], slot=m["slot"] or "-"))

    def act_remove_motor(self):
        mid = self.sel_motor
        if mid not in OPTIONAL_MOTORS:
            self._log(tr("motors.cannot_remove", motor=MOTOR_LABEL[mid]))
            return
        m = self.P["motors"][mid]
        m["enabled"], m["slot"] = False, ""
        self.sel_motor = PRIMARY[mid]
        self._fill_motors()

    def act_copy_axis(self):
        src = self.P["motors"][PRIMARY.get(self.sel_motor, self.sel_motor)]
        base = PRIMARY.get(self.sel_motor, self.sel_motor)
        done = []
        for mid in MOTOR_IDS:
            if PRIMARY.get(mid) == base and self.P["motors"][mid]["enabled"]:
                for k in COPY_KEYS:
                    self.P["motors"][mid][k] = src[k]
                done.append(MOTOR_LABEL[mid])
        self._fill_motors()
        self._log(tr("motors.copied", source=MOTOR_LABEL[base], motors=", ".join(done) or "-"))
