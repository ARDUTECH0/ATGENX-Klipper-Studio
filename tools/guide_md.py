# -*- coding: utf-8 -*-
"""Writes docs/GUIDE.md (English) and docs/GUIDE.ar.md (Arabic).

    python tools/guide_md.py

The settings reference comes from studio/help.py - the same text the app shows in its help panel -
so the guide and the app never disagree. Workflows and FAQ are written below.
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from studio import __version__, i18n  # noqa: E402
from studio.features import BUILTIN, CATALOG  # noqa: E402
from studio.help import HELP, PAGE_GUIDE  # noqa: E402
from studio.i18n import tr  # noqa: E402

MOTOR_TITLES = {
    "motor.slot": "motors.col.socket", "motor.driver": "motors.col.driver", "motor.run_current": "motors.col.current",
    "motor.microsteps": "motors.col.microsteps", "motor.rotation_distance": "motors.col.rotation",
    "motor.invert": "motors.col.invert", "motor.stealthchop": "motors.col.stealth", "motor.sensorless": "motors.col.sensorless",
    "motor.hold_current": "motors.hold", "motor.sense_resistor": "motors.sense", "motor.full_steps": "motors.full_steps",
    "motor.interpolate": "motors.interpolate", "motor.sg": "motors.sg", "motor.diag_pin": "motors.diag",
    "motor.z_position": "motors.zpos", "motor.autotune": "motors.autotune", "motor.tuning_goal": "motors.tuning_goal",
    "motor.bus": "uart_pin / tx_pin / uart_address / cs_pin / spi_bus", "keep_inversion": "board.keep_inversion",
    "preview.merge": "preview.merge", "preview.full": "preview.full",
    "host": "connection.host", "board": "board.board", "z_tilt_points": "motors.points", "qgl_corners": "motors.gantry_corners",
    "pid_e_kp": "PID Kp", "pid_e_ki": "PID Ki", "pid_e_kd": "PID Kd", "pid_b_kp": "PID Kp", "pid_b_ki": "PID Ki", "pid_b_kd": "PID Kd",
}

T = {
    "title": ("Klipper Studio - User guide", "Klipper Studio - دليل الاستخدام"),
    "intro": ("This guide explains every page and every setting of Klipper Studio %s, and walks through the most common tasks. "
              "The same explanations appear inside the app in the help panel on the right - point at any setting to read them.",
              "الدليل ده بيشرح كل صفحة وكل إعداد في Klipper Studio %s، وبيمشي معاك خطوة بخطوة في أشهر المهام. "
              "نفس الشرح موجود جوه البرنامج في لوحة الشرح على اليمين - قف بالماوس على أي إعداد عشان تقراه."),
    "toc": ("Contents", "المحتويات"),
    "s_install": ("1. Install and start", "1. التسطيب والتشغيل"),
    "install": ("Install Python 3.9 or newer, then:", "سطّب Python 3.9 أو أحدث، وبعدين:"),
    "install_after": ("On Windows you can double-click `run.bat`. Language: toolbar -> العربية / English.",
                      "على ويندوز تقدر تدوس دبل كليك على `run.bat`. اللغة: من شريط الأدوات -> العربية / English."),
    "s_screen": ("2. The screen", "2. شكل الشاشة"),
    "screen": ([
        "**Sidebar** - the pages, top to bottom in the order you normally use them. A page with problems shows a badge: ✖ errors, ▲ warnings.",
        "**Page** - the settings. Use Next / Back at the bottom, or click any page in the sidebar.",
        "**Help panel** (right) - what the current page is for, and the explanation of the setting under the mouse, including where it goes in printer.cfg. Hide it from the toolbar.",
        "**Toolbar** - new project, open / save a project (.studio.json), open a local printer.cfg, help panel, user guide, language, support, about.",
    ], [
        "**الشريط الجانبي** - الصفحات بالترتيب اللي بتستخدمها بيه عادةً. الصفحة اللي فيها مشاكل بيظهر جنبها علامة: ✖ أخطاء، ▲ تحذيرات.",
        "**الصفحة** - الإعدادات. استخدم التالي / السابق تحت، أو اضغط على أي صفحة في الشريط الجانبي.",
        "**لوحة الشرح** (يمين) - الصفحة دي بتعمل إيه، وشرح الإعداد اللي الماوس واقف عليه، ومكانه في printer.cfg. تقدر تخفيها من شريط الأدوات.",
        "**شريط الأدوات** - مشروع جديد، فتح / حفظ مشروع (.studio.json)، فتح printer.cfg من الجهاز، لوحة الشرح، دليل الاستخدام، اللغة، الدعم، عن البرنامج.",
    ]),
    "s_tasks": ("3. Common tasks", "3. أشهر المهام"),
    "s_pages": ("4. Pages and settings", "4. الصفحات والإعدادات"),
    "col_setting": ("Setting", "الإعداد"), "col_what": ("What it does", "بيعمل إيه"), "col_cfg": ("In printer.cfg", "في printer.cfg"),
    "s_features": ("5. Features and catalog", "5. المميزات والكتالوج"),
    "features_builtin": ("Built-in features (switch on the Features page)", "المميزات الأساسية (مفاتيح في صفحة المميزات)"),
    "features_catalog": ("Catalog - features you can add", "الكتالوج - مميزات تقدر تضيفها"),
    "col_feature": ("Feature", "الميزة"), "col_needs": ("Needs", "محتاج"), "col_section": ("Adds", "بيضيف"),
    "s_file": ("6. How the generated printer.cfg is organized", "6. ترتيب ملف printer.cfg الناتج"),
    "file": ([
        "**Smart merge** (recommended for a working printer) keeps your file: only values that really change are rewritten; comments, order, macros and unknown sections stay. New sections get a one-line explanation.",
        "**Clean new file** writes the sections grouped in this order, each group with a heading and each section with a short explanation: Controller board, Motion limits, Motors and drivers, Hotend/bed/fans, Probe/mesh/Z leveling, Lights, Extras, Print macros. Your other sections follow at the end.",
        "**SAVE_CONFIG** stays at the bottom. Values the app now writes (PID, probe offset, input shaper) are removed from it so the main file wins; bed meshes are kept.",
        "Macros written by the app contain `Klipper Studio` in their description. Remove that word to keep your own edits - the app never replaces a macro without it.",
    ], [
        "**الدمج الذكي** (الأفضل لطابعة شغالة) بيحافظ على ملفك: بيغيّر القيم اللي اتغيرت فعلًا بس، والتعليقات والترتيب والماكروهات والأقسام التانية بتفضل. الأقسام الجديدة بيتحط فوقها سطر شرح.",
        "**الملف الجديد النظيف** بيكتب الأقسام متجمعة بالترتيب ده، وكل مجموعة ليها عنوان وكل قسم فوقه شرح قصير: بوردة التحكم، حدود الحركة، المحركات والدرايفرات، النوزل/القاعدة/المراوح، المسبار/الشبكة/تسوية Z، الإضاءة، الإضافات، ماكروهات الطباعة. وأقسامك التانية بتيجي في الآخر.",
        "**SAVE_CONFIG** بيفضل في آخر الملف. القيم اللي البرنامج بقى بيكتبها (PID، أوفست المسبار، Input Shaper) بتتشال منه عشان الملف الأساسي هو اللي يمشي، وشبكات القاعدة بتفضل.",
        "الماكروهات اللي البرنامج بيكتبها فيها `Klipper Studio` في الوصف. امسح الكلمة دي لو عايز تحتفظ بتعديلاتك - البرنامج عمره ما بيغيّر ماكرو مفيهوش الكلمة دي.",
    ]),
    "s_safety": ("7. Safety and backups", "7. الأمان والنسخ الاحتياطية"),
    "safety": ([
        "Nothing is sent to the printer until you press **Upload and restart** (or **Save to printer** on All config files).",
        "Upload is refused while the printer is printing or paused, and when printer.cfg changed on the printer after you loaded it (for example after SAVE_CONFIG). Load it again first.",
        "Before every upload a backup is saved on the printer in `studio_backups/` and on your computer in `~/.atgenx-studio/backups/`.",
        "After an upload that doesn't start Klipper, press **Restore last backup**.",
    ], [
        "مفيش حاجة بتتبعت للطابعة غير لما تضغط **رفع وإعادة تشغيل** (أو **حفظ على الطابعة** في كل ملفات الإعداد).",
        "الرفع بيترفض والطابعة بتطبع أو متوقفة مؤقتًا، ولو printer.cfg اتغير على الطابعة بعد ما حمّلته (زي بعد SAVE_CONFIG). حمّله تاني الأول.",
        "قبل كل رفع بتتحفظ نسخة احتياطية على الطابعة في `studio_backups/` وعلى جهازك في `~/.atgenx-studio/backups/`.",
        "لو رفعت وكليبر ما اشتغلش، اضغط **استرجاع آخر نسخة احتياطية**.",
    ]),
    "s_faq": ("8. FAQ", "8. أسئلة شائعة"),
}

TASKS = [
    (("Set up a printer that already runs Klipper", "ظبّط طابعة شغالة بكليبر"), [
        ("Start -> **I have a running Klipper printer**.", "البداية -> **عندي طابعة شغالة بكليبر**."),
        ("Type the printer address, press **Test connection**, then **Import from printer**. Every setting and every config file is loaded.",
         "اكتب عنوان الطابعة، واضغط **اختبار الاتصال**، وبعدين **استيراد من الطابعة**. كل الإعدادات وكل ملفات الإعداد بتتحمّل."),
        ("Check **Board** (the detected board is selected) and change what you need on the other pages.",
         "راجع **البورده** (البورده اللي اتعرفت بتبقى مختارة) وغيّر اللي محتاجه في باقي الصفحات."),
        ("Open **Review & upload**: fix every red check (click it to jump to its page), read **Differences**, then **Upload and restart**.",
         "افتح **المراجعة والرفع**: صلّح كل خطأ أحمر (اضغط عليه يوديك لصفحته)، واقرا **الفروق**، وبعدين **رفع وإعادة تشغيل**."),
    ]),
    (("Set up a new printer", "جهّز طابعة جديدة"), [
        ("Start -> **Set up a new printer**, choose your board and press **Apply board pins**.", "البداية -> **تجهيز طابعة جديدة**، اختار البورده واضغط **طبّق أرجل البورده**."),
        ("Untick **Keep my motor directions** for a new printer so the board's default directions are used.", "شيل علامة **احتفظ باتجاهات المحركات** لطابعة جديدة عشان تاخد الاتجاهات الافتراضية."),
        ("Fill **Machine**, **Motors & drivers**, **Hotend & bed**, **Probe** and switch features on in **Features**.", "املا **الماكينة** و**المحركات** و**النوزل والقاعدة** و**المسبار**، وشغّل المميزات من **المميزات**."),
        ("**Review & upload** -> **Save to computer**, or connect and upload.", "**المراجعة والرفع** -> **حفظ على الجهاز**، أو اتصل وارفع."),
        ("On the printer: run `PID_CALIBRATE`, `PROBE_CALIBRATE` and `SHAPER_CALIBRATE`, each followed by `SAVE_CONFIG`. Import again afterwards - the app keeps those values.",
         "على الطابعة: اعمل `PID_CALIBRATE` و `PROBE_CALIBRATE` و `SHAPER_CALIBRATE` وبعد كل واحد `SAVE_CONFIG`. استورد تاني بعدها - البرنامج بيحافظ على القيم دي."),
    ]),
    (("Move a motor to another driver socket / add a second Z motor", "انقل محرك لمخرج تاني / ضيف محرك Z تاني"), [
        ("**Motors & drivers** -> in the motor's row choose another **Driver socket**. All its pins, bus pins and DIAG pin move with it.",
         "**المحركات والدرايفرات** -> في صف المحرك اختار **مخرج درايفر** تاني. كل أرجله وأرجل الاتصال ورجل DIAG بتتنقل معاه."),
        ("**Add motor** -> Z2 (or Z3, Z4, X2, Y2). It takes the next free socket and the settings of the first Z motor.",
         "**إضافة محرك** -> Z2 (أو Z3، Z4، X2، Y2). بياخد أول مخرج فاضي وإعدادات محرك Z الأول."),
        ("With a probe, `z_tilt` is added automatically; choose `quad_gantry_level` for a 4-motor moving gantry. Run `Z_TILT_ADJUST` or `QUAD_GANTRY_LEVEL` after homing.",
         "لو فيه مسبار، `z_tilt` بيتضاف لوحده، واختار `quad_gantry_level` لجسر متحرك بـ 4 محركات. اعمل `Z_TILT_ADJUST` أو `QUAD_GANTRY_LEVEL` بعد التصفير."),
    ]),
    (("Turn on sensorless homing", "فعّل التصفير من غير ليميت"), [
        ("Put the DIAG jumpers for X and Y on the board (see its manual) and unplug the X/Y endstop switches.", "ركّب جمبرات DIAG لـ X و Y على البورده (شوف دليلها) وافصل سويتشات الليميت."),
        ("**Features** -> **Sensorless homing** on (or tick **Sensorless** per motor). Hold current is removed automatically.", "**المميزات** -> شغّل **تصفير من غير ليميت** (أو علّم **من غير ليميت** لكل محرك). تيار الوقوف بيتشال لوحده."),
        ("Upload, then tune: `SET_TMC_FIELD STEPPER=stepper_x FIELD=SGTHRS VALUE=255` and lower it until `G28 X` stops at the end without stopping early. Put the final value in **StallGuard threshold**.",
         "ارفع، وبعدين اضبط: `SET_TMC_FIELD STEPPER=stepper_x FIELD=SGTHRS VALUE=255` وقلّلها لحد ما `G28 X` يقف في الآخر من غير ما يقف بدري. حط القيمة النهائية في **حساسية StallGuard**."),
    ]),
    (("Switch a feature on or off, or add a new one", "شغّل أو اقفل ميزة، أو ضيف ميزة جديدة"), [
        ("**Features -> Built-in**: flip the switch. Whatever it needs is switched on with it (for example adaptive mesh turns on the probe, print macros and exclude object).",
         "**المميزات -> الأساسية**: اقلب المفتاح. اللي الميزة محتاجاه بيتشغّل معاها (زي الشبكة الذكية بتشغّل المسبار وماكروهات الطباعة وإلغاء القطعة)."),
        ("**Features -> In your file**: every other section of printer.cfg. Off comments it out with `#`; on removes the `#` again. Nothing is deleted.",
         "**المميزات -> في ملفك**: كل الأقسام التانية في printer.cfg. الإيقاف بيعمل تعليق بـ `#`، والتشغيل بيشيله. مفيش حاجة بتتمسح."),
        ("**Features -> Add a feature**: press **Add** on a catalog item, edit the template (fill empty pins), then upload. It is added at the end of printer.cfg.",
         "**المميزات -> إضافة ميزة**: اضغط **إضافة** على عنصر من الكتالوج، وعدّل القالب (املا الأرجل الفاضية)، وبعدين ارفع. بيتضاف في آخر printer.cfg."),
    ]),
    (("Edit moonraker.conf, crowsnest.conf or any other file", "عدّل moonraker.conf أو crowsnest.conf أو أي ملف تاني"), [
        ("**All config files** -> **Load all files from printer**.", "**كل ملفات الإعداد** -> **تحميل كل الملفات من الطابعة**."),
        ("Click a file or a section in the tree, edit, then **Save to printer**. A backup is made and only the matching service is restarted.",
         "اضغط على ملف أو قسم في الشجرة، عدّل، وبعدين **حفظ على الطابعة**. بتتعمل نسخة احتياطية وبيتعمل إعادة تشغيل للخدمة المناسبة بس."),
    ]),
    (("Fix a Klipper error", "صلّح خطأ في كليبر"), [
        ("**Troubleshooter** -> **Check printer now** (or paste the error message).", "**حل المشاكل** -> **افحص الطابعة دلوقتي** (أو الصق رسالة الخطأ)."),
        ("Read the cause and the steps, and press **Open the related page** to fix it there.", "اقرا السبب والخطوات، واضغط **افتح الصفحة المتعلقة** عشان تصلحها من هناك."),
    ]),
]

FAQ = [
    (("Is my printer changed when I import?", "هل الطابعة بتتغير لما أعمل استيراد؟"),
     ("No. Importing only reads files. Only Upload / Save to printer write, after a backup.", "لأ. الاستيراد بيقرا بس. الرفع / الحفظ على الطابعة هما بس اللي بيكتبوا، بعد نسخة احتياطية.")),
    (("My board isn't in the list.", "البورده بتاعتي مش في القايمة."),
     ("Choose Custom, type the pins on the Pins page, and please open a board request on GitHub with the pinout.", "اختار «مخصص»، واكتب الأرجل في صفحة الأرجل، ويا ريت تفتح طلب بورده على GitHub ومعاه الـ pinout.")),
    (("Moonraker refuses the connection.", "Moonraker رافض الاتصال."),
     ("Add your computer's network to `trusted_clients` in moonraker.conf, or enter an API key on the Connection page.", "ضيف شبكة جهازك في `trusted_clients` جوه moonraker.conf، أو اكتب مفتاح API في صفحة الاتصال.")),
    (("Why did my SAVE_CONFIG values move into the main file?", "ليه قيم SAVE_CONFIG اتنقلت للملف الأساسي؟"),
     ("Values in the main file are overridden by SAVE_CONFIG. Moving them keeps one source of truth, so what you set in the app really applies. The next SAVE_CONFIG works as usual.",
      "القيم في الملف الأساسي بيغطي عليها SAVE_CONFIG. نقلها بيخلي فيه مصدر واحد، فاللي بتظبطه في البرنامج بيمشي فعلًا. و SAVE_CONFIG الجاي بيشتغل عادي.")),
    (("Does it support delta printers?", "بيدعم طابعات الدلتا؟"),
     ("Not yet. Delta, polar and other machines are never rewritten - the app leaves those files untouched.", "لسه. الدلتا والأنواع التانية عمرها ما بتتعدّل - البرنامج بيسيب الملفات دي زي ما هي.")),
]


def pick(pair, ar):
    return pair[1] if ar else pair[0]


def page_order():
    with io.open(os.path.join(ROOT, "studio", "gui", "pages.py"), encoding="utf-8") as f:
        src = f.read()
    return re.findall(r'\("(nav\.[a-z]+)", "(page_[a-z]+)"\)', src)


def setting_titles():
    """Bound setting -> its label key, read from the GUI source (no Qt import)."""
    titles = {}
    for name in ("pages.py", "motors_page.py"):
        with io.open(os.path.join(ROOT, "studio", "gui", name), encoding="utf-8") as f:
            src = f.read()
        for label, key in re.findall(r'addRow\(tr\("([a-z_.]+)"[^)]*\), self\.(?:spin|combo|line|_multi_line)\("([a-z_0-9]+)"', src):
            titles[key] = label
        for key, label in re.findall(r'self\.check\("([a-z_0-9]+)", tr\("([a-z_.]+)"\)', src):
            titles[key] = label
    titles.update({k: v for k, v in MOTOR_TITLES.items() if v})
    return titles


def cell(text):
    return (text or "").replace("|", "\\|").replace("\n", " ")


def build(lang):
    ar = lang == "ar"
    i18n.set_lang(lang)
    titles = setting_titles()
    out = []
    if ar:
        out.append('<div dir="rtl">\n')
    out += ["# " + pick(T["title"], ar), "", pick(T["intro"], ar) % __version__, "",
            "## " + pick(T["toc"], ar), ""]
    sections = ["s_install", "s_screen", "s_tasks", "s_pages", "s_features", "s_file", "s_safety", "s_faq"]
    for s in sections:
        out.append("- " + pick(T[s], ar))
    out += ["", "## " + pick(T["s_install"], ar), "", pick(T["install"], ar), "", '<div dir="ltr">' if ar else "", "",
            "```bash", "git clone https://github.com/ARDUTECH0/ATGENX-Klipper-Studio.git", "cd ATGENX-Klipper-Studio",
            "pip install -r requirements.txt", "python -m studio" + (" --lang ar" if ar else ""), "```", "",
            "</div>" if ar else "", "", pick(T["install_after"], ar), "",
            "## " + pick(T["s_screen"], ar), ""]
    out += ["- " + line for line in pick(T["screen"], ar)]
    out += ["", "## " + pick(T["s_tasks"], ar), ""]
    for title, steps in TASKS:
        out += ["### " + pick(title, ar), ""]
        out += ["%d. %s" % (i, pick(step, ar)) for i, step in enumerate(steps, 1)]
        out.append("")
    out += ["## " + pick(T["s_pages"], ar), ""]
    for nav_key, builder in page_order():
        name = tr(nav_key).split("   ", 1)[-1].strip()
        out += ["### " + name, ""]
        guide = PAGE_GUIDE.get(builder)
        if guide:
            out += [pick(guide, ar).replace("\n", "  \n"), ""]
        rows = [(k, h) for k, h in HELP.items() if h["page"] == builder]
        if rows:
            out += ["| %s | %s | %s |" % (pick(T["col_setting"], ar), pick(T["col_what"], ar), pick(T["col_cfg"], ar)),
                    "|---|---|---|"]
            for key, h in rows:
                label = tr(titles[key]) if key in titles else key
                cfg = "`%s`" % h["cfg"] if h["cfg"] else ""
                out.append("| **%s** | %s | %s |" % (cell(label), cell(h["ar"] if ar else h["en"]), cell(cfg)))
            out.append("")
    out += ["## " + pick(T["s_features"], ar), "", "### " + pick(T["features_builtin"], ar), "",
            "| %s | %s | %s |" % (pick(T["col_feature"], ar), pick(T["col_what"], ar), pick(T["col_needs"], ar)), "|---|---|---|"]
    for fid, (icon, _cat, _page, plugin, deps) in BUILTIN.items():
        needs = ", ".join([plugin] if plugin else [] + [tr("feat.%s.title" % d) for d in deps])
        out.append("| %s **%s** | %s | %s |" % (icon, cell(tr("feat.%s.title" % fid)), cell(tr("feat.%s.desc" % fid)), cell(needs)))
    out += ["", "### " + pick(T["features_catalog"], ar), "",
            "| %s | %s | %s |" % (pick(T["col_feature"], ar), pick(T["col_what"], ar), pick(T["col_section"], ar)), "|---|---|---|"]
    for cid, (icon, _cat, requires, template) in CATALOG.items():
        secs = " ".join("`[%s]`" % s for s in re.findall(r"^\[([^\]]+)\]", template, re.M))
        what = tr("cat.%s.desc" % cid) + ((" (%s)" % requires) if requires else "")
        out.append("| %s **%s** | %s | %s |" % (icon, cell(tr("cat.%s.title" % cid)), cell(what), secs))
    out += ["", "## " + pick(T["s_file"], ar), ""]
    out += ["- " + line for line in pick(T["file"], ar)]
    out += ["", "## " + pick(T["s_safety"], ar), ""]
    out += ["- " + line for line in pick(T["safety"], ar)]
    out += ["", "## " + pick(T["s_faq"], ar), ""]
    for q, a in FAQ:
        out += ["**%s**  " % pick(q, ar), pick(a, ar), ""]
    if ar:
        out.append("</div>")
    return "\n".join(out).rstrip() + "\n"


def main():
    for lang, name in (("en", "GUIDE.md"), ("ar", "GUIDE.ar.md")):
        path = os.path.join(ROOT, "docs", name)
        with io.open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(build(lang))
        print(path)


if __name__ == "__main__":
    main()
