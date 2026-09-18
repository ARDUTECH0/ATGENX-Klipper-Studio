# -*- coding: utf-8 -*-
"""ATGENX Klipper Studio - a guided printer.cfg builder for Klipper."""
import os
import sys

APP_NAME = "ATGENX Klipper Studio"
__version__ = "1.0.0-beta.4"
LICENSE_NAME = "GNU GPL v3.0 or later"
REPO_URL = "https://github.com/ARDUTECH0/ATGENX-Klipper-Studio"
SUPPORT_URL = "https://buymeacoffee.com/seifemadatv"

if getattr(sys, "frozen", False):  # PyInstaller
    ROOT = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
else:
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BOARDS_DIR = os.path.join(ROOT, "boards")
ASSETS_DIR = os.path.join(ROOT, "studio", "assets")
DATA_DIR = os.path.join(ROOT, "studio", "data")
