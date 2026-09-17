# -*- coding: utf-8 -*-
import re

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat
from PySide6.QtWidgets import QComboBox, QCompleter


class CfgHighlighter(QSyntaxHighlighter):
    """Klipper config / unified diff highlighting."""

    def __init__(self, doc, diff=False):
        super().__init__(doc)
        self.diff = diff

        def fmt(color, bold=False):
            f = QTextCharFormat()
            f.setForeground(QColor(color))
            if bold:
                f.setFontWeight(QFont.Bold)
            return f
        self.f_sec, self.f_key = fmt("#58a6ff", True), fmt("#d2a8ff")
        self.f_com, self.f_save = fmt("#6e7681"), fmt("#d29922")
        self.f_add, self.f_del, self.f_hunk = fmt("#3fb950"), fmt("#f85149"), fmt("#58a6ff")

    def highlightBlock(self, t):
        if self.diff:
            if t.startswith("+") and not t.startswith("+++"):
                self.setFormat(0, len(t), self.f_add)
            elif t.startswith("-") and not t.startswith("---"):
                self.setFormat(0, len(t), self.f_del)
            elif t.startswith("@@"):
                self.setFormat(0, len(t), self.f_hunk)
            return
        if t.startswith("#*#"):
            self.setFormat(0, len(t), self.f_save)
        elif t.lstrip().startswith(("#", ";")):
            self.setFormat(0, len(t), self.f_com)
        elif t.startswith("["):
            self.setFormat(0, len(t), self.f_sec)
        else:
            m = re.match(r"^([A-Za-z0-9_]+)\s*:", t)
            if m:
                self.setFormat(0, m.end(1), self.f_key)


class Bridge(QObject):
    """Delivers background thread results back to the UI thread."""
    done = Signal(object, object, object)
    log = Signal(str)


class SearchCombo(QComboBox):
    """Editable combo that filters items by any part of the text."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.NoInsert)
        c = self.completer()
        c.setFilterMode(Qt.MatchContains)
        c.setCompletionMode(QCompleter.PopupCompletion)
        c.setCaseSensitivity(Qt.CaseInsensitive)
