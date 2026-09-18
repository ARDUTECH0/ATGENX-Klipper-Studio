# -*- coding: utf-8 -*-
"""Help for every page and setting: what it is, when to change it, typical values and where it
goes in printer.cfg. Used by the in-app help panel, tooltips and docs/GUIDE*.md."""
from collections import OrderedDict

from .i18n import get_lang


def _h(page, cfg, en, ar):
    return {"page": page, "cfg": cfg, "en": en, "ar": ar}


# --------------------------------------------------------------------------- pages
PAGE_GUIDE = OrderedDict([
    ("page_printers", (
        "Your printers, and sending the same files to all of them at once.\n"
        "1. Add printer: name, address, and - if they are not the usual ones - the Moonraker port, "
        "the SSH port and the folder its files go into.\n"
        "2. Tick the printers you want, add files or a whole folder, and press Sync.\n"
        "3. Each printer gets its own progress bar with speed and time left, and the log says what "
        "happened.\n\n"
        "Dry run does everything except write. A file that is printing or waiting in the queue is "
        "never overwritten - it is skipped and listed for you.",
        "طابعاتك، وإرسال نفس الملفات لكلها في نفس الوقت. جرب Dry run الأول.")),
    ("page_remote", (
        "What is on a printer right now. Double-click a folder to open it, hover a file to see the "
        "thumbnail the slicer put in it, and select files to delete them.\n\n"
        "Anything printing or queued is marked and cannot be deleted.",
        "اللي موجود على الطابعة دلوقتي. اللي بيتطبع محمي.")),
    ("page_start", (
        "Pick what you want to do. Every path ends on Review & upload, where you see the checks and the exact changes before anything reaches the printer.",
        "اختار عايز تعمل إيه. كل الطرق بتنتهي في صفحة المراجعة والرفع، وهناك بتشوف نتيجة الفحص والتغييرات بالظبط قبل ما أي حاجة توصل للطابعة.")),
    ("page_connection", (
        "1. Type the printer address (the same one you open Mainsail or Fluidd with).\n2. Test connection: you should see Klipper, Moonraker and the MCU.\n3. Import from printer: every field is filled from your printer.cfg and its included files.\n\nNothing is changed on the printer here.",
        "1. اكتب عنوان الطابعة (نفس اللي بتفتح بيه Mainsail أو Fluidd).\n2. اختبار الاتصال: المفروض يظهر كليبر و Moonraker والمعالج.\n3. استيراد من الطابعة: كل الخانات بتتملى من printer.cfg والملفات المتضمنة فيه.\n\nمفيش أي حاجة بتتغير على الطابعة في الصفحة دي.")),
    ("page_board", (
        "1. Choose your board (type to search). After importing, the detected board is already selected.\n2. Apply board pins fills every motor socket, heater, fan and sensor pin.\n3. Detect on printer finds the serial path of the board.\n\nKeep 'Keep my motor directions' ticked on a printer that already moves correctly.",
        "1. اختار البورده (اكتب جزء من الاسم للبحث). بعد الاستيراد البورده اللي اتعرفت بتبقى مختارة.\n2. «طبّق أرجل البورده» بيملا مخارج المحركات والسخانات والمراوح والحساسات.\n3. «اكتشاف من الطابعة» بيجيب مسار السيريال بتاع البورده.\n\nخلي «احتفظ باتجاهات المحركات» متعلّم لو الطابعة بتتحرك صح أصلًا.")),
    ("page_features", (
        "Built-in: switch app features on or off - what a feature needs is switched on with it.\nIn your file: every other section of printer.cfg. Off comments it out with #, on removes the #.\nAdd a feature: pick a well-known section or plugin, edit the template, and it is added at the end of printer.cfg.\n\nAll changes show up in Review & upload before anything is sent.",
        "المميزات الأساسية: شغّل أو اقفل مميزات البرنامج - واللي الميزة محتاجاه بيتشغّل معاها.\nفي ملفك: كل الأقسام التانية في printer.cfg. الإيقاف بيعمل تعليق بـ #، والتشغيل بيشيل الـ #.\nإضافة ميزة: اختار قسم أو إضافة مشهورة، عدّل القالب، وبتتضاف في آخر printer.cfg.\n\nكل التغييرات بتظهر في المراجعة والرفع قبل ما أي حاجة تتبعت.")),
    ("page_machine", (
        "Set the build volume and the motion limits. Start conservative (acceleration 3000, velocity 300) and raise them after input shaper tuning.",
        "حدد مساحة الطباعة وحدود الحركة. ابدأ بقيم آمنة (تسارع 3000 وسرعة 300) وزوّدها بعد ضبط الـ Input Shaper.")),
    ("page_motors", (
        "Each row is one motor.\n1. Driver socket: where the motor is plugged on the board.\n2. Driver: the driver module in that socket.\n3. Current, microsteps, rotation distance.\n4. Click a row for its details: hold current, step angle, sensorless homing, bus pins, TMC Autotune.\n\nAdd motor: second X/Y motor (AWD) or up to 4 Z motors. Copy to motors of the same axis keeps Z motors identical.",
        "كل صف = محرك.\n1. مخرج الدرايفر: المحرك متركب فين على البورده.\n2. الدرايفر: نوع الدرايفر اللي في المخرج ده.\n3. التيار والمايكروستب و rotation_distance.\n4. اضغط على الصف تشوف التفاصيل: تيار الوقوف، زاوية الخطوة، التصفير من غير ليميت، أرجل الاتصال، TMC Autotune.\n\n«إضافة محرك»: محرك X/Y تاني (AWD) أو لحد 4 محركات Z. «انسخ لمحركات نفس المحور» بيخلي محركات Z زي بعض.")),
    ("page_thermal", (
        "Set the hotend and bed thermistors and heater limits. After the first start run PID_CALIBRATE for both heaters and SAVE_CONFIG; the app keeps those values.",
        "حدد ثرمستور النوزل والقاعدة وحدود الحرارة. بعد أول تشغيل اعمل PID_CALIBRATE للسخانين وبعدين SAVE_CONFIG، والبرنامج بيحافظ على القيم دي.")),
    ("page_probe", (
        "1. Choose the probe type and its X/Y offset from the nozzle.\n2. The mesh area is calculated so the probe can reach every point.\n3. With 2-4 Z motors the leveling (z_tilt / quad gantry) is on the Motors page.\n\nZ offset: run PROBE_CALIBRATE, then SAVE_CONFIG.",
        "1. اختار نوع المسبار وإزاحته X/Y عن النوزل.\n2. منطقة الشبكة بتتحسب لوحدها بحيث المسبار يوصل لكل نقطة.\n3. لو فيه من 2 لـ 4 محركات Z، التسوية (z_tilt / quad gantry) في صفحة المحركات.\n\nأوفست Z: اعمل PROBE_CALIBRATE وبعدين SAVE_CONFIG.")),
    ("page_extras", (
        "Optional features. Each one adds its own section to printer.cfg and can be switched off later - the app removes the section again.",
        "مميزات اختيارية. كل ميزة بتضيف القسم بتاعها في printer.cfg، ولو قفلتها بعدين البرنامج بيشيل القسم تاني.")),
    ("page_map", (
        "The wiring map: your board in the middle and every device around it, each line labelled with the pin it uses.\n\n"
        "Click a device to see and edit its pins. Red = a problem (empty pin, the same pin used twice, or a pin on a "
        "second board that is switched off).\n"
        "Drag devices to arrange them, scroll to zoom, and Export image saves the diagram as a PNG - handy for "
        "documenting your printer or asking for help.\n\n"
        "Add device adds a motor, a feature or a section from the catalog.",
        "خريطة التوصيلات: البورده في النص وكل الأجهزة حواليها، وكل خط مكتوب عليه الرجل اللي مستخدمة.\n\n"
        "اضغط على أي جهاز تشوف أرجله وتعدّلها. الأحمر = فيه مشكلة (رجل فاضية، أو رجل مستخدمة مرتين، أو رجل على "
        "بورده تانية مقفولة).\n"
        "اسحب الأجهزة عشان ترتبها، واستخدم عجلة الماوس للتصغير والتكبير، و«تصدير صورة» بيحفظ الرسم PNG - مفيد "
        "لتوثيق طابعتك أو لما تسأل حد.\n\n"
        "«إضافة جهاز» بيضيف محرك أو ميزة أو قسم من الكتالوج.")),
    ("page_pins", (
        "Every pin in one table: motor pins, driver bus pins, heaters, fans, probe, LEDs. Filled from the board page - edit only if your wiring differs.\n^ = pull-up, ~ = pull-down, ! = inverted.",
        "كل الأرجل في جدول واحد: أرجل المحركات، أرجل اتصال الدرايفرات، السخانات، المراوح، المسبار، الإضاءة. بتتملى من صفحة البورده - عدّل بس لو توصيلك مختلف.\n^ = pull-up و ~ = pull-down و ! = عكس.")),
    ("page_preview", (
        "1. Checks: errors (red) must be fixed - click one to open its page. Warnings (yellow) are advice.\n2. Differences: exactly which lines change in your printer.cfg.\n3. Upload and restart: backup, upload, FIRMWARE_RESTART, wait for Klipper.\n\nSmart merge keeps your file and changes only what's needed. Clean new file rewrites it in a tidy order.",
        "1. الفحص: الأخطاء (أحمر) لازم تتصلح - اضغط عليها تفتح صفحتها. التحذيرات (أصفر) نصايح.\n2. الفروق: السطور اللي هتتغير في printer.cfg بالظبط.\n3. رفع وإعادة تشغيل: نسخة احتياطية، رفع، FIRMWARE_RESTART، ويستنى كليبر.\n\nالدمج الذكي بيحافظ على ملفك ويغيّر اللازم بس. الملف الجديد النظيف بيعيد كتابته بترتيب مرتب.")),
    ("page_files", (
        "All files of the printer. Click a file or a section in the tree, edit, then Save to printer. A backup is made first and only the matching service restarts (Klipper for .cfg, Moonraker for moonraker.conf...).",
        "كل ملفات الطابعة. اضغط على ملف أو قسم في الشجرة، عدّل، وبعدين «حفظ على الطابعة». بيتعمل نسخة احتياطية الأول وبيتعمل إعادة تشغيل للخدمة المناسبة بس (كليبر لملفات .cfg، و Moonraker لـ moonraker.conf...).")),
    ("page_doctor", (
        "Check printer now reads Klipper's state and the last klippy.log session. Or paste an error message. Each problem shows the cause, the fix, and a button to the page where you fix it.",
        "«افحص الطابعة دلوقتي» بيقرا حالة كليبر وآخر تشغيل في klippy.log. أو الصق رسالة الخطأ. كل مشكلة بيظهر سببها وحلها وزرار يوديك للصفحة اللي بتصلحها منها.")),
])

