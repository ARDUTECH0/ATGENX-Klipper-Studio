# -*- coding: utf-8 -*-
"""Builds the final printer.cfg: smart merge into an existing file, or a clean new file."""
import re
from collections import OrderedDict
from datetime import datetime

from . import APP_NAME, __version__
from .cfgtools import body_items, clean_save, item_value, parse_blocks, split_save, values_equal
from .generator import APP_MACROS, LED_EFFECTS, MACRO_MARK, generate, soft_keys
from .features import apply_section_toggles, section_names
from .i18n import tr

# Sections the app is responsible for. If one of them exists in the file but is
# no longer generated (feature switched off), it is removed.
MANAGED_EXACT = {
    "mcu", "printer", "stepper_x", "stepper_x1", "stepper_y", "stepper_y1", "stepper_z", "stepper_z1",
    "stepper_z2", "stepper_z3", "extruder", "heater_bed",
    "verify_heater extruder", "verify_heater heater_bed", "fan", "heater_fan hotend_fan",
    "probe", "bltouch", "safe_z_home", "bed_mesh", "z_tilt", "quad_gantry_level", "neopixel case_leds",
    "filament_switch_sensor filament_sensor", "input_shaper", "gcode_arcs", "exclude_object",
    "virtual_sdcard", "pause_resume", "display_status", "respond", "firmware_retraction", "idle_timeout",
} | {"led_effect " + k for k in LED_EFFECTS}

SUPPORTED_KINEMATICS = ("cartesian", "corexy")

_MOTORS = r"(stepper_x|stepper_x1|stepper_y|stepper_y1|stepper_z|stepper_z1|stepper_z2|stepper_z3|extruder)"
TMC_SECTION_RE = re.compile(r"^tmc(2130|2208|2209|2240|2660|5160)\s+" + _MOTORS + "$")
AUTOTUNE_SECTION_RE = re.compile(r"^autotune_tmc\s+" + _MOTORS + "$")

# Keys removed from a managed section when the generator no longer writes them
DROP_IF_ABSENT = {
    "stepper_x": {"homing_retract_dist", "full_steps_per_rotation"},
    "stepper_y": {"homing_retract_dist", "full_steps_per_rotation"},
    "stepper_z": {"position_endstop", "full_steps_per_rotation"},
    "fan": {"max_power"},
    "input_shaper": {"shaper_type_z", "shaper_freq_z", "damping_ratio_z"},
    "bed_mesh": {"relative_reference_index"},
    "tmc": {"hold_current", "tx_pin", "uart_address", "spi_bus", "spi_software_miso_pin",
            "spi_software_mosi_pin", "spi_software_sclk_pin", "diag_pin", "diag0_pin", "diag1_pin",
            "driver_sgthrs", "driver_sgt", "sense_resistor", "interpolate"},
    "autotune": {"tuning_goal", "voltage", "sg4_thrs", "sgt"},
    "motor": {"full_steps_per_rotation"},
}


def is_managed(name, P=None, body=None):
    """Is this section owned by the app? Macros only when they carry the app's mark."""
    if name.startswith("gcode_macro "):
        return name[len("gcode_macro "):] in APP_MACROS and body is not None and MACRO_MARK in "\n".join(body)
    if name in MANAGED_EXACT or TMC_SECTION_RE.match(name) or AUTOTUNE_SECTION_RE.match(name):
        return True
    if P is not None and name in ("temperature_sensor " + P["host_temp_name"], "temperature_sensor " + P["mcu_temp_name"]):
        return True
    return False


def _drop_keys(name):
    if TMC_SECTION_RE.match(name):
        return DROP_IF_ABSENT["tmc"]
    if AUTOTUNE_SECTION_RE.match(name):
        return DROP_IF_ABSENT["autotune"]
    if name in ("stepper_x1", "stepper_y1", "stepper_z1", "stepper_z2", "stepper_z3", "extruder"):
        return DROP_IF_ABSENT["motor"]
    return DROP_IF_ABSENT.get(name, set())


