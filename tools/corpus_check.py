# -*- coding: utf-8 -*-
"""Runs every .cfg in a folder through import -> merge -> validate and reports problems.

    python tools/corpus_check.py <klipper>/config [--verbose]

For each file it checks that:
  * import doesn't crash
  * merge and full outputs parse, have no duplicate sections
  * merge keeps every section the app doesn't manage, and every macro
  * merge is idempotent (merging the result again changes nothing)
"""
import io
import os
import re
import sys
import traceback
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("ATGENX_STUDIO_HOME", os.path.join(ROOT, "tests", ".studio_home"))

from studio import i18n  # noqa: E402
from studio.boards import get_board  # noqa: E402
from studio.cfgtools import cfg_parser, split_save  # noqa: E402
from studio.importer import import_config  # noqa: E402
from studio.merge import build, is_managed  # noqa: E402
from studio.validate import validate  # noqa: E402

SECTION_RE = re.compile(r"^\[([^\]\n]+)\]", re.M)


def sections(text):
    return SECTION_RE.findall(split_save(text)[0])


def check(path):
    problems = []
    with io.open(path, encoding="utf-8") as f:
        text = f.read().replace("\r\n", "\n")
    P, notes = import_config(text)
    board = get_board(P["board"])
    before = sections(text)
    for mode in ("merge", "full"):
        out = build(P, text, mode, True, board)
        try:
            cfg_parser(out)
        except Exception as e:
            problems.append("%s: does not parse: %s" % (mode, str(e).splitlines()[0]))
            continue
        after = sections(out)
        dups = sorted({s for s in after if after.count(s) > 1 and before.count(s) < 2})
        if dups:
            problems.append("%s: duplicate sections %s" % (mode, dups))
        lost = [s for s in before if s not in after and not is_managed(s, P, None)
                and not s.startswith("gcode_macro ")]
        if lost:
            problems.append("%s: lost sections %s" % (mode, lost))
        macros_before = [s for s in before if s.startswith("gcode_macro ")]
        macros_lost = [s for s in macros_before if s not in after]
        if macros_lost:
            problems.append("%s: lost macros %s" % (mode, macros_lost))
        if mode == "merge":
            P2, _ = import_config(out)
            again = build(P2, out, "merge", True, get_board(P2["board"]))
            if again != out:
                import difflib
                d = [l for l in difflib.unified_diff(out.splitlines(), again.splitlines(), lineterm="", n=0)
                     if l[:1] in "+-" and l[:3] not in ("+++", "---")]
                problems.append("merge not idempotent: %s" % d[:6])
            errors = [m for k, m in validate(P, out, board) if k == "error"]
    return P, problems, errors


def main(argv):
    i18n.set_lang("en")
    folder = argv[1]
    verbose = "--verbose" in argv
    files = sorted(f for f in os.listdir(folder) if f.endswith(".cfg"))
    crashed, failed, err_kinds, boards = 0, 0, Counter(), 0
    for f in files:
        path = os.path.join(folder, f)
        try:
            P, problems, errors = check(path)
        except Exception:
            crashed += 1
            print("CRASH  %s\n%s" % (f, traceback.format_exc(limit=3)))
            continue
        boards += bool(P["board"])
        for e in errors:
            err_kinds[re.sub(r"[\d.]+|'[^']*'|: .*", "#", e)[:70]] += 1
        if problems:
            failed += 1
            print("FAIL   %s" % f)
            for p in problems:
                print("         - " + p)
        elif verbose:
            print("ok     %s  board=%s  errors=%d" % (f, P["board"] or "-", len(errors)))
    print("\n%d files  |  crashed %d  |  failed %d  |  board detected %d" % (len(files), crashed, failed, boards))
    print("validation errors reported on the example files (expected: placeholder serials etc.):")
    for k, v in err_kinds.most_common(12):
        print("  %4d  %s" % (v, k))
    return 1 if crashed or failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
