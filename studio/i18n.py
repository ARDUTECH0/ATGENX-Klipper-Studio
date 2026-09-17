# -*- coding: utf-8 -*-
"""Translations. Add a language by adding a column to every entry (see CONTRIBUTING.md)."""
import locale
import os

LANGS = ("en", "ar")
RTL = {"ar"}
_lang = "en"


def set_lang(lang):
    global _lang
    _lang = lang if lang in LANGS else "en"


def get_lang():
    return _lang


def is_rtl():
    return _lang in RTL


def system_lang():
    env = os.environ.get("ATGENX_STUDIO_LANG")
    if env:
        return env
    try:
        loc = (locale.getlocale()[0] or "").lower()
    except ValueError:
        loc = ""
    return "ar" if loc.startswith("ar") or "arabic" in loc else "en"


def tr(key, /, **kw):
    entry = STRINGS.get(key)
    if entry is None:
        return key
    text = entry.get(_lang) or entry["en"]
    try:
        return text.format(**kw) if kw else text
    except (KeyError, IndexError, ValueError):
        return text


def _t(en, ar):
    return {"en": en, "ar": ar}


STRINGS = {
    # ---------- app ----------
    "app.tagline": _t("Klipper configuration, done right", "إعداد كليبر باحتراف"),
    "app.ready": _t("Ready", "جاهز"),
    "nav.connection": _t("🔌   Connection", "🔌   الاتصال"),
    "nav.board": _t("🧩   Board", "🧩   البورده"),
    "nav.machine": _t("📐   Machine", "📐   الماكينة"),
    "nav.motors": _t("⚙️   Motors & drivers", "⚙️   المحركات والدرايفرات"),
    "nav.thermal": _t("🔥   Hotend & bed", "🔥   النوزل والقاعدة"),
    "nav.probe": _t("🎯   Probe & leveling", "🎯   المسبار والتسوية"),
    "nav.extras": _t("💡   LEDs & extras", "💡   الإضاءة والإضافات"),
    "nav.pins": _t("📌   Pins", "📌   الأرجل (Pins)"),
    "nav.preview": _t("🚀   Review & upload", "🚀   المراجعة والرفع"),
    "nav.prev": _t("Back", "السابق"),
    "nav.next": _t("Next", "التالي"),
    "tb.new": _t("New", "جديد"),
    "tb.open_project": _t("Open project", "فتح مشروع"),
    "tb.save_project": _t("Save project", "حفظ مشروع"),
    "tb.open_cfg": _t("Open local printer.cfg", "فتح printer.cfg من الجهاز"),
    "tb.language": _t("العربية", "English"),
    "tb.about": _t("About", "عن البرنامج"),
    "about.text": _t(
        "<h3>{app} {ver}</h3>"
        "<p>A guided printer.cfg builder for Klipper printers.</p>"
        "<p>License: <b>{license}</b><br>Free for personal, educational and other noncommercial use. "
        "Selling it or using it commercially is not allowed.</p>"
        "<p><a href='{repo}'>Source code</a> &nbsp;·&nbsp; <a href='{support}'>Support the project</a></p>"
        "<p style='color:#8b949e'>Board pin data is derived from Klipper's config files. "
        "Klipper is a separate project by Kevin O'Connor and contributors.</p>",
        "<h3>{app} {ver}</h3>"
        "<p>برنامج بيساعدك تبني printer.cfg لطابعات كليبر خطوة بخطوة.</p>"
        "<p>الترخيص: <b>{license}</b><br>مجاني للاستخدام الشخصي والتعليمي وأي استخدام غير تجاري. "
        "ممنوع بيعه أو استخدامه تجاريًا.</p>"
        "<p><a href='{repo}'>الكود المصدري</a> &nbsp;·&nbsp; <a href='{support}'>ادعم المشروع</a></p>"
        "<p style='color:#8b949e'>بيانات أرجل البوردات مأخوذة من ملفات إعداد كليبر. "
        "كليبر مشروع منفصل لـ Kevin O'Connor والمساهمين.</p>"),

    "conn.offline": _t("Not connected", "غير متصل"),
    "conn.connected": _t("Connected  -  {state}", "متصل  -  {state}"),
    "state.printing": _t("printing", "بتطبع"),
    "state.paused": _t("paused", "متوقفة مؤقتًا"),

    # ---------- connection ----------
    "connection.title": _t("Connect to the printer", "الاتصال بالطابعة"),
    "connection.hint": _t(
        "The app talks to Moonraker directly - no SSH and no passwords. Start with "
        "“Import from printer” so every field is filled with your current settings.",
        "البرنامج بيتكلم مع Moonraker مباشرة - مفيش SSH ولا باسوردات. ابدأ بـ "
        "«استيراد من الطابعة» عشان كل الخانات تتملى بإعداداتك الحالية."),
    "connection.host": _t("Printer address", "عنوان الطابعة"),
    "connection.port": _t("Port", "المنفذ"),
    "connection.api_key": _t("API key", "مفتاح API"),
    "connection.api_key_hint": _t("Only if Moonraker requires it (not saved)", "بس لو Moonraker طالبه (مش بيتحفظ)"),
    "connection.test": _t("Test connection", "اختبار الاتصال"),
    "connection.import": _t("Import from printer", "استيراد من الطابعة"),
    "connection.project": _t("Project", "المشروع"),
    "connection.printer_name": _t("Printer name", "اسم الطابعة"),

    # ---------- board ----------
    "board.title": _t("Controller board", "بوردة التحكم"),
    "board.hint": _t(
        "Pick your board to fill every pin automatically. The list comes from Klipper's official board files. "
        "Your board isn't listed? Choose “Custom” and type the pins on the Pins page, then share it with the project.",
        "اختار البورده بتاعتك وكل الأرجل هتتملى لوحدها. القايمة مأخوذة من ملفات كليبر الرسمية. "
        "البورده بتاعتك مش موجودة؟ اختار «مخصص» واكتب الأرجل في صفحة الأرجل، وشاركها مع المشروع."),
    "board.group": _t("Board", "البورده"),
    "board.board": _t("Board", "البورده"),
    "board.custom": _t("Custom / not listed", "مخصص / مش موجودة"),
    "board.custom_info": _t("No board selected - pins are taken from the Pins page as they are.",
                            "مفيش بورده مختارة - الأرجل بتتاخد من صفحة الأرجل زي ما هي."),
    "board.z1_slot": _t("Driver used for Z2 (dual Z)", "الدرايفر المستخدم لـ Z التاني"),
    "board.keep_inversion": _t("Keep my motor directions (recommended when importing)",
                               "احتفظ باتجاهات المحركات الحالية (مفضل بعد الاستيراد)"),
    "board.extras": _t("Add the sections this board requires (USB pull-up, digipots, ...)",
                       "ضيف الأقسام اللي البورده محتاجاها (USB pull-up، مقاومات رقمية، ...)"),
    "board.apply": _t("Apply board pins", "طبّق أرجل البورده"),
    "board.driver_slots": _t("Driver slots", "مخارج الدرايفرات"),
    "board.required_sections": _t("Required sections", "أقسام مطلوبة"),
    "board.source_link": _t("Klipper board file", "ملف البورده في كليبر"),
    "board.flash_link": _t("How to build and flash", "إزاي تبني وتحرق الفيرموير"),
    "board.serial_group": _t("MCU connection", "اتصال البورده"),
    "board.serial": _t("Serial", "السيريال"),
    "board.detect_serial": _t("Detect on printer", "اكتشاف من الطابعة"),
    "board.serial_hint": _t(
        "Use the /dev/serial/by-id/... path. For CAN boards type:  canbus_uuid: <uuid>",
        "استخدم المسار /dev/serial/by-id/... . لبوردات CAN اكتب:  canbus_uuid: <uuid>"),

    # ---------- machine ----------
    "machine.title": _t("Machine", "الماكينة"),
    "machine.hint": _t("Build volume and motion limits. All distances are in millimetres.",
                       "مساحة الطباعة وحدود الحركة. كل المسافات بالمليمتر."),
    "machine.volume": _t("Build volume", "مساحة الطباعة"),
    "machine.kinematics": _t("Kinematics", "نوع الحركة"),
    "kin.cartesian": _t("Cartesian (bed slinger / i3)", "Cartesian (قاعدة متحركة)"),
    "kin.corexy": _t("CoreXY", "CoreXY"),
    "machine.bed_x": _t("X size", "عرض X"),
    "machine.bed_y": _t("Y size", "عمق Y"),
    "machine.bed_z": _t("Max Z height", "أقصى ارتفاع Z"),
    "machine.x_min": _t("X minimum", "أقل X"),
    "machine.y_min": _t("Y minimum", "أقل Y"),
    "machine.z_min": _t("Z minimum", "أقل Z"),
    "machine.x_endstop": _t("X endstop position", "مكان ليميت X"),
    "machine.y_endstop": _t("Y endstop position", "مكان ليميت Y"),
    "machine.limits": _t("Speed and acceleration", "السرعات والتسارع"),
    "machine.max_velocity": _t("Max velocity", "أقصى سرعة"),
    "machine.max_accel": _t("Max acceleration", "أقصى تسارع"),
    "machine.max_z_velocity": _t("Max Z velocity", "أقصى سرعة Z"),
    "machine.max_z_accel": _t("Max Z acceleration", "أقصى تسارع Z"),
    "machine.scv": _t("Square corner velocity", "سرعة الأركان"),
    "machine.homing_speed": _t("Homing speed", "سرعة التصفير"),

    # ---------- motors ----------
    "motors.title": _t("Motors & drivers", "المحركات والدرايفرات"),
    "motors.hint": _t("If an axis moves the wrong way, tick its “invert direction” box.",
                      "لو محور بيتحرك بالعكس، علّم على «عكس الاتجاه» بتاعه."),
    "motors.mechanics": _t("Mechanics", "الميكانيكا"),
    "motors.microsteps": _t("Microsteps", "المايكروستب"),
    "motors.rd_xy": _t("X/Y rotation_distance", "rotation_distance لـ X/Y"),
    "motors.rd_z": _t("Z rotation_distance", "rotation_distance لـ Z"),
    "motors.inv_x": _t("Invert X direction", "عكس اتجاه X"),
    "motors.inv_y": _t("Invert Y direction", "عكس اتجاه Y"),
    "motors.inv_z": _t("Invert Z direction (both Z motors)", "عكس اتجاه Z (المحركين)"),
    "motors.inv_e": _t("Invert extruder direction", "عكس اتجاه الإكسترودر"),
    "motors.dual_z": _t("Dual Z", "دبل Z"),
    "motors.dual_z_on": _t("Two Z motors on separate drivers (Z + Z1) with z_tilt",
                           "محركين Z على درايفرين منفصلين (Z + Z1) مع z_tilt"),
    "motors.z_tilt_swap": _t("First Z motor is on the right (flip this if Z_TILT_ADJUST makes the tilt worse)",
                             "محرك Z الأول على اليمين (اعكسها لو Z_TILT_ADJUST بيزوّد الميل)"),
    "motors.drivers": _t("Drivers", "الدرايفرات"),
    "motors.driver": _t("Driver type", "نوع الدرايفر"),
    "driver.none": _t("Standalone (A4988 / DRV8825 / no UART-SPI)", "عادي (A4988 / DRV8825 / من غير UART-SPI)"),
    "motors.cur_xy": _t("X/Y run current", "تيار X/Y"),
    "motors.cur_z": _t("Z run current", "تيار Z"),
    "motors.cur_e": _t("Extruder run current", "تيار الإكسترودر"),
    "motors.hold_ratio": _t("Hold current ratio (1 = same as run)", "نسبة تيار الوقوف (1 = نفس تيار الحركة)"),
    "motors.stealth_xy": _t("X/Y stealthChop threshold (0 = off)", "عتبة الوضع الصامت X/Y (0 = مقفول)"),
    "motors.stealth_z": _t("Z stealthChop threshold", "عتبة الوضع الصامت Z"),
    "motors.stealth_e": _t("Extruder stealthChop threshold", "عتبة الوضع الصامت E"),

    # ---------- thermal ----------
    "thermal.title": _t("Hotend & bed", "النوزل والقاعدة"),
    "thermal.hint": _t("Get PID values from PID_CALIBRATE on your own machine - don't copy them from another printer.",
                       "قيم PID الصح بتيجي من PID_CALIBRATE على طابعتك - متنقلهاش من طابعة تانية."),
    "thermal.extruder": _t("Extruder", "الإكسترودر"),
    "thermal.rd_e": _t("rotation_distance", "rotation_distance"),
    "thermal.nozzle": _t("Nozzle diameter", "قطر النوزل"),
    "thermal.filament": _t("Filament diameter", "قطر الفيلامنت"),
    "thermal.bowden": _t("Bowden (not direct drive)", "بودن (مش دايركت درايف)"),
    "thermal.pa": _t("Pressure advance", "Pressure advance"),
    "thermal.pa_smooth": _t("Pressure advance smooth time", "زمن تنعيم Pressure advance"),
    "thermal.heat": _t("Heating", "التسخين"),
    "thermal.therm_e": _t("Hotend thermistor", "ثرمستور النوزل"),
    "thermal.max_temp_e": _t("Hotend max temperature", "أقصى حرارة للنوزل"),
    "thermal.therm_bed": _t("Bed thermistor", "ثرمستور القاعدة"),
    "thermal.max_temp_bed": _t("Bed max temperature", "أقصى حرارة للقاعدة"),
    "thermal.cool_room": _t("Cold room / strong part fan - relaxed heater verification",
                            "أوضة باردة / مروحة قوية - حماية حرارية أوسع"),
    "thermal.fans": _t("Fans", "المراوح"),
    "thermal.fan_max": _t("Part fan max power", "أقصى قوة لمروحة القطعة"),
    "thermal.hotend_fan_temp": _t("Hotend fan turns on at", "مروحة الهيت سنك تشتغل عند"),

    # ---------- probe ----------
    "probe.title": _t("Probe & leveling", "المسبار والتسوية"),
    "probe.hint": _t("The mesh area and z_tilt points are calculated so the probe can actually reach them.",
                     "منطقة الشبكة ونقط z_tilt بتتحسب لوحدها بحيث المسبار يوصلها فعلًا."),
    "probe.probe": _t("Probe", "المسبار"),
    "probe.type": _t("Type", "النوع"),
    "probe.inductive": _t("Inductive / switch probe", "بروكسيمتي / سويتش"),
    "probe.bltouch": _t("BLTouch / CR Touch", "BLTouch / CR Touch"),
    "probe.none": _t("No probe (Z endstop)", "من غير مسبار (ليميت Z)"),
    "probe.x": _t("X offset", "إزاحة X"),
    "probe.y": _t("Y offset", "إزاحة Y"),
    "probe.z": _t("Z offset", "أوفست Z"),
    "probe.samples": _t("Samples per point", "عدد القياسات لكل نقطة"),
    "probe.mesh": _t("Bed mesh", "شبكة القاعدة"),
    "probe.margin": _t("Margin from the edges", "الهامش من الحواف"),
    "probe.count": _t("Points per axis", "عدد النقط لكل محور"),
    "probe.area": _t("Calculated area", "المنطقة المحسوبة"),

    # ---------- extras ----------
    "extras.title": _t("LEDs & extras", "الإضاءة والإضافات"),
    "extras.hint": _t("LED effects need the klipper-led_effect plugin installed on the printer.",
                      "تأثيرات الإضاءة محتاجة إضافة klipper-led_effect متسطبة على الطابعة."),
    "extras.leds": _t("LED strip", "شريط الإضاءة"),
    "extras.leds_on": _t("NeoPixel / WS2812 strip installed", "فيه شريط NeoPixel / WS2812"),
    "extras.led_count": _t("LED count", "عدد اللمبات"),
    "extras.led_order": _t("Color order", "ترتيب الألوان"),
    "extras.led_effects": _t("Live indicators (fill with temperature and print progress)",
                             "مؤشرات حية (الشريط يمتلي مع الحرارة وتقدم الطبعة)"),
    "extras.shaper": _t("Input shaper", "Input Shaper"),
    "extras.shaper_on": _t("Enabled", "مفعّل"),
    "extras.freq": _t("{axis} frequency", "تردد {axis}"),
    "extras.type": _t("{axis} type", "نوع {axis}"),
    "extras.freq_z": _t("Z frequency (0 = off)", "تردد Z  (0 = مقفول)"),
    "extras.damping": _t("Damping ratio", "نسبة التخميد"),
    "extras.more": _t("Extras", "إضافات"),
    "extras.fil_sensor": _t("Filament runout sensor (pauses the print)", "حساس خلصان الفيلامنت (بيوقف الطبعة مؤقتًا)"),
    "extras.arcs": _t("Arc support G2/G3", "دعم الأقواس G2/G3"),
    "extras.exclude_object": _t("Cancel single objects during a print", "إلغاء قطعة واحدة أثناء الطباعة"),

    # ---------- pins ----------
    "pins.title": _t("Pins", "أرجل البورده"),
    "pins.hint": _t(
        "Filled from the board page - edit any pin by hand. Write direction pins without “!”: "
        "inversion is set on the Motors page. Prefixes: ^ pull-up, ~ pull-down, ! inverted.",
        "بتتملى من صفحة البورده - وتقدر تعدّل أي رجل بإيدك. اكتب أرجل الاتجاه من غير «!»: "
        "العكس بيتحدد من صفحة المحركات. الرموز: ^ pull-up · ~ pull-down · ! عكس."),
    "pins.role": _t("Function", "الوظيفة"),
    "pins.pin": _t("Pin", "الرجل"),
    "pin.x_step": _t("X step", "X خطوة"),
    "pin.x_dir": _t("X dir", "X اتجاه"),
    "pin.x_en": _t("X enable", "X تفعيل"),
    "pin.x_stop": _t("X endstop", "X ليميت"),
    "pin.y_step": _t("Y step", "Y خطوة"),
    "pin.y_dir": _t("Y dir", "Y اتجاه"),
    "pin.y_en": _t("Y enable", "Y تفعيل"),
    "pin.y_stop": _t("Y endstop", "Y ليميت"),
    "pin.z_step": _t("Z step", "Z خطوة"),
    "pin.z_dir": _t("Z dir", "Z اتجاه"),
    "pin.z_en": _t("Z enable", "Z تفعيل"),
    "pin.z_stop": _t("Z endstop (no probe)", "Z ليميت (من غير مسبار)"),
    "pin.z1_step": _t("Z2 step", "Z2 خطوة"),
    "pin.z1_dir": _t("Z2 dir", "Z2 اتجاه"),
    "pin.z1_en": _t("Z2 enable", "Z2 تفعيل"),
    "pin.e_step": _t("Extruder step", "الإكسترودر خطوة"),
    "pin.e_dir": _t("Extruder dir", "الإكسترودر اتجاه"),
    "pin.e_en": _t("Extruder enable", "الإكسترودر تفعيل"),
    "pin.e_heater": _t("Hotend heater", "سخان النوزل"),
    "pin.e_sensor": _t("Hotend thermistor", "ثرمستور النوزل"),
    "pin.bed_heater": _t("Bed heater", "سخان القاعدة"),
    "pin.bed_sensor": _t("Bed thermistor", "ثرمستور القاعدة"),
    "pin.fan": _t("Part cooling fan", "مروحة تبريد القطعة"),
    "pin.hotend_fan": _t("Hotend (heatsink) fan", "مروحة الهيت سنك"),
    "pin.probe": _t("Probe", "المسبار"),
    "pin.bl_sensor": _t("BLTouch sensor", "BLTouch حساس"),
    "pin.bl_control": _t("BLTouch control", "BLTouch تحكم"),
    "pin.neopixel": _t("LED strip data", "داتا شريط الإضاءة"),
    "pin.fil_sensor": _t("Filament sensor", "حساس الفيلامنت"),

    # ---------- preview ----------
    "preview.title": _t("Review & upload", "المراجعة والرفع"),
    "preview.hint": _t(
        "Check the result, the differences and the checks. Uploading makes a backup first and refuses "
        "while the printer is printing or if the file changed on the printer.",
        "راجع الملف والفروق ونتيجة الفحص. الرفع بيعمل نسخة احتياطية الأول، "
        "وبيرفض لو الطابعة بتطبع أو الملف اتغير عليها."),
    "preview.merge": _t("Smart merge - keeps your order, comments and macros",
                        "دمج ذكي - بيحافظ على ترتيبك وتعليقاتك وماكروهاتك"),
    "preview.full": _t("Clean new file", "ملف جديد نظيف"),
    "preview.keep_custom": _t("Keep macros and other sections", "احتفظ بالماكروهات والأقسام التانية"),
    "preview.checks": _t("Checks", "الفحص"),
    "preview.checks_errors": _t("Checks  ({count} errors)", "الفحص  ({count} خطأ)"),
    "preview.diff": _t("Differences", "الفروق"),
    "preview.output": _t("Result", "الملف الناتج"),
    "preview.log": _t("Log", "السجل"),
    "preview.download": _t("Download from printer", "تحميل من الطابعة"),
    "preview.save_local": _t("Save to computer", "حفظ على الجهاز"),
    "preview.upload": _t("Upload and restart", "رفع وإعادة تشغيل"),
    "preview.restore": _t("Restore last backup", "استرجاع آخر نسخة احتياطية"),
    "preview.gen_error": _t("Generation error: {err}", "خطأ في التوليد: {err}"),
    "preview.current": _t("current", "الحالي"),
    "preview.new": _t("new", "الجديد"),
    "preview.no_diff": _t("No differences from the current file", "مفيش أي فرق عن الملف الحالي"),
    "preview.based_on": _t("Based on: {src}", "مبني على: {src}"),
    "preview.no_current": _t("No current file - download from the printer to see differences and merge",
                             "مفيش ملف حالي - حمّل من الطابعة عشان تشوف الفروق وتدمج"),
    "preview.no_current_full": _t("No current file - a complete new file will be generated (without your macros)",
                                  "مفيش ملف حالي - هيتولّد ملف كامل جديد (من غير ماكروهاتك)"),

    # ---------- messages ----------
    "msg.busy": _t("Another operation is running - please wait", "فيه عملية شغالة - استنى تخلص"),
    "msg.confirm_new": _t("Reset every field to the defaults?", "ترجّع كل الخانات للقيم الافتراضية؟"),
    "msg.project_opened": _t("Project opened: {name}", "اتفتح المشروع: {name}"),
    "msg.project_open_failed": _t("Could not open the project:\n{err}", "مقدرتش أفتح المشروع:\n{err}"),
    "msg.project_saved": _t("Project saved: {name}", "اتحفظ المشروع: {name}"),
    "msg.local_file": _t("{name} (local file)", "{name} (ملف على الجهاز)"),
    "msg.printer_file": _t("printer.cfg on {host}", "printer.cfg على {host}"),
    "msg.loaded": _t("Loaded {src}  -  {lines} lines", "اتقرا {src}  -  {lines} سطر"),
    "msg.connecting": _t("Connecting to {url} ...", "بيتصل بـ {url} ..."),
    "msg.connected": _t("Connected", "متصل"),
    "msg.boards_for_mcu": _t("{count} boards in the list use this MCU:", "{count} بورده في القايمة بتستخدم نفس المعالج:"),
    "msg.download_failed": _t("Could not download the file:\n{err}", "مقدرتش أحمّل الملف:\n{err}"),
    "msg.imported": _t("printer.cfg was downloaded and every field now shows your current settings.",
                       "اتحمّل printer.cfg وكل الخانات دلوقتي فيها إعداداتك الحالية."),
    "msg.import_failed": _t("Could not read the file:\n{err}", "مقدرتش أقرا الملف:\n{err}"),
    "msg.no_serial": _t("No serial devices found on the printer host.", "مفيش أجهزة سيريال على الطابعة."),
    "msg.serial_found": _t("{count} serial devices found", "اتلقى {count} جهاز سيريال"),
    "msg.choose_board": _t("Choose a board from the list first.", "اختار بورده من القايمة الأول."),
    "msg.board_applied": _t("Pins applied from: {name}", "اتطبقت أرجل: {name}"),
    "msg.saved": _t("Saved: {path}", "اتحفظ: {path}"),
    "msg.fix_errors": _t("Fix these errors before uploading:", "فيه أخطاء لازم تتصلح قبل الرفع:"),
    "msg.no_current_upload": _t(
        "No file was downloaded from the printer.\nUploading will REPLACE printer.cfg with a new file "
        "and your macros will be lost.\n\nContinue?",
        "مفيش ملف متحمّل من الطابعة.\nالرفع هيستبدل printer.cfg بملف جديد وكل الماكروهات هتضيع.\n\nمتأكد؟"),
    "msg.upload_steps": _t(
        "This will:\n\n1. make sure the printer is not printing\n2. make sure printer.cfg did not change on the printer\n"
        "3. back up the current file on the printer and on this computer\n4. upload the new printer.cfg\n5. FIRMWARE_RESTART",
        "هيحصل الآتي:\n\n1. التأكد إن الطابعة مش بتطبع\n2. التأكد إن printer.cfg ما اتغيرش على الطابعة\n"
        "3. نسخة احتياطية على الطابعة وعلى الجهاز\n4. رفع printer.cfg الجديد\n5. FIRMWARE_RESTART"),
    "msg.warnings": _t("Warnings:", "تحذيرات:"),
    "msg.upload_ok": _t("✔ Uploaded - Klipper is ready.", "✔ اترفع - كليبر جاهز."),
    "msg.upload_not_ready": _t("Klipper did not start correctly ({state}):\n\n{msg}\n\nUse “Restore last backup” to go back.",
                               "كليبر ما قامش صح ({state}):\n\n{msg}\n\nاستخدم «استرجاع آخر نسخة احتياطية» عشان ترجع."),
    "msg.confirm_restore": _t("Restore printer.cfg from {name} and restart?", "ترجّع printer.cfg من {name} وتعيد التشغيل؟"),
    "msg.restored": _t("Backup {name} restored - Klipper: {state}", "اترجعت النسخة {name} - كليبر: {state}"),

    # ---------- moonraker / upload ----------
    "mr.no_host": _t("Enter the printer address first", "اكتب عنوان الطابعة الأول"),
    "mr.unauthorized": _t("Moonraker refused the request - add this computer to trusted_clients or enter an API key",
                          "Moonraker رفض الطلب - ضيف الجهاز ده في trusted_clients أو اكتب مفتاح API"),
    "mr.no_connection": _t("Cannot reach {url}  ({reason})", "مفيش اتصال بـ {url}  ({reason})"),
    "mr.network": _t("Network error: {err}", "خطأ في الشبكة: {err}"),
    "mr.bad_reply": _t("Unexpected reply from Moonraker", "رد غير مفهوم من Moonraker"),
    "mr.timeout": _t("Klipper did not answer in time", "كليبر ما ردّش في الوقت المحدد"),
    "up.state": _t("Printer state: {state}", "حالة الطابعة: {state}"),
    "up.busy_printing": _t("The printer is printing - upload and restart are blocked", "الطابعة بتطبع - ممنوع الرفع وإعادة التشغيل"),
    "up.busy_paused": _t("The printer has a paused print - upload and restart are blocked", "فيه طبعة متوقفة مؤقتًا - ممنوع الرفع وإعادة التشغيل"),
    "up.changed_on_printer": _t(
        "printer.cfg changed on the printer after you downloaded it (for example SAVE_CONFIG). "
        "Download it again and review before uploading.",
        "printer.cfg اتغير على الطابعة بعد ما حمّلته (زي SAVE_CONFIG). حمّله تاني وراجع قبل الرفع."),
    "up.backup_remote": _t("Backup on printer: {name}", "نسخة احتياطية على الطابعة: {name}"),
    "up.backup_local": _t("Backup on this computer: {path}", "نسخة احتياطية على الجهاز: {path}"),
    "up.uploaded": _t("printer.cfg uploaded ({lines} lines)", "اترفع printer.cfg ({lines} سطر)"),
    "up.restarting": _t("FIRMWARE_RESTART ... waiting for Klipper", "FIRMWARE_RESTART ... مستني كليبر"),

    # ---------- config files ----------
    "nav.files": _t("📁   All config files", "📁   كل ملفات الإعداد"),
    "files.title": _t("All config files", "كل ملفات الإعداد"),
    "files.hint": _t(
        "Every file on the printer: printer.cfg with its include tree, moonraker.conf, crowsnest.conf, "
        "KlipperScreen, add-ons... Click a section to jump to it. Saving makes a backup first, refuses while "
        "printing and restarts only what the file needs.",
        "كل الملفات اللي على الطابعة: printer.cfg وكل الملفات المتضمنة فيه، moonraker.conf، crowsnest.conf، "
        "KlipperScreen والإضافات... اضغط على أي قسم تروح له. الحفظ بيعمل نسخة احتياطية الأول، وبيرفض "
        "والطابعة بتطبع، وبيعيد تشغيل اللي الملف محتاجه بس."),
    "files.load_printer": _t("Load all files from printer", "تحميل كل الملفات من الطابعة"),
    "files.summary": _t("{files} files  ·  {included} in the printer.cfg include tree  ·  {source}",
                        "{files} ملف  ·  {included} متضمنين في printer.cfg  ·  {source}"),
    "files.find": _t("Find (Enter)", "بحث (Enter)"),
    "files.restart_after": _t("Restart after saving", "إعادة تشغيل بعد الحفظ"),
    "files.revert": _t("Discard changes", "إلغاء التعديلات"),
    "files.save": _t("Save to printer", "حفظ على الطابعة"),
    "files.other_files": _t("Other files", "ملفات تانية"),
    "files.missing_include": _t("Included file not found: {path}", "ملف متضمن مش موجود: {path}"),
    "files.no_issues": _t("No missing includes and no Klipper warnings", "مفيش ملفات ناقصة ولا تحذيرات من كليبر"),
    "files.no_changes": _t("No changes to save", "مفيش تعديلات تتحفظ"),
    "files.no_restart": _t("no restart", "من غير إعادة تشغيل"),
    "files.confirm_save": _t("Save {path}?\n\nA backup is made first.\nAfter saving: {restart}",
                             "تحفظ {path}؟\n\nهيتعمل نسخة احتياطية الأول.\nبعد الحفظ: {restart}"),
    "files.changed_on_printer": _t("{path} changed on the printer after it was loaded - load the files again first",
                                   "{path} اتغير على الطابعة بعد ما اتحمّل - حمّل الملفات تاني الأول"),
    "files.saved": _t("Saved: {path}", "اتحفظ: {path}"),
    "files.service_restarted": _t("Service restarted: {service}", "اتعمل إعادة تشغيل للخدمة: {service}"),
    "msg.no_printer_cfg": _t("printer.cfg was not found in the config folder", "مفيش printer.cfg في فولدر الإعداد"),
    "msg.imported_all": _t("{files} config files were loaded. Every field now shows your current settings - "
                           "see “All config files” for the rest.",
                           "اتحمّل {files} ملف إعداد. كل الخانات دلوقتي فيها إعداداتك الحالية - "
                           "وباقي الملفات في «كل ملفات الإعداد»."),
    "val.section_elsewhere": _t("[{section}] is also defined in {file} - values in printer.cfg and that file may override each other",
                                "[{section}] موجود كمان في {file} - القيم في printer.cfg والملف ده ممكن يغطوا على بعض"),
    "val.klipper_warning": _t("Klipper: {msg}", "كليبر: {msg}"),

    # ---------- generated file ----------
    "cfg.header_line1": _t("Sections managed by the app were regenerated.", "الأقسام اللي البرنامج مسؤول عنها اتولّدت من جديد."),
    "cfg.header_line2": _t("Macros and every other section were kept as they were.", "الماكروهات وأي أقسام تانية فضلت زي ما هي."),
    "cfg.kept_sections": _t("From the previous file - macros, menus and add-ons", "من الملف السابق - ماكروهات وقوايم وإضافات"),

    # ---------- import notes ----------
    "note.no_z1_slot": _t("The board has no free driver for a second Z motor", "البورده مفيهاش درايفر فاضي لمحرك Z تاني"),
    "note.hotend_fan_on_heater": _t("Hotend fan set to the spare heater output {pin} - check your wiring",
                                    "مروحة الهيت سنك اتحطت على مخرج السخان الاحتياطي {pin} - راجع التوصيل"),
    "note.fil_sensor_guess": _t("Filament sensor set to {pin} (extruder endstop connector) - check your wiring",
                                "حساس الفيلامنت اتحط على {pin} (مخرج ليميت الإكسترودر) - راجع التوصيل"),
    "note.kinematics_unsupported": _t("Kinematics '{kin}' is not fully supported yet - review the result carefully",
                                      "نوع الحركة '{kin}' مش مدعوم بالكامل لسه - راجع الناتج كويس"),
    "note.multi_z_unsupported": _t("3/4 Z motors are not supported yet - stepper_z2/z3 are kept as they are",
                                   "3 أو 4 محركات Z مش مدعومين لسه - stepper_z2/z3 هيفضلوا زي ما هما"),
    "note.driver_unsupported": _t("Driver {drv} is not supported - its sections are kept as they are",
                                  "الدرايفر {drv} مش مدعوم - أقسامه هتفضل زي ما هي"),
    "note.renamed_section": _t("[{old}] will be written as [{new}]", "[{old}] هيتكتب باسم [{new}]"),
    "note.probe_unsupported": _t("Eddy/beacon style probes are not managed - their sections are kept as they are",
                                 "مسابير Eddy/Beacon مش مدارة من البرنامج - أقسامها هتفضل زي ما هي"),
    "note.board_detected": _t("Board detected: {name}", "اتعرفت البورده: {name}"),
    "note.board_unknown": _t("Board not recognised - pins were imported as they are",
                             "البورده ما اتعرفتش - الأرجل اتاخدت زي ما هي"),
    "note.save_config_read": _t("SAVE_CONFIG values were read (PID, probe offset, input shaper, mesh)",
                                "اتقرت قيم SAVE_CONFIG (PID، أوفست المسبار، Input Shaper، الشبكة)"),

    # ---------- validation ----------
    "val.parse_ok": _t("File parses correctly ({count} sections)", "الملف بيتقري من غير أخطاء صياغة ({count} قسم)"),
    "val.parse_error": _t("Syntax error: {err}", "خطأ صياغة: {err}"),
    "val.duplicates": _t("Duplicate sections: {names}", "أقسام متكررة: {names}"),
    "val.no_duplicates": _t("No duplicate sections", "مفيش أقسام متكررة"),
    "val.serial_placeholder": _t("MCU serial is still a placeholder - use “Detect on printer” or ls /dev/serial/by-id/*",
                                 "سيريال البورده لسه مش متظبط - استخدم «اكتشاف من الطابعة» أو ls /dev/serial/by-id/*"),
    "val.serial_board_mismatch": _t("The serial says '{chip}' but {board} uses a different MCU - wrong board selected?",
                                    "السيريال بيقول '{chip}' بس {board} معالجها مختلف - يمكن اخترت بورده غلط؟"),
    "val.pins_empty": _t("Missing pins: {pins}", "أرجل ناقصة: {pins}"),
    "val.pin_conflict": _t("Pin {pin} is used twice: {a} and {b}", "الرجل {pin} مستخدمة مرتين: {a} و {b}"),
    "val.tmc_missing": _t("{axis} driver needs {key}", "درايفر {axis} محتاج {key}"),
    "val.tmc2208_shared_uart": _t("This board uses a shared UART bus with addresses - choose TMC2209",
                                  "البورده دي بتستخدم UART مشترك بعناوين - اختار TMC2209"),
    "val.current_high": _t("Run current above {limit}A - the drivers will run hot",
                           "تيار أعلى من {limit}A - الدرايفرات هتسخن"),
    "val.z_accel": _t("max_z_accel ({z}) is higher than max_accel ({xy}) - Klipper will refuse to start",
                      "max_z_accel ({z}) أكبر من max_accel ({xy}) - كليبر هيرفض يشتغل"),
    "val.microsteps": _t("Microsteps must be a power of 2 (8, 16, 32 ...)", "المايكروستب لازم يكون من مضاعفات 2 (8 · 16 · 32 ...)"),
    "val.kinematics": _t("Kinematics '{kin}' is not generated by the app yet", "نوع الحركة '{kin}' البرنامج مش بيولّده لسه"),
    "val.mesh_empty": _t("Mesh area is empty - margin too large or probe offsets are wrong",
                         "منطقة الشبكة فاضية - الهامش كبير أو إزاحة المسبار مش منطقية"),
    "val.mesh_area": _t("Mesh area: X {x0}..{x1}  Y {y0}..{y1}", "منطقة الشبكة: X {x0}..{x1}  Y {y0}..{y1}"),
    "val.probe_z_zero": _t("Probe Z offset is 0 - run PROBE_CALIBRATE before printing",
                           "أوفست Z للمسبار = 0 - اعمل PROBE_CALIBRATE قبل ما تطبع"),
    "val.dual_z_no_probe": _t("Dual Z without a probe - z_tilt is not generated", "دبل Z من غير مسبار - z_tilt مش هيتولّد"),
    "val.pa_zero": _t("Pressure advance is 0 - calibrate it (reduces stringing and blobs)",
                      "Pressure advance = 0 - اعمله معايرة (بيقلل الخيوط والتكتلات)"),
    "val.pa_bowden_low": _t("Pressure advance {pa} is low for a Bowden setup - typical 0.30-0.80",
                            "Pressure advance {pa} قليل على البودن - المعتاد 0.30-0.80"),
    "val.shaper_equal": _t("Input shaper X = Y ({f} Hz) - Y was probably measured with the sensor on the toolhead",
                           "Input Shaper X = Y ({f} Hz) - غالبًا Y اتقاس والحساس على الراس"),
    "val.shaper_z_low_accel": _t("Z input shaping is on but max_z_accel is low - little benefit",
                                 "Input Shaper لـ Z مفعّل بس max_z_accel قليل - الفايدة محدودة"),
    "val.fan_low": _t("Part fan limited below 20% - cooling may be too weak", "مروحة القطعة محدودة تحت 20% - التبريد ممكن يبقى ضعيف"),
    "val.led_plugin": _t("LED effects require the klipper-led_effect plugin", "تأثيرات الإضاءة محتاجة إضافة klipper-led_effect"),
    "val.ref_leds": _t("LED strip is off but macros use case_leds - Klipper will error",
                       "الشريط مقفول بس فيه ماكروهات بتستخدم case_leds - كليبر هيطلع خطأ"),
    "val.ref_led_effects": _t("LED effects are off but macros call SET_LED_EFFECT - Klipper will error",
                              "التأثيرات مقفولة بس فيه ماكروهات بتستدعي SET_LED_EFFECT - كليبر هيطلع خطأ"),
    "val.ref_z_tilt": _t("Dual Z is off but macros use Z_TILT_ADJUST or stepper_z1 - Klipper will error",
                         "الدبل Z مقفول بس فيه ماكروهات بتستخدم Z_TILT_ADJUST أو stepper_z1 - كليبر هيطلع خطأ"),
    "val.ref_probe": _t("No probe but macros run BED_MESH_CALIBRATE / PROBE_CALIBRATE - Klipper will error",
                        "مفيش مسبار بس فيه ماكروهات بتعمل BED_MESH_CALIBRATE / PROBE_CALIBRATE - كليبر هيطلع خطأ"),
    "val.ref_fil_sensor": _t("Filament sensor is off but it is referenced elsewhere - Klipper will error",
                             "حساس الفيلامنت مقفول بس فيه إشارات ليه - كليبر هيطلع خطأ"),
    "val.ready": _t("No errors - ready to upload", "مفيش أخطاء - جاهز للرفع"),
}
