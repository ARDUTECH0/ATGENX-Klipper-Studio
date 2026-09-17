# -*- coding: utf-8 -*-
"""Builds a single-file executable (no Python needed by the user).

    python tools/build_exe.py            build for the current platform
    python tools/build_exe.py --test     build, then start it with --smoke and check it works

Result: dist/KlipperStudio.exe (Windows) or dist/KlipperStudio (Linux/macOS).
Everything the app needs is bundled: the 83 board files, the icons and the TMC motor list.
"""
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from studio import APP_NAME, __version__  # noqa: E402

NAME = "KlipperStudio"
ENTRY = os.path.join(ROOT, "tools", "_entry.py")
SEP = ";" if os.name == "nt" else ":"


def write_entry():
    with open(ENTRY, "w", encoding="utf-8") as f:
        f.write("# -*- coding: utf-8 -*-\n"
                "import sys\n\n"
                "from studio.cli import main\n\n"
                "sys.exit(main())\n")


def build():
    write_entry()
    icon = os.path.join(ROOT, "studio", "assets", "icon.ico")
    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onefile", "--windowed",
           "--name", NAME, "--distpath", os.path.join(ROOT, "dist"),
           "--workpath", os.path.join(ROOT, "build"), "--specpath", os.path.join(ROOT, "build"),
           "--add-data", "%s%s%s" % (os.path.join(ROOT, "boards"), SEP, "boards"),
           "--add-data", "%s%s%s" % (os.path.join(ROOT, "studio", "data"), SEP, os.path.join("studio", "data")),
           "--add-data", "%s%s%s" % (os.path.join(ROOT, "studio", "assets"), SEP, os.path.join("studio", "assets")),
           "--exclude-module", "tkinter", "--exclude-module", "PySide6.QtWebEngineCore",
           "--exclude-module", "PySide6.Qt3DCore", "--exclude-module", "PySide6.QtMultimedia",
           "--exclude-module", "PySide6.QtQuick", "--exclude-module", "PySide6.QtQml",
           "--exclude-module", "PySide6.QtCharts", "--exclude-module", "PySide6.QtDataVisualization",
           "--exclude-module", "PIL", "--exclude-module", "numpy",
           ENTRY]
    if os.path.exists(icon):
        cmd[cmd.index("--windowed") + 1:cmd.index("--windowed") + 1] = ["--icon", icon]
    print("building %s %s ..." % (APP_NAME, __version__))
    subprocess.run(cmd, check=True, cwd=ROOT)
    os.remove(ENTRY)
    exe = os.path.join(ROOT, "dist", NAME + (".exe" if os.name == "nt" else ""))
    print("\n%s  (%.1f MB)" % (exe, os.path.getsize(exe) / 1024 / 1024))
    return exe


def test(exe):
    """Start the built app in offscreen mode and check that it opens every page."""
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
    env.pop("ATGENX_STUDIO_HOME", None)
    ok = True
    for args, what in (([exe, "--smoke"], "the app starts and builds every page"),
                       ([exe, "boards"], "the bundled board files are found"),
                       ([exe, "check", os.path.join(ROOT, "tests", "fixtures", "simple_printer.cfg")],
                        "import / merge / validate work")):
        r = subprocess.run(args, env=env, capture_output=True, timeout=300)
        good = r.returncode == 0
        ok = ok and good
        print("%s  %s" % ("PASS" if good else "FAIL", what))
        if not good:
            print((r.stdout + r.stderr).decode("utf-8", "replace")[-1500:])
    return ok


def main():
    if shutil.which("pyinstaller") is None:
        try:
            import PyInstaller  # noqa: F401
        except ImportError:
            print("PyInstaller is missing:  pip install pyinstaller")
            return 2
    exe = build()
    if "--test" in sys.argv:
        return 0 if test(exe) else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
