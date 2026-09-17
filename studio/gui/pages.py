# -*- coding: utf-8 -*-
"""Wizard pages."""
import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QCheckBox, QComboBox, QGridLayout, QGroupBox, QHBoxLayout, QHeaderView, QLabel,
                               QLineEdit, QVBoxLayout, QWidget,
                               QListWidget, QPlainTextEdit, QPushButton, QRadioButton, QTabWidget,
                               QTableWidget)

from .. import ASSETS_DIR
from ..boards import board_label, load_boards
from ..i18n import tr
from ..model import KINEMATICS, LED_ORDERS, PROBES, SHAPERS, THERMISTORS
from .widgets import CfgHighlighter, SearchCombo


class PagesMixin:
    PAGES = [("nav.start", "page_start"), ("nav.connection", "page_connection"), ("nav.board", "page_board"), ("nav.features", "page_features"),
             ("nav.machine", "page_machine"), ("nav.motors", "page_motors"),
             ("nav.thermal", "page_thermal"), ("nav.probe", "page_probe"),
             ("nav.extras", "page_extras"), ("nav.pins", "page_pins"), ("nav.map", "page_map"),
             ("nav.preview", "page_preview"), ("nav.files", "page_files"), ("nav.doctor", "page_doctor")]

    def page_start(self):
        w = QWidget(objectName="page")
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 10, 8, 0)
        v.setSpacing(14)
        head = QHBoxLayout()
        logo = QLabel()
        logo.setPixmap(QIcon(os.path.join(ASSETS_DIR, "icon.svg")).pixmap(96, 96))
        head.addWidget(logo)
        titles = QVBoxLayout()
        t = QLabel(tr("start.title"), objectName="title")
        t.setStyleSheet("font-size:26px;")
        titles.addWidget(t)
        s = QLabel(tr("start.subtitle"), objectName="hint")
        s.setWordWrap(True)
        s.setStyleSheet("font-size:14px;")
        titles.addWidget(s)
        head.addLayout(titles, 1)
        v.addLayout(head)

        grid = QGridLayout()
        grid.setSpacing(12)
        cards = [("🔌", "start.printer", lambda: (self.goto_page("page_connection"), self.binds_by_key["host"].setFocus())),
                 ("🆕", "start.new", lambda: self.goto_page("page_board")),
                 ("📂", "start.open", self.act_open_cfg),
                 ("🩺", "start.doctor", lambda: self.goto_page("page_doctor"))]
        for i, (icon, key, fn) in enumerate(cards):
            b = QPushButton(objectName="card")
            b.setCursor(Qt.PointingHandCursor)
            b.setMinimumHeight(104)
            lay = QVBoxLayout(b)
            lay.setContentsMargins(18, 14, 18, 14)
            ttl = QLabel("%s   %s" % (icon, tr(key + "_title")))
            ttl.setStyleSheet("font-size:16px; font-weight:600; background:transparent;")
            dsc = QLabel(tr(key + "_desc"), objectName="hint")
            dsc.setWordWrap(True)
            dsc.setStyleSheet("background:transparent;")
            for lab in (ttl, dsc):
                lab.setAttribute(Qt.WA_TransparentForMouseEvents)
                lay.addWidget(lab)
            b.clicked.connect(lambda _=False, f=fn: f())
            grid.addWidget(b, i // 2, i % 2)
        v.addLayout(grid)

        steps = QGroupBox(tr("start.steps_title"))
        sl = QHBoxLayout(steps)
        for n in range(1, 5):
            lab = QLabel("<span style='font-size:22px;color:#3b8eea;font-weight:700'>%d</span><br>%s" % (n, tr("start.step%d" % n)))
            lab.setWordWrap(True)
            lab.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
            sl.addWidget(lab, 1)
        v.addWidget(steps)
        safe = QLabel("🛡️  " + tr("start.safe"), objectName="hint")
        safe.setWordWrap(True)
        v.addWidget(safe)
        v.addStretch(1)
        return w

    def page_connection(self):
        w, v = self._page(tr("connection.title"), tr("connection.hint"))
        f = self._group(v, "Moonraker")
        host = self.line("host")
        host.setPlaceholderText("192.168.1.50  /  mainsailos.local")
        f.addRow(tr("connection.host"), host)
        f.addRow(tr("connection.port"), self.spin("port", 1, 65535))
        self.api_key = QLineEdit()
        self.api_key.setEchoMode(QLineEdit.Password)
        self.api_key.setPlaceholderText(tr("connection.api_key_hint"))
        self.api_key.setLayoutDirection(Qt.LeftToRight)
        f.addRow(tr("connection.api_key"), self.api_key)
        row = QHBoxLayout()
        b1 = QPushButton(tr("connection.test"))
        b2 = QPushButton(tr("connection.import"), objectName="primary")
        b1.clicked.connect(self.act_test)
        b2.clicked.connect(self.act_import_printer)
        row.addWidget(b1)
        row.addWidget(b2)
        row.addStretch(1)
        v.addLayout(row)
        self.info_box = QPlainTextEdit(readOnly=True)
        self.info_box.setLayoutDirection(Qt.LeftToRight)
        self.info_box.setMinimumHeight(190)
        v.addWidget(self.info_box)
        f2 = self._group(v, tr("connection.project"))
        f2.addRow(tr("connection.printer_name"), self.line("printer_name"))
        v.addStretch(1)
        return w

    def page_board(self):
        w, v = self._page(tr("board.title"), tr("board.hint"))
        f = self._group(v, tr("board.group"))
        self.board_cb = SearchCombo()
        self.board_cb.setMinimumWidth(320)
        self.board_ids = [""]
        self.board_cb.addItem(tr("board.custom"))
        for bid, b in load_boards().items():
            self.board_ids.append(bid)
            self.board_cb.addItem(board_label(b))

        def set_board(val):
            i = self.board_ids.index(val) if val in self.board_ids else 0
            self.board_cb.setCurrentIndex(i)
            self._board_changed()

        def get_board():
            i = self.board_cb.currentIndex()
            return self.board_ids[i] if 0 <= i < len(self.board_ids) else ""
        self._bind("board", self.board_cb, set_board, get_board)
        self.board_cb.currentIndexChanged.connect(lambda _=None: self._board_changed())
        f.addRow(tr("board.board"), self.board_cb)
        self.keep_inv = QCheckBox(tr("board.keep_inversion"))
        self.keep_inv.setChecked(True)
        f.addRow("", self.keep_inv)
        self.register_help(self.keep_inv, "keep_inversion", tr("board.keep_inversion"))
        f.addRow("", self.check("board_extras", tr("board.extras")))
        row = QHBoxLayout()
        b = QPushButton(tr("board.apply"), objectName="primary")
        b.clicked.connect(self.act_apply_board)
        row.addWidget(b)
        row.addStretch(1)
        f.addRow("", row)

        self.board_info = QLabel(objectName="card")
        self.board_info.setWordWrap(True)
        self.board_info.setTextFormat(Qt.RichText)
        self.board_info.setOpenExternalLinks(True)
        self.board_info.setLayoutDirection(Qt.LeftToRight)
        v.addWidget(self.board_info)

        f2 = self._group(v, tr("board.serial_group"))
        f2.addRow(tr("board.serial"), self.line("mcu_serial"))
        row2 = QHBoxLayout()
        b2 = QPushButton(tr("board.detect_serial"))
        b2.clicked.connect(self.act_detect_serial)
        self.serial_cb = QComboBox()
        self.serial_cb.setMinimumWidth(300)
        self.serial_cb.setLayoutDirection(Qt.LeftToRight)
        self.serial_cb.activated.connect(lambda i: self.binds_by_key["mcu_serial"].setText(self.serial_cb.itemText(i)))
        row2.addWidget(b2)
        row2.addWidget(self.serial_cb, 1)
        f2.addRow("", row2)
        hint = QLabel(tr("board.serial_hint"), objectName="hint")
        hint.setWordWrap(True)
        f2.addRow("", hint)
        v.addStretch(1)
        return w

    def page_machine(self):
        w, v = self._page(tr("machine.title"), tr("machine.hint"))
        f = self._group(v, tr("machine.volume"))
        f.addRow(tr("machine.kinematics"), self.combo("kinematics", [(k, tr("kin." + k)) for k in KINEMATICS]))
        f.addRow(tr("machine.bed_x"), self.spin("bed_x", 50, 2000, 1, 1, "mm"))
        f.addRow(tr("machine.bed_y"), self.spin("bed_y", 50, 2000, 1, 1, "mm"))
        f.addRow(tr("machine.bed_z"), self.spin("bed_z", 50, 2000, 1, 1, "mm"))
        f.addRow(tr("machine.x_min"), self.spin("x_min", -50, 50, 1, 1, "mm"))
        f.addRow(tr("machine.y_min"), self.spin("y_min", -50, 50, 1, 1, "mm"))
        f.addRow(tr("machine.z_min"), self.spin("z_min", -10, 10, 1, 0.5, "mm"))
        f.addRow(tr("machine.x_endstop"), self.spin("x_endstop", -50, 2000, 1, 1, "mm"))
        f.addRow(tr("machine.y_endstop"), self.spin("y_endstop", -50, 2000, 1, 1, "mm"))
        f2 = self._group(v, tr("machine.limits"))
        f2.addRow(tr("machine.max_velocity"), self.spin("max_velocity", 10, 2000, 0, 5, "mm/s"))
        f2.addRow(tr("machine.max_accel"), self.spin("max_accel", 100, 50000, 0, 100, "mm/s²"))
        f2.addRow(tr("machine.max_z_velocity"), self.spin("max_z_velocity", 1, 200, 0, 1, "mm/s"))
        f2.addRow(tr("machine.max_z_accel"), self.spin("max_z_accel", 10, 50000, 0, 50, "mm/s²"))
        f2.addRow(tr("machine.scv"), self.spin("scv", 1, 30, 1, 0.5, "mm/s"))
        f2.addRow(tr("machine.homing_speed"), self.spin("homing_speed", 5, 300, 0, 5, "mm/s"))
        v.addStretch(1)
        return w

    def page_thermal(self):
        w, v = self._page(tr("thermal.title"), tr("thermal.hint"))
        f = self._group(v, tr("thermal.extruder"))
        f.addRow(tr("thermal.nozzle"), self.spin("nozzle", 0.1, 2.0, 2, 0.05, "mm"))
        f.addRow(tr("thermal.filament"), self.spin("filament", 1.0, 3.5, 2, 0.05, "mm"))
        f.addRow("", self.check("bowden", tr("thermal.bowden")))
        f.addRow(tr("thermal.pa"), self.spin("pa", 0, 2, 3, 0.01))
        f.addRow(tr("thermal.pa_smooth"), self.spin("pa_smooth", 0, 0.2, 3, 0.005, "s"))
        f2 = self._group(v, tr("thermal.heat"))
        f2.addRow(tr("thermal.therm_e"), self.combo("therm_e", THERMISTORS))
        f2.addRow("PID Kp", self.spin("pid_e_kp", 0, 1000, 3, 0.1))
        f2.addRow("PID Ki", self.spin("pid_e_ki", 0, 1000, 3, 0.01))
        f2.addRow("PID Kd", self.spin("pid_e_kd", 0, 5000, 3, 1))
        f2.addRow(tr("thermal.max_temp_e"), self.spin("max_temp_e", 150, 500, 0, 5, "°C"))
        f2.addRow(tr("thermal.therm_bed"), self.combo("therm_bed", THERMISTORS))
        f2.addRow("PID Kp ", self.spin("pid_b_kp", 0, 1000, 3, 0.1))
        f2.addRow("PID Ki ", self.spin("pid_b_ki", 0, 1000, 3, 0.01))
        f2.addRow("PID Kd ", self.spin("pid_b_kd", 0, 5000, 3, 1))
        f2.addRow(tr("thermal.max_temp_bed"), self.spin("max_temp_bed", 60, 200, 0, 5, "°C"))
        f2.addRow("", self.check("cool_room", tr("thermal.cool_room")))
        f3 = self._group(v, tr("thermal.fans"))
        f3.addRow(tr("thermal.fan_max"), self.spin("fan_max", 0.1, 1.0, 2, 0.05))
        f3.addRow(tr("thermal.hotend_fan_temp"), self.spin("hotend_fan_temp", 30, 100, 0, 5, "°C"))
        v.addStretch(1)
        return w

    def page_probe(self):
        w, v = self._page(tr("probe.title"), tr("probe.hint"))
        f = self._group(v, tr("probe.probe"))
        f.addRow(tr("probe.type"), self.combo("probe", [(p, tr("probe." + p)) for p in PROBES]))
        f.addRow(tr("probe.x"), self.spin("probe_x", -100, 100, 2, 0.5, "mm"))
        f.addRow(tr("probe.y"), self.spin("probe_y", -100, 100, 2, 0.5, "mm"))
        f.addRow(tr("probe.z"), self.spin("probe_z", -10, 10, 3, 0.01, "mm"))
        f.addRow(tr("probe.samples"), self.spin("probe_samples", 1, 10))
        f2 = self._group(v, tr("probe.mesh"))
        f2.addRow(tr("probe.margin"), self.spin("mesh_margin", 0, 100, 1, 5, "mm"))
        f2.addRow(tr("probe.count"), self.spin("mesh_count", 3, 15))
        self.mesh_lbl = QLabel()
        self.mesh_lbl.setStyleSheet("color:#3fb950;")
        self.mesh_lbl.setLayoutDirection(Qt.LeftToRight)
        f2.addRow(tr("probe.area"), self.mesh_lbl)
        v.addStretch(1)
        return w

    def page_extras(self):
        w, v = self._page(tr("extras.title"), tr("extras.hint"))
        f = self._group(v, tr("extras.leds"))
        f.addRow("", self.check("leds", tr("extras.leds_on")))
        f.addRow(tr("extras.led_count"), self.spin("led_count", 1, 1000))
        f.addRow(tr("extras.led_order"), self.combo("led_order", LED_ORDERS))
        f.addRow("", self.check("led_effects", tr("extras.led_effects")))
        f2 = self._group(v, tr("extras.shaper"))
        f2.addRow("", self.check("shaper", tr("extras.shaper_on")))
        f2.addRow(tr("extras.freq", axis="X"), self.spin("shaper_x", 0, 200, 1, 0.1, "Hz"))
        f2.addRow(tr("extras.type", axis="X"), self.combo("shaper_type_x", SHAPERS))
        f2.addRow(tr("extras.freq", axis="Y"), self.spin("shaper_y", 0, 200, 1, 0.1, "Hz"))
        f2.addRow(tr("extras.type", axis="Y"), self.combo("shaper_type_y", SHAPERS))
        f2.addRow(tr("extras.freq_z"), self.spin("shaper_z", 0, 200, 1, 0.1, "Hz"))
        f2.addRow(tr("extras.type", axis="Z"), self.combo("shaper_type_z", SHAPERS))
        f2.addRow(tr("extras.damping"), self.spin("damping", 0.01, 0.5, 3, 0.01))
        f3 = self._group(v, tr("extras.more"))
        f3.addRow("", self.check("fil_sensor", tr("extras.fil_sensor")))
        f3.addRow("", self.check("arcs", tr("extras.arcs")))
        f3.addRow("", self.check("exclude_object", tr("extras.exclude_object")))
        f3.addRow("", self.check("host_temp", tr("extras.host_temp")))
        f3.addRow("", self.check("mcu_temp", tr("extras.mcu_temp")))
        f3.addRow(tr("extras.idle_timeout"), self.spin("idle_timeout_min", 0, 1440, 0, 5, tr("extras.minutes")))
        f4 = self._group(v, tr("extras.retraction"))
        f4.addRow("", self.check("retraction", tr("extras.retraction_on")))
        f4.addRow(tr("extras.retract_length"), self.spin("retract_length", 0, 15, 2, 0.1, "mm"))
        f4.addRow(tr("extras.retract_speed"), self.spin("retract_speed", 1, 150, 0, 5, "mm/s"))
        f4.addRow(tr("extras.unretract_speed"), self.spin("unretract_speed", 1, 150, 0, 5, "mm/s"))
        f5 = self._group(v, tr("extras.macros"))
        f5.addRow("", self.check("print_macros", tr("extras.macros_on")))
        f5.addRow("", self.check("adaptive_mesh", tr("extras.adaptive_mesh")))
        f5.addRow("", self.check("purge_line", tr("extras.purge_line")))
        slicer = QLineEdit("START_PRINT BED=[first_layer_bed_temperature] EXTRUDER=[first_layer_temperature]")
        slicer.setReadOnly(True)
        slicer.setLayoutDirection(Qt.LeftToRight)
        f5.addRow(tr("extras.slicer_start"), slicer)
        f5.addRow(tr("extras.slicer_end"), QLabel("END_PRINT"))
        hint = QLabel(tr("extras.macros_hint"), objectName="hint")
        hint.setWordWrap(True)
        f5.addRow(hint)
        v.addStretch(1)
        return w

    def page_pins(self):
        w, v = self._page(tr("pins.title"), tr("pins.hint"))
        self.pin_table = QTableWidget(0, 2)
        self.pin_table.setHorizontalHeaderLabels([tr("pins.role"), tr("pins.pin")])
        self.pin_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.pin_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.pin_table.verticalHeader().setVisible(False)
        self.pin_table.setMinimumHeight(600)
        v.addWidget(self.pin_table, 1)
        return w

    def page_preview(self):
        w, v = self._page(tr("preview.title"), tr("preview.hint"))
        opts = QHBoxLayout()
        self.rb_merge = QRadioButton(tr("preview.merge"))
        self.rb_full = QRadioButton(tr("preview.full"))
        self.rb_merge.setChecked(True)
        self.cb_keep = QCheckBox(tr("preview.keep_custom"))
        self.cb_keep.setChecked(True)
        self.register_help(self.rb_merge, "preview.merge", tr("preview.merge"))
        self.register_help(self.rb_full, "preview.full", tr("preview.full"))
        self.register_help(self.cb_keep, "preview.full", tr("preview.keep_custom"))
        for x in (self.rb_merge, self.rb_full, self.cb_keep):
            opts.addWidget(x)
            x.toggled.connect(lambda _=None: self.do_generate())
        opts.addStretch(1)
        v.addLayout(opts)
        self.src_lbl = QLabel(objectName="hint")
        v.addWidget(self.src_lbl)

        self.tabs = QTabWidget()
        self.out_box = QPlainTextEdit(readOnly=True)
        self.diff_box = QPlainTextEdit(readOnly=True)
        self.val_list = QListWidget()
        self.val_list.setCursor(Qt.PointingHandCursor)
        self.val_list.itemClicked.connect(
            lambda it: it.data(Qt.UserRole) and it.data(Qt.UserRole) != "page_preview" and self.goto_page(it.data(Qt.UserRole)))
        self.log_box = QPlainTextEdit(readOnly=True)
        for x in (self.out_box, self.diff_box, self.log_box):
            x.setLayoutDirection(Qt.LeftToRight)
            x.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.hl_out = CfgHighlighter(self.out_box.document())
        self.hl_diff = CfgHighlighter(self.diff_box.document(), diff=True)
        self.tabs.addTab(self.val_list, tr("preview.checks"))
        self.tabs.addTab(self.diff_box, tr("preview.diff"))
        self.tabs.addTab(self.out_box, tr("preview.output"))
        self.tabs.addTab(self.log_box, tr("preview.log"))
        self.tabs.setMinimumHeight(470)
        v.addWidget(self.tabs, 1)

        row = QHBoxLayout()
        for text, fn, name in ((tr("preview.download"), self.act_import_printer, None),
                               (tr("preview.save_local"), self.act_save_cfg, None),
                               (tr("preview.upload"), self.act_upload, "primary")):
            b = QPushButton(text)
            if name:
                b.setObjectName(name)
            b.clicked.connect(fn)
            row.addWidget(b)
        self.btn_restore = QPushButton(tr("preview.restore"), objectName="danger")
        self.btn_restore.clicked.connect(self.act_restore)
        self.btn_restore.setEnabled(False)
        row.addWidget(self.btn_restore)
        row.addStretch(1)
        v.addLayout(row)
        self.last_backup = None
        return w
