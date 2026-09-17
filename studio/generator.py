# -*- coding: utf-8 -*-
"""Project parameters -> Klipper config sections."""
from collections import OrderedDict

from .cfgtools import block, fmt as n
from .model import DRIVER_INFO, MOTOR_SECTION, SPI_KEYS, Z_MOTORS, bus_keys, driver_bus, enabled_motors, z_motors

# Marks macros written by the app. A macro without it belongs to the user and is never touched.
MACRO_MARK = "Klipper Studio"
APP_MACROS = ("START_PRINT", "END_PRINT", "M600")

LED_EFFECTS = OrderedDict([
    ("heating", ("heater_bed", "heatergauge -1 0 add (1.0,0.35,0.0),(0.25,0.05,0.0)")),
    ("heating_nozzle", ("extruder", "heatergauge -1 0 add (1.0,0.15,0.0),(0.25,0.03,0.0)")),
    ("printing", (None, "progress -1 0 add (0.0,0.6,1.0),(0.0,0.12,0.3)")),
    ("leveling", (None, "chase 1.5 1.0 add (0.6, 0.0, 1.0)")),
    ("rainbow", (None, "gradient 1.0 1 add (1.0, 0.0, 0.0),(0.0, 1.0, 0.0),(0.0, 0.0, 1.0)")),
    ("idle_twinkle", (None, "twinkle 1.0 0.15 add (0.0, 0.3, 1.0)")),
    ("done", (None, "strobe 1.0 1.5 add (0.0, 1.0, 0.0)")),
    ("error", (None, "strobe 1.0 0.5 add (1.0, 0.0, 0.0)")),
])

# Values the generator only provides as sensible defaults for NEW sections.
# When merging into an existing file, the user's value for these keys is kept.
_PROBE_SOFT = {"speed", "lift_speed", "samples_result", "sample_retract_dist", "samples_tolerance",
               "samples_tolerance_retries"}
SOFT_KEYS = {
    "stepper_z": {"homing_speed", "second_homing_speed"},
    "extruder": {"min_temp", "max_extrude_only_distance", "max_extrude_cross_section"},
    "heater_bed": {"min_temp"},
    "fan": {"off_below", "kick_start_time"},
    "heater_fan hotend_fan": {"fan_speed"},
    "verify_heater extruder": {"max_error", "check_gain_time", "hysteresis", "heating_gain"},
    "verify_heater heater_bed": {"max_error", "check_gain_time", "hysteresis", "heating_gain"},
    "probe": _PROBE_SOFT,
    "bltouch": _PROBE_SOFT,
    "safe_z_home": {"speed", "z_hop", "z_hop_speed"},
    "bed_mesh": {"speed", "horizontal_move_z", "algorithm", "fade_start", "fade_end", "fade_target",
                 "adaptive_margin"},
    "z_tilt": {"speed", "horizontal_move_z", "retries", "retry_tolerance"},
    "quad_gantry_level": {"speed", "horizontal_move_z", "retries", "retry_tolerance", "max_adjust"},
    "neopixel case_leds": {"initial_red", "initial_green", "initial_blue"},
    "filament_switch_sensor filament_sensor": {"pause_on_runout", "runout_gcode", "insert_gcode",
                                               "event_delay", "pause_delay"},
    "firmware_retraction": {"unretract_extra_length"},
    "gcode_arcs": {"resolution"},
    "virtual_sdcard": {"path"},
    "led_effect *": {"autostart", "frame_rate", "layers", "heater"},
}


def soft_keys(section):
    if section.startswith("led_effect "):
        return SOFT_KEYS["led_effect *"]
    return SOFT_KEYS.get(section, set())


def dpin(base, inv):
    base = (base or "").lstrip("!")
    return "!" + base if inv else base


