# -*- coding: utf-8 -*-
"""Checks that catch the mistakes that stop Klipper from starting (or ruin prints)."""
import re

from .boards import mcu_temp_supported, strip_mods
from .cfgtools import cfg_parser, fmt as n, save_as_cfg, split_save
from .generator import mesh_bounds
from .i18n import tr
from .model import DRIVER_INFO, MOTOR_LABEL, PRIMARY, bus_keys, driver_bus, enabled_motors, z_motors


def active_pins(P):
    """[(label, pin)] of every pin the generated config will use."""
    out = []
    for mid in enabled_motors(P):
        m = P["motors"][mid]
        lab = MOTOR_LABEL[mid]
        out += [(lab + " step", m["step_pin"]), (lab + " dir", m["dir_pin"]), (lab + " enable", m["enable_pin"])]
        if mid in ("x", "y"):
            if m["sensorless"]:
                out.append((lab + " diag", m["diag_pin"]))
            else:
                out.append((lab + " endstop", m["endstop_pin"]))
        if mid == "z" and P["probe"] == "none":
            out.append((lab + " endstop", m["endstop_pin"]))
    p = P["pins"]
    roles = ["e_heater", "e_sensor"] + (["bed_heater", "bed_sensor"] if p.get("bed_heater") else [])
    roles += [r for r in ("fan", "hotend_fan") if p.get(r)]
    if P["probe"] == "bltouch":
        roles += ["bl_sensor", "bl_control"]
    elif P["probe"] == "inductive":
        roles.append("probe")
    if P["leds"]:
        roles.append("neopixel")
    if P["fil_sensor"]:
        roles.append("fil_sensor")
    return out + [(tr("pin." + r), p.get(r, "")) for r in roles]


# which page fixes a check (by message key)
VAL_PAGE = {
    "parse": "page_files", "duplicates": "page_files", "no_duplicates": "page_files", "section_elsewhere": "page_files",
    "klipper_warning": "page_files", "serial": "page_board", "pins_empty": "page_pins", "pin_conflict": "page_pins",
    "slot_conflict": "page_motors", "no_slot": "page_motors", "tmc": "page_motors", "current_high": "page_motors",
    "hold_above_run": "page_motors", "microsteps": "page_motors", "sensorless": "page_motors",
    "diag_polarity": "page_motors", "sg_range": "page_motors", "autotune": "page_motors",
    "mechanics_differ": "page_motors", "qgl": "page_motors", "multi_z_no_probe": "page_motors",
    "ref_z_tilt": "page_motors", "ref_qgl": "page_motors", "z_accel": "page_machine", "kinematics": "page_machine",
    "mesh": "page_probe", "probe_z_zero": "page_probe", "ref_probe": "page_probe", "pa": "page_thermal",
    "fan_low": "page_thermal", "shaper": "page_extras", "led_plugin": "page_extras", "mcu_temp": "page_extras",
    "adaptive_needs_exclude": "page_extras", "slicer_start": "page_extras", "retraction_slicer": "page_extras",
    "ref_leds": "page_extras", "ref_led_effects": "page_extras", "ref_fil_sensor": "page_extras",
    "ref_retraction": "page_extras", "ready": "page_preview", "custom": "page_features",
    "section_enabled": "page_features", "section_disabled": "page_features", "mcu_missing": "page_features",
}


def check_page(key):
    name = key.split(".", 1)[-1]
    for prefix in sorted(VAL_PAGE, key=len, reverse=True):
        if name == prefix or name.startswith(prefix + "_") or name.startswith(prefix):
            return VAL_PAGE[prefix]
    return "page_preview"