def merge_section(existing, generated, name):
    """Key level merge of one section.

    existing  - list of lines (first is the [header])
    generated - section text from the generator

    Unchanged values keep the user's exact line (formatting and inline comment).
    Changed values take the generated line. Keys the app doesn't know stay.
    """
    items = body_items(existing[1:])
    gen_items = body_items(generated.split("\n")[1:])
    gen = OrderedDict((it["key"], it) for it in gen_items if it["kind"] == "key")
    soft = soft_keys(name)
    drop = _drop_keys(name)

    out, seen, last_key_end = [existing[0]], set(), 1
    for it in items:
        if it["kind"] == "other":
            out += it["lines"]
            continue
        k = it["key"]
        if k in gen:
            if k in seen:
                continue
            seen.add(k)
            if k in soft or values_equal(item_value(it), item_value(gen[k])):
                out += it["lines"]
            else:
                out += gen[k]["lines"]
        elif k in drop:
            continue
        else:
            out += it["lines"]
        last_key_end = len(out)
    # defaults (soft keys) are only written into new sections, never added to existing ones
    missing = [line for k, g in gen.items() if k not in seen and k not in soft for line in g["lines"]]
    out[last_key_end:last_key_end] = missing
    return out


# ---------------------------------------------------------------- file layout & explanations
CATEGORIES = ("board", "motion", "motors", "heat", "probe", "lights", "extras", "macros")
BOARD_EXTRA_TYPES = ("static_digital_output", "output_pin", "mcp4018", "mcp4451", "mcp4728", "ad5206", "dac084",
                     "adc_scaled", "replicape", "sx1509", "pca9533", "controller_fan", "thermistor", "temperature_fan")
CATEGORY_OF = {"mcu": "board", "board_extra": "board", "printer": "motion", "stepper": "motors", "tmc": "motors",
               "autotune": "motors", "extruder": "heat", "heater_bed": "heat", "verify_heater": "heat", "fan": "heat",
               "heater_fan": "heat", "probe": "probe", "bltouch": "probe", "safe_z_home": "probe", "bed_mesh": "probe",
               "z_tilt": "probe", "quad_gantry_level": "probe", "neopixel": "lights", "led_effect": "lights",
               "gcode_macro": "macros"}


def section_type(name):
    t = name.split()[0]
    if t.startswith("stepper_"):
        return "stepper"
    if t.startswith("tmc"):
        return "tmc"
    if t == "autotune_tmc":
        return "autotune"
    if t in BOARD_EXTRA_TYPES:
        return "board_extra"
    return t


def section_category(name):
    return CATEGORY_OF.get(section_type(name), "extras")


def section_doc(name, previous=None):
    """Comment lines explaining a generated section (once for a run of the same type)."""
    t = section_type(name)
    if previous is not None and section_type(previous) == t and t not in ("stepper", "tmc"):
        return []
    text = tr("cfgdoc." + t)
    return [] if text == "cfgdoc." + t else ["# " + text]


def banner(category):
    return ["", "#" * 72, "#  " + tr("cfgcat." + category), "#" * 72]


def generated_comment_lines():
    """Every comment line the app itself writes (in any language)."""
    from .i18n import LANGS, STRINGS
    out = {"#" * 72}
    for key, entry in STRINGS.items():
        if key.startswith(("cfgdoc.", "cfgcat.", "cfg.")):
            for lang in LANGS:
                out.add("# " + entry[lang])
                out.add("#  " + entry[lang])
    return out


def layout_sections(gen):
    """Generated sections grouped by category, with a banner per group and an explanation per section."""
    names = sorted(gen, key=lambda s: CATEGORIES.index(section_category(s)))
    lines, cat, prev = [], None, None
    for name in names:
        c = section_category(name)
        if c != cat:
            lines += banner(c)
            cat, prev = c, None
        lines += [""] + section_doc(name, prev) + gen[name].split("\n")
        prev = name
    return lines


