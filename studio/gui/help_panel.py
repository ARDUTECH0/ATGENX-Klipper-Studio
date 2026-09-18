# -*- coding: utf-8 -*-
"""Help panel (explains the hovered / focused setting), page guides, and status badges in the sidebar."""
from PySide6.QtCore import QEvent, QObject, Qt, QUrl
from PySide6.QtGui import QColor, QDesktopServices
from PySide6.QtWidgets import QCheckBox, QFormLayout, QFrame, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from .. import REPO_URL
from ..help import HELP, help_cfg, help_text, page_guide
from ..i18n import get_lang, tr
from .icons import strip_emoji


class _HelpFilter(QObject):
    """Shows the help of a widget when the mouse enters it or it gets keyboard focus."""

    def __init__(self, window):
        super().__init__(window)
        self.window = window

    def eventFilter(self, obj, ev):
        if ev.type() in (QEvent.Enter, QEvent.FocusIn):
            key = obj.property("helpKey")
            if key:
                self.window.show_help(key, obj.property("helpTitle") or "")
        return False


def _first_sentence(text):
    for sep in (". ", "، ", ": "):
        if sep in text:
            return text.split(sep, 1)[0] + sep.strip()
    return text


class HelpMixin:
    def build_help_panel(self):
        self._help_filter = _HelpFilter(self)
        panel = QFrame(objectName="helpPanel")
        panel.setFixedWidth(310)
        outer = QVBoxLayout(panel)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        body = QWidget(objectName="helpBody")
        v = QVBoxLayout(body)
        v.setContentsMargins(18, 16, 18, 16)
        v.setSpacing(8)

        cap = QLabel(tr("help.page_caption"), objectName="helpCaption")
        v.addWidget(cap)
        self.help_page_title = QLabel(objectName="helpTitle")
        self.help_page_title.setWordWrap(True)
        v.addWidget(self.help_page_title)
        self.help_page_text = QLabel(objectName="helpText")
        self.help_page_text.setWordWrap(True)
        self.help_page_text.setTextFormat(Qt.PlainText)
        v.addWidget(self.help_page_text)

        line = QFrame(objectName="helpLine")
        line.setFixedHeight(1)
        v.addSpacing(6)
        v.addWidget(line)
        v.addSpacing(6)

        cap2 = QLabel(tr("help.setting_caption"), objectName="helpCaption")
        v.addWidget(cap2)
        self.help_title = QLabel(tr("help.hover_hint"), objectName="helpTitle")
        self.help_title.setWordWrap(True)
        v.addWidget(self.help_title)
        self.help_text = QLabel(objectName="helpText")
        self.help_text.setWordWrap(True)
        self.help_text.setTextFormat(Qt.PlainText)
        v.addWidget(self.help_text)
        self.help_cfg_caption = QLabel(tr("help.cfg_caption"), objectName="helpCaption")
        v.addWidget(self.help_cfg_caption)
        self.help_cfg = QLabel(objectName="helpCfg")
        self.help_cfg.setWordWrap(True)
        self.help_cfg.setLayoutDirection(Qt.LeftToRight)
        self.help_cfg.setTextInteractionFlags(Qt.TextSelectableByMouse)
        v.addWidget(self.help_cfg)
        self.help_cfg_caption.hide()
        self.help_cfg.hide()
        v.addStretch(1)

        guide = QPushButton("📖  " + tr("help.open_guide"))
        guide.clicked.connect(self.act_guide)
        v.addWidget(guide)
        scroll.setWidget(body)
        outer.addWidget(scroll)
        self.help_panel = panel
        return panel

    # ---------- registration ----------
    def register_help(self, widget, key, title=""):
        if widget is None or key not in HELP:
            return
        widgets = [widget] + widget.findChildren(QWidget)
        for w in widgets:
            w.setProperty("helpKey", key)
            w.setProperty("helpTitle", title)
            w.installEventFilter(self._help_filter)
        tip = _first_sentence(help_text(key))
        if help_cfg(key):
            tip += "\n" + help_cfg(key)
        widget.setToolTip(tip)

    def register_bound_help(self):
        """Every bound field gets the help of its key; the form label next to it too."""
        for key, w in self.binds_by_key.items():
            title = ""
            parent = w.parentWidget()
            lay = parent.layout() if parent else None
            label = lay.labelForField(w) if isinstance(lay, QFormLayout) else None
            if isinstance(label, QLabel) and label.text().strip():
                title = label.text().strip()
                self.register_help(label, key, title)
            elif isinstance(w, QCheckBox):
                title = w.text()
            self.register_help(w, key, title)

    # ---------- display ----------
    def show_help(self, key, title=""):
        text = help_text(key)
        if not text:
            return
        self.help_title.setText(title or key)
        self.help_text.setText(text)
        cfg = help_cfg(key)
        self.help_cfg.setText(cfg)
        self.help_cfg.setVisible(bool(cfg))
        self.help_cfg_caption.setVisible(bool(cfg))

    def show_page_help(self, idx):
        if not hasattr(self, "help_page_title"):
            return
        key, builder = self.PAGES[idx]
        self.help_page_title.setText(strip_emoji(tr(key)))
        self.help_page_text.setText(page_guide(builder))
        self.help_title.setText(tr("help.hover_hint"))
        self.help_text.setText("")
        self.help_cfg.hide()
        self.help_cfg_caption.hide()

    def act_toggle_help(self, on):
        self.help_panel.setVisible(on)

    def act_guide(self):
        name = "GUIDE.ar.md" if get_lang() == "ar" else "GUIDE.md"
        QDesktopServices.openUrl(QUrl("%s/blob/main/docs/%s" % (REPO_URL, name)))

    # ---------- sidebar status ----------
    def update_nav_status(self):
        counts = {}
        for level, _msg, page in self.results:
            if level in ("error", "warn"):
                c = counts.setdefault(page, [0, 0])
                c[0 if level == "error" else 1] += 1
        for i, (key, builder) in enumerate(self.PAGES):
            item = self.nav.item(i)
            errs, warns = counts.get(builder, [0, 0])
            badge = ("   ✕ %d" % errs) if errs else (("   △ %d" % warns) if warns else "")
            item.setText(strip_emoji(tr(key)) + badge)
            item.setForeground(QColor("#ffa198") if errs else QColor("#e6c07b") if warns else QColor("#8b949e"))
            item.setToolTip(tr("help.nav_badge", errors=errs, warnings=warns) if (errs or warns) else "")
