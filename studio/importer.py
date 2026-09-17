# -*- coding: utf-8 -*-
"""Reads an existing printer.cfg (including SAVE_CONFIG values) into project parameters."""
import re
from collections import OrderedDict

from .boards import detect_board, load_boards
from .cfgtools import cfg_parser, num, save_as_cfg, split_save
from .model import AXIS_SECTION, DRIVERS, SHAPERS, SPI_KEYS, UART_KEYS, new_params

DRIVER_IDS = [d for d, _ in DRIVERS]


class ImportError_(ValueError):
    pass


def import_config(text, boards=None, includes_text=""):
    """Returns (params, notes). notes = [(i18n key, kwargs)].

    includes_text: the other files included by printer.cfg, so modular configs import completely.
    """
    main, save = split_save(text)
    notes = []
    try:
        c = cfg_parser(includes_text + "\n" + main + "\n" + save_as_cfg(save))
    except Exception as e:  # configparser raises several error types
        raise ImportError_(str(e))
    P = new_params()
    pins, tmc = P["pins"], P["tmc"]

    def has(s):
        return c.has_section(s)

    def g(s, k, cast=float):
        if c.has_section(s) and c.has_option(s, k):
            return num(c.get(s, k), cast)
        return None

    def gs(s, k):
        if c.has_section(s) and c.has_option(s, k):
            return (c.get(s, k) or "").strip()
        return None

    def setp(key, val):
        if val is not None:
            P[key] = val

    setp("mcu_serial", gs("mcu", "serial") or (("canbus_uuid: " + gs("mcu", "canbus_uuid")) if gs("mcu", "canbus_uuid") else None))
    kin = gs("printer", "kinematics")
    if kin:
        P["kinematics"] = kin
        if kin not in ("cartesian", "corexy"):
            notes.append(("note.kinematics_unsupported", {"kin": kin}))
    for k, key, cast in (("max_velocity", "max_velocity", int), ("max_accel", "max_accel", int),
                         ("max_z_velocity", "max_z_velocity", int), ("max_z_accel", "max_z_accel", int),
                         ("square_corner_velocity", "scv", float)):
        setp(key, g("printer", k, cast))

    setp("bed_x", g("stepper_x", "position_max"))
    setp("x_min", g("stepper_x", "position_min"))
    setp("x_endstop", g("stepper_x", "position_endstop"))
    setp("bed_y", g("stepper_y", "position_max"))
    setp("y_min", g("stepper_y", "position_min"))
    setp("y_endstop", g("stepper_y", "position_endstop"))
    setp("bed_z", g("stepper_z", "position_max"))
    setp("z_min", g("stepper_z", "position_min"))
    setp("rd_xy", g("stepper_x", "rotation_distance"))
    setp("rd_z", g("stepper_z", "rotation_distance"))
    setp("microsteps", g("stepper_x", "microsteps", int))
    setp("homing_speed", g("stepper_x", "homing_speed", int))

    for ax, sec in AXIS_SECTION.items():
        if not has(sec):
            continue
        for fld, suffix in (("step_pin", "_step"), ("enable_pin", "_en")):
            v = gs(sec, fld)
            if v:
                pins[ax + suffix] = v
        v = gs(sec, "dir_pin")
        if v:
            pins[ax + "_dir"] = v.lstrip("!")
            if ax != "z1":
                P["inv_" + ax] = v.startswith("!")
        if ax in ("x", "y", "z"):
            v = gs(sec, "endstop_pin")
            if v and "probe:" not in v:
                pins[ax + "_stop"] = v

    P["dual_z"] = has("stepper_z1")
    if has("stepper_z2"):
        notes.append(("note.multi_z_unsupported", {}))

    drv = None
    for s in c.sections():
        m = re.match(r"^(tmc\d+)\s+stepper_x$", s)
        if m:
            drv = m.group(1)
    if drv is None:
        P["driver"] = "none"
    elif drv in DRIVER_IDS:
        P["driver"] = drv
    else:
        P["driver"] = "tmc2209"
        notes.append(("note.driver_unsupported", {"drv": drv}))
    if drv:
        for ax, sec in AXIS_SECTION.items():
            ts = "%s %s" % (drv, sec)
            if has(ts):
                tmc[ax] = OrderedDict((k, gs(ts, k)) for k in UART_KEYS + SPI_KEYS if gs(ts, k))
        setp("cur_xy", g("%s stepper_x" % drv, "run_current"))
        setp("cur_z", g("%s stepper_z" % drv, "run_current"))
        setp("cur_e", g("%s extruder" % drv, "run_current"))
        hc, rc = g("%s stepper_x" % drv, "hold_current"), g("%s stepper_x" % drv, "run_current")
        P["hold_ratio"] = round(hc / rc, 2) if hc and rc else 1.0
        setp("stealth_xy", g("%s stepper_x" % drv, "stealthchop_threshold", int))
        setp("stealth_z", g("%s stepper_z" % drv, "stealthchop_threshold", int))
        setp("stealth_e", g("%s extruder" % drv, "stealthchop_threshold", int))

    setp("rd_e", g("extruder", "rotation_distance"))
    setp("nozzle", g("extruder", "nozzle_diameter"))
    setp("filament", g("extruder", "filament_diameter"))
    setp("therm_e", gs("extruder", "sensor_type"))
    setp("therm_bed", gs("heater_bed", "sensor_type"))
    for sec, pre in (("extruder", "pid_e_"), ("heater_bed", "pid_b_")):
        for k in ("kp", "ki", "kd"):
            setp(pre + k, g(sec, "pid_" + k))
    setp("max_temp_e", g("extruder", "max_temp", int))
    setp("max_temp_bed", g("heater_bed", "max_temp", int))
    setp("pa", g("extruder", "pressure_advance"))
    setp("pa_smooth", g("extruder", "pressure_advance_smooth_time"))
    if P["pa"] >= 0.2:
        P["bowden"] = True
    for fld, role in (("heater_pin", "e_heater"), ("sensor_pin", "e_sensor")):
        pins[role] = gs("extruder", fld) or pins[role]
    for fld, role in (("heater_pin", "bed_heater"), ("sensor_pin", "bed_sensor")):
        pins[role] = gs("heater_bed", fld) or pins[role]
    P["cool_room"] = has("verify_heater extruder") or has("verify_heater heater_bed")

    if has("fan"):
        setp("fan_max", g("fan", "max_power"))
        pins["fan"] = gs("fan", "pin") or ""
    hf = "heater_fan hotend_fan" if has("heater_fan hotend_fan") else next(
        (s for s in c.sections() if s.startswith("heater_fan ")), None)
    if hf:
        setp("hotend_fan_temp", g(hf, "heater_temp"))
        pins["hotend_fan"] = gs(hf, "pin") or ""
        if hf != "heater_fan hotend_fan":
            notes.append(("note.renamed_section", {"old": hf, "new": "heater_fan hotend_fan"}))

    if has("bltouch"):
        P["probe"], sec = "bltouch", "bltouch"
        pins["bl_sensor"] = gs(sec, "sensor_pin") or ""
        pins["bl_control"] = gs(sec, "control_pin") or ""
    elif has("probe"):
        P["probe"], sec = "inductive", "probe"
        pins["probe"] = gs(sec, "pin") or ""
    else:
        P["probe"], sec = "none", None
        if any(s.split()[0] in ("beacon", "cartographer", "probe_eddy_current", "smart_effector") for s in c.sections()):
            notes.append(("note.probe_unsupported", {}))
    if sec:
        setp("probe_x", g(sec, "x_offset"))
        setp("probe_y", g(sec, "y_offset"))
        setp("probe_z", g(sec, "z_offset"))
        setp("probe_samples", g(sec, "samples", int))

    if has("bed_mesh"):
        mm = gs("bed_mesh", "mesh_min")
        if mm:
            try:
                P["mesh_margin"] = float(mm.split(",")[0])
            except ValueError:
                pass
        pc = gs("bed_mesh", "probe_count")
        if pc:
            try:
                P["mesh_count"] = int(pc.split(",")[0])
            except ValueError:
                pass

    if has("z_tilt"):
        zp = [x for x in (gs("z_tilt", "z_positions") or "").split("\n") if x.strip()]
        if zp:
            try:
                P["z_tilt_swap"] = float(zp[0].split(",")[0]) > P["bed_x"] / 2
            except ValueError:
                pass

    neo = "neopixel case_leds" if has("neopixel case_leds") else next(
        (s for s in c.sections() if s.startswith("neopixel ") and "display" not in s and "board" not in s), None)
    P["leds"] = bool(neo)
    if neo:
        setp("led_count", g(neo, "chain_count", int))
        setp("led_order", gs(neo, "color_order"))
        pins["neopixel"] = gs(neo, "pin") or ""
        if neo != "neopixel case_leds":
            notes.append(("note.renamed_section", {"old": neo, "new": "neopixel case_leds"}))
    P["led_effects"] = any(s.startswith("led_effect ") for s in c.sections())

    fs = [s for s in c.sections() if s.startswith("filament_switch_sensor ")]
    P["fil_sensor"] = bool(fs)
    if fs:
        pins["fil_sensor"] = gs(fs[0], "switch_pin") or ""
        if fs[0] != "filament_switch_sensor filament_sensor":
            notes.append(("note.renamed_section", {"old": fs[0], "new": "filament_switch_sensor filament_sensor"}))

    if has("input_shaper"):
        P["shaper"] = True
        setp("shaper_x", g("input_shaper", "shaper_freq_x"))
        setp("shaper_y", g("input_shaper", "shaper_freq_y"))
        setp("shaper_z", g("input_shaper", "shaper_freq_z"))
        st = gs("input_shaper", "shaper_type")
        for ax in ("x", "y", "z"):
            v = gs("input_shaper", "shaper_type_" + ax) or st
            if v and v.lower() in SHAPERS:
                P["shaper_type_" + ax] = v.lower()
        setp("damping", g("input_shaper", "damping_ratio_x"))
    else:
        P["shaper"] = False

    P["arcs"] = has("gcode_arcs")
    P["exclude_object"] = has("exclude_object")

    boards = boards if boards is not None else load_boards()
    P["board"] = detect_board(P, boards, P["mcu_serial"] or "")
    P["board_extras"] = False  # keep the user's own extra sections untouched
    if P["board"]:
        notes.append(("note.board_detected", {"name": boards[P["board"]]["name"]}))
    else:
        notes.append(("note.board_unknown", {}))
    if save:
        notes.append(("note.save_config_read", {}))
    return P, notes
