# -*- coding: utf-8 -*-
"""Project parameters -> Klipper config sections."""
from collections import OrderedDict

from .cfgtools import block, fmt as n
from .model import SPI_KEYS, UART_KEYS, driver_bus

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
SOFT_KEYS = {
    "stepper_z": {"homing_speed", "second_homing_speed"},
    "extruder": {"min_temp", "max_extrude_only_distance", "max_extrude_cross_section"},
    "heater_bed": {"min_temp"},
    "fan": {"off_below", "kick_start_time"},
    "heater_fan hotend_fan": {"fan_speed"},
    "verify_heater extruder": {"max_error", "check_gain_time", "hysteresis", "heating_gain"},
    "verify_heater heater_bed": {"max_error", "check_gain_time", "hysteresis", "heating_gain"},
    "probe": {"speed", "lift_speed", "samples_result", "sample_retract_dist", "samples_tolerance",
              "samples_tolerance_retries"},
    "bltouch": {"speed", "lift_speed", "samples_result", "sample_retract_dist", "samples_tolerance",
                "samples_tolerance_retries"},
    "safe_z_home": {"speed", "z_hop", "z_hop_speed"},
    "bed_mesh": {"speed", "horizontal_move_z", "algorithm", "fade_start", "fade_end", "fade_target",
                 "adaptive_margin"},
    "z_tilt": {"speed", "horizontal_move_z", "retries", "retry_tolerance"},
    "neopixel case_leds": {"initial_red", "initial_green", "initial_blue"},
    "filament_switch_sensor filament_sensor": {"pause_on_runout", "runout_gcode", "insert_gcode",
                                               "event_delay", "pause_delay"},
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


def tmc_rows(P, ax):
    """Bus options for one axis according to the selected driver type."""
    opts = P["tmc"].get(ax) or {}
    bus = driver_bus(P["driver"], opts)
    rows = []
    if bus == "uart":
        keys = UART_KEYS if P["driver"] != "tmc2208" else ("uart_pin", "tx_pin")
        rows = [(k, opts.get(k)) for k in keys if opts.get(k)]
    elif bus == "spi":
        rows = [("cs_pin", opts.get("cs_pin"))]
        if opts.get("spi_bus"):
            rows.append(("spi_bus", opts["spi_bus"]))
        else:
            rows += [(k, opts.get(k)) for k in SPI_KEYS[2:] if opts.get(k)]
    return rows


def generate(P, board=None):
    """Returns OrderedDict: section name -> section text."""
    S = OrderedDict()
    pins = P["pins"]
    drv = P["driver"]
    ms = int(P["microsteps"])
    has_probe = P["probe"] != "none"

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

    def tmc(ax, sec, cur, stealth):
        if drv == "none":
            return
        rows = tmc_rows(P, ax) + [("run_current", n(cur))]
        if P["hold_ratio"] < 0.999:
            rows.append(("hold_current", n(cur * P["hold_ratio"])))
        rows.append(("stealthchop_threshold", n(stealth)))
        S["%s %s" % (drv, sec)] = block("%s %s" % (drv, sec), rows)

    for ax, bed, mn, es in (("x", "bed_x", "x_min", "x_endstop"), ("y", "bed_y", "y_min", "y_endstop")):
        S["stepper_" + ax] = block("stepper_" + ax, [
            ("step_pin", pins[ax + "_step"]), ("dir_pin", dpin(pins[ax + "_dir"], P["inv_" + ax])),
            ("enable_pin", pins[ax + "_en"]), ("microsteps", ms), ("rotation_distance", n(P["rd_xy"])),
            ("endstop_pin", pins[ax + "_stop"]), ("position_endstop", n(P[es])),
            ("position_min", n(P[mn])), ("position_max", n(P[bed])), ("homing_speed", n(P["homing_speed"])),
        ])
        tmc(ax, "stepper_" + ax, P["cur_xy"], P["stealth_xy"])

    S["stepper_z"] = block("stepper_z", [
        ("step_pin", pins["z_step"]), ("dir_pin", dpin(pins["z_dir"], P["inv_z"])),
        ("enable_pin", pins["z_en"]), ("microsteps", ms), ("rotation_distance", n(P["rd_z"])),
        ("endstop_pin", "probe:z_virtual_endstop" if has_probe else pins["z_stop"]),
        ("position_endstop", None if has_probe else "0"),
        ("position_min", n(P["z_min"])), ("position_max", n(P["bed_z"])),
        ("homing_speed", "8"), ("second_homing_speed", "3"),
    ])
    tmc("z", "stepper_z", P["cur_z"], P["stealth_z"])

    if P["dual_z"]:
        S["stepper_z1"] = block("stepper_z1", [
            ("step_pin", pins["z1_step"]), ("dir_pin", dpin(pins["z1_dir"], P["inv_z"])),
            ("enable_pin", pins["z1_en"]), ("microsteps", ms), ("rotation_distance", n(P["rd_z"])),
        ])
        tmc("z1", "stepper_z1", P["cur_z"], P["stealth_z"])

    S["extruder"] = block("extruder", [
        ("step_pin", pins["e_step"]), ("dir_pin", dpin(pins["e_dir"], P["inv_e"])),
        ("enable_pin", pins["e_en"]), ("microsteps", ms), ("rotation_distance", n(P["rd_e"])),
        ("nozzle_diameter", "%.3f" % P["nozzle"]), ("filament_diameter", "%.3f" % P["filament"]),
        ("heater_pin", pins["e_heater"]), ("sensor_type", P["therm_e"]), ("sensor_pin", pins["e_sensor"]),
        ("control", "pid"), ("pid_Kp", n(P["pid_e_kp"])), ("pid_Ki", n(P["pid_e_ki"])), ("pid_Kd", n(P["pid_e_kd"])),
        ("min_temp", "0"), ("max_temp", n(P["max_temp_e"])),
        ("max_extrude_only_distance", "150"), ("max_extrude_cross_section", "5"),
        ("pressure_advance", n(P["pa"])), ("pressure_advance_smooth_time", n(P["pa_smooth"])),
    ])
    tmc("e", "extruder", P["cur_e"], P["stealth_e"])

    S["heater_bed"] = block("heater_bed", [
        ("heater_pin", pins["bed_heater"]), ("sensor_type", P["therm_bed"]), ("sensor_pin", pins["bed_sensor"]),
        ("control", "pid"), ("pid_Kp", n(P["pid_b_kp"])), ("pid_Ki", n(P["pid_b_ki"])), ("pid_Kd", n(P["pid_b_kd"])),
        ("min_temp", "0"), ("max_temp", n(P["max_temp_bed"])),
    ])

    if P["cool_room"]:
        S["verify_heater extruder"] = block("verify_heater extruder", [
            ("max_error", "130"), ("check_gain_time", "60"), ("hysteresis", "6"), ("heating_gain", "2")])
        S["verify_heater heater_bed"] = block("verify_heater heater_bed", [
            ("max_error", "180"), ("check_gain_time", "150"), ("hysteresis", "4"), ("heating_gain", "2")])

    S["fan"] = block("fan", [("pin", pins["fan"]), ("max_power", n(P["fan_max"], 2) if P["fan_max"] < 0.999 else None),
                             ("off_below", "0.10"), ("kick_start_time", "0.100")])
    if pins["hotend_fan"]:
        S["heater_fan hotend_fan"] = block("heater_fan hotend_fan", [
            ("pin", pins["hotend_fan"]), ("heater", "extruder"),
            ("heater_temp", "%.1f" % P["hotend_fan_temp"]), ("fan_speed", "1.0")])

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

        if P["dual_z"]:
            lo, hi, yc = tilt_points(P)
            zp = ["%s, %s" % (n(P["bed_x"]), n(yc)), "0, %s" % n(yc)]
            if not P["z_tilt_swap"]:
                zp.reverse()
            S["z_tilt"] = block("z_tilt", [
                ("z_positions", "\n".join(zp)),
                ("points", "%s, %s\n%s, %s" % (n(lo), n(yc), n(hi), n(yc))),
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
    return S
