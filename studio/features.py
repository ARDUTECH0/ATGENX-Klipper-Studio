# -*- coding: utf-8 -*-
"""Features: built-in switches, turning any config section on/off, and a catalog of sections to add.

* Built-in features are app settings (probe, LEDs, input shaper, ...) with dependencies.
* Any other section of printer.cfg can be switched off (commented out with '#', never deleted)
  and switched back on (uncommented).
* The catalog adds well-known Klipper sections and plugin sections from a template.
"""
import re
from collections import OrderedDict

from .cfgtools import SECTION_RE, split_save
from .i18n import get_lang
from .model import Z_MOTORS

# --------------------------------------------------------------------------- built-in features
# id: (icon, category, page, requires plugin, depends on)
BUILTIN = OrderedDict([
    ("probe", ("🎯", "leveling", "page_probe", "", [])),
    ("multi_z", ("⚖️", "leveling", "page_motors", "", ["probe"])),
    ("adaptive_mesh", ("🗺️", "leveling", "page_extras", "", ["probe", "print_macros", "exclude_object"])),
    ("sensorless", ("🧲", "motion", "page_motors", "", [])),
    ("awd", ("🔁", "motion", "page_motors", "", [])),
    ("autotune", ("🎛️", "motion", "page_motors", "klipper_tmc_autotune", [])),
    ("shaper", ("〰️", "quality", "page_extras", "", [])),
    ("retraction", ("↩️", "quality", "page_extras", "", [])),
    ("arcs", ("⌒", "quality", "page_extras", "", [])),
    ("exclude_object", ("✂️", "printing", "page_extras", "", [])),
    ("print_macros", ("▶️", "printing", "page_extras", "", [])),
    ("fil_sensor", ("🧵", "printing", "page_extras", "", [])),
    ("leds", ("💡", "lights", "page_extras", "", [])),
    ("led_effects", ("🌈", "lights", "page_extras", "klipper-led_effect", ["leds"])),
    ("host_temp", ("🌡️", "monitoring", "page_extras", "", [])),
    ("mcu_temp", ("🔥", "monitoring", "page_extras", "", [])),
    ("idle_timeout", ("⏱️", "monitoring", "page_extras", "", [])),
    ("cool_room", ("❄️", "monitoring", "page_thermal", "", [])),
])
CATEGORY_ICONS = OrderedDict([("leveling", "🎯"), ("motion", "⚙️"), ("quality", "✨"), ("printing", "🖨️"),
                              ("lights", "💡"), ("monitoring", "📈")])

BOOL_KEYS = {"shaper", "retraction", "arcs", "exclude_object", "print_macros", "fil_sensor", "leds",
             "led_effects", "host_temp", "mcu_temp", "cool_room", "adaptive_mesh"}


def feature_on(P, fid):
    if fid in BOOL_KEYS:
        on = bool(P[fid])
        return on and (P["probe"] != "none" and P["print_macros"]) if fid == "adaptive_mesh" else on
    if fid == "probe":
        return P["probe"] != "none"
    if fid == "multi_z":
        return P["motors"]["z1"]["enabled"]
    if fid == "sensorless":
        return any(P["motors"][m]["sensorless"] for m in ("x", "y"))
    if fid == "awd":
        return P["motors"]["x1"]["enabled"] or P["motors"]["y1"]["enabled"]
    if fid == "autotune":
        return any(P["motors"][m]["autotune"] for m in P["motors"] if P["motors"][m]["enabled"])
    if fid == "idle_timeout":
        return P["idle_timeout_min"] > 0
    return False


def set_feature(P, fid, on, changes=None):
    """Switches a feature and its dependencies. Returns the list of feature ids that changed."""
    changes = [] if changes is None else changes
    if feature_on(P, fid) == on:
        return changes
    if on:
        for dep in BUILTIN[fid][4]:
            if not feature_on(P, dep):
                set_feature(P, dep, True, changes)
    else:
        for other, spec in BUILTIN.items():
            if fid in spec[4] and feature_on(P, other):
                set_feature(P, other, False, changes)
    if fid in BOOL_KEYS:
        P[fid] = on
    elif fid == "probe":
        P["probe"] = "inductive" if on else "none"
    elif fid == "multi_z":
        m = P["motors"]["z1"]
        if on:
            _copy_motor(P, "z", "z1")
        m["enabled"] = on
        if not on:
            for z in Z_MOTORS[2:]:
                P["motors"][z]["enabled"] = False
    elif fid == "sensorless":
        for ax in ("x", "y"):
            m = P["motors"][ax]
            m["sensorless"] = on and m["driver"] in ("tmc2209", "tmc2130", "tmc5160", "tmc2240")
            if m["sensorless"]:
                m["hold_current"] = 0.0
                if not m["diag_pin"] and m["endstop_pin"]:
                    m["diag_pin"] = "^" + m["endstop_pin"].lstrip("^~!")
    elif fid == "awd":
        for ax in ("x1", "y1"):
            if on:
                _copy_motor(P, ax[0], ax)
            P["motors"][ax]["enabled"] = on
    elif fid == "autotune":
        if not on:
            for m in P["motors"].values():
                m["autotune"] = ""
    elif fid == "idle_timeout":
        P["idle_timeout_min"] = 30 if on else 0
    changes.append(fid)
    return changes


