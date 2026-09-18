# -*- coding: utf-8 -*-
"""Records a demo video of the real app - no screen recorder, no printer needed.

    python tools/demo_video.py             the full demo  -> docs/demo/demo.mp4
    python tools/demo_video.py --gif       also a short loop for the README -> docs/demo/demo.gif
    python tools/demo_video.py --fast      half the frame rate, for checking the script quickly

It drives the actual window offscreen, frame by frame: pages change, values are edited, a switch is
flipped, a device is dragged around the wiring map. A pointer is drawn moving between the things it
"clicks", and a caption bar explains what is happening. ffmpeg turns the frames into an MP4.

The script beats answer the things Klipper users actually complain about: SAVE_CONFIG surprises,
board pins, "Timer too close", and tools that eat your macros.
"""
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("ATGENX_STUDIO_HOME", os.path.join(ROOT, "tests", ".studio_home"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
if os.name == "nt":
    os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")

from PySide6.QtCore import QPoint, QPointF, QRectF, Qt  # noqa: E402
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPainterPath, QPen  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from studio import APP_NAME, REPO_URL, __version__  # noqa: E402
from studio import i18n  # noqa: E402
from studio.boards import apply_board, get_board  # noqa: E402
from studio.gui.app import Studio  # noqa: E402
from studio.gui.files_page import local_configset  # noqa: E402
from studio.gui.style import STYLE  # noqa: E402

W, H = 1600, 900
FPS = 30
OUT = os.path.join(ROOT, "docs", "demo")
FRAMES = os.path.join(ROOT, "build", "demo-frames")
BG, FG, ACCENT = QColor("#0d1117"), QColor("#e6edf3"), QColor("#2f81f7")

# The captions in Arabic, keyed by the English line the script uses (--ar records the Arabic version).
AR = {
    "Set up Klipper without editing printer.cfg by hand": "اضبط كليبر من غير ما تعدّل printer.cfg بإيدك",
    "83 boards  ·  imports what you already have  ·  changes only what you ask":
        "83 بورده · يقرأ ملفك الحالي · ما يغيّرش غير اللي تطلبه",
    "Start from the printer you already have": "ابدأ من الطابعة اللي عندك",
    "Or from nothing at all - it fills in the board's pins for you.":
        "أو من الصفر - هو بيحط pins البورد بدالك.",
    "It reads your real config over Moonraker": "بيقرأ ملف الإعدادات الحقيقي عن طريق Moonraker",
    "Every [include] file and the SAVE_CONFIG block come with it - nothing gets lost.":
        "كل ملفات [include] وقسم SAVE_CONFIG بييجوا معاه - مفيش حاجة بتضيع.",
    "83 boards, with pins taken from Klipper's own board files":
        "83 بورده، والـ pins متاخدة من ملفات كليبر نفسها",
    "It even shows the make menuconfig values for your board.": "وكمان بيوريك قيم make menuconfig لبوردك.",
    "Every motor on its own driver socket": "كل موتور على سوكيت الدرايفر بتاعه",
    "Driver type, current, microsteps, sensorless homing, TMC Autotune - per motor.":
        "نوع الدرايفر، التيار، المايكروستيبس، التوجيه من غير حساسات، وTMC Autotune - لكل موتور.",
    "Switch a feature on - or off": "شغّل أي ميزة - أو اقفلها",
    "Off comments the section out with #. Nothing is ever deleted, not even your own sections.":
        "القفل بيحط # على القسم. مفيش حاجة بتتمسح، ولا حتى الأقسام اللي كتبتها بنفسك.",
    "A wiring map of the machine you just described": "خريطة توصيلات للماكينة اللي لسه واصفها",
    "Each line labelled with its pin. Red means an empty pin, a pin used twice, or a board switched off.":
        "كل سلك مكتوب عليه الـ pin. الأحمر معناه pin فاضي، أو مستخدم مرتين، أو بورده مقفولة.",
    "Drag anything - the wires follow": "اسحب أي حاجة - والأسلاك بتمشي معاها",
    "Arrange it like your printer, export it as a PNG, and it is saved with the project.":
        "رتّبها زي طابعتك، صدّرها صورة PNG، وترتيبك بيتحفظ مع المشروع.",
    "Everything is checked before it leaves your computer": "كل حاجة بتتفحص قبل ما تخرج من جهازك",
    "Pin conflicts, missing pins, TMC bus, mesh area, macros that point at things you removed.":
        "تعارض الـ pins، وpins ناقصة، وباص الـ TMC، ومساحة الميش، وماكروهات بتشاور على حاجات شيلتها.",
    "And it rewrites only the lines that actually change": "وبيعيد كتابة السطور اللي بتتغير بس",
    "Your comments, your macros, your formatting and your SAVE_CONFIG values stay exactly as they are.":
        "تعليقاتك وماكروهاتك وتنسيقك وقيم SAVE_CONFIG بتفضل زي ما هي بالظبط.",
    "When Klipper throws one of its errors, it explains it": "لما كليبر يطلّع خطأ، التطبيق بيشرحهولك",
    "31 common problems - Timer too close, TMC UART, ADC out of range - with the cause and the fix.":
        "31 مشكلة شائعة - Timer too close وTMC UART وADC out of range - بالسبب والحل.",
    "All your config files in one place": "كل ملفات الإعدادات في مكان واحد",
    "moonraker.conf, crowsnest.conf, every include - saved with the right service restart.":
        "moonraker.conf وcrowsnest.conf وكل include - بتتحفظ مع إعادة تشغيل الخدمة الصح.",
    "Uploading is the careful part": "الرفع هو الجزء اللي محتاج حرص",
    "Refused while printing, backed up on the printer and on your PC, FIRMWARE_RESTART, one-click restore.":
        "مرفوض أثناء الطباعة، نسخة احتياطية على الطابعة وعلى جهازك، FIRMWARE_RESTART، واسترجاع بضغطة واحدة.",
    "Tested on a real printer": "مجرّب على طابعة حقيقية",
    "Free software  ·  GPL-3.0": "برنامج حر  ·  GPL-3.0",
    "Windows: download KlipperStudio.exe and double-click": "ويندوز: نزّل KlipperStudio.exe ودوس عليه دبل كليك",
    "English and Arabic": "بالإنجليزي",
}


def ffmpeg():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return ""


def ease(t):
    return t * t * (3 - 2 * t)


class Recorder(object):
    def __init__(self, win, app, fps=FPS):
        self.win, self.app, self.fps = win, app, fps
        self.n = 0
        self.cursor = QPointF(W * 0.5, H * 0.75)
        self.font = QFont("Segoe UI", 15)
        self.big = QFont("Segoe UI", 21, QFont.DemiBold)
        if not os.path.isdir(FRAMES):
            os.makedirs(FRAMES)
        for f in os.listdir(FRAMES):
            os.remove(os.path.join(FRAMES, f))

    # --- helpers the script uses ------------------------------------------------
    def at(self, w, dx=0.5, dy=0.5):
        """A point on a widget, in window coordinates - where the pointer should go."""
        p = w.mapTo(self.win, QPoint(int(w.width() * dx), int(w.height() * dy)))
        return QPointF(p.x(), p.y())

    def nav_at(self, builder):
        row = self.win.page_index(builder)
        r = self.win.nav.visualItemRect(self.win.nav.item(row))
        return self.at(self.win.nav, 0, 0) + QPointF(r.center().x(), r.center().y())

    def sync(self):
        self.app.processEvents()

    def t(self, s):
        return AR.get(s, s) if i18n.is_rtl() else s

    # --- one step of the script -------------------------------------------------
    def step(self, caption, seconds=2.4, do=None, move_to=None, click=False, frame=None, sub=""):
        if do:
            do()
            self.sync()
        total = max(1, int(seconds * self.fps))
        start = QPointF(self.cursor)
        target = move_to if move_to is not None else start
        shot = None if frame else self.win.grab().toImage()
        for i in range(total):
            t = (i + 1) / float(total)
            if frame:
                frame(t)
                self.sync()
                shot = self.win.grab().toImage()
            self.cursor = start + (target - start) * ease(min(1.0, t / 0.55))
            img = shot.copy()
            p = QPainter(img)
            p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
            self._caption(p, caption, sub, min(1.0, t * 5), min(1.0, (1 - t) * 6))
            if click and 0.55 <= t <= 0.85:
                self._ripple(p, (t - 0.55) / 0.30)
            self._cursor(p)
            p.end()
            img.save(os.path.join(FRAMES, "%05d.png" % self.n))
            self.n += 1

    def card(self, title, lines, seconds=3.2, logo=True):
        """A full-screen title or end card."""
        from PySide6.QtGui import QImage
        base = QImage(W, H, QImage.Format_ARGB32)
        base.fill(BG)
        p = QPainter(base)
        p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        y = 330
        if logo:
            icon = QIcon(os.path.join(ROOT, "studio", "assets", "icon.svg"))
            pm = icon.pixmap(150, 150)
            if not pm.isNull():
                p.drawPixmap(int(W / 2 - 75), 235, pm)
                y = 415
        p.setPen(FG)
        p.setFont(QFont("Segoe UI", 44, QFont.DemiBold))
        p.drawText(QRectF(0, y, W, 80), Qt.AlignHCenter | Qt.AlignVCenter, self.t(title))
        p.setFont(QFont("Segoe UI", 19))
        lines = [self.t(x) for x in lines]
        for i, line in enumerate(lines):
            p.setPen(ACCENT if line.startswith("http") or line.startswith("buymeacoffee") else QColor("#9aa7b4"))
            p.drawText(QRectF(0, y + 90 + i * 42, W, 40), Qt.AlignHCenter | Qt.AlignVCenter, line)
        p.end()
        total = int(seconds * self.fps)
        for i in range(total):
            t = (i + 1) / float(total)
            img = base.copy()
            p = QPainter(img)
            a = min(1.0, t * 6) * min(1.0, (1 - t) * 8 + 0.15)
            p.fillRect(img.rect(), QColor(13, 17, 23, int(255 * (1 - min(1.0, a)))))
            p.end()
            img.save(os.path.join(FRAMES, "%05d.png" % self.n))
            self.n += 1

    # --- overlay painting -------------------------------------------------------
    def _caption(self, p, text, sub, fade_in, fade_out):
        if not text:
            return
        text, sub = self.t(text), self.t(sub)
        rtl = i18n.is_rtl()
        align = (Qt.AlignRight if rtl else Qt.AlignLeft) | Qt.AlignVCenter
        a = int(235 * min(fade_in, fade_out))
        h = 104 if sub else 74
        box = QRectF(46, H - h - 46, W - 92, h)
        path = QPainterPath()
        path.addRoundedRect(box, 14, 14)
        p.fillPath(path, QColor(13, 17, 23, int(a * 0.93)))
        p.setPen(QPen(QColor(47, 129, 247, int(a * 0.8)), 3))
        edge = box.right() - 2 if rtl else box.left() + 2
        p.drawLine(edge, box.top() + 12, edge, box.bottom() - 12)
        left, right = (20, -26) if rtl else (26, -20)
        p.setFont(self.big)
        p.setPen(QColor(230, 237, 243, a))
        p.drawText(box.adjusted(left, 8, right, -h / 2 if sub else 0), align, text)
        if sub:
            p.setFont(self.font)
            p.setPen(QColor(154, 167, 180, a))
            p.drawText(box.adjusted(left, h / 2 - 4, right, -8), align, sub)

    def _cursor(self, p):
        x, y = self.cursor.x(), self.cursor.y()
        arrow = QPainterPath()
        arrow.moveTo(x, y)
        arrow.lineTo(x, y + 20)
        arrow.lineTo(x + 5.5, y + 15)
        arrow.lineTo(x + 9, y + 22)
        arrow.lineTo(x + 13, y + 20)
        arrow.lineTo(x + 9.5, y + 13)
        arrow.lineTo(x + 16, y + 12.5)
        arrow.closeSubpath()
        p.setPen(Qt.NoPen)
        p.fillPath(arrow.translated(1.5, 1.5), QColor(0, 0, 0, 120))
        p.fillPath(arrow, QColor("#ffffff"))
        p.setPen(QPen(QColor(20, 24, 30, 200), 1.2))
        p.drawPath(arrow)

    def _ripple(self, p, t):
        r = 8 + 26 * t
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor(47, 129, 247, int(200 * (1 - t))), 3))
        p.drawEllipse(self.cursor, r, r)


