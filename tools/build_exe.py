# -*- coding: utf-8 -*-
"""Builds a single-file executable (no Python needed by the user).

    python tools/build_exe.py            build for the current platform
    python tools/build_exe.py --test     build, then start it with --smoke and check it works

Result: dist/KlipperStudio.exe (Windows) or dist/KlipperStudio (Linux/macOS), next to a
.sha256 file users can check the download against.
Everything the app needs is bundled: the 83 board files, the icons and the TMC motor list.
On Windows the file gets proper properties (right-click -> Properties -> Details): name,
version, author and license, so it does not look like an anonymous binary.
"""
import hashlib
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from studio import APP_NAME, LICENSE_NAME, REPO_URL, __version__  # noqa: E402

NAME = "KlipperStudio"
ENTRY = os.path.join(ROOT, "tools", "_entry.py")
VERSION_RC = os.path.join(ROOT, "build", "version_info.txt")
SEP = ";" if os.name == "nt" else ":"


def write_entry():
    with open(ENTRY, "w", encoding="utf-8") as f:
        f.write("# -*- coding: utf-8 -*-\n"
                "import sys\n\n"
                "from studio.cli import main\n\n"
                "sys.exit(main())\n")


def file_version():
    """1.0.0-beta.4 -> (1, 0, 0, 4)  - Windows wants four plain numbers."""
    nums = [int(n) for n in re.findall(r"\d+", __version__)]
    return tuple((nums + [0, 0, 0, 0])[:4])


def write_version_info():
    """Windows file properties, so the exe shows who made it and which version it is."""
    v = file_version()
    fields = [("CompanyName", "ATGENX"), ("FileDescription", APP_NAME),
              ("FileVersion", __version__), ("InternalName", NAME),
              ("LegalCopyright", "seifemad - %s" % LICENSE_NAME),
              ("OriginalFilename", NAME + ".exe"), ("ProductName", APP_NAME),
              ("ProductVersion", __version__), ("Comments", REPO_URL)]
    text = ("VSVersionInfo(\n"
            "  ffi=FixedFileInfo(filevers=%r, prodvers=%r, mask=0x3f, flags=0x0,\n"
            "                    OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),\n"
            "  kids=[StringFileInfo([StringTable('040904B0', [\n%s\n  ])]),\n"
            "        VarFileInfo([VarStruct('Translation', [1033, 1200])])]\n)\n"
            % (v, v, "\n".join("    StringStruct(%r, %r)," % f for f in fields)))
    if not os.path.isdir(os.path.dirname(VERSION_RC)):
        os.makedirs(os.path.dirname(VERSION_RC))
    with open(VERSION_RC, "w", encoding="utf-8") as f:
        f.write(text)
    return VERSION_RC


def write_checksum(exe):
    h = hashlib.sha256()
    with open(exe, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    path = exe + ".sha256"
    with open(path, "w", encoding="utf-8") as f:
        f.write("%s  %s\n" % (h.hexdigest(), os.path.basename(exe)))
    print("sha256  %s" % h.hexdigest())
    return path


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
    if os.name == "nt":
        cmd[-1:-1] = ["--version-file", write_version_info()]
    print("building %s %s ..." % (APP_NAME, __version__))
    subprocess.run(cmd, check=True, cwd=ROOT)
    os.remove(ENTRY)
    exe = os.path.join(ROOT, "dist", NAME + (".exe" if os.name == "nt" else ""))
    print("\n%s  (%.1f MB)" % (exe, os.path.getsize(exe) / 1024 / 1024))
    write_checksum(exe)
    return exe


def test(exe):
    """Start the built app in offscreen mode and check that it opens every page."""
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
    env.pop("ATGENX_STUDIO_HOME", None)
    ok = True
    for args, what in (([exe, "--smoke"], "the app starts and builds every page"),
                       ([exe, "boards"], "the bundled board files are found"),
                       ([exe, "--version"], "it answers with its version"),
                       ([exe, "check", os.path.join(ROOT, "tests", "fixtures", "simple_printer.cfg")],
                        "import / merge / validate work")):
        r = subprocess.run(args, env=env, capture_output=True, timeout=300)
        good = r.returncode == 0
        ok = ok and good
        print("%s  %s" % ("PASS" if good else "FAIL", what))
        if not good:
            print((r.stdout + r.stderr).decode("utf-8", "replace")[-1500:])
    if os.name == "nt":
        ok = check_properties(exe) and ok
    return ok


def check_properties(exe):
    """Windows only: the file properties really carry the name and version."""
    ps = ("$i = (Get-Item '%s').VersionInfo; "
          "Write-Output \"$($i.ProductName)|$($i.ProductVersion)|$($i.CompanyName)\"" % exe)
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, timeout=120)
    got = r.stdout.decode("utf-8", "replace").strip()
    want = "%s|%s|ATGENX" % (APP_NAME, __version__)
    good = got == want
    print("%s  the file properties say %s" % ("PASS" if good else "FAIL", want))
    if not good:
        print("   properties are: %s" % (got or "(none)"))
    return good


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
