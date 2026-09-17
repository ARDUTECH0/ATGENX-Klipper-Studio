# -*- coding: utf-8 -*-
"""Renders the brand images from studio/assets/icon.svg.

    python tools/make_brand.py

  studio/assets/icon.png        256 px app icon
  studio/assets/icon.ico        Windows icon (16-256 px)
  docs/brand/logo-banner.png    README header
  docs/brand/social-preview.png GitHub social preview (1280x640)
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
if os.name == "nt":
    os.environ.setdefault("QT_QPA_FONTDIR", os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts"))

from PySide6.QtCore import QRectF, Qt  # noqa: E402
from PySide6.QtGui import QColor, QFont, QGuiApplication, QImage, QLinearGradient, QPainter, QPen  # noqa: E402
from PySide6.QtSvg import QSvgRenderer  # noqa: E402

from studio import __version__  # noqa: E402

ICON = os.path.join(ROOT, "studio", "assets", "icon.svg")


def render_icon(size):
    img = QImage(size, size, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    QSvgRenderer(ICON).render(p, QRectF(0, 0, size, size))
    p.end()
    return img


def font(size, weight=QFont.Normal, family="Segoe UI"):
    f = QFont(family)
    f.setPixelSize(size)
    f.setWeight(weight)
    return f


def background(p, w, h, radius=0):
    g = QLinearGradient(0, 0, w, h)
    g.setColorAt(0, QColor("#0f1c33"))
    g.setColorAt(1, QColor("#0a0f1a"))
    p.setPen(Qt.NoPen)
    p.setBrush(g)
    p.drawRoundedRect(QRectF(0, 0, w, h), radius, radius)


def banner(path):
    w, h = 1600, 400
    img = QImage(w, h, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.TextAntialiasing)
    background(p, w, h, 48)
    QSvgRenderer(ICON).render(p, QRectF(70, 60, 280, 280))
    p.setPen(QColor("#e6edf3"))
    p.setFont(font(118, QFont.DemiBold))
    p.drawText(QRectF(400, 70, 1150, 150), Qt.AlignLeft | Qt.AlignVCenter, "Klipper Studio")
    p.setPen(QColor("#8b9bb0"))
    p.setFont(font(40))
    p.drawText(QRectF(406, 215, 1150, 60), Qt.AlignLeft | Qt.AlignVCenter,
               "Build, check and safely upload your printer.cfg")
    p.setPen(QColor("#3b8eea"))
    p.setFont(font(30, QFont.DemiBold))
    p.drawText(QRectF(406, 280, 1150, 50), Qt.AlignLeft | Qt.AlignVCenter, "by ATGENX")
    p.end()
    img.save(path)


def social(path):
    w, h = 1280, 640
    img = QImage(w, h, QImage.Format_ARGB32)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.TextAntialiasing)
    background(p, w, h)
    QSvgRenderer(ICON).render(p, QRectF(90, 150, 300, 300))
    p.setPen(QColor("#e6edf3"))
    p.setFont(font(92, QFont.DemiBold))
    p.drawText(QRectF(440, 130, 800, 120), Qt.AlignLeft | Qt.AlignVCenter, "Klipper Studio")
    p.setPen(QColor("#b7c3d1"))
    p.setFont(font(34))
    p.drawText(QRectF(446, 250, 800, 110), Qt.AlignLeft | Qt.TextWordWrap,
               "Build, check and safely upload your Klipper printer.cfg")
    y = 380
    p.setFont(font(26, QFont.DemiBold))
    for text, color in (("83 boards", "#3b8eea"), ("Motors & drivers", "#2ea043"), ("Troubleshooter", "#ff9f43")):
        width = p.fontMetrics().horizontalAdvance(text) + 44
        x = 446 + sum(p.fontMetrics().horizontalAdvance(t) + 60 for t, _ in
                      (("83 boards", 0), ("Motors & drivers", 0), ("Troubleshooter", 0))[:["83 boards", "Motors & drivers", "Troubleshooter"].index(text)])
        p.setPen(QPen(QColor(color), 2))
        p.setBrush(QColor(color).darker(400))
        p.drawRoundedRect(QRectF(x, y, width, 52), 26, 26)
        p.setPen(QColor(color))
        p.drawText(QRectF(x, y, width, 52), Qt.AlignCenter, text)
    p.setPen(QColor("#8b9bb0"))
    p.setFont(font(28))
    x = 446
    for part in ("English", "  ·  ", "العربية", "  ·  ", "v" + __version__):
        p.drawText(QRectF(x, 470, 400, 50), Qt.AlignLeft | Qt.AlignVCenter, part)
        x += p.fontMetrics().horizontalAdvance(part)
    p.end()
    img.save(path)


def main():
    app = QGuiApplication.instance() or QGuiApplication(sys.argv)  # noqa: F841
    assets = os.path.join(ROOT, "studio", "assets")
    brand = os.path.join(ROOT, "docs", "brand")
    os.makedirs(brand, exist_ok=True)
    render_icon(256).save(os.path.join(assets, "icon.png"))
    try:
        from PIL import Image
        big = render_icon(256)
        big.save(os.path.join(assets, "_tmp.png"))
        Image.open(os.path.join(assets, "_tmp.png")).save(
            os.path.join(assets, "icon.ico"), sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
        os.remove(os.path.join(assets, "_tmp.png"))
    except ImportError:
        render_icon(256).save(os.path.join(assets, "icon.ico"))
    banner(os.path.join(brand, "logo-banner.png"))
    social(os.path.join(brand, "social-preview.png"))
    for f in ("icon.png", "icon.ico"):
        print(os.path.join(assets, f))
    for f in ("logo-banner.png", "social-preview.png"):
        print(os.path.join(brand, f))


if __name__ == "__main__":
    main()
