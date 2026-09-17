# -*- coding: utf-8 -*-
"""Reads an existing printer.cfg (including SAVE_CONFIG values) into project parameters."""
import re
from collections import OrderedDict

from .boards import detect_board, get_board, load_boards, match_slots
from .cfgtools import cfg_parser, num, save_as_cfg, split_save
from .generator import MACRO_MARK
from .model import (DRIVER_INFO, MOTOR_IDS, MOTOR_SECTION, SHAPERS, SPI_KEYS, UART_KEYS, Z_MOTORS,
                    new_params)


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
    pins = P["pins"]

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

    uuid = gs("mcu", "canbus_uuid")
    setp("mcu_serial", gs("mcu", "serial") or (("canbus_uuid: " + uuid) if uuid else None))
    kin = gs("printer", "kinematics")
    if not has("printer"):
        P["kinematics"] = ""  # not a printer config (or [printer] is missing) - it will not be rewritten
        notes.append(("note.kinematics_unsupported", {"kin": "-"}))
    elif kin:
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
    setp("homing_speed", g("stepper_x", "homing_speed", int))

    # ---------------- motors
    tmc_sections = {}
    for s in c.sections():
        mt = re.match(r"^(tmc\d+)\s+(\S+)$", s)
        if mt:
            tmc_sections[mt.group(2)] = (mt.group(1), s)
    for mid, sec in MOTOR_SECTION.items():
        m = P["motors"][mid]
        if not has(sec):
            if mid not in ("x", "y", "z", "e"):
                m["enabled"] = False
            else:
                m["driver"] = "none"
            continue
        m["enabled"] = True
        m["step_pin"] = gs(sec, "step_pin") or ""
        m["enable_pin"] = gs(sec, "enable_pin") or ""
        d = gs(sec, "dir_pin") or ""
        m["dir_pin"], m["invert"] = d.lstrip("!"), d.startswith("!")
        for key, opt, cast in (("microsteps", "microsteps", int), ("rotation_distance", "rotation_distance", float),
                               ("full_steps", "full_steps_per_rotation", int)):
            v = g(sec, opt, cast)
            if v is not None:
                m[key] = v
        endstop = gs(sec, "endstop_pin") or ""
        if mid in ("x", "y", "z") and endstop and "probe:" not in endstop and "virtual_endstop" not in endstop:
            m["endstop_pin"] = endstop

        drv_sec = tmc_sections.get(sec)
        if not drv_sec:
            m["driver"] = "none"
        else:
            drv, ts = drv_sec
            if drv not in DRIVER_INFO:
                notes.append(("note.driver_unsupported", {"drv": drv}))
                drv = "tmc2209"
            m["driver"] = drv
            m["bus"] = OrderedDict((k, gs(ts, k)) for k in UART_KEYS + SPI_KEYS if gs(ts, k))
            for key, opt in (("run_current", "run_current"), ("hold_current", "hold_current"),
                             ("sense_resistor", "sense_resistor")):
                v = g(ts, opt)
                if v is not None:
                    m[key] = v
            v = g(ts, "stealthchop_threshold", int)
            if v is not None:
                m["stealthchop"] = v
            interp = gs(ts, "interpolate")
            if interp is not None:
                m["interpolate"] = interp.lower() in ("true", "1", "yes")
            diag = gs(ts, "diag_pin") or gs(ts, "diag1_pin") or gs(ts, "diag0_pin")
            if diag:
                m["diag_pin"] = diag
                if re.match(r"^tmc\d+_stepper_\w+:virtual_endstop$", endstop):
                    m["sensorless"] = True
                else:
                    m["keep_diag"] = True  # used for something else (crash detection...) - keep it
            sg_key = DRIVER_INFO[drv]["sg_key"]
            if sg_key and g(ts, sg_key.lower(), int) is not None:
                m["sg"] = g(ts, sg_key.lower(), int)
        at = "autotune_tmc " + sec
        if has(at):
            m["autotune"] = gs(at, "motor") or ""
            m["tuning_goal"] = gs(at, "tuning_goal") or "auto"
            if m["sensorless"]:
                key = DRIVER_INFO.get(m["driver"], {}).get("autotune_sg")
                if key and g(at, key, int) is not None:
                    m["sg"] = g(at, key, int)
            setp("motor_voltage", g(at, "voltage"))

    if has("stepper_z2") and not has("z_tilt") and not has("quad_gantry_level"):
        notes.append(("note.multi_z_no_leveling", {}))
    for extra in ("stepper_a", "stepper_b", "stepper_c", "extruder1"):
        if has(extra):
            notes.append(("note.section_kept", {"section": extra}))

    # ---------------- thermal
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

    # ---------------- probe / leveling
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

    if has("quad_gantry_level"):
        P["z_leveling"] = "quad_gantry_level"
        P["qgl_corners"] = gs("quad_gantry_level", "gantry_corners") or ""
        P["z_tilt_points"] = gs("quad_gantry_level", "points") or ""
    elif has("z_tilt"):
        P["z_leveling"] = "z_tilt"
        positions = [x.strip() for x in (gs("z_tilt", "z_positions") or "").split("\n") if x.strip()]
        for mid, pos in zip([z for z in Z_MOTORS if P["motors"][z]["enabled"]], positions):
            P["motors"][mid]["z_position"] = pos
        P["z_tilt_points"] = gs("z_tilt", "points") or ""

    # ---------------- extras
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
    P["retraction"] = has("firmware_retraction")
    if P["retraction"]:
        setp("retract_length", g("firmware_retraction", "retract_length"))
        setp("retract_speed", g("firmware_retraction", "retract_speed"))
        setp("unretract_speed", g("firmware_retraction", "unretract_speed"))
    if has("idle_timeout"):
        t = g("idle_timeout", "timeout")
        if t:
            P["idle_timeout_min"] = int(round(t / 60))
    for s in c.sections():
        st = (gs(s, "sensor_type") or "") if s.startswith("temperature_sensor ") else ""
        if st == "temperature_host":
            P["host_temp"], P["host_temp_name"] = True, s.split(None, 1)[1]
        elif st == "temperature_mcu":
            P["mcu_temp"], P["mcu_temp_name"] = True, s.split(None, 1)[1]
    P["print_macros"] = MACRO_MARK in (gs("gcode_macro START_PRINT", "description") or "")

    # ---------------- board
    boards = boards if boards is not None else load_boards()
    P["board"] = detect_board(P, boards, P["mcu_serial"] or "")
    P["board_extras"] = False  # keep the user's own extra sections untouched
    if P["board"]:
        match_slots(P, get_board(P["board"], boards))
        notes.append(("note.board_detected", {"name": boards[P["board"]]["name"]}))
    else:
        notes.append(("note.board_unknown", {}))
    if save:
        notes.append(("note.save_config_read", {}))
    return P, notes