def build_scene(win, app):
    """The printer the demo shows: a real config imported from a printer, then changed."""
    fix = os.path.join(ROOT, "tests", "fixtures")
    win.P["host"] = "mainsailos.local"
    with open(os.path.join(fix, "simple_printer.cfg"), encoding="utf-8") as f:
        text = f.read()
    win._load_text(text, "printer.cfg on mainsailos.local")
    win.set_configset(local_configset(os.path.join(fix, "modular")), ("local", "mainsailos.local"))
    app.processEvents()


def script(r, win, app):
    P = win.P
    r.card(APP_NAME, ["Set up Klipper without editing printer.cfg by hand",
                      "83 boards  ·  imports what you already have  ·  changes only what you ask"])

    win.goto_page("page_start")
    r.step("Start from the printer you already have",
           sub="Or from nothing at all - it fills in the board's pins for you.",
           seconds=2.6, move_to=r.nav_at("page_connection"))

    r.step("It reads your real config over Moonraker",
           sub="Every [include] file and the SAVE_CONFIG block come with it - nothing gets lost.",
           seconds=3.0, do=lambda: win.goto_page("page_connection"), move_to=r.nav_at("page_board"), click=True)

    def to_board():
        win.goto_page("page_board")
    r.step("83 boards, with pins taken from Klipper's own board files",
           sub="It even shows the make menuconfig values for your board.",
           seconds=3.0, do=to_board, move_to=r.nav_at("page_motors"), click=True)

    def voron():
        # the app collects widget values whenever the page changes, so: set, refresh, then navigate
        board = get_board("bigtreetech-octopus-v1.1")
        P["kinematics"], P["bed_x"], P["bed_y"] = "corexy", 350.0, 350.0
        P["probe"], P["z_leveling"] = "inductive", "quad_gantry_level"
        for mid in ("z1", "z2", "z3"):
            P["motors"][mid]["enabled"] = True
        apply_board(P, board, keep_inversion=False)
        for mid in ("x", "y"):
            P["motors"][mid].update(run_current=1.4, microsteps=32, sensorless=True, sg=80)
        for mid in ("z", "z1", "z2", "z3"):
            P["motors"][mid].update(run_current=0.8, rotation_distance=40.0)
        win.sel_motor = "x"
        win.refresh()
        app.processEvents()
        win.goto_page("page_motors")
    r.step("Every motor on its own driver socket",
           sub="Driver type, current, microsteps, sensorless homing, TMC Autotune - per motor.",
           seconds=3.4, do=voron, move_to=r.nav_at("page_features"), click=True)

    def features():
        win.goto_page("page_features")
        win.refresh()
    r.step("Switch a feature on - or off",
           sub="Off comments the section out with #. Nothing is ever deleted, not even your own sections.",
           seconds=3.2, do=features, move_to=r.nav_at("page_map"), click=True)

    def to_map():
        P["leds"], P["fil_sensor"] = True, True
        P["pins"].update(probe="^PB7", neopixel="PB0", fil_sensor="^PG12")
        win.refresh()
        app.processEvents()
        win.goto_page("page_map")
        app.processEvents()
        win._map_fit()
    r.step("A wiring map of the machine you just described",
           sub="Each line labelled with its pin. Red means an empty pin, a pin used twice, or a board switched off.",
           seconds=3.2, do=to_map, move_to=QPointF(W * 0.52, H * 0.42))

    node = None
    for it in win.map_scene.items():
        if type(it).__name__ == "NodeItem" and node is None:
            node = it
    if node is not None:
        origin = QPointF(node.pos())
        start_pt = r.at(win.map_view, 0, 0) + QPointF(win.map_view.mapFromScene(node.sceneBoundingRect().center()))
        r.step("", seconds=0.7, move_to=start_pt)

        def drag(t):
            node.setPos(origin + QPointF(120 * ease(min(1.0, t * 1.4)), -90 * ease(min(1.0, t * 1.4))))
            p = r.at(win.map_view, 0, 0) + QPointF(win.map_view.mapFromScene(node.sceneBoundingRect().center()))
            r.cursor = p
        r.step("Drag anything - the wires follow",
               sub="Arrange it like your printer, export it as a PNG, and it is saved with the project.",
               seconds=2.6, frame=drag)

    def review():
        win.goto_page("page_preview")
        win.tabs.setCurrentIndex(0)
        win.do_generate()
    r.step("Everything is checked before it leaves your computer",
           sub="Pin conflicts, missing pins, TMC bus, mesh area, macros that point at things you removed.",
           seconds=3.2, do=review, move_to=r.at(win.tabs, 0.18, 0.02), click=True)

    def diff():
        win.tabs.setCurrentIndex(1)
    r.step("And it rewrites only the lines that actually change",
           sub="Your comments, your macros, your formatting and your SAVE_CONFIG values stay exactly as they are.",
           seconds=3.6, do=diff, move_to=QPointF(W * 0.55, H * 0.45))

    def doctor():
        win._doctor_show("MCU 'mcu' shutdown: Timer too close\n"
                         "Unable to read tmc uart 'stepper_x' register IFCNT", "klippy.log")
        win.goto_page("page_doctor")
    r.step("When Klipper throws one of its errors, it explains it",
           sub="31 common problems - Timer too close, TMC UART, ADC out of range - with the cause and the fix.",
           seconds=3.4, do=doctor, move_to=QPointF(W * 0.45, H * 0.5))

    def files():
        win.goto_page("page_files")
    r.step("All your config files in one place",
           sub="moonraker.conf, crowsnest.conf, every include - saved with the right service restart.",
           seconds=3.0, do=files, move_to=QPointF(W * 0.3, H * 0.4))

    def upload():
        win.goto_page("page_preview")
        win.tabs.setCurrentIndex(0)
    r.step("Uploading is the careful part",
           sub="Refused while printing, backed up on the printer and on your PC, FIRMWARE_RESTART, one-click restore.",
           seconds=3.4, do=upload, move_to=r.at(win.tabs, 0.5, 0.9))

    r.card("Free software  ·  GPL-3.0", [REPO_URL, "Windows: download KlipperStudio.exe and double-click",
                                     "", "%s  ·  %s" % (r.t("Tested on a real printer"), __version__)], logo=True, seconds=4.0)


