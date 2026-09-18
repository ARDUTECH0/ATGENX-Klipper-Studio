# -*- coding: utf-8 -*-
"""Features page: built-in feature switches, on/off for any section of the file, and the add-a-feature catalog."""
from PySide6.QtCore import QPropertyAnimation, QRectF, QSize, Qt, Property
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (QAbstractButton, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit,
                               QPushButton, QScrollArea, QTabWidget, QVBoxLayout, QWidget)

from ..features import (BUILTIN, CATALOG, CATEGORY_ICONS, feature_on, fill_template, list_sections, section_names,
                        set_feature)
from ..help import help_text
from ..i18n import tr
from .icons import icon as draw
from .style import accent
from .widgets import CfgHighlighter


class ToggleSwitch(QAbstractButton):
    """An on/off switch like on phones and modern apps."""

    def __init__(self, checked=False, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setChecked(checked)
        self.setCursor(Qt.PointingHandCursor)
        self._pos = 1.0 if checked else 0.0
        self._anim = QPropertyAnimation(self, b"knob", self)
        self._anim.setDuration(120)
        self.toggled.connect(self._animate)

    def sizeHint(self):
        return QSize(46, 26)

    def _animate(self, on):
        self._anim.stop()
        self._anim.setStartValue(self._pos)
        self._anim.setEndValue(1.0 if on else 0.0)
        self._anim.start()

    def _get_knob(self):
        return self._pos

    def _set_knob(self, v):
        self._pos = v
        self.update()

    knob = Property(float, _get_knob, _set_knob)

    def set_quiet(self, on):
        self.blockSignals(True)
        self.setChecked(on)
        self._pos = 1.0 if on else 0.0
        self.blockSignals(False)
        self.update()

    def paintEvent(self, _ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        track = QColor("#2ea043") if self.isChecked() else QColor("#30363d")
        if not self.isEnabled():
            track = QColor("#21262d")
        p.setPen(Qt.NoPen)
        p.setBrush(track)
        p.drawRoundedRect(QRectF(1, 1, w - 2, h - 2), (h - 2) / 2, (h - 2) / 2)
        d = h - 8
        x = 4 + self._pos * (w - 8 - d)
        p.setBrush(QColor("#ffffff") if self.isEnabled() else QColor("#6e7681"))
        p.drawEllipse(QRectF(x, 4, d, d))
        p.end()


def _clear(layout):
    while layout.count():
        item = layout.takeAt(0)
        w = item.widget()
        if w is not None:
            w.setParent(None)   # leave the page at once, not only when Qt deletes it
            w.deleteLater()
        elif item.layout():
            _clear(item.layout())
            item.layout().deleteLater()


def _with_icon(label, name):
    """A heading with its drawn icon in front of it."""
    from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget
    box = QWidget()
    lay = QHBoxLayout(box)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(8)
    ic = QLabel()
    ic.setPixmap(draw(name, accent(), 20).pixmap(20, 20))
    lay.addWidget(ic)
    lay.addWidget(label, 1)
    return box


class FeaturesMixin:
    def page_features(self):
        w, v = self._page(tr("features.title"), tr("features.hint"))
        self.feature_search = QLineEdit()
        self.feature_search.setPlaceholderText(tr("features.search"))
        self.feature_search.textChanged.connect(lambda _t: self._fill_features())
        v.addWidget(self.feature_search)

        self._feature_cards, self._feature_heads = {}, {}
        self.feature_tabs = QTabWidget()
        self.feature_tabs.setMinimumHeight(640)
        self.tab_builtin, self.tab_builtin_lay = self._scroll_tab()
        self.tab_file, self.tab_file_lay = self._scroll_tab()
        self.tab_add, self.tab_add_lay = self._scroll_tab()
        self.feature_tabs.addTab(self.tab_builtin, tr("features.tab_builtin"))
        self.feature_tabs.addTab(self.tab_file, tr("features.tab_file", count=0))
        self.feature_tabs.addTab(self.tab_add, tr("features.tab_add"))
        v.addWidget(self.feature_tabs, 1)
        return w

    def _scroll_tab(self):
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        body = QWidget(objectName="page")
        lay = QVBoxLayout(body)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(10)
        sc.setWidget(body)
        return sc, lay

    def _match(self, *texts):
        q = self.feature_search.text().strip().lower() if hasattr(self, "feature_search") else ""
        return not q or any(q in (t or "").lower() for t in texts)

    def _fill_features(self):
        if not hasattr(self, "feature_tabs"):
            return
        self._fill_builtin()
        self._fill_file_sections()
        self._fill_catalog()

    # ---------- built-in ----------
    def _fill_builtin(self):
        """Cards are built once; refreshing only updates the switches and the search filter."""
        if not self._feature_cards:
            self._build_builtin()
        for fid, (card, sw, head) in self._feature_cards.items():
            on = feature_on(self.P, fid)
            sw.set_quiet(on)
            card.setProperty("on", on)
            card.style().unpolish(card)
            card.style().polish(card)
            card.setVisible(self._match(tr("feat.%s.title" % fid), tr("feat.%s.desc" % fid), fid))
        for cat, head in self._feature_heads.items():
            head.setVisible(any(c.isVisible() for f, (c, _s, hc) in self._feature_cards.items() if hc == cat))

    def _build_builtin(self):
        lay = self.tab_builtin_lay
        for cat, icon in CATEGORY_ICONS.items():
            ids = [f for f, spec in BUILTIN.items() if spec[1] == cat]
            if not ids:
                continue
            head = QLabel(tr("fcat." + cat), objectName="sectionHead")
            head.setPixmap  # the category icon is drawn next to it below
            head = _with_icon(head, icon)
            lay.addWidget(head)
            self._feature_heads[cat] = head
            grid = QGridLayout()
            grid.setSpacing(10)
            for i, fid in enumerate(ids):
                card, sw = self._feature_card(fid)
                self._feature_cards[fid] = (card, sw, cat)
                grid.addWidget(card, i // 2, i % 2)
            lay.addLayout(grid)
        lay.addStretch(1)

    def _feature_card(self, fid):
        icon, _cat, page, plugin, deps = BUILTIN[fid]
        card = QFrame(objectName="featureCard")
        card.setMinimumHeight(118)
        h = QHBoxLayout(card)
        h.setContentsMargins(14, 12, 14, 12)
        ic = QLabel(objectName="featureIcon")
        ic.setPixmap(draw(icon, accent(), 26).pixmap(26, 26))
        ic.setFixedWidth(30)
        ic.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        h.addWidget(ic)
        col = QVBoxLayout()
        col.setSpacing(3)
        col.addWidget(QLabel(tr("feat.%s.title" % fid), objectName="featureTitle"))
        desc = QLabel(tr("feat.%s.desc" % fid), objectName="hint")
        desc.setWordWrap(True)
        col.addWidget(desc)
        badges = []
        if plugin:
            badges.append(tr("features.needs", what=plugin))
        if deps:
            badges.append(tr("features.depends", what=", ".join(tr("feat.%s.title" % d) for d in deps)))
        if badges:
            b = QLabel("   ".join(badges), objectName="featureBadge")
            b.setWordWrap(True)
            col.addWidget(b)
        col.addStretch(1)
        link = QPushButton(tr("features.settings") + "  ", objectName="link")
        link.setCursor(Qt.PointingHandCursor)
        link.clicked.connect(lambda _=False, p=page: self.goto_page(p))
        row = QHBoxLayout()
        row.addWidget(link)
        row.addStretch(1)
        col.addLayout(row)
        h.addLayout(col, 1)
        sw = ToggleSwitch(feature_on(self.P, fid))
        sw.toggled.connect(lambda on, f=fid: self._toggle_builtin(f, on))
        h.addWidget(sw, 0, Qt.AlignTop)
        return card, sw

    def _toggle_builtin(self, fid, on):
        self.collect()
        changed = set_feature(self.P, fid, on)
        if changed:
            names = ", ".join(tr("feat.%s.title" % c) for c in changed)
            self._log(tr("features.changed", state=tr("features.on") if on else tr("features.off"), what=names))
        self.refresh()
        self.do_generate()

    # ---------- sections of the file ----------
    def _fill_file_sections(self):
        lay = self.tab_file_lay
        _clear(lay)
        from ..merge import is_managed
        if not self.current_text:
            self.feature_tabs.setTabText(1, tr("features.tab_file", count=0))
            msg = QLabel(tr("features.no_file"), objectName="hint")
            msg.setWordWrap(True)
            lay.addWidget(msg)
            lay.addStretch(1)
            return
        secs = list_sections(self.current_text, lambda n: is_managed(n, self.P))
        self.feature_tabs.setTabText(1, tr("features.tab_file", count=len(secs)))
        hint = QLabel(tr("features.file_hint"), objectName="hint")
        hint.setWordWrap(True)
        lay.addWidget(hint)
        groups = [("features.group_sections", lambda n: not n.startswith(("gcode_macro ", "include "))),
                  ("features.group_includes", lambda n: n.startswith("include ")),
                  ("features.group_macros", lambda n: n.startswith("gcode_macro "))]
        for title, test in groups:
            rows = [(n, on) for n, on in secs if test(n) and self._match(n)]
            if not rows:
                continue
            lay.addWidget(QLabel("%s  (%d)" % (tr(title), len(rows)), objectName="sectionHead"))
            box = QFrame(objectName="listBox")
            bl = QVBoxLayout(box)
            bl.setContentsMargins(0, 4, 0, 4)
            bl.setSpacing(0)
            for name, originally_on in rows:
                bl.addWidget(self._section_row(name, originally_on))
            lay.addWidget(box)
        lay.addStretch(1)

    def _section_row(self, name, originally_on):
        disabled, enabled = self.P["disabled_sections"], self.P["enabled_sections"]
        now_on = (originally_on and name not in disabled) or (not originally_on and name in enabled)
        row = QFrame(objectName="listRow")
        h = QHBoxLayout(row)
        h.setContentsMargins(14, 6, 14, 6)
        lab = QLabel("[%s]" % name, objectName="mono")
        lab.setLayoutDirection(Qt.LeftToRight)
        h.addWidget(lab, 1)
        state = QLabel(objectName="hint")
        if now_on != originally_on:
            state.setText(" " + tr("features.pending_on" if now_on else "features.pending_off"))
            state.setStyleSheet("color:#d29922;")
        elif not originally_on:
            state.setText(tr("features.was_off"))
        h.addWidget(state)
        sw = ToggleSwitch(now_on)
        sw.toggled.connect(lambda on, n=name, o=originally_on: self._toggle_section(n, o, on))
        h.addWidget(sw)
        return row

    def _toggle_section(self, name, originally_on, on):
        disabled, enabled = self.P["disabled_sections"], self.P["enabled_sections"]
        for lst in (disabled, enabled):
            if name in lst:
                lst.remove(name)
        if originally_on and not on:
            disabled.append(name)
        elif not originally_on and on:
            enabled.append(name)
        self._fill_file_sections()
        self.do_generate()

    # ---------- catalog ----------
    def _fill_catalog(self):
        lay = self.tab_add_lay
        _clear(lay)
        lay.addWidget(QLabel(tr("features.added"), objectName="sectionHead"))
        items = self.P["custom_sections"]
        if not items:
            e = QLabel(tr("features.added_empty"), objectName="hint")
            lay.addWidget(e)
        for idx, item in enumerate(items):
            lay.addWidget(self._custom_editor(idx, item))

        lay.addSpacing(8)
        lay.addWidget(QLabel(tr("features.catalog"), objectName="sectionHead"))
        existing = set(section_names(self.current_text or ""))
        cats = []
        for cid, (icon, cat, requires, template) in CATALOG.items():
            if not self._match(tr("cat.%s.title" % cid), tr("cat.%s.desc" % cid), template):
                continue
            if cat not in cats:
                cats.append(cat)
        for cat in cats:
            lay.addWidget(QLabel(tr("fcat." + cat), objectName="subHead"))
            grid = QGridLayout()
            grid.setSpacing(10)
            ids = [c for c, spec in CATALOG.items() if spec[1] == cat and
                   self._match(tr("cat.%s.title" % c), tr("cat.%s.desc" % c), spec[3])]
            for i, cid in enumerate(ids):
                grid.addWidget(self._catalog_card(cid, existing), i // 2, i % 2)
            lay.addLayout(grid)
        lay.addStretch(1)

    def _catalog_card(self, cid, existing):
        icon, _cat, requires, template = CATALOG[cid]
        card = QFrame(objectName="featureCard")
        h = QHBoxLayout(card)
        h.setContentsMargins(14, 10, 14, 10)
        ic = QLabel(objectName="featureIcon")
        ic.setPixmap(draw(icon, accent(), 26).pixmap(26, 26))
        ic.setFixedWidth(34)
        h.addWidget(ic)
        col = QVBoxLayout()
        col.setSpacing(2)
        col.addWidget(QLabel(tr("cat.%s.title" % cid), objectName="featureTitle"))
        d = QLabel(tr("cat.%s.desc" % cid), objectName="hint")
        d.setWordWrap(True)
        col.addWidget(d)
        names = section_names(template)
        tag = QLabel(" ".join("[%s]" % n for n in names) + (("    " + requires) if requires else ""), objectName="featureBadge")
        tag.setWordWrap(True)
        col.addWidget(tag)
        h.addLayout(col, 1)
        taken = [n for n in names if n in existing] if cid != "blank" else []
        added = any(it.get("id") == cid for it in self.P["custom_sections"]) and cid != "blank"
        btn = QPushButton("" if added else tr("features.add"), objectName="primary" if not (taken or added) else "")
        btn.setEnabled(not taken and not added)
        if taken:
            btn.setToolTip(tr("features.exists", section=taken[0]))
        btn.clicked.connect(lambda _=False, c=cid: self._add_catalog(c))
        h.addWidget(btn, 0, Qt.AlignVCenter)
        return card

    def _add_catalog(self, cid):
        self.collect()
        text = fill_template(self.P, CATALOG[cid][3])
        self.P["custom_sections"].append({"id": cid, "text": text, "enabled": True})
        self._fill_catalog()
        self.do_generate()

    def _custom_editor(self, idx, item):
        box = QFrame(objectName="featureCard")
        v = QVBoxLayout(box)
        v.setContentsMargins(14, 10, 14, 12)
        head = QHBoxLayout()
        cid = item.get("id", "blank")
        head.addWidget(QLabel("%s  %s" % (CATALOG.get(cid, CATALOG["blank"])[0], tr("cat.%s.title" % cid)),
                              objectName="featureTitle"), 1)
        rm = QPushButton(tr("features.remove"), objectName="danger")
        rm.clicked.connect(lambda _=False, i=idx: self._remove_custom(i))
        head.addWidget(rm)
        sw = ToggleSwitch(item.get("enabled", True))
        sw.toggled.connect(lambda on, i=idx: self._custom_set(i, "enabled", on))
        head.addWidget(sw)
        v.addLayout(head)
        hint = QLabel(tr("features.edit_hint"), objectName="hint")
        hint.setWordWrap(True)
        v.addWidget(hint)
        ed = QPlainTextEdit(item.get("text", ""))
        ed.setLayoutDirection(Qt.LeftToRight)
        ed.setMinimumHeight(120)
        ed.setMaximumHeight(240)
        ed._hl = CfgHighlighter(ed.document())
        ed.textChanged.connect(lambda i=idx, e=ed: self._custom_set(i, "text", e.toPlainText(), regenerate=False))
        v.addWidget(ed)
        return box

    def _custom_set(self, idx, key, value, regenerate=True):
        if 0 <= idx < len(self.P["custom_sections"]):
            self.P["custom_sections"][idx][key] = value
            if regenerate:
                self.do_generate()

    def _remove_custom(self, idx):
        if 0 <= idx < len(self.P["custom_sections"]):
            del self.P["custom_sections"][idx]
        self._fill_catalog()
        self.do_generate()
