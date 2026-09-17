# -*- coding: utf-8 -*-
"""Every config file of a printer: include tree, section index and helpers."""
import fnmatch
import posixpath
import re
from collections import OrderedDict

from .cfgtools import SECTION_RE, split_save

INCLUDE_RE = re.compile(r"^\[include\s+([^\]]+)\]", re.M)
TEXT_EXTS = (".cfg", ".conf", ".txt", ".ini", ".json", ".yaml", ".yml", ".sh", ".py", ".md")
MAX_FILE_SIZE = 1024 * 1024

# which service to restart after editing a file
SERVICE_FOR_FILE = [
    ("moonraker.conf", "moonraker"), ("moonraker-obico.cfg", "moonraker-obico"), ("crowsnest.conf", "crowsnest"),
    ("KlipperScreen.conf", "KlipperScreen"), ("sonar.conf", "sonar"), ("telegram.conf", "moonraker-telegram-bot"),
]


def restart_kind(path):
    """'klipper', a service name, or '' when nothing needs restarting."""
    base = posixpath.basename(path)
    for name, service in SERVICE_FOR_FILE:
        if base == name:
            return service
    if base.endswith(".cfg") and not base.startswith("printer-"):
        return "klipper"
    return ""


def include_targets(text, base_dir, available):
    """Paths included by a file. Supports globs, resolved against the list of existing files."""
    main, _ = split_save(text)
    out = []
    for m in INCLUDE_RE.finditer(main):
        pattern = posixpath.normpath(posixpath.join(base_dir, m.group(1).strip()))
        if any(ch in pattern for ch in "*?["):
            out += sorted(p for p in available if fnmatch.fnmatch(p, pattern))
        else:
            out.append(pattern)
    return out


class ConfigSet:
    """files: OrderedDict path -> text (include order first, then other files)."""

    def __init__(self):
        self.files = OrderedDict()
        self.included = []      # paths reachable from printer.cfg, in include order
        self.missing = []       # includes that don't exist
        self.tree = {}          # path -> [included paths]
        self.warnings = []      # Klipper's config warnings (from Moonraker)

    @classmethod
    def load(cls, fetch, listing, root="printer.cfg", others=True):
        """fetch(path) -> text; listing = [(path, size)] of the config root."""
        cs = cls()
        available = [p for p, _ in listing]
        sizes = dict(listing)

        def walk(path, depth=0):
            if path in cs.files or depth > 16:
                return
            try:
                text = fetch(path).replace("\r\n", "\n")
            except Exception:  # missing include: reported, not fatal
                cs.missing.append(path)
                return
            cs.files[path] = text
            cs.included.append(path)
            kids = include_targets(text, posixpath.dirname(path), available)
            cs.tree[path] = kids
            for k in kids:
                walk(k, depth + 1)

        walk(root)
        if others:
            for p in sorted(available, key=lambda x: (x.count("/"), x.lower())):
                if p in cs.files or not p.lower().endswith(TEXT_EXTS) or sizes.get(p, 0) > MAX_FILE_SIZE:
                    continue
                if p.startswith(("studio_backups/", ".")) or "/." in p:
                    continue
                try:
                    cs.files[p] = fetch(p).replace("\r\n", "\n")
                except Exception:
                    continue
        return cs

    def includes_text(self, root="printer.cfg"):
        """Main parts of every included file except root, joined (for importing modular configs)."""
        parts = []
        for p in self.included:
            if p != root and p.endswith(".cfg"):
                parts.append(split_save(self.files[p])[0])
        return "\n".join(parts)

    def sections(self, path):
        """[(section name, line number)] of one file (1-based)."""
        out = []
        for i, ln in enumerate(self.files.get(path, "").split("\n"), 1):
            m = SECTION_RE.match(ln)
            if m:
                out.append((m.group(1).strip(), i))
        return out

    def section_files(self, exclude=("printer.cfg",)):
        """section name -> file, for Klipper config files outside `exclude`."""
        out = {}
        for p in self.included:
            if p in exclude:
                continue
            for name, _ in self.sections(p):
                out.setdefault(name, p)
        return out