def header(P, ts):
    return "\n".join([
        "#" * 72,
        "#  %s  -  printer.cfg" % P.get("printer_name", "Klipper"),
        "#  %s %s  -  %s" % (APP_NAME, __version__, ts),
        "#",
        "#  " + tr("cfg.header_line1"),
        "#  " + tr("cfg.header_line2"),
        "#  " + tr("cfg.header_line3"),
        "#" * 72,
    ])


def added_features(P, existing_text):
    """Lines for the enabled catalog / custom sections that are not in the file yet."""
    existing = set(section_names(split_save(existing_text or "")[0]))
    lines = []
    for item in P.get("custom_sections", []):
        text = (item.get("text") or "").strip("\n")
        names = section_names(text)
        if not item.get("enabled", True) or not names or any(nm in existing for nm in names):
            continue
        lines += ["", "# " + tr("cfgdoc.custom")] + text.split("\n")
        existing.update(names)
    return lines


def _append_before_save(text, lines):
    if not lines:
        return text
    main, save = split_save(text)
    main = main.rstrip("\n") + "\n" + "\n".join(lines) + "\n"
    return main + ("\n" + save if save else "")


def build(P, current_text=None, mode="merge", keep_custom=True, board=None):
    gen = generate(P, board)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    if not current_text:
        text = "\n".join([header(P, ts)] + layout_sections(gen)).rstrip("\n") + "\n"
        return _append_before_save(text, added_features(P, text))

    # features switched on / off on the Features page (comment / uncomment, never delete)
    current_text = apply_section_toggles(current_text.replace("\r\n", "\n"),
                                         P.get("disabled_sections", ()), P.get("enabled_sections", ()))
    if P["kinematics"] not in SUPPORTED_KINEMATICS:
        # delta, polar, winch ... - never rewrite a machine the app can't model
        return _append_before_save(current_text, added_features(P, current_text))

    main, save = split_save(current_text)
    head, blocks = parse_blocks(main)
    save = clean_save(save)
    # the user's own START_PRINT / END_PRINT / M600 always win over the app's version
    user_macros = {b["name"] for b in blocks if b["name"] in gen and b["name"].startswith("gcode_macro ")
                   and not is_managed(b["name"], P, b["body"])}
    for name in user_macros:
        gen.pop(name)

    if mode == "merge":
        # line by line, so every untouched line (blank lines included) stays exactly as it was
        lines, used, insert_at = list(head), set(), None
        for b in blocks:
            name = b["name"]
            if name in user_macros:
                lines += b["lead"] + b["body"]
            elif name in gen and name not in used:
                used.add(name)
                lines += b["lead"] + merge_section(b["body"], gen[name], name)
                insert_at = len(lines)
            elif name in gen or is_managed(name, P, b["body"]):
                # duplicate of a generated section, or a feature that was switched off
                if any(l.strip() for l in b["lead"]):
                    lines += b["lead"]
            else:
                lines += b["lead"] + b["body"]
        new = [k for k in gen if k not in used]
        if new:
            add, prev = [], None
            for k in new:
                add += [""] + section_doc(k, prev) + gen[k].split("\n")
                prev = k
            at = len(head) if insert_at is None else insert_at
            lines[at:at] = add + [""]
        text = "\n".join(lines).rstrip("\n") + "\n"
    else:
        parts = [header(P, ts)] + layout_sections(gen) + [""]
        if keep_custom:
            kept = [b for b in blocks if not is_managed(b["name"], P, b["body"]) and b["name"] not in gen]
            if kept:
                ours = generated_comment_lines()
                parts += ["#" * 72, "#  " + tr("cfg.kept_sections"), "#" * 72, ""]
                parts += ["\n".join([l for l in b["lead"] if l.strip() not in ours] + b["body"]).strip("\n") + "\n"
                          for b in kept]
        text = re.sub(r"\n{4,}", "\n\n\n", "\n".join(parts)).rstrip("\n") + "\n"
    if save:
        text += "\n" + save
    return _append_before_save(text, added_features(P, text))