def validate(P, text, board=None, elsewhere=None, klipper_warnings=None):
    """Returns [(level, message, page)] with level in error / warn / ok and the page that fixes it.

    elsewhere        - {section: file} of sections defined in included files
    klipper_warnings - configfile.warnings reported by the running Klipper
    """
    R = []
    E = lambda k, **kw: R.append(("error", tr(k, **kw), check_page(k)))
    W = lambda k, **kw: R.append(("warn", tr(k, **kw), check_page(k)))
    O = lambda k, **kw: R.append(("ok", tr(k, **kw), check_page(k)))

    main, save = split_save(text)
    try:
        c = cfg_parser(main + "\n" + save_as_cfg(save))
        O("val.parse_ok", count=len(c.sections()))
    except Exception as e:
        E("val.parse_error", err=str(e))
        return R

    names = re.findall(r"^\[([^\]\n]+)\]", main, re.M)
    dup = sorted({x for x in names if names.count(x) > 1})
    if dup:
        W("val.duplicates", names=", ".join(dup))
    else:
        O("val.no_duplicates")

    serial = P["mcu_serial"]
    if "XXXX" in serial or "12345" in serial or not serial.strip():
        E("val.serial_placeholder")
    elif board and serial.startswith("/dev/serial/by-id/usb-Klipper_"):
        chip = serial[len("/dev/serial/by-id/usb-Klipper_"):].split("_")[0].lower()
        procs = board.get("mcu", {}).get("processors") or []
        if procs and chip and not any(chip.startswith(p) or p.startswith(chip.replace("xx", "")) for p in procs):
            W("val.serial_board_mismatch", chip=chip, board=board["name"])

    # ---------------- pins
    pins = active_pins(P)
    empty = [lab for lab, v in pins if not (v or "").strip()]
    if empty:
        E("val.pins_empty", pins=" / ".join(empty))
    seen = {}
    for lab, pin in pins:
        base = strip_mods(pin)
        if not base or lab.endswith(" enable"):  # several boards share one enable pin between drivers
            continue
        pair = {seen.get(base, ""), lab}
        probe_share = any("Z endstop" in x for x in pair) and any(x in (tr("pin.probe"), tr("pin.bl_sensor")) for x in pair)
        if base in seen and not probe_share:
            E("val.pin_conflict", pin=base, a=seen[base], b=lab)
        seen.setdefault(base, lab)

    # ---------------- motors & drivers
    slots_used = {}
    for mid in enabled_motors(P):
        m = P["motors"][mid]
        lab = MOTOR_LABEL[mid]
        info = DRIVER_INFO.get(m["driver"], DRIVER_INFO["none"])
        if m["slot"]:
            if m["slot"] in slots_used:
                E("val.slot_conflict", slot=m["slot"], a=slots_used[m["slot"]], b=lab)
            slots_used.setdefault(m["slot"], lab)
        elif board:
            W("val.no_slot", motor=lab)
        bus = driver_bus(m["driver"], m["bus"])
        if bus == "uart" and not m["bus"].get("uart_pin"):
            E("val.tmc_missing", axis=lab, key="uart_pin")
        if bus == "spi" and not m["bus"].get("cs_pin"):
            E("val.tmc_missing", axis=lab, key="cs_pin")
        if m["driver"] == "tmc2660" and m["sense_resistor"] <= 0:
            E("val.tmc_missing", axis=lab, key="sense_resistor")
        if m["driver"] == "tmc2208" and m["bus"].get("uart_address", "0").strip() not in ("", "0"):
            E("val.tmc2208_shared_uart", motor=lab)
        if info["max_current"] and m["run_current"] > info["max_current"]:
            W("val.current_high", motor=lab, current=n(m["run_current"]), limit=n(info["max_current"]),
              driver=m["driver"].upper())
        if m["hold_current"] > m["run_current"]:
            W("val.hold_above_run", motor=lab)
        if m["microsteps"] & (m["microsteps"] - 1):
            E("val.microsteps", motor=lab)
        if m["microsteps"] > 64:
            W("val.microsteps_high", motor=lab)
        if m["sensorless"]:
            if mid not in ("x", "y"):
                E("val.sensorless_axis", motor=lab)
            elif not info["sg_key"]:
                E("val.sensorless_driver", motor=lab, driver=m["driver"].upper())
            else:
                if not m["diag_pin"]:
                    E("val.sensorless_diag", motor=lab)
                elif bus == "spi" and "!" not in m["diag_pin"]:
                    W("val.diag_polarity", motor=lab)
                if m["hold_current"] > 0:
                    W("val.sensorless_hold", motor=lab)
                if m["autotune"] and P["homing_speed"] <= m["rotation_distance"]:
                    W("val.sensorless_autotune_speed", motor=lab)
                sg = m["sg"] if m["sg"] is not None else info["sg_default"]
                lo, hi = info["sg_range"]
                if not lo <= sg <= hi:
                    E("val.sg_range", motor=lab, lo=lo, hi=hi)
        if m["autotune"] and m["driver"] not in ("tmc2209", "tmc2240", "tmc5160", "tmc2130", "tmc2208"):
            W("val.autotune_driver", motor=lab)
        prim = PRIMARY.get(mid)
        if prim and P["motors"][prim]["enabled"]:
            pm = P["motors"][prim]
            if abs(pm["rotation_distance"] - m["rotation_distance"]) > 1e-6 or pm["microsteps"] != m["microsteps"] \
                    or pm["full_steps"] != m["full_steps"]:
                W("val.mechanics_differ", motor=lab, primary=MOTOR_LABEL[prim])
    if any(P["motors"][mid]["autotune"] for mid in enabled_motors(P)):
        O("val.autotune_plugin")

    # ---------------- motion
    if P["max_z_accel"] > P["max_accel"]:
        E("val.z_accel", z=P["max_z_accel"], xy=P["max_accel"])
    if P["kinematics"] not in ("cartesian", "corexy"):
        E("val.kinematics", kin=P["kinematics"])

    # ---------------- probe / leveling
    zs = z_motors(P)
    if P["probe"] != "none":
        x0, y0, x1, y1 = mesh_bounds(P)
        if x0 >= x1 or y0 >= y1:
            E("val.mesh_empty")
        else:
            O("val.mesh_area", x0=n(x0), x1=n(x1), y0=n(y0), y1=n(y1))
        if abs(P["probe_z"]) < 0.001:
            W("val.probe_z_zero")
        if P["z_leveling"] == "quad_gantry_level" and len(zs) >= 2 and len(zs) != 4:
            E("val.qgl_needs_4", count=len(zs))
        if P["z_leveling"] == "quad_gantry_level" and len(zs) == 4 and P["kinematics"] == "cartesian":
            W("val.qgl_bed_slinger")
    elif len(zs) >= 2:
        W("val.multi_z_no_probe")

    # ---------------- tuning & add-ons
    if P["pa"] <= 0:
        W("val.pa_zero")
    elif P["bowden"] and P["pa"] < 0.12:
        W("val.pa_bowden_low", pa=n(P["pa"]))
    if P["shaper"] and abs(P["shaper_x"] - P["shaper_y"]) < 0.05:
        W("val.shaper_equal", f=n(P["shaper_x"], 1))
    if P["shaper"] and P["shaper_z"] > 0 and P["max_z_accel"] < 500:
        W("val.shaper_z_low_accel")
    if P["fan_max"] < 0.2:
        W("val.fan_low")
    if P["leds"] and P["led_effects"]:
        O("val.led_plugin")
    if P["mcu_temp"] and mcu_temp_supported(board) is False:
        E("val.mcu_temp_unsupported", family=board.get("mcu", {}).get("family"))
    if P["print_macros"]:
        if P["probe"] != "none" and P["adaptive_mesh"] and not P["exclude_object"]:
            W("val.adaptive_needs_exclude")
        O("val.slicer_start", cmd="START_PRINT BED=[first_layer_bed_temperature] EXTRUDER=[first_layer_temperature]")
    if P["retraction"]:
        O("val.retraction_slicer")

    # ---------------- references from the user's own macros
    body = re.sub(r"^\s*(\[[^\]\n]+\]|[#;]).*$", "", main, flags=re.M)  # ignore headers and comments
    refs = [
        (not P["leds"] and "case_leds" in body, "val.ref_leds"),
        (P["leds"] and not P["led_effects"] and "SET_LED_EFFECT" in body, "val.ref_led_effects"),
        (len(zs) < 2 and ("Z_TILT_ADJUST" in body or "stepper_z1" in body), "val.ref_z_tilt"),
        (not (len(zs) == 4 and P["z_leveling"] == "quad_gantry_level") and "QUAD_GANTRY_LEVEL" in body, "val.ref_qgl"),
        (P["probe"] == "none" and ("BED_MESH_CALIBRATE" in body or "PROBE_CALIBRATE" in body), "val.ref_probe"),
        (not P["fil_sensor"] and "filament_switch_sensor" in body, "val.ref_fil_sensor"),
        (not P["retraction"] and re.search(r"^\s*(G10|G11|SET_RETRACTION)\b", body, re.M), "val.ref_retraction"),
    ]
    for cond, key in refs:
        if cond:
            E(key)

    # ---------------- added features and switched sections
    from .features import empty_pins, section_names
    from .merge import is_managed as _managed
    for item in P.get("custom_sections", []):
        if not item.get("enabled", True):
            continue
        text = item.get("text") or ""
        secs = section_names(text)
        if not secs:
            E("val.custom_no_section")
            continue
        try:
            cfg_parser(text)
        except Exception as e:  # configparser raises several error types
            E("val.custom_parse", section=secs[0], err=str(e).splitlines()[0])
        for s in secs:
            if _managed(s, P):
                E("val.custom_managed", section=s)
        pins_left = empty_pins(text)
        if pins_left:
            W("val.custom_pins", section=secs[0], pins=", ".join(pins_left))
    # a pin on a second MCU (pico:gpio1, rpi:None) needs that [mcu name] section switched on
    mcus = {n.split(None, 1)[1] for n in names if n.startswith("mcu ")}
    for key, mcu in re.findall(r"^\s*([a-z_]*pin)\s*[:=]\s*[\^~!]*([a-z][a-z0-9_]*):", body, re.M):
        if mcu != "probe" and "_stepper_" not in mcu and mcu not in mcus:
            E("val.mcu_missing", mcu=mcu, key=key)
            break
    for s in P.get("enabled_sections", []):
        O("val.section_enabled", section=s)
    for s in P.get("disabled_sections", []):
        O("val.section_disabled", section=s)

    # ---------------- modular configs
    if elsewhere:
        from .merge import is_managed
        for name in sorted(set(names)):
            if name in elsewhere and is_managed(name, P):
                W("val.section_elsewhere", section=name, file=elsewhere[name])
    for w in klipper_warnings or []:
        W("val.klipper_warning", msg=w.get("message", str(w)) if isinstance(w, dict) else str(w))

    if not [r for r in R if r[0] == "error"]:
        O("val.ready")
    return R
