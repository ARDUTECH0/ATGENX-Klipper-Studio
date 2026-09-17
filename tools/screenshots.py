# -*- coding: utf-8 -*-
"""Renders README screenshots from the test fixtures (no printer needed).

    python tools/screenshots.py [en|ar]
"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("ATGENX_STUDIO_HOME", os.path.join(ROOT, "tests", ".studio_home"))

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from studio import i18n  # noqa: E402
from studio.gui.app import Studio  # noqa: E402
from studio.gui.files_page import local_configset  # noqa: E402
from studio.gui.style import STYLE  # noqa: E402


def main(lang="en"):
    i18n.set_lang(lang)
    app = QApplication.instance() or QApplication(sys.argv)
    app.setLayoutDirection(Qt.RightToLeft if i18n.is_rtl() else Qt.LeftToRight)
    app.setStyleSheet(STYLE)
    fix = os.path.join(ROOT, "tests", "fixtures")
    win = Studio()
    win.resize(1360, 900)
    win.P["host"] = "mainsailos.local"
    win.refresh()
    with io.open(os.path.join(fix, "simple_printer.cfg"), encoding="utf-8") as f:
        text = f.read()
    win._load_text(text, "printer.cfg on mainsailos.local")
    win.set_configset(local_configset(os.path.join(fix, "modular")), ("local", "mainsailos.local"))
    win.show()
    out = os.path.join(ROOT, "docs", "screenshots")
    os.makedirs(out, exist_ok=True)
    shots = {"page_board": "board", "page_motors": "motors", "page_probe": "probe",
             "page_preview": "review", "page_files": "files"}
    for i, (_, builder) in enumerate(win.PAGES):
        if builder not in shots:
            continue
        win.nav.setCurrentRow(i)
        if builder == "page_preview":
            win.tabs.setCurrentIndex(1)
        app.processEvents()
        path = os.path.join(out, "%s-%s.png" % (shots[builder], lang))
        win.grab().save(path)
        print(path)
    win.close()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "en")