# --------------------------------------------------------------------------- settings
HELP = OrderedDict([
    # printers and sync
    ("fleet.dry_run", _h("page_printers", "",
                         "Runs the whole sync without writing anything: it connects, compares every file and "
                         "tells you what it would send, replace or skip. Use it the first time you point the app "
                         "at a printer you care about.",
                         "بيشغل العملية كلها من غير ما يكتب حاجة: بيتصل ويقارن كل ملف ويقولك هيبعت إيه.")),
    ("fleet.skip_same", _h("page_printers", "",
                           "A file already on the printer with exactly the same size is left alone. Turn this off "
                           "to send everything again, for example after re-slicing with the same file names.",
                           "الملف الموجود على الطابعة بنفس الحجم بيتساب زي ما هو. اقفلها عشان يبعت كل حاجة تاني.")),

    # connection
    ("host", _h("page_connection", "",
                "The printer's IP address or host name, the same one you open Mainsail or Fluidd with. Example: 192.168.1.50 or mainsailos.local.",
                "عنوان الطابعة (IP أو اسم)، نفس اللي بتفتح بيه Mainsail أو Fluidd. مثال: 192.168.1.50 أو mainsailos.local.")),
    ("port", _h("page_connection", "moonraker.conf [server] port",
                "Moonraker's port. Leave 7125 unless you changed it.", "منفذ Moonraker. سيبه 7125 إلا لو انت غيرته.")),
    ("printer_name", _h("page_connection", "",
                        "A name for this project. It appears in the header of the generated file and in the project file name.",
                        "اسم للمشروع. بيظهر في أول الملف الناتج وفي اسم ملف المشروع.")),
    # board
    ("board", _h("page_board", "",
                 "Your controller board. The app knows its driver sockets, heater and fan outputs, sensor inputs and the required extra sections. Choose Custom if it isn't listed and type the pins yourself.",
                 "بوردة التحكم بتاعتك. البرنامج عارف مخارج الدرايفرات والسخانات والمراوح ومداخل الحساسات والأقسام الإضافية المطلوبة. اختار «مخصص» لو مش موجودة واكتب الأرجل بنفسك.")),
    ("board_extras", _h("page_board", "[static_digital_output ...] / [output_pin ...]",
                        "Some boards need extra sections to work at all (USB pull-up, stepper current PWM, digipots). Leave it on for a new printer.",
                        "بعض البوردات محتاجة أقسام إضافية عشان تشتغل أصلًا (USB pull-up، تيار المحركات بالـ PWM، مقاومات رقمية). سيبها مفعّلة لطابعة جديدة.")),
    ("mcu_serial", _h("page_board", "[mcu] serial",
                      "How Klipper finds the board. Use Detect on printer and pick the /dev/serial/by-id/usb-Klipper_... path. For CAN boards write canbus_uuid: <uuid>.",
                      "إزاي كليبر يلاقي البورده. استخدم «اكتشاف من الطابعة» واختار مسار /dev/serial/by-id/usb-Klipper_... . لبوردات CAN اكتب canbus_uuid: <uuid>.")),
    ("keep_inversion", _h("page_board", "[stepper_*] dir_pin",
                          "Keeps the Invert setting of every motor when applying a board. Untick it only for a new printer, to use the board file's default directions.",
                          "بيحافظ على «عكس» كل محرك وانت بتطبّق البورده. شيل العلامة بس لطابعة جديدة عشان تاخد الاتجاهات الافتراضية من ملف البورده.")),
    # machine
    ("kinematics", _h("page_machine", "[printer] kinematics",
                      "Cartesian: X and Y each move one axis (bed slingers like Ender 3, Prusa). CoreXY: two motors move the head together (Voron, Bambu-style frames).",
                      "Cartesian: كل محرك بيحرك محور (القاعدة المتحركة زي Ender 3 و Prusa). CoreXY: محركين بيحركوا الراس مع بعض (Voron وأشكال Bambu).")),
    ("bed_x", _h("page_machine", "[stepper_x] position_max",
                 "Furthest X position the nozzle can reach. Measure it: home, then move X in small steps until it touches the end.",
                 "أبعد مكان النوزل يوصله على X. قيسه: اعمل تصفير وحرّك X خطوات صغيرة لحد آخر المحور.")),
    ("bed_y", _h("page_machine", "[stepper_y] position_max", "Furthest Y position the nozzle can reach.", "أبعد مكان النوزل يوصله على Y.")),
    ("bed_z", _h("page_machine", "[stepper_z] position_max", "Maximum print height.", "أقصى ارتفاع للطباعة.")),
    ("x_min", _h("page_machine", "[stepper_x] position_min",
                 "Lowest X position, usually 0. Negative when the endstop sits before the bed edge.",
                 "أقل مكان على X، غالبًا 0. بيبقى بالسالب لو الليميت قبل حرف القاعدة.")),
    ("y_min", _h("page_machine", "[stepper_y] position_min", "Lowest Y position, usually 0.", "أقل مكان على Y، غالبًا 0.")),
    ("z_min", _h("page_machine", "[stepper_z] position_min",
                 "Lowest Z. A small negative value (-2 to -5) lets you lower the nozzle during PROBE_CALIBRATE.",
                 "أقل Z. قيمة سالبة صغيرة (من -2 لـ -5) بتسمحلك تنزّل النوزل وقت PROBE_CALIBRATE.")),
    ("x_endstop", _h("page_machine", "[stepper_x] position_endstop",
                     "X position when the endstop triggers: 0 if the endstop is at the minimum, position_max if it's at the maximum.",
                     "مكان X لما الليميت يشتغل: 0 لو الليميت في الأول، و position_max لو في الآخر.")),
    ("y_endstop", _h("page_machine", "[stepper_y] position_endstop", "Y position when the endstop triggers.", "مكان Y لما الليميت يشتغل.")),
    ("max_velocity", _h("page_machine", "[printer] max_velocity",
                        "Speed limit for any move. The slicer can't go faster. 200-300 mm/s for bed slingers, 300-500 for CoreXY.",
                        "حد السرعة لأي حركة، والسلايسر مش هيقدر يعدّيه. 200-300 مم/ث للقاعدة المتحركة، و 300-500 لـ CoreXY.")),
    ("max_accel", _h("page_machine", "[printer] max_accel",
                     "Acceleration limit. Too high causes ringing and layer shifts. Start at 2000-3000; after SHAPER_CALIBRATE use the value it recommends.",
                     "حد التسارع. العالي زيادة بيعمل تموجات وإزاحة طبقات. ابدأ بـ 2000-3000، وبعد SHAPER_CALIBRATE استخدم القيمة اللي بيقترحها.")),
    ("max_z_velocity", _h("page_machine", "[printer] max_z_velocity",
                          "Z speed limit. Lead screws: 10-20 mm/s. Belt-driven Z: higher.", "حد سرعة Z. البريمة: 10-20 مم/ث. Z بسير: أعلى.")),
    ("max_z_accel", _h("page_machine", "[printer] max_z_accel",
                       "Z acceleration limit. Must not be higher than max_accel. Lead screws: 100-500.",
                       "حد تسارع Z. مينفعش يكون أعلى من max_accel. البريمة: 100-500.")),
    ("scv", _h("page_machine", "[printer] square_corner_velocity",
               "Speed through 90° corners. 5 is the Klipper default; lower it if corners bulge.",
               "السرعة في الأركان 90°. 5 هي قيمة كليبر الافتراضية، قلّلها لو الأركان منفوخة.")),
    ("homing_speed", _h("page_machine", "[stepper_x/y] homing_speed",
                        "Speed while homing X and Y. 50 is typical; sensorless homing often needs 40-100.",
                        "سرعة التصفير لـ X و Y. 50 عادي، والتصفير من غير ليميت غالبًا محتاج 40-100.")),
    # motors (global)
    ("z_leveling", _h("page_motors", "[z_tilt] / [quad_gantry_level]",
                      "With 2-4 Z motors: z_tilt levels a bed or a fixed gantry (run Z_TILT_ADJUST). quad_gantry_level is for a Voron 2.4 style gantry with 4 motors (run QUAD_GANTRY_LEVEL). Needs a probe.",
                      "مع 2-4 محركات Z: z_tilt بيسوّي قاعدة أو جسر ثابت (اعمل Z_TILT_ADJUST). quad_gantry_level لجسر متحرك بـ 4 محركات زي Voron 2.4 (اعمل QUAD_GANTRY_LEVEL). محتاج مسبار.")),
    ("z_tilt_points", _h("page_motors", "[z_tilt] points / [quad_gantry_level] points",
                         "Where the probe measures, one X, Y per line. Leave empty and the app places them near each Z motor inside the reachable area.",
                         "أماكن القياس، X, Y في كل سطر. سيبها فاضية والبرنامج بيحطها جنب كل محرك Z جوه المنطقة اللي المسبار يوصلها.")),
    ("qgl_corners", _h("page_motors", "[quad_gantry_level] gantry_corners",
                       "Two opposite corners of the gantry (front-left, back-right), usually outside the bed. Empty = estimated from the bed size.",
                       "ركنين متقابلين للجسر (قدام شمال، ورا يمين)، غالبًا برا القاعدة. فاضي = بيتقدّر من مقاس القاعدة.")),
    ("motor_voltage", _h("page_motors", "[autotune_tmc ...] voltage",
                         "Power supply voltage of the motors, used only by TMC Autotune. 24 V for most printers.",
                         "جهد باور المحركات، بيستخدمه TMC Autotune بس. 24 فولت لمعظم الطابعات.")),
    ("motor.slot", _h("page_motors", "[stepper_*] step_pin / dir_pin / enable_pin",
                      "The driver socket on the board this motor is plugged into. Changing it moves all its pins, the driver bus pins and the DIAG pin at once.",
                      "مخرج الدرايفر على البورده اللي المحرك متركب فيه. تغييره بينقل كل أرجله وأرجل اتصال الدرايفر ورجل DIAG مرة واحدة.")),
    ("motor.driver", _h("page_motors", "[tmcXXXX stepper_*]",
                        "The driver module in that socket. TMC2209/2208 use UART, TMC2130/5160/2240 use SPI. Standalone means A4988, DRV8825 or a TMC in standalone mode (no current setting).",
                        "الدرايفر اللي في المخرج. TMC2209/2208 بيستخدموا UART، و TMC2130/5160/2240 بيستخدموا SPI. «عادي» يعني A4988 أو DRV8825 أو TMC من غير UART (مفيش ضبط تيار).")),
    ("motor.run_current", _h("page_motors", "[tmcXXXX stepper_*] run_current",
                             "RMS current while moving. Start at about 70% of the motor's rated current (a 1.5 A motor -> ~1.0 A). Too high: hot motors and drivers. Too low: skipped steps.",
                             "التيار RMS وقت الحركة. ابدأ بحوالي 70% من تيار المحرك المكتوب (محرك 1.5 A -> حوالي 1.0 A). عالي زيادة: المحركات والدرايفرات تسخن. قليل: يفوّت خطوات.")),
    ("motor.microsteps", _h("page_motors", "[stepper_*] microsteps",
                            "Steps per full step. 16 is the best default (with interpolate). 32 on X/Y can be quieter; more than 64 overloads the board.",
                            "خطوات لكل خطوة كاملة. 16 أفضل قيمة افتراضية (مع interpolate). 32 على X/Y ممكن تبقى أهدى، وأكتر من 64 بيضغط البورده.")),
    ("motor.rotation_distance", _h("page_motors", "[stepper_*] rotation_distance",
                                   "Distance moved per motor revolution. Belts: pulley teeth x belt pitch (20T GT2 = 40). Lead screws: pitch x starts (T8x8 = 8, T8x2 = 2). Extruder: calibrate by extruding 100 mm and measuring.",
                                   "المسافة لكل لفة محرك. السيور: عدد أسنان البكرة × خطوة السير (20 سنة GT2 = 40). البريمة: الخطوة × عدد البدايات (T8x8 = 8 و T8x2 = 2). الإكسترودر: اعمل معايرة بسحب 100 مم وقيس.")),
    ("motor.invert", _h("page_motors", "[stepper_*] dir_pin: !PIN",
                        "Tick it if the motor turns the wrong way. Test with STEPPER_BUZZ or a small move after homing.",
                        "علّم عليها لو المحرك بيلف عكس. اختبر بـ STEPPER_BUZZ أو حركة صغيرة بعد التصفير.")),
    ("motor.stealthchop", _h("page_motors", "[tmcXXXX stepper_*] stealthchop_threshold",
                             "spreadCycle (0) is accurate and strong - best for X/Y. A speed turns on silent stealthChop below it. 999999 = always silent (fine for Z and the extruder).",
                             "spreadCycle (0) دقيق وقوي - الأفضل لـ X/Y. لو كتبت سرعة، الوضع الصامت بيشتغل تحتها. 999999 = صامت دايمًا (مناسب لـ Z والإكسترودر).")),
    ("motor.sensorless", _h("page_motors", "[stepper_x] endstop_pin: tmc2209_stepper_x:virtual_endstop",
                            "Home X/Y without endstop switches, using the driver's StallGuard. Needs a TMC2209/2130/5160/2240, the DIAG jumper on the board and tuning of the threshold.",
                            "تصفير X/Y من غير سويتشات ليميت، باستخدام StallGuard في الدرايفر. محتاج TMC2209/2130/5160/2240، وجمبر DIAG على البورده، وضبط الحساسية.")),
    ("motor.hold_current", _h("page_motors", "[tmcXXXX stepper_*] hold_current",
                              "Lower current while the motor stands still. Usually leave it empty (same as run current) - Klipper recommends that, and it's required for sensorless homing.",
                              "تيار أقل والمحرك واقف. غالبًا سيبه فاضي (نفس تيار الحركة) - كليبر بينصح بكده، ولازم يبقى كده مع التصفير من غير ليميت.")),
    ("motor.sense_resistor", _h("page_motors", "[tmcXXXX stepper_*] sense_resistor",
                                "Resistor value on the driver module. Leave the default unless your module is different (BTT TMC5160 Pro = 0.075, TMC2660 on Duet 2 = 0.051).",
                                "قيمة مقاومة القياس على الدرايفر. سيب الافتراضي إلا لو الدرايفر مختلف (BTT TMC5160 Pro = 0.075، و TMC2660 على Duet 2 = 0.051).")),
    ("motor.full_steps", _h("page_motors", "[stepper_*] full_steps_per_rotation",
                            "1.8° motors (most printers) = 200. 0.9° motors (e.g. LDO 0.9° on Voron) = 400.",
                            "محركات 1.8° (معظم الطابعات) = 200. محركات 0.9° (زي LDO 0.9° في Voron) = 400.")),
    ("motor.interpolate", _h("page_motors", "[tmcXXXX stepper_*] interpolate",
                             "The driver smooths each microstep into 256. Quieter and smoother with a very small position error. Keep it on unless you need maximum dimensional precision.",
                             "الدرايفر بينعّم كل مايكروستب لـ 256. أهدى وأنعم مع خطأ مكان صغير جدًا. سيبه مفعّل إلا لو محتاج أقصى دقة مقاسات.")),
    ("motor.sg", _h("page_motors", "[tmc2209 stepper_x] driver_SGTHRS / [tmc5160 stepper_x] driver_SGT",
                    "Sensorless sensitivity. TMC2209: 255 most sensitive, lower it until homing stops at the end without stopping early. TMC2130/5160/2240: -64 most sensitive, raise it. Tune live with SET_TMC_FIELD.",
                    "حساسية التصفير من غير ليميت. TMC2209: ‏255 أعلى حساسية، قلّلها لحد ما يقف في الآخر من غير ما يقف بدري. TMC2130/5160/2240: ‏-64 أعلى حساسية، زوّدها. اضبطها مباشرة بـ SET_TMC_FIELD.")),
    ("motor.diag_pin", _h("page_motors", "[tmc2209 stepper_x] diag_pin",
                          "The board pin connected to the driver's DIAG output - on most boards it's the endstop header of that socket, with a DIAG jumper. TMC2209: ^PIN. SPI drivers: ^!PIN.",
                          "رجل البورده المتوصلة بخرج DIAG في الدرايفر - في معظم البوردات هي فيشة الليميت بتاعة المخرج ده، مع جمبر DIAG. TMC2209: ‏^PIN. درايفرات SPI: ‏^!PIN.")),
    ("motor.z_position", _h("page_motors", "[z_tilt] z_positions",
                            "Where this Z motor (lead screw or pivot) is, in nozzle coordinates X, Y. Empty = estimated (2 motors: left/right; 3: front-left, back, front-right; 4: corners).",
                            "مكان محرك Z ده (البريمة أو نقطة الارتكاز) بإحداثيات النوزل X, Y. فاضي = بيتقدّر (محركين: شمال/يمين، 3: قدام شمال، ورا، قدام يمين، 4: الأركان).")),
    ("motor.autotune", _h("page_motors", "[autotune_tmc stepper_*] motor",
                          "Optional: the klipper_tmc_autotune plugin tunes the driver for your exact motor model. Install the plugin first, then choose your motor (type to search).",
                          "اختياري: إضافة klipper_tmc_autotune بتظبط الدرايفر على موديل محركك بالظبط. سطّب الإضافة الأول، وبعدين اختار المحرك (اكتب للبحث).")),
    ("motor.tuning_goal", _h("page_motors", "[autotune_tmc stepper_*] tuning_goal",
                             "auto = performance for X/Y and silent for Z/extruder. Choose silent or performance to force one.",
                             "تلقائي = أداء لـ X/Y وهادي لـ Z والإكسترودر. اختار هادي أو أداء لو عايز تفرض واحد.")),
    ("motor.bus", _h("page_motors", "[tmcXXXX stepper_*] uart_pin / cs_pin ...",
                     "How the board talks to the driver. Filled from the board. uart_address is used on boards with one shared UART line (SKR Mini, Manta...).",
                     "إزاي البورده بتكلم الدرايفر. بتتملى من البورده. uart_address بيستخدم في البوردات اللي فيها خط UART واحد مشترك (SKR Mini و Manta...).")),
    # review
    ("preview.merge", _h("page_preview", "",
                         "Changes only the lines that really change. Your order, comments, macros and extra sections stay exactly as they are. Recommended for a printer that already works.",
                         "بيغيّر السطور اللي اتغيرت فعلًا بس. ترتيبك وتعليقاتك وماكروهاتك وأقسامك الإضافية بتفضل زي ما هي. الأفضل لطابعة شغالة.")),
    ("preview.full", _h("page_preview", "",
                        "Writes a tidy new printer.cfg: sections grouped (board, motion, motors, heaters, probe, extras) with a short explanation above each. With 'Keep macros' your macros and other sections are added at the end.",
                        "بيكتب printer.cfg جديد مرتب: الأقسام متجمعة (البورده، الحركة، المحركات، السخانات، المسبار، الإضافات) وفوق كل قسم شرح قصير. مع «احتفظ بالماكروهات» ماكروهاتك وأقسامك التانية بتتحط في الآخر.")),
    # thermal
    ("nozzle", _h("page_thermal", "[extruder] nozzle_diameter", "Nozzle size, usually 0.4 mm.", "مقاس النوزل، غالبًا 0.4 مم.")),
    ("filament", _h("page_thermal", "[extruder] filament_diameter", "1.75 mm for almost all printers.", "1.75 مم لمعظم الطابعات.")),
    ("bowden", _h("page_thermal", "",
                  "Tick for a Bowden tube (extruder on the frame). It only changes the pressure advance advice: Bowden needs 0.3-0.8, direct drive 0.02-0.1.",
                  "علّم لو فيه أنبوبة بودن (الإكسترودر على الفريم). بتغيّر نصيحة Pressure advance بس: البودن محتاج 0.3-0.8، والدايركت 0.02-0.1.")),
    ("pa", _h("page_thermal", "[extruder] pressure_advance",
              "Compensates filament pressure in the nozzle: sharper corners, less stringing and blobs. Calibrate with a pressure advance tower (Orca Slicer has one).",
              "بيعوّض ضغط الفيلامنت في النوزل: أركان أحد وخيوط وتكتلات أقل. اعمل معايرة ببرج Pressure advance (موجود في Orca Slicer).")),
    ("pa_smooth", _h("page_thermal", "[extruder] pressure_advance_smooth_time",
                     "Smoothing for pressure advance. Keep 0.040 unless you know why to change it.", "تنعيم Pressure advance. سيبها 0.040 إلا لو عارف ليه بتغيرها.")),
    ("therm_e", _h("page_thermal", "[extruder] sensor_type",
                   "Hotend thermistor type. Most stock hotends: EPCOS 100K B57560G104F or Generic 3950. A wrong type reads the wrong temperature.",
                   "نوع ثرمستور النوزل. معظم الهوت إند الأصلية: EPCOS 100K B57560G104F أو Generic 3950. النوع الغلط بيقرا حرارة غلط.")),
    ("pid_e_kp", _h("page_thermal", "[extruder] pid_Kp", "PID values come from PID_CALIBRATE HEATER=extruder TARGET=220, then SAVE_CONFIG. Don't copy them from another printer.",
                    "قيم PID بتيجي من PID_CALIBRATE HEATER=extruder TARGET=220 وبعدين SAVE_CONFIG. متنقلهاش من طابعة تانية.")),
    ("pid_e_ki", _h("page_thermal", "[extruder] pid_Ki", "See PID Kp.", "شوف PID Kp.")),
    ("pid_e_kd", _h("page_thermal", "[extruder] pid_Kd", "See PID Kp.", "شوف PID Kp.")),
    ("max_temp_e", _h("page_thermal", "[extruder] max_temp",
                      "Klipper shuts down above this. 260-280 for PTFE-lined hotends, up to 300+ for all-metal.",
                      "كليبر بيقفل لو الحرارة عدّت القيمة دي. 260-280 للهوت إند بـ PTFE، ولحد 300+ للـ all-metal.")),
    ("therm_bed", _h("page_thermal", "[heater_bed] sensor_type", "Bed thermistor type.", "نوع ثرمستور القاعدة.")),
    ("pid_b_kp", _h("page_thermal", "[heater_bed] pid_Kp", "From PID_CALIBRATE HEATER=heater_bed TARGET=60, then SAVE_CONFIG.",
                    "من PID_CALIBRATE HEATER=heater_bed TARGET=60 وبعدين SAVE_CONFIG.")),
    ("pid_b_ki", _h("page_thermal", "[heater_bed] pid_Ki", "See bed PID Kp.", "شوف PID Kp بتاع القاعدة.")),
    ("pid_b_kd", _h("page_thermal", "[heater_bed] pid_Kd", "See bed PID Kp.", "شوف PID Kp بتاع القاعدة.")),
    ("max_temp_bed", _h("page_thermal", "[heater_bed] max_temp", "Bed safety limit, usually 110-130.", "حد أمان القاعدة، غالبًا 110-130.")),
    ("cool_room", _h("page_thermal", "[verify_heater extruder] / [verify_heater heater_bed]",
                     "Relaxed heater verification for cold rooms or strong part fans that cause 'Heater not heating at expected rate'. Keep it off otherwise.",
                     "حماية حرارية أوسع للأوض الباردة أو المراوح القوية اللي بتعمل 'Heater not heating at expected rate'. سيبها مقفولة غير كده.")),
    ("fan_max", _h("page_thermal", "[fan] max_power",
                   "Caps the part cooling fan. 1.0 = full power; lower it if 100% is too strong for your fan.",
                   "حد أقصى لمروحة تبريد القطعة. 1.0 = كاملة، قلّله لو 100% قوية زيادة على مروحتك.")),
    ("hotend_fan_temp", _h("page_thermal", "[heater_fan hotend_fan] heater_temp",
                           "The heatsink fan turns on above this hotend temperature. 50 °C is safe.", "مروحة الهيت سنك بتشتغل فوق الحرارة دي. 50 درجة آمنة.")),
    # probe
    ("probe", _h("page_probe", "[probe] / [bltouch]",
                 "Inductive/switch probe, BLTouch (or clones like CR Touch), or none (Z endstop switch). A probe enables bed mesh and Z leveling.",
                 "مسبار بروكسيمتي/سويتش، أو BLTouch (أو شبيهه زي CR Touch)، أو مفيش (سويتش ليميت Z). المسبار بيفعّل شبكة القاعدة وتسوية Z.")),
    ("probe_x", _h("page_probe", "[probe] x_offset",
                   "Probe position relative to the nozzle on X. Probe to the right of the nozzle = positive, left = negative.",
                   "مكان المسبار بالنسبة للنوزل على X. المسبار يمين النوزل = موجب، شمال = سالب.")),
    ("probe_y", _h("page_probe", "[probe] y_offset", "Probe behind the nozzle = positive, in front = negative.", "المسبار ورا النوزل = موجب، قدامه = سالب.")),
    ("probe_z", _h("page_probe", "[probe] z_offset",
                   "Distance between probe trigger and nozzle. Run PROBE_CALIBRATE (paper test), then SAVE_CONFIG. The app reads it back from SAVE_CONFIG.",
                   "المسافة بين لحظة اشتغال المسبار والنوزل. اعمل PROBE_CALIBRATE (اختبار الورقة) وبعدين SAVE_CONFIG. البرنامج بيقراها من SAVE_CONFIG.")),
    ("probe_samples", _h("page_probe", "[probe] samples", "How many times each point is probed. 2-3 is more reliable.", "كام مرة كل نقطة بتتقاس. 2-3 أدق.")),
    ("mesh_margin", _h("page_probe", "[bed_mesh] mesh_min / mesh_max",
                       "Distance kept from the bed edges (clips, magnets). The app also keeps the probe reachable.",
                       "المسافة من حواف القاعدة (المشابك، المغناطيس). البرنامج بيتأكد كمان إن المسبار يوصل.")),
    ("mesh_count", _h("page_probe", "[bed_mesh] probe_count", "Points per axis. 5 is a good default, 7-9 for large or warped beds.", "عدد النقط لكل محور. 5 كويسة، و 7-9 للقواعد الكبيرة أو المعووجة.")),
    # extras
    ("leds", _h("page_extras", "[neopixel case_leds]", "A WS2812/NeoPixel strip connected to the board.", "شريط WS2812/NeoPixel متوصل بالبورده.")),
    ("led_count", _h("page_extras", "[neopixel case_leds] chain_count", "Number of LEDs on the strip.", "عدد اللمبات في الشريط.")),
    ("led_order", _h("page_extras", "[neopixel case_leds] color_order", "Try GRB first; if red and green are swapped use RGB.", "جرّب GRB الأول، ولو الأحمر والأخضر متبدلين استخدم RGB.")),
    ("led_effects", _h("page_extras", "[led_effect ...]",
                       "Animated indicators: the strip fills with heater temperature and print progress. Requires the klipper-led_effect plugin.",
                       "مؤشرات متحركة: الشريط يمتلي مع حرارة السخان وتقدم الطبعة. محتاج إضافة klipper-led_effect.")),
    ("shaper", _h("page_extras", "[input_shaper]",
                  "Cancels ringing so you can print faster. Measure the frequencies with SHAPER_CALIBRATE (accelerometer) or a ringing tower.",
                  "بيلغي التموجات عشان تطبع أسرع. قيس الترددات بـ SHAPER_CALIBRATE (حساس تسارع) أو برج التموجات.")),
    ("shaper_x", _h("page_extras", "[input_shaper] shaper_freq_x", "Resonance frequency of X, from SHAPER_CALIBRATE.", "تردد الرنين لـ X، من SHAPER_CALIBRATE.")),
    ("shaper_type_x", _h("page_extras", "[input_shaper] shaper_type_x", "Shaper algorithm. mzv is a good default; use what SHAPER_CALIBRATE recommends.", "نوع التنعيم. mzv كويس كبداية، واستخدم اللي SHAPER_CALIBRATE بيقترحه.")),
    ("shaper_y", _h("page_extras", "[input_shaper] shaper_freq_y", "Resonance frequency of Y. On a bed slinger measure it with the sensor on the bed.", "تردد الرنين لـ Y. في القاعدة المتحركة قيسه والحساس على القاعدة.")),
    ("shaper_type_y", _h("page_extras", "[input_shaper] shaper_type_y", "Shaper algorithm for Y.", "نوع التنعيم لـ Y.")),
    ("shaper_z", _h("page_extras", "[input_shaper] shaper_freq_z", "Optional Z shaping (0 = off). Only useful with fast Z moves.", "تنعيم Z اختياري (0 = مقفول). مفيد بس مع حركات Z سريعة.")),
    ("shaper_type_z", _h("page_extras", "[input_shaper] shaper_type_z", "Shaper algorithm for Z.", "نوع التنعيم لـ Z.")),
    ("damping", _h("page_extras", "[input_shaper] damping_ratio_x / y", "Keep 0.1 unless SHAPER_CALIBRATE tells you otherwise.", "سيبها 0.1 إلا لو SHAPER_CALIBRATE قال غير كده.")),
    ("fil_sensor", _h("page_extras", "[filament_switch_sensor filament_sensor]", "Pauses the print when the filament runs out.", "بيوقف الطبعة مؤقتًا لما الفيلامنت يخلص.")),
    ("arcs", _h("page_extras", "[gcode_arcs]", "Accept G2/G3 arcs (Arc Fitting in the slicer).", "يقبل أقواس G2/G3 (Arc Fitting في السلايسر).")),
    ("exclude_object", _h("page_extras", "[exclude_object]", "Cancel one failed part during a print. Turn on 'Label objects' in the slicer.", "إلغاء قطعة فاشلة أثناء الطباعة. فعّل 'Label objects' في السلايسر.")),
    ("host_temp", _h("page_extras", "[temperature_sensor host]", "Shows the Raspberry Pi temperature in Mainsail/Fluidd.", "بيعرض حرارة الراسبيري في Mainsail/Fluidd.")),
    ("mcu_temp", _h("page_extras", "[temperature_sensor mcu]", "Shows the board temperature. Not available on LPC176x (SKR 1.3/1.4) and AVR boards.", "بيعرض حرارة البورده. مش متاح على LPC176x (SKR 1.3/1.4) ولا بوردات AVR.")),
    ("idle_timeout_min", _h("page_extras", "[idle_timeout] timeout", "Turn off motors and heaters after this many idle minutes. 0 = Klipper default (10 minutes).", "يقفل المحركات والسخانات بعد الدقائق دي من الخمول. 0 = افتراضي كليبر (10 دقايق).")),
    ("retraction", _h("page_extras", "[firmware_retraction]",
                      "The printer handles retraction (G10/G11) instead of the slicer, so you can tune it during a print with SET_RETRACTION. Enable 'Use firmware retraction' in the slicer.",
                      "الطابعة بتعمل السحب (G10/G11) بدل السلايسر، فتقدر تظبطه أثناء الطباعة بـ SET_RETRACTION. فعّل 'Use firmware retraction' في السلايسر.")),
    ("retract_length", _h("page_extras", "[firmware_retraction] retract_length", "Direct drive: 0.5-1 mm. Bowden: 3-6 mm.", "دايركت: 0.5-1 مم. بودن: 3-6 مم.")),
    ("retract_speed", _h("page_extras", "[firmware_retraction] retract_speed", "Typically 30-50 mm/s.", "غالبًا 30-50 مم/ث.")),
    ("unretract_speed", _h("page_extras", "[firmware_retraction] unretract_speed", "Typically 20-40 mm/s.", "غالبًا 20-40 مم/ث.")),
    ("print_macros", _h("page_extras", "[gcode_macro START_PRINT] / END_PRINT / M600",
                        "Ready macros: heat, home, level, mesh, purge / retract, park, cool down / filament change. Put START_PRINT and END_PRINT in the slicer's start and end G-code.",
                        "ماكروهات جاهزة: تسخين، تصفير، تسوية، شبكة، خط تنضيف / سحب، ركن، تبريد / تغيير فيلامنت. حط START_PRINT و END_PRINT في كود البداية والنهاية في السلايسر.")),
    ("adaptive_mesh", _h("page_extras", "BED_MESH_CALIBRATE ADAPTIVE=1",
                         "Measure the bed only under the printed parts - faster starts. Needs exclude object and 'Label objects' in the slicer.",
                         "يقيس القاعدة تحت القطع المطبوعة بس - بداية أسرع. محتاج «إلغاء قطعة» و 'Label objects' في السلايسر.")),
    ("purge_line", _h("page_extras", "START_PRINT", "Draws a line at the front-left edge before printing to prime the nozzle.", "بيرسم خط عند الحرف القدامي الشمال قبل الطباعة عشان يجهّز النوزل.")),
])


def page_guide(builder):
    item = PAGE_GUIDE.get(builder)
    if not item:
        return ""
    return item[1] if get_lang() == "ar" and item[1] else item[0]


def help_text(key):
    h = HELP.get(key)
    if not h:
        return ""
    return h["ar"] if get_lang() == "ar" and h["ar"] else h["en"]


def help_cfg(key):
    h = HELP.get(key)
    return h["cfg"] if h else ""
