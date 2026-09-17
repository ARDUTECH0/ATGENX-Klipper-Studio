# -*- coding: utf-8 -*-
"""Checks, builds and (optionally) publishes a release - exe included, every time.

    python tools/release.py                  run every check and build the exe
    python tools/release.py --publish        ... and create the GitHub release with the exe attached
    python tools/release.py --notes FILE     use FILE as the release notes (default: the CHANGELOG top section)

Nothing is published unless --publish is given, and even then it refuses if a check failed,
if the working tree is dirty, if you are not on main, or if the tag already exists.
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from studio import APP_NAME, __version__  # noqa: E402

TAG = "v" + __version__
EXE = os.path.join(ROOT, "dist", "KlipperStudio" + (".exe" if os.name == "nt" else ""))


def run(args, what, env=None):
    print("\n>>> %s" % what)
    r = subprocess.run(args, cwd=ROOT, env=dict(os.environ, **(env or {})))
    print("%s  %s" % ("PASS" if r.returncode == 0 else "FAIL", what))
    return r.returncode == 0


def out(args):
    r = subprocess.run(args, cwd=ROOT, capture_output=True)
    return r.stdout.decode("utf-8", "replace").strip()


def changelog_notes():
    """The top section of CHANGELOG.md, without its own heading."""
    path = os.path.join(ROOT, "CHANGELOG.md")
    if not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    parts = re.split(r"^## ", text, flags=re.M)
    return parts[1].split("\n", 1)[1].strip() if len(parts) > 1 else ""


def checks():
    ok = run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"], "core tests")
    e2e = os.path.join(ROOT, "tools", "gui_e2e.py")
    if os.path.exists(e2e):
        ok = run([sys.executable, e2e], "end-to-end test against a fake Moonraker",
                 {"QT_QPA_PLATFORM": "offscreen"}) and ok
    return ok


def publish(notes_file):
    if out(["git", "status", "--porcelain"]):
        print("\nrefusing: there are uncommitted changes - commit and merge them first")
        return False
    branch = out(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    if branch != "main":
        print("\nrefusing: you are on '%s', release from main" % branch)
        return False
    if TAG in out(["git", "tag", "-l", TAG]) or TAG in out(["gh", "release", "list", "--limit", "100"]):
        print("\n%s already exists - bump __version__ in studio/__init__.py first" % TAG)
        return False
    title = "%s %s" % (APP_NAME.replace("ATGENX ", ""), __version__.replace("-beta.", " Beta "))
    cmd = ["gh", "release", "create", TAG, "--target", "main", "--title", title, "--notes-file", notes_file]
    if "beta" in __version__ or "rc" in __version__ or "alpha" in __version__:
        cmd.append("--prerelease")
    if not run(cmd, "create the release %s" % TAG):
        return False
    return run(["gh", "release", "upload", TAG, EXE, EXE + ".sha256"], "upload the exe and its checksum")


def main():
    print("%s %s\n" % (APP_NAME, __version__))
    ok = checks()
    ok = run([sys.executable, os.path.join(ROOT, "tools", "build_exe.py"), "--test"],
             "build the executable and test it") and ok
    if not ok:
        print("\nsomething failed - not releasing")
        return 1
    print("\nready: %s  (%.1f MB)" % (EXE, os.path.getsize(EXE) / 1024 / 1024))
    print("Double-click it once yourself before publishing - the tests prove it runs, not that it looks right.")
    if "--publish" not in sys.argv:
        print("\nAdd --publish to create %s on GitHub with the exe attached." % TAG)
        return 0
    notes = sys.argv[sys.argv.index("--notes") + 1] if "--notes" in sys.argv else ""
    if not notes:
        notes = os.path.join(ROOT, "build", "release-notes.md")
        with open(notes, "w", encoding="utf-8") as f:
            f.write(changelog_notes() or "See CHANGELOG.md.")
    return 0 if publish(notes) else 1


if __name__ == "__main__":
    sys.exit(main())