def _copy_motor(P, src, dst):
    for k in ("driver", "run_current", "microsteps", "rotation_distance", "full_steps", "stealthchop",
              "interpolate", "invert"):
        P["motors"][dst][k] = P["motors"][src][k]


# --------------------------------------------------------------------------- sections of a file
COMMENTED_SECTION_RE = re.compile(r"^#\s?\[([^\]\n]+)\]\s*$")


def list_sections(text, is_managed):
    """[(name, enabled)] of the sections a user can switch: active ones not managed by the app,
    and commented-out ones ('#[name]') that could be switched back on."""
    main, _ = split_save(text or "")
    out, seen = [], set()
    for ln in main.split("\n"):
        m = SECTION_RE.match(ln)
        if m:
            name = m.group(1).strip()
            if name not in seen and not is_managed(name):
                out.append((name, True))
                seen.add(name)
            continue
        c = COMMENTED_SECTION_RE.match(ln)
        if c:
            name = c.group(1).strip()
            if name not in seen and not is_managed(name) and _looks_like_section(name):
                out.append((name, False))
                seen.add(name)
    active = {n for n, on in out if on}
    return [(n, on) for n, on in out if on or n not in active]


def _looks_like_section(name):
    return bool(re.match(r"^[a-z_0-9]+( [A-Za-z0-9_.\-/* ]+)?$", name))


def apply_section_toggles(text, disable=(), enable=()):
    """Comments out sections in `disable` and uncomments sections in `enable`. Only printer.cfg's
    main part is touched; SAVE_CONFIG is kept as is."""
    if not text or not (disable or enable):
        return text
    main, save = split_save(text)
    lines = main.split("\n")
    out, i = [], 0
    while i < len(lines):
        ln = lines[i]
        m = SECTION_RE.match(ln)
        c = COMMENTED_SECTION_RE.match(ln)
        if m and m.group(1).strip() in disable:
            j = i + 1
            while j < len(lines) and not SECTION_RE.match(lines[j]) and not COMMENTED_SECTION_RE.match(lines[j]):
                j += 1
            block = lines[i:j]
            while len(block) > 1 and (not block[-1].strip() or block[-1].lstrip().startswith("#")):
                j -= 1
                block.pop()
            out += [("#" + b) if b.strip() and not b.lstrip().startswith("#") else b for b in block]
            i = j
            continue
        if c and c.group(1).strip() in enable:
            out.append(re.sub(r"^#\s?", "", ln, count=1))
            i += 1
            while i < len(lines):
                nxt = lines[i]
                body = re.sub(r"^#\s?", "", nxt, count=1) if nxt.startswith("#") else None
                if body is None or COMMENTED_SECTION_RE.match(nxt) or not nxt.strip():
                    break
                # keep going over options, indented continuation lines and inner comments ("# # note")
                if not (re.match(r"^[A-Za-z0-9_]+\s*[:=]", body) or body[:1].isspace() or body.startswith("#")
                        or not body.strip()):
                    break  # an ordinary comment line - the section ends here
                out.append(body)
                i += 1
            continue
        out.append(ln)
        i += 1
    return "\n".join(out) + save