def mesh_bounds(P):
    """Mesh rectangle the probe can actually reach."""
    m = P["mesh_margin"]
    rx0, rx1 = P["x_min"] + P["probe_x"], P["bed_x"] + P["probe_x"]
    ry0, ry1 = P["y_min"] + P["probe_y"], P["bed_y"] + P["probe_y"]
    return (max(m, rx0), max(m, ry0), min(P["bed_x"] - m, rx1), min(P["bed_y"] - m, ry1))


def tilt_points(P):
    m, px = P["mesh_margin"], P["probe_x"]
    lo = max(m, 5 - px, P["x_min"])
    hi = min(P["bed_x"] - m, P["bed_x"] - 5 - px, P["bed_x"])
    return lo, hi, round(P["bed_y"] * 0.55, 1)


def default_z_positions(P, count):
    """Pivot points of the Z motors, in stepper_z, z1, z2, z3 order."""
    bx, by = P["bed_x"], P["bed_y"]
    if count == 2:
        yc = round(by * 0.55, 1)
        return [(0, yc), (bx, yc)]
    if count == 3:  # front-left, back-centre, front-right (Voron Trident style)
        return [(0, 0), (round(bx / 2, 1), by), (bx, 0)]
    return [(0, 0), (0, by), (bx, by), (bx, 0)]  # quad: front-left, back-left, back-right, front-right


def leveling_points(P, positions):
    """Probe points near every pivot, clamped to the area the probe can reach."""
    x0, y0, x1, y1 = mesh_bounds(P)
    if len(positions) == 2:
        lo, hi, yc = tilt_points(P)
        return [(lo, yc), (hi, yc)]
    out = []
    for px, py in positions:
        out.append((min(max(px, x0), x1), min(max(py, y0), y1)))
    return out


def _xy_lines(points):
    return "\n".join("%s, %s" % (n(x), n(y)) for x, y in points)


def _parse_xy(text):
    try:
        x, y = [float(v) for v in text.replace(" ", "").split(",")[:2]]
        return x, y
    except ValueError:
        return None


def z_positions(P):
    zs = z_motors(P)
    defaults = default_z_positions(P, len(zs))
    out = []
    for i, mid in enumerate(zs):
        pos = _parse_xy(P["motors"][mid]["z_position"]) if P["motors"][mid]["z_position"] else None
        out.append(pos or defaults[i])
    return out


def park_xy(P):
    return round(max(P["x_min"], 0) + 10, 1), round(P["bed_y"] - 10, 1)


def tmc_bus_rows(m):
    opts = m["bus"] or {}
    keys = bus_keys(m["driver"], opts)
    bus = driver_bus(m["driver"], opts)
    if bus == "spi":
        rows = [("cs_pin", opts.get("cs_pin"))]
        if opts.get("spi_bus"):
            rows.append(("spi_bus", opts["spi_bus"]))
        else:
            rows += [(k, opts.get(k)) for k in SPI_KEYS[2:] if opts.get(k)]
        return rows
    return [(k, opts.get(k)) for k in keys if opts.get(k)]


