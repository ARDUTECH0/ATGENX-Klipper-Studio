# -*- coding: utf-8 -*-
"""Builds the final printer.cfg: smart merge into an existing file, or a clean new file."""
import re
from collections import OrderedDict
from datetime import datetime

from . import APP_NAME, __version__
from .cfgtools import body_items, clean_save, item_value, parse_blocks, split_save, values_equal
from .generator import LED_EFFECTS, generate, soft_keys
from .i18n import tr

# Sections the app is responsible for. If one of them exists in the file but is
# no longer generated (feature switched off), it is removed.
MANAGED_EXACT = {
    "mcu", "printer", "stepper_x", "stepper_y", "stepper_z", "stepper_z1", "extruder", "heater_bed",
    "verify_heater extruder", "verify_heater heater_bed", "fan", "heater_fan hotend_fan",
    "probe", "bltouch", "safe_z_home", "bed_mesh", "z_tilt", "neopixel case_leds",
    "filament_switch_sensor filament_sensor", "input_shaper", "gcode_arcs", "exclude_object",
    "virtual_sdcard", "pause_resume", "display_status", "respond",
} | {"led_effect " + k for k in LED_EFFECTS}

TMC_SECTION_RE = re.compile(r"^tmc\d+\s+(stepper_x|stepper_y|stepper_z|stepper_z1|extruder)$")

# Keys removed from a managed section when the generator no longer writes them
DROP_IF_ABSENT = {
    "stepper_z": {"position_endstop"},
    "fan": {"max_power"},
    "input_shaper": {"shaper_type_z", "shaper_freq_z", "damping_ratio_z"},
    "bed_mesh": {"relative_reference_index"},
    "tmc": {"hold_current", "tx_pin", "uart_address", "spi_bus", "spi_software_miso_pin",
            "spi_software_mosi_pin", "spi_software_sclk_pin"},
}


def is_managed(name):
    return name in MANAGED_EXACT or bool(TMC_SECTION_RE.match(name))


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
    drop = DROP_IF_ABSENT.get("tmc" if TMC_SECTION_RE.match(name) else name, set())

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


def header(P, ts):
    return "\n".join([
        "#" * 72,
        "#  %s  -  printer.cfg" % P.get("printer_name", "Klipper"),
        "#  %s %s  -  %s" % (APP_NAME, __version__, ts),
        "#",
        "#  " + tr("cfg.header_line1"),
        "#  " + tr("cfg.header_line2"),
        "#" * 72,
    ])


def build(P, current_text=None, mode="merge", keep_custom=True, board=None):
    gen = generate(P, board)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    if not current_text:
        parts = [header(P, ts), ""] + [b + "\n" for b in gen.values()]
        return "\n".join(parts).rstrip("\n") + "\n"

    main, save = split_save(current_text)
    head, blocks = parse_blocks(main)
    save = clean_save(save)

    if mode == "merge":
        # line by line, so every untouched line (blank lines included) stays exactly as it was
        lines, used, insert_at = list(head), set(), None
        for b in blocks:
            name = b["name"]
            if name in gen and name not in used:
                used.add(name)
                lines += b["lead"] + merge_section(b["body"], gen[name], name)
                insert_at = len(lines)
            elif name in gen or is_managed(name):
                # duplicate of a generated section, or a feature that was switched off
                if any(l.strip() for l in b["lead"]):
                    lines += b["lead"]
            else:
                lines += b["lead"] + b["body"]
        new = [gen[k] for k in gen if k not in used]
        if new:
            add = []
            for g in new:
                add += [""] + g.split("\n")
            at = len(head) if insert_at is None else insert_at
            lines[at:at] = add + [""]
        text = "\n".join(lines).rstrip("\n") + "\n"
    else:
        parts = [header(P, ts), ""] + [g + "\n" for g in gen.values()]
        if keep_custom:
            kept = [b for b in blocks if not is_managed(b["name"]) and b["name"] not in gen]
            if kept:
                parts += ["#" * 72, "#  " + tr("cfg.kept_sections"), "#" * 72, ""]
                parts += ["\n".join(b["lead"] + b["body"]).strip("\n") + "\n" for b in kept]
        text = re.sub(r"\n{4,}", "\n\n\n", "\n".join(parts)).rstrip("\n") + "\n"
    if save:
        text += "\n" + save
    return text
