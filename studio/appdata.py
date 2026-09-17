# -*- coding: utf-8 -*-
"""Per-user settings and backups (outside the install folder)."""
import io
import json
import os

DATA_DIR = os.environ.get("ATGENX_STUDIO_HOME") or os.path.join(os.path.expanduser("~"), ".atgenx-studio")
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
BOARDS_USER_DIR = os.path.join(DATA_DIR, "boards")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")


def load_settings():
    try:
        with io.open(SETTINGS_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_settings(data):
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with io.open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def write_backup(name, text):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    path = os.path.join(BACKUP_DIR, name)
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return path