def generate(P, board=None):
    """Returns OrderedDict: section name -> section text."""
    S = OrderedDict()
    pins = P["pins"]
    has_probe = P["probe"] != "none"
    motors = P["motors"]

    serial = P["mcu_serial"].strip()
    if serial.startswith("canbus_uuid:"):
        S["mcu"] = block("mcu", [("canbus_uuid", serial.split(":", 1)[1].strip())])
    else:
        S["mcu"] = block("mcu", [("serial", serial)])
    S["printer"] = block("printer", [
        ("kinematics", P["kinematics"]),
        ("max_velocity", n(P["max_velocity"])), ("max_accel", n(P["max_accel"])),
        ("max_z_velocity", n(P["max_z_velocity"])), ("max_z_accel", n(P["max_z_accel"])),
        ("square_corner_velocity", n(P["scv"], 2)),
    ])

    def driver_sections(mid):
        m = motors[mid]
        sec = MOTOR_SECTION[mid]
        info = DRIVER_INFO.get(m["driver"], DRIVER_INFO["none"])
        if m["driver"] == "none":
            return
        rows = tmc_bus_rows(m)
        sensorless = m["sensorless"] and info["diag_key"] and mid in ("x", "y")
        if (sensorless or m["keep_diag"]) and info["diag_key"] and m["diag_pin"]:
            rows.append((info["diag_key"], m["diag_pin"]))
        rows.append(("run_current", n(m["run_current"])))
        if m["hold_current"] > 0 and m["driver"] != "tmc2660":
            rows.append(("hold_current", n(m["hold_current"])))
        if m["sense_resistor"] > 0:
            rows.append(("sense_resistor", n(m["sense_resistor"])))
        if not m["interpolate"]:
            rows.append(("interpolate", "False"))
        if m["driver"] != "tmc2660":
            rows.append(("stealthchop_threshold", n(m["stealthchop"])))
        sg = m["sg"] if m["sg"] is not None else info["sg_default"]
        if info["sg_key"] and not m["autotune"] and (sensorless or m["sg"] is not None):
            rows.append((info["sg_key"], n(sg)))
        name = "%s %s" % (m["driver"], sec)
        S[name] = block(name, rows)
        if m["autotune"]:
            at = [("motor", m["autotune"])]
            if m["tuning_goal"] != "auto":
                at.append(("tuning_goal", m["tuning_goal"]))
            if abs(P["motor_voltage"] - 24) > 0.01:
                at.append(("voltage", n(P["motor_voltage"])))
            if sensorless and info["autotune_sg"]:
                at.append((info["autotune_sg"], n(sg)))
            S["autotune_tmc " + sec] = block("autotune_tmc " + sec, at)

    def mech_rows(m):
        return [("step_pin", m["step_pin"]), ("dir_pin", dpin(m["dir_pin"], m["invert"])),
                ("enable_pin", m["enable_pin"]), ("microsteps", int(m["microsteps"])),
                ("rotation_distance", n(m["rotation_distance"])),
                ("full_steps_per_rotation", int(m["full_steps"]) if int(m["full_steps"]) != 200 else None)]

    for ax in ("x", "y"):
        m = motors[ax]
        sensorless = m["sensorless"] and DRIVER_INFO.get(m["driver"], {}).get("diag_key")
        endstop = "%s_stepper_%s:virtual_endstop" % (m["driver"], ax) if sensorless else m["endstop_pin"]
        S["stepper_" + ax] = block("stepper_" + ax, mech_rows(m) + [
            ("endstop_pin", endstop), ("position_endstop", n(P[ax + "_endstop"])),
            ("position_min", n(P[ax + "_min"])), ("position_max", n(P["bed_" + ax])),
            ("homing_speed", n(P["homing_speed"])),
            ("homing_retract_dist", "0" if sensorless else None),
        ])
        driver_sections(ax)
        second = ax + "1"
        if motors[second]["enabled"]:
            S["stepper_" + second] = block("stepper_" + second, mech_rows(motors[second]))
            driver_sections(second)

    m = motors["z"]
    S["stepper_z"] = block("stepper_z", mech_rows(m) + [
        ("endstop_pin", "probe:z_virtual_endstop" if has_probe else m["endstop_pin"]),
        ("position_endstop", None if has_probe else "0"),
        ("position_min", n(P["z_min"])), ("position_max", n(P["bed_z"])),
        ("homing_speed", "8"), ("second_homing_speed", "3"),
    ])
    driver_sections("z")
    for mid in Z_MOTORS[1:]:
        if motors[mid]["enabled"]:
            S[MOTOR_SECTION[mid]] = block(MOTOR_SECTION[mid], mech_rows(motors[mid]))
            driver_sections(mid)

    m = motors["e"]
    S["extruder"] = block("extruder", mech_rows(m) + [
        ("nozzle_diameter", "%.3f" % P["nozzle"]), ("filament_diameter", "%.3f" % P["filament"]),
        ("heater_pin", pins["e_heater"]), ("sensor_type", P["therm_e"]), ("sensor_pin", pins["e_sensor"]),
        ("control", "pid"), ("pid_Kp", n(P["pid_e_kp"])), ("pid_Ki", n(P["pid_e_ki"])), ("pid_Kd", n(P["pid_e_kd"])),
        ("min_temp", "0"), ("max_temp", n(P["max_temp_e"])),
        ("max_extrude_only_distance", "150"), ("max_extrude_cross_section", "5"),
        ("pressure_advance", n(P["pa"])), ("pressure_advance_smooth_time", n(P["pa_smooth"])),
    ])
    driver_sections("e")

    if pins["bed_heater"]:
        S["heater_bed"] = block("heater_bed", [
            ("heater_pin", pins["bed_heater"]), ("sensor_type", P["therm_bed"]), ("sensor_pin", pins["bed_sensor"]),
            ("control", "pid"), ("pid_Kp", n(P["pid_b_kp"])), ("pid_Ki", n(P["pid_b_ki"])), ("pid_Kd", n(P["pid_b_kd"])),
            ("min_temp", "0"), ("max_temp", n(P["max_temp_bed"])),
        ])

    if P["cool_room"]:
        S["verify_heater extruder"] = block("verify_heater extruder", [
            ("max_error", "130"), ("check_gain_time", "60"), ("hysteresis", "6"), ("heating_gain", "2")])
    if P["cool_room"] and pins["bed_heater"]:
        S["verify_heater heater_bed"] = block("verify_heater heater_bed", [
            ("max_error", "180"), ("check_gain_time", "150"), ("hysteresis", "4"), ("heating_gain", "2")])

    if pins["fan"]:
        S["fan"] = block("fan", [("pin", pins["fan"]), ("max_power", n(P["fan_max"], 2) if P["fan_max"] < 0.999 else None),
                                 ("off_below", "0.10"), ("kick_start_time", "0.100")])
    if pins["hotend_fan"]:
        S["heater_fan hotend_fan"] = block("heater_fan hotend_fan", [
            ("pin", pins["hotend_fan"]), ("heater", "extruder"),
            ("heater_temp", "%.1f" % P["hotend_fan_temp"]), ("fan_speed", "1.0")])

    zs = z_motors(P)
    if has_probe:
        common = [("x_offset", n(P["probe_x"])), ("y_offset", n(P["probe_y"])), ("z_offset", n(P["probe_z"])),
                  ("speed", "3.0"), ("lift_speed", "5.0"), ("samples", n(P["probe_samples"])),
                  ("samples_result", "median"), ("sample_retract_dist", "3.0"),
                  ("samples_tolerance", "0.02"), ("samples_tolerance_retries", "3")]
        if P["probe"] == "bltouch":
            S["bltouch"] = block("bltouch", [("sensor_pin", pins["bl_sensor"]),
                                             ("control_pin", pins["bl_control"])] + common)
        else:
            S["probe"] = block("probe", [("pin", pins["probe"])] + common)

        hx = round(P["bed_x"] / 2 - P["probe_x"], 1)
        hy = round(P["bed_y"] / 2 - P["probe_y"], 1)
        S["safe_z_home"] = block("safe_z_home", [
            ("home_xy_position", "%s, %s" % (n(hx), n(hy))), ("speed", "100"),
            ("z_hop", "10"), ("z_hop_speed", "10")])

        x0, y0, x1, y1 = mesh_bounds(P)
        cnt = int(P["mesh_count"])
        S["bed_mesh"] = block("bed_mesh", [
            ("speed", "80"), ("horizontal_move_z", "8"),
            ("mesh_min", "%s, %s" % (n(x0), n(y0))), ("mesh_max", "%s, %s" % (n(x1), n(y1))),
            ("probe_count", "%d, %d" % (cnt, cnt)),
            ("algorithm", "bicubic" if cnt >= 4 else "lagrange"),
            ("fade_start", "1"), ("fade_end", "10"), ("fade_target", "0"),
            ("zero_reference_position", "%s, %s" % (n(P["bed_x"] / 2), n(P["bed_y"] / 2))),
            ("adaptive_margin", "5"),
        ])

        if len(zs) == 4 and P["z_leveling"] == "quad_gantry_level":
            corners = P["qgl_corners"] or "-60, -10\n%s, %s" % (n(P["bed_x"] + 60), n(P["bed_y"] + 10))
            points = P["z_tilt_points"] or _xy_lines([(x0, y0), (x0, y1), (x1, y1), (x1, y0)])
            S["quad_gantry_level"] = block("quad_gantry_level", [
                ("gantry_corners", corners), ("points", points),
                ("speed", "100"), ("horizontal_move_z", "10"), ("retries", "5"),
                ("retry_tolerance", "0.0075"), ("max_adjust", "10")])
        elif len(zs) >= 2:
            positions = z_positions(P)
            points = P["z_tilt_points"] or _xy_lines(leveling_points(P, positions))
            S["z_tilt"] = block("z_tilt", [
                ("z_positions", _xy_lines(positions)), ("points", points),
                ("speed", "80"), ("horizontal_move_z", "8"), ("retries", "5"), ("retry_tolerance", "0.02")])

    if P["leds"]:
        S["neopixel case_leds"] = block("neopixel case_leds", [
            ("pin", pins["neopixel"]), ("chain_count", n(P["led_count"])), ("color_order", P["led_order"]),
            ("initial_RED", "0.0"), ("initial_GREEN", "0.0"), ("initial_BLUE", "0.0")])
        if P["led_effects"]:
            for name, (heater, layer) in LED_EFFECTS.items():
                rows = [("leds", "neopixel:case_leds")]
                if heater:
                    rows.append(("heater", heater))
                rows += [("autostart", "false"), ("frame_rate", "24"), ("layers", "\n" + layer)]
                S["led_effect " + name] = block("led_effect " + name, rows)

    if P["fil_sensor"]:
        S["filament_switch_sensor filament_sensor"] = block("filament_switch_sensor filament_sensor", [
            ("switch_pin", pins["fil_sensor"]), ("pause_on_runout", "True"),
            ("runout_gcode", "\nM117 Filament runout\nPAUSE"), ("insert_gcode", "\nM117 Filament inserted"),
            ("event_delay", "1.0"), ("pause_delay", "0.5")])

    if P["shaper"]:
        rows = [("shaper_type_x", P["shaper_type_x"]), ("shaper_freq_x", n(P["shaper_x"], 1)),
                ("shaper_type_y", P["shaper_type_y"]), ("shaper_freq_y", n(P["shaper_y"], 1))]
        if P["shaper_z"] > 0:
            rows += [("shaper_type_z", P["shaper_type_z"]), ("shaper_freq_z", n(P["shaper_z"], 1))]
        rows += [("damping_ratio_x", n(P["damping"], 3)), ("damping_ratio_y", n(P["damping"], 3))]
        S["input_shaper"] = block("input_shaper", rows)

    if P["retraction"]:
        S["firmware_retraction"] = block("firmware_retraction", [
            ("retract_length", n(P["retract_length"], 2)), ("retract_speed", n(P["retract_speed"])),
            ("unretract_extra_length", "0"), ("unretract_speed", n(P["unretract_speed"]))])
    if P["idle_timeout_min"] > 0:
        S["idle_timeout"] = block("idle_timeout", [("timeout", str(int(P["idle_timeout_min"]) * 60))])
    if P["host_temp"]:
        name = "temperature_sensor " + P["host_temp_name"]
        S[name] = block(name, [("sensor_type", "temperature_host")])
    if P["mcu_temp"]:
        name = "temperature_sensor " + P["mcu_temp_name"]
        S[name] = block(name, [("sensor_type", "temperature_mcu")])

    if board and P.get("board_extras"):
        for ex in board.get("extra_sections", []):
            S[ex["name"]] = block(ex["name"], [(k, v) for k, v in ex["options"]])

    if P["arcs"]:
        S["gcode_arcs"] = block("gcode_arcs", [("resolution", "0.1")])
    if P["exclude_object"]:
        S["exclude_object"] = "[exclude_object]"
    S["virtual_sdcard"] = block("virtual_sdcard", [("path", "~/printer_data/gcodes")])
    for s in ("pause_resume", "display_status", "respond"):
        S[s] = "[%s]" % s

    if P["print_macros"]:
        S.update(print_macros(P, zs, has_probe))
    return S