# --------------------------------------------------------------------------- catalog
# id: (icon, category, requires, template). {bed_x2} etc. are filled from the project.
CATALOG = OrderedDict([
    ("mainsail", ("🖥️", "interface", "Mainsail", "[include mainsail.cfg]")),
    ("fluidd", ("🖥️", "interface", "Fluidd", "[include fluidd.cfg]")),
    ("timelapse", ("🎞️", "interface", "moonraker-timelapse", "[include timelapse.cfg]")),
    ("shaketune", ("📊", "tuning", "Klippain Shake&Tune", "[shaketune]\n# result_folder: ~/printer_data/config/ShakeTune_results")),
    ("adxl_pi", ("📐", "tuning", "", "[mcu rpi]\nserial: /tmp/klipper_host_mcu\n\n[adxl345]\ncs_pin: rpi:None\n\n"
                                     "[resonance_tester]\naccel_chip: adxl345\nprobe_points:\n    {bed_x2}, {bed_y2}, 20")),
    ("adxl_pico", ("📐", "tuning", "", "[mcu adxl]\nserial: /dev/serial/by-id/usb-Klipper_rp2040_XXXX-if00\n\n"
                                       "[adxl345]\ncs_pin: adxl:gpio1\nspi_bus: spi0a\naxes_map: x,z,y\n\n"
                                       "[resonance_tester]\naccel_chip: adxl345\nprobe_points:\n    {bed_x2}, {bed_y2}, 20\n\n"
                                       "[output_pin power_mode]\npin: adxl:gpio23")),
    ("adxl_board", ("📐", "tuning", "", "[adxl345]\ncs_pin: \nspi_bus: \n\n[resonance_tester]\naccel_chip: adxl345\n"
                                        "probe_points:\n    {bed_x2}, {bed_y2}, 20")),
    ("skew_correction", ("📏", "tuning", "", "[skew_correction]")),
    ("axis_twist", ("🌀", "tuning", "", "[axis_twist_compensation]\ncalibrate_start_x: {margin}\ncalibrate_end_x: {bed_x_m}\n"
                                        "calibrate_y: {bed_y2}")),
    ("screws_tilt", ("🔩", "leveling", "", "[screws_tilt_adjust]\nscrew1: 30, 30\nscrew1_name: front left\n"
                                          "screw2: {bed_x_30}, 30\nscrew2_name: front right\nscrew3: {bed_x_30}, {bed_y_30}\n"
                                          "screw3_name: rear right\nscrew4: 30, {bed_y_30}\nscrew4_name: rear left\n"
                                          "horizontal_move_z: 10\nspeed: 50\nscrew_thread: CW-M3")),
    ("bed_screws", ("🔩", "leveling", "", "[bed_screws]\nscrew1: 30, 30\nscrew2: {bed_x_30}, 30\n"
                                         "screw3: {bed_x_30}, {bed_y_30}\nscrew4: 30, {bed_y_30}")),
    ("save_variables", ("💾", "macros", "", "[save_variables]\nfilename: ~/printer_data/config/variables.cfg")),
    ("force_move", ("🛠️", "macros", "", "[force_move]\nenable_force_move: True")),
    ("motion_sensor", ("🧵", "printing", "", "[filament_motion_sensor smart_sensor]\ndetection_length: 7.0\n"
                                             "extruder: extruder\nswitch_pin: \npause_on_runout: True")),
    ("controller_fan", ("🌬️", "fans", "", "[controller_fan electronics_fan]\npin: \nstepper: stepper_x, stepper_y, stepper_z")),
    ("chamber_fan", ("🌬️", "fans", "", "[temperature_fan chamber]\npin: \nsensor_type: Generic 3950\nsensor_pin: \n"
                                        "control: watermark\nmax_temp: 70\nmin_temp: 0\ntarget_temp: 40")),
    ("chamber_sensor", ("🌡️", "fans", "", "[temperature_sensor chamber]\nsensor_type: Generic 3950\nsensor_pin: ")),
    ("case_light", ("💡", "lights", "", "[output_pin caselight]\npin: \npwm: True\nvalue: 0\ncycle_time: 0.010")),
    ("beeper", ("🔔", "interface", "", "[output_pin beeper]\npin: \npwm: True\nvalue: 0\ncycle_time: 0.001")),
    ("button", ("🔘", "interface", "", "[gcode_button my_button]\npin: \npress_gcode:\n    M117 Button pressed")),
    ("servo", ("🦾", "hardware", "", "[servo my_servo]\npin: \nmaximum_servo_angle: 180")),
    ("blank", ("📝", "hardware", "", "[my_section]\n")),
])


def fill_template(P, template):
    m = P.get("mesh_margin", 15)
    values = {
        "bed_x2": _n(P["bed_x"] / 2), "bed_y2": _n(P["bed_y"] / 2),
        "bed_x_30": _n(P["bed_x"] - 30), "bed_y_30": _n(P["bed_y"] - 30),
        "margin": _n(max(m, 20)), "bed_x_m": _n(P["bed_x"] - max(m, 20)),
    }
    return template.format(**values)


def _n(v):
    return str(int(v)) if float(v).is_integer() else ("%.1f" % v)


def section_names(text):
    return [m.group(1).strip() for m in (SECTION_RE.match(l) for l in (text or "").split("\n")) if m]


def empty_pins(text):
    """Option names like 'pin:' or 'switch_pin:' left empty in a section template."""
    return re.findall(r"^([a-z_]*pin):\s*$", text or "", re.M)


def lang_text(pair):
    return pair[1] if get_lang() == "ar" and len(pair) > 1 and pair[1] else pair[0]