def encode(gif=False, fps=FPS, suffix=""):
    exe = ffmpeg()
    if not exe:
        print("ffmpeg not found - frames are in %s" % FRAMES)
        return 1
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    mp4 = os.path.join(OUT, "demo%s.mp4" % suffix)
    subprocess.run([exe, "-y", "-loglevel", "error", "-framerate", str(fps), "-i",
                    os.path.join(FRAMES, "%05d.png"), "-c:v", "libx264", "-preset", "slow", "-crf", "20",
                    "-pix_fmt", "yuv420p", "-movflags", "+faststart", mp4], check=True)
    print("%s  (%.1f MB)" % (mp4, os.path.getsize(mp4) / 1024 / 1024))
    if gif:
        pal = os.path.join(FRAMES, "palette.png")
        vf = "fps=12,scale=900:-1:flags=lanczos"
        subprocess.run([exe, "-y", "-loglevel", "error", "-i", mp4, "-vf", vf + ",palettegen", pal], check=True)
        out = os.path.join(OUT, "demo%s.gif" % suffix)
        subprocess.run([exe, "-y", "-loglevel", "error", "-i", mp4, "-i", pal,
                        "-lavfi", vf + " [x]; [x][1:v] paletteuse", out], check=True)
        print("%s  (%.1f MB)" % (out, os.path.getsize(out) / 1024 / 1024))
    return 0


def main():
    fast = "--fast" in sys.argv
    fps = 15 if fast else FPS
    i18n.set_lang("ar" if "--ar" in sys.argv else "en")
    app = QApplication.instance() or QApplication(sys.argv)
    app.setLayoutDirection(Qt.RightToLeft if i18n.is_rtl() else Qt.LeftToRight)
    app.setStyleSheet(STYLE)
    win = Studio()
    win.resize(W, H)
    build_scene(win, app)
    win.show()
    app.processEvents()
    r = Recorder(win, app, fps)
    script(r, win, app)
    win.close()
    print("%d frames  (%.1f s)" % (r.n, r.n / float(fps)))
    return encode("--gif" in sys.argv, fps, "-ar" if i18n.is_rtl() else "")


if __name__ == "__main__":
    sys.exit(main())
