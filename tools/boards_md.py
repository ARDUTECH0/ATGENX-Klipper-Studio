# -*- coding: utf-8 -*-
"""Writes docs/BOARDS.md from boards/*.json.   python tools/boards_md.py"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from studio.boards import load_boards  # noqa: E402


def main():
    boards = load_boards()
    lines = ["# Supported boards", "",
             "%d controller boards, generated from `boards/*.json`. Pin data comes from "
             "[Klipper's config files](https://github.com/Klipper3d/klipper/tree/master/config)." % len(boards), "",
             "Board missing or wrong? See [CONTRIBUTING.md](../CONTRIBUTING.md#adding-or-fixing-a-board).", "",
             "| Board | MCU | Drivers | TMC documented | Klipper file |",
             "|---|---|---|---|---|"]
    for bid, b in boards.items():
        m = b.get("mcu", {})
        mcu = ", ".join(p.upper() if p.startswith("stm32") else p for p in m.get("processors") or []) or (m.get("family") or "")
        lines.append("| %s | %s | %d | %s | [%s](%s) |" % (
            b["name"], mcu, len(b["drivers"]), ", ".join(b.get("tmc_types") or []) or "-",
            b["source"].rsplit("/", 1)[-1], b["source"]))
    path = os.path.join(ROOT, "docs", "BOARDS.md")
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print(path)


if __name__ == "__main__":
    main()
