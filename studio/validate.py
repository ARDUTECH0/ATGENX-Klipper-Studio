# -*- coding: utf-8 -*-
"""Checks that catch the mistakes that stop Klipper from starting (or ruin prints)."""
import re

from .boards import strip_mods
from .cfgtools import cfg_parser, fmt as n, save_as_cfg, split_save
from .generator import mesh_bounds
from .i18n import tr
from .model import driver_bus


def active_pins(P):
    """[(role, pin)] of every pin the generated config will use."""
    p = P["pins"]
    roles = ["x_step", "x_dir", "x_en", "x_stop", "y_step", "y_dir", "y_en", "y_stop",
             "z_step", "z_dir", "z_en", "e_step", "e_dir", "e_en",
             "e_heater", "e_sensor", "bed_heater", "bed_sensor", "fan", "hotend_fan"]
    if P["probe"] == "none":
        roles.append("z_stop")
    elif P["probe"] == "bltouch":
        roles += ["bl_sensor", "bl_control"]
    else:
        roles.append("probe")
    if P["dual_z"]:
        roles += ["z1_step", "z1_dir", "z1_en"]
    if P["leds"]:
        roles.append("neopixel")
    if P["fil_sensor"]:
        roles.append("fil_sensor")
    return [(r, p.get(r, "")) for r in roles]


def validate(P, text, board=None, elsewhere=None, klipper_warnings=None):
    """Returns [(level, message)] with level in error / warn / ok.

    elsewhere        - {section: file} of sections defined in included files
    klipper_warnings - configfile.warnings reported by the running Klipper
    """
    R = []
    E = lambda k, **kw: R.append(("error", tr(k, **kw)))
    W = lambda k, **kw: R.append(("warn", tr(k, **kw)))
    O = lambda k, **kw: R.append(("ok", tr(k, **kw)))

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
        E("val.duplicates", names=", ".join(dup))
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

    # pins
    empty = [tr("pin." + r) for r, v in active_pins(P) if not v.strip()]
    if empty:
        E("val.pins_empty", pins=" / ".join(empty))
    seen = {}
    for role, pin in active_pins(P):
        base = strip_mods(pin)
        if not base or role.endswith("_en"):  # several boards share one enable pin between drivers
            continue
        if base in seen and not {seen[base], role} <= {"z_stop", "probe", "bl_sensor"}:
            E("val.pin_conflict", pin=base, a=tr("pin." + seen[base]), b=tr("pin." + role))
        seen.setdefault(base, role)

    # drivers
    if P["driver"] != "none":
        axes = ["x", "y", "z", "e"] + (["z1"] if P["dual_z"] else [])
        for ax in axes:
            opts = P["tmc"].get(ax) or {}
            bus = driver_bus(P["driver"], opts)
            if bus == "uart" and not opts.get("uart_pin"):
                E("val.tmc_missing", axis=ax.upper(), key="uart_pin")
            if bus == "spi" and not opts.get("cs_pin"):
                E("val.tmc_missing", axis=ax.upper(), key="cs_pin")
            if P["driver"] == "tmc2208" and opts.get("uart_address"):
                E("val.tmc2208_shared_uart")
                break
    if P["driver"] == "tmc2208" and max(P["cur_xy"], P["cur_z"], P["cur_e"]) > 1.2:
        W("val.current_high", limit="1.2")
    if P["driver"] in ("tmc2209", "tmc2130") and max(P["cur_xy"], P["cur_z"], P["cur_e"]) > 1.7:
        W("val.current_high", limit="1.7")

    # motion
    if P["max_z_accel"] > P["max_accel"]:
        E("val.z_accel", z=P["max_z_accel"], xy=P["max_accel"])
    if P["microsteps"] & (P["microsteps"] - 1):
        E("val.microsteps")
    if P["kinematics"] not in ("cartesian", "corexy"):
        W("val.kinematics", kin=P["kinematics"])

    # probe / mesh
    if P["probe"] != "none":
        x0, y0, x1, y1 = mesh_bounds(P)
        if x0 >= x1 or y0 >= y1:
            E("val.mesh_empty")
        else:
            O("val.mesh_area", x0=n(x0), x1=n(x1), y0=n(y0), y1=n(y1))
        if abs(P["probe_z"]) < 0.001:
            W("val.probe_z_zero")
    elif P["dual_z"]:
        W("val.dual_z_no_probe")

    # tuning
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

    # references from the user's own macros
    body = re.sub(r"^\[[^\]\n]+\].*$", "", main, flags=re.M)
    refs = [
        (not P["leds"] and "case_leds" in body, "val.ref_leds"),
        (P["leds"] and not P["led_effects"] and "SET_LED_EFFECT" in body, "val.ref_led_effects"),
        (not P["dual_z"] and ("Z_TILT_ADJUST" in body or "stepper_z1" in body), "val.ref_z_tilt"),
        (P["probe"] == "none" and ("BED_MESH_CALIBRATE" in body or "PROBE_CALIBRATE" in body), "val.ref_probe"),
        (not P["fil_sensor"] and "filament_switch_sensor" in body, "val.ref_fil_sensor"),
    ]
    for cond, key in refs:
        if cond:
            E(key)
    # modular configs: a generated section that also lives in an included file
    if elsewhere:
        from .merge import is_managed
        for name in sorted(set(names)):
            if name in elsewhere and is_managed(name):
                W("val.section_elsewhere", section=name, file=elsewhere[name])
    for w in klipper_warnings or []:
        W("val.klipper_warning", msg=w.get("message", str(w)) if isinstance(w, dict) else str(w))

    if not [r for r in R if r[0] == "error"]:
        O("val.ready")
    return R