def print_macros(P, zs, has_probe):
    px, py = park_xy(P)
    lines = [
        "{% set BED = params.BED|default(params.BED_TEMP|default(60))|float %}",
        "{% set EXTRUDER = params.EXTRUDER|default(params.EXTRUDER_TEMP|default(210))|float %}",
    ]
    has_bed = bool(P["pins"]["bed_heater"])
    lines += (["M140 S{BED}"] if has_bed else []) + ["M104 S150", "G90", "G28"] + (["M190 S{BED}"] if has_bed else [])
    if has_probe and len(zs) >= 2:
        lines += ["QUAD_GANTRY_LEVEL" if (len(zs) == 4 and P["z_leveling"] == "quad_gantry_level") else "Z_TILT_ADJUST",
                  "G28 Z"]
    if has_probe and P["adaptive_mesh"]:
        lines += ["BED_MESH_CLEAR", "BED_MESH_CALIBRATE ADAPTIVE=1"]
    elif has_probe:
        lines += ["{% if 'default' in printer.bed_mesh.profiles %}", "BED_MESH_PROFILE LOAD=default", "{% endif %}"]
    lines += ["M109 S{EXTRUDER}"]
    if P["purge_line"]:
        x = round(max(P["x_min"], 0) + 5, 1)
        y0 = round(max(P["y_min"], 0) + 20, 1)
        y1 = round(min(P["bed_y"] - 20, y0 + 100), 1)
        lines += ["G1 Z5 F600", "G1 X%s Y%s F6000" % (n(x), n(y0)), "G1 Z0.3 F600", "G92 E0",
                  "G1 Y%s E15 F1200" % n(y1), "G1 X%s E0.3 F1200" % n(x + 0.4),
                  "G1 Y%s E15 F1200" % n(y0), "G92 E0", "G1 Z2 F600"]

    end = [
        "{% set z = [printer.toolhead.position.z + 10, printer.toolhead.axis_maximum.z]|min %}",
        "G91", "G1 E-2 F2700", "G90",
        "G1 Z{z} F900",
        "G1 X%s Y%s F6000" % (n(px), n(py)),
        "TURN_OFF_HEATERS", "M107", "M84",
    ]
    m600 = [
        "{% set z = [printer.toolhead.position.z + 10, printer.toolhead.axis_maximum.z]|min %}",
        "PAUSE", "G91", "G1 E-5 F1800", "G90",
        "G1 Z{z} F900",
        "G1 X%s Y%s F6000" % (n(px), n(py)),
        "M117 Change filament, then RESUME",
    ]
    out = OrderedDict()
    for name, desc, body in (("START_PRINT", "heat, home, level, mesh, purge", lines),
                             ("END_PRINT", "retract, park, cool down", end),
                             ("M600", "filament change - continue with RESUME", m600)):
        out["gcode_macro " + name] = block("gcode_macro " + name, [
            ("description", "%s - %s" % (MACRO_MARK, desc)), ("gcode", "\n" + "\n".join(body))])
    return out
