# -*- coding: utf-8 -*-
"""The app's icons, drawn in code.

No emoji (they look different on every machine and ignore the theme) and no image files to ship.
Each icon is a few strokes on a 24x24 grid, painted in whatever colour the caller asks for, so the
whole set follows the accent colour.
"""
import re

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap

_CACHE = {}
EMOJI = re.compile("[\U0001F000-\U0001FAFF←-⯿️☀-➿]+")


def strip_emoji(text):
    return EMOJI.sub("", text).strip()


def _pen(p, color, width=1.8):
    pen = QPen(QColor(color), width)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    return pen


def _draw(name, p, c):
    """Everything is drawn inside a 24x24 box."""
    _pen(p, c)
    if name == "start":
        path = QPainterPath(QPointF(9, 6))
        path.lineTo(18, 12)
        path.lineTo(9, 18)
        path.closeSubpath()
        p.setBrush(QColor(c))
        p.drawPath(path)
    elif name == "connection":
        p.drawLine(9, 4, 9, 9)
        p.drawLine(15, 4, 15, 9)
        p.drawRoundedRect(QRectF(6.5, 9, 11, 7), 2, 2)
        p.drawLine(12, 16, 12, 20)
    elif name == "board":
        p.drawRoundedRect(QRectF(4.5, 5.5, 15, 13), 2, 2)
        p.drawRect(QRectF(9, 9.5, 6, 5))
        for x in (7, 12, 17):
            p.drawLine(x, 18.5, x, 20.5)
    elif name == "features":
        p.drawRoundedRect(QRectF(3.5, 8, 17, 8), 4, 4)
        p.setBrush(QColor(c))
        p.drawEllipse(QPointF(16, 12), 2.6, 2.6)
    elif name == "machine":
        p.drawRect(QRectF(4.5, 7.5, 15, 11))
        p.drawLine(4.5, 11, 19.5, 11)
        p.drawLine(9, 4.5, 15, 4.5)
    elif name == "motors":
        p.drawEllipse(QPointF(12, 12), 5.2, 5.2)
        p.drawEllipse(QPointF(12, 12), 1.6, 1.6)
        for dx, dy in ((0, -8), (0, 8), (-8, 0), (8, 0)):
            p.drawLine(12 + dx * 0.72, 12 + dy * 0.72, 12 + dx * 0.95, 12 + dy * 0.95)
    elif name == "thermal":
        p.drawLine(10, 5, 10, 14)
        p.drawEllipse(QPointF(10, 16.5), 3.2, 3.2)
        p.drawLine(15, 6, 15, 9)
        p.drawLine(18, 6, 18, 9)
    elif name == "probe":
        p.drawEllipse(QPointF(12, 12), 5.5, 5.5)
        p.drawLine(12, 3, 12, 6.5)
        p.drawLine(12, 17.5, 12, 21)
        p.drawLine(3, 12, 6.5, 12)
        p.drawLine(17.5, 12, 21, 12)
    elif name == "extras":
        p.drawEllipse(QPointF(12, 10), 4.6, 4.6)
        p.drawLine(9.5, 16.5, 14.5, 16.5)
        p.drawLine(10.5, 19, 13.5, 19)
    elif name == "pins":
        p.setBrush(QColor(c))
        for x in (7, 12, 17):
            for y in (7, 12, 17):
                p.drawEllipse(QPointF(x, y), 1.5, 1.5)
    elif name == "map":
        p.drawEllipse(QPointF(6, 7), 2.3, 2.3)
        p.drawEllipse(QPointF(18, 9), 2.3, 2.3)
        p.drawEllipse(QPointF(11, 18), 2.3, 2.3)
        p.drawLine(7.8, 8.4, 9.8, 15.8)
        p.drawLine(16.2, 10.4, 12.6, 16.2)
    elif name == "preview":
        p.drawRoundedRect(QRectF(5.5, 4, 13, 16), 2, 2)
        p.drawLine(8.5, 13, 11, 15.5)
        p.drawLine(11, 15.5, 15.5, 9.5)
    elif name in ("files", "open_project", "open_cfg", "remote"):
        path = QPainterPath(QPointF(4, 18.5))
        path.lineTo(4, 6.5)
        path.lineTo(10, 6.5)
        path.lineTo(12, 9)
        path.lineTo(20, 9)
        path.lineTo(20, 18.5)
        path.closeSubpath()
        p.drawPath(path)
        if name == "remote":
            p.drawLine(9.5, 13.8, 12, 13.8)
            p.drawLine(11, 12.4, 12.4, 13.8)
            p.drawLine(11, 15.2, 12.4, 13.8)
    elif name == "printers":
        p.drawRoundedRect(QRectF(4.5, 9, 15, 7), 2, 2)
        p.drawRect(QRectF(8, 4.5, 8, 4.5))
        p.drawRect(QRectF(8, 16, 8, 4))
    elif name == "doctor":
        p.drawEllipse(QPointF(12, 12), 7.5, 7.5)
        p.drawLine(12, 8.5, 12, 15.5)
        p.drawLine(8.5, 12, 15.5, 12)
    elif name == "new":
        p.drawLine(12, 5, 12, 19)
        p.drawLine(5, 12, 19, 12)
    elif name == "save_project":
        p.drawRoundedRect(QRectF(5, 5, 14, 14), 2, 2)
        p.drawRect(QRectF(8.5, 5, 7, 5))
        p.drawRect(QRectF(8.5, 13, 7, 6))
    elif name == "help_panel":
        p.drawEllipse(QPointF(12, 12), 7.5, 7.5)
        p.drawArc(QRectF(9, 7, 6, 6), 200 * 16, -220 * 16)
        p.drawLine(12, 13, 12, 14.5)
        p.setBrush(QColor(c))
        p.drawEllipse(QPointF(12, 16.8), 0.9, 0.9)
    elif name == "guide":
        p.drawRect(QRectF(4.5, 5.5, 15, 13))
        p.drawLine(12, 5.5, 12, 18.5)
        p.drawLine(7, 9.5, 10, 9.5)
        p.drawLine(14, 9.5, 17, 9.5)
    elif name == "support":
        p.drawRoundedRect(QRectF(5, 8, 11, 9), 2, 2)
        p.drawArc(QRectF(15, 9, 5, 6), 90 * 16, -180 * 16)
        p.drawLine(8, 4.5, 8, 6.5)
        p.drawLine(12, 4.5, 12, 6.5)
    elif name == "about":
        p.drawEllipse(QPointF(12, 12), 7.5, 7.5)
        p.drawLine(12, 11, 12, 16)
        p.setBrush(QColor(c))
        p.drawEllipse(QPointF(12, 8.2), 0.9, 0.9)
    elif name == "theme":
        p.drawEllipse(QPointF(12, 12), 7.5, 7.5)
        p.setBrush(QColor(c))
        for x, y in ((9, 9), (15, 9.5), (9.5, 15)):
            p.drawEllipse(QPointF(x, y), 1.4, 1.4)
    else:  # anything unnamed still gets a mark rather than nothing
        p.drawEllipse(QPointF(12, 12), 6, 6)


def icon(name, color="#8b949e", size=22):
    key = (name, color, size)
    if key not in _CACHE:
        pm = QPixmap(size, size)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        p.scale(size / 24.0, size / 24.0)
        _draw(name, p, color)
        p.end()
        _CACHE[key] = QIcon(pm)
    return _CACHE[key]


def clear_cache():
    _CACHE.clear()
