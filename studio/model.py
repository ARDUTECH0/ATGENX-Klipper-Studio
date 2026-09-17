# -*- coding: utf-8 -*-
"""Project parameters: constants, defaults, motors and project files."""
import io
import json
import os
from collections import OrderedDict

from . import DATA_DIR, __version__

THERMISTORS = [
    "EPCOS 100K B57560G104F", "Generic 3950", "ATC Semitec 104GT-2", "ATC Semitec 104NT-4-R025H42G",
    "NTC 100K MGB18-104F39050L32", "SliceEngineering 450", "Honeywell 100K 135-104LAG-J01",
    "NTC 100K beta 3950", "PT1000", "PT1000 (MAX31865)",
]

# ---------------------------------------------------------------- drivers
# bus, StallGuard option in the tmc section, its range and a safe starting value,
# the diag pin option, a comfortable RMS current limit and the Klipper default sense resistor.
DRIVER_INFO = OrderedDict([
    ("tmc2209", dict(label="TMC2209 / TMC2226", bus="uart", sg_key="driver_SGTHRS", sg_range=(0, 255),
                     sg_default=100, diag_key="diag_pin", max_current=1.7, rsense=0.110, autotune_sg="sg4_thrs")),
    ("tmc2208", dict(label="TMC2208 / TMC2225", bus="uart", sg_key=None, sg_range=None,
                     sg_default=None, diag_key=None, max_current=1.2, rsense=0.110, autotune_sg=None)),
    ("tmc2130", dict(label="TMC2130", bus="spi", sg_key="driver_SGT", sg_range=(-64, 63),
                     sg_default=1, diag_key="diag1_pin", max_current=1.2, rsense=0.110, autotune_sg="sgt")),
    ("tmc5160", dict(label="TMC5160 / TMC2160", bus="spi", sg_key="driver_SGT", sg_range=(-64, 63),
                     sg_default=1, diag_key="diag1_pin", max_current=3.0, rsense=0.075, autotune_sg="sgt")),
    ("tmc2240", dict(label="TMC2240", bus="spi", sg_key="driver_SGT", sg_range=(-64, 63),
                     sg_default=1, diag_key="diag1_pin", max_current=2.1, rsense=None, autotune_sg="sgt")),
    ("tmc2660", dict(label="TMC2660", bus="spi", sg_key=None, sg_range=None,
                     sg_default=None, diag_key=None, max_current=2.4, rsense=None, autotune_sg=None)),
    ("none", dict(label="Standalone (A4988 / DRV8825)", bus=None, sg_key=None, sg_range=None,
                  sg_default=None, diag_key=None, max_current=None, rsense=None, autotune_sg=None)),
])
DRIVERS = [(k, v["label"]) for k, v in DRIVER_INFO.items()]
UART_DRIVERS = {k for k, v in DRIVER_INFO.items() if v["bus"] == "uart"}
SPI_DRIVERS = {k for k, v in DRIVER_INFO.items() if v["bus"] == "spi"}
UART_KEYS = ("uart_pin", "tx_pin", "uart_address")
SPI_KEYS = ("cs_pin", "spi_bus", "spi_software_miso_pin", "spi_software_mosi_pin", "spi_software_sclk_pin")
TUNING_GOALS = ["auto", "silent", "performance"]

PROBES = ["inductive", "bltouch", "none"]
SHAPERS = ["zv", "mzv", "zvd", "ei", "2hump_ei", "3hump_ei"]
LED_ORDERS = ["GRB", "RGB", "GRBW", "RGBW"]
KINEMATICS = ["cartesian", "corexy"]
Z_LEVELING = ["z_tilt", "quad_gantry_level"]

# ---------------------------------------------------------------- motors
MOTOR_IDS = ("x", "x1", "y", "y1", "z", "z1", "z2", "z3", "e")
REQUIRED_MOTORS = ("x", "y", "z", "e")
OPTIONAL_MOTORS = ("x1", "y1", "z1", "z2", "z3")
Z_MOTORS = ("z", "z1", "z2", "z3")
MOTOR_SECTION = OrderedDict([("x", "stepper_x"), ("x1", "stepper_x1"), ("y", "stepper_y"), ("y1", "stepper_y1"),
                             ("z", "stepper_z"), ("z1", "stepper_z1"), ("z2", "stepper_z2"), ("z3", "stepper_z3"),
                             ("e", "extruder")])
MOTOR_LABEL = {"x": "X", "x1": "X2", "y": "Y", "y1": "Y2", "z": "Z", "z1": "Z2", "z2": "Z3", "z3": "Z4", "e": "E"}
# a secondary motor copies mechanics from its primary
PRIMARY = {"x1": "x", "y1": "y", "z1": "z", "z2": "z", "z3": "z"}
HOMING_MOTORS = ("x", "y", "z")
SENSORLESS_MOTORS = ("x", "y")

# pin roles that don't belong to a motor -> i18n label key
PIN_ROLES = OrderedDict([
    ("e_heater", "pin.e_heater"), ("e_sensor", "pin.e_sensor"),
    ("bed_heater", "pin.bed_heater"), ("bed_sensor", "pin.bed_sensor"),
    ("fan", "pin.fan"), ("hotend_fan", "pin.hotend_fan"),
    ("probe", "pin.probe"), ("bl_sensor", "pin.bl_sensor"), ("bl_control", "pin.bl_control"),
    ("neopixel", "pin.neopixel"), ("fil_sensor", "pin.fil_sensor"),
])

SERIAL_PLACEHOLDER = "/dev/serial/by-id/usb-Klipper_XXXX-if00"


def new_motor(mid):
    rd = 8.0 if mid in Z_MOTORS else (33.5 if mid == "e" else 40.0)
    return OrderedDict(
        enabled=mid in REQUIRED_MOTORS, slot="",
        step_pin="", dir_pin="", enable_pin="", invert=False, endstop_pin="",
        driver="tmc2209", bus=OrderedDict(), run_current=0.6 if mid == "e" else 0.8, hold_current=0.0,
        sense_resistor=0.0, microsteps=16, rotation_distance=rd, full_steps=200,
        stealthchop=0, interpolate=True,
        sensorless=False, diag_pin="", sg=None, keep_diag=False,
        autotune="", tuning_goal="auto",
        z_position="",
    )


DEFAULTS = OrderedDict(
    printer_name="My Printer",
    host="", port=7125,
    board="", mcu_serial=SERIAL_PLACEHOLDER, board_extras=True,
    kinematics="cartesian",
    bed_x=220.0, bed_y=220.0, bed_z=250.0,
    x_min=0.0, y_min=0.0, z_min=-2.0, x_endstop=0.0, y_endstop=0.0,
    max_velocity=300, max_accel=3000, max_z_velocity=15, max_z_accel=100, scv=5.0,
    homing_speed=50, motor_voltage=24.0,
    z_leveling="z_tilt", z_tilt_points="", qgl_corners="",
    nozzle=0.4, filament=1.75, bowden=False,
    therm_e="EPCOS 100K B57560G104F", therm_bed="EPCOS 100K B57560G104F",
    pid_e_kp=22.2, pid_e_ki=1.08, pid_e_kd=114.0,
    pid_b_kp=54.027, pid_b_ki=0.770, pid_b_kd=948.182,
    max_temp_e=260, max_temp_bed=120, pa=0.0, pa_smooth=0.040, cool_room=False,
    fan_max=1.0, hotend_fan_temp=50.0,
    probe="none", probe_x=0.0, probe_y=0.0, probe_z=0.0, probe_samples=2,
    mesh_margin=15.0, mesh_count=5,
    leds=False, led_count=10, led_order="GRB", led_effects=False,
    fil_sensor=False,
    shaper=False, shaper_x=50.0, shaper_type_x="mzv", shaper_y=40.0, shaper_type_y="mzv",
    shaper_z=0.0, shaper_type_z="ei", damping=0.1,
    arcs=True, exclude_object=True,
    retraction=False, retract_length=0.8, retract_speed=35.0, unretract_speed=25.0,
    idle_timeout_min=0, host_temp=False, mcu_temp=False, host_temp_name="host", mcu_temp_name="mcu",
    print_macros=False, adaptive_mesh=True, purge_line=True,
)


def new_params():
    p = OrderedDict((k, v) for k, v in DEFAULTS.items())
    p["pins"] = OrderedDict((k, "") for k in PIN_ROLES)
    p["motors"] = OrderedDict((m, new_motor(m)) for m in MOTOR_IDS)
    p["map_positions"] = {}        # where the user dragged devices on the wiring map
    p["custom_sections"] = []      # [{"id", "text", "enabled"}] added from the feature catalog
    p["disabled_sections"] = []    # sections of the current file to comment out
    p["enabled_sections"] = []     # commented-out sections of the current file to switch back on
    return p


def enabled_motors(P):
    return [m for m in MOTOR_IDS if P["motors"][m]["enabled"]]


def z_motors(P):
    return [m for m in Z_MOTORS if P["motors"][m]["enabled"]]


def driver_bus(driver, bus_opts):
    """'uart', 'spi' or None for a driver type and its bus options."""
    info = DRIVER_INFO.get(driver, {})
    if driver == "tmc2240" and bus_opts.get("uart_pin") and not bus_opts.get("cs_pin"):
        return "uart"
    return info.get("bus")


def bus_keys(driver, bus_opts):
    bus = driver_bus(driver, bus_opts)
    if bus == "uart":
        return UART_KEYS
    if bus == "spi":
        return SPI_KEYS
    return ()


def autotune_motors():
    path = os.path.join(DATA_DIR, "autotune_motors.txt")
    try:
        with io.open(path, encoding="utf-8") as f:
            return [ln.strip() for ln in f if ln.strip()]
    except OSError:
        return []


# ---------------------------------------------------------------- projects
PROJECT_KIND = "atgenx-klipper-studio"
PROJECT_SCHEMA = 2


def save_project(P, path):
    data = OrderedDict([("kind", PROJECT_KIND), ("schema", PROJECT_SCHEMA), ("version", __version__)])
    data.update(P)
    with io.open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _cast(default, v):
    if isinstance(default, bool):
        return bool(v)
    if isinstance(default, int):
        return int(v)
    if isinstance(default, float):
        return float(v)
    return v


def load_project(path):
    with io.open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("not a project file")
    return project_from_dict(data)


def project_from_dict(data):
    P = new_params()
    for k, v in data.items():
        if k in DEFAULTS and v is not None:
            P[k] = _cast(DEFAULTS[k], v)
    for k, v in (data.get("pins") or {}).items():
        if k in P["pins"]:
            P["pins"][k] = str(v)
    for key in ("custom_sections", "disabled_sections", "enabled_sections"):
        if isinstance(data.get(key), list):
            P[key] = data[key]
    if isinstance(data.get("map_positions"), dict):
        P["map_positions"] = {k: list(v) for k, v in data["map_positions"].items() if isinstance(v, (list, tuple))}
    if isinstance(data.get("motors"), dict):
        for mid, m in data["motors"].items():
            if mid in P["motors"] and isinstance(m, dict):
                base = P["motors"][mid]
                for k, v in m.items():
                    if k == "bus" and isinstance(v, dict):
                        base["bus"] = OrderedDict((bk, str(bv)) for bk, bv in v.items())
                    elif k in base and v is not None:
                        base[k] = v if base[k] is None else _cast(base[k], v)
    else:
        _convert_schema1(P, data)
    return P


def _convert_schema1(P, d):
    """Projects saved by 1.0.0-beta.1 (global driver settings, flat pins)."""
    pins = d.get("pins") or {}
    tmc = d.get("tmc") or {}
    axis_opts = {"x": ("cur_xy", "stealth_xy", "rd_xy", "inv_x"), "y": ("cur_xy", "stealth_xy", "rd_xy", "inv_y"),
                 "z": ("cur_z", "stealth_z", "rd_z", "inv_z"), "z1": ("cur_z", "stealth_z", "rd_z", "inv_z"),
                 "e": ("cur_e", "stealth_e", "rd_e", "inv_e")}
    for mid, (cur, stealth, rd, inv) in axis_opts.items():
        m = P["motors"][mid]
        if mid == "z1":
            m["enabled"] = bool(d.get("dual_z"))
        m["step_pin"] = pins.get(mid + "_step", "")
        m["dir_pin"] = pins.get(mid + "_dir", "")
        m["enable_pin"] = pins.get(mid + "_en", "")
        m["endstop_pin"] = pins.get(mid + "_stop", "")
        m["bus"] = OrderedDict((k, str(v)) for k, v in (tmc.get(mid) or {}).items())
        m["driver"] = d.get("driver", "tmc2209")
        for key, src, cast in (("run_current", cur, float), ("stealthchop", stealth, int),
                               ("rotation_distance", rd, float), ("invert", inv, bool)):
            if d.get(src) is not None:
                m[key] = cast(d[src])
        if d.get("microsteps"):
            m["microsteps"] = int(d["microsteps"])
        ratio = float(d.get("hold_ratio") or 1.0)
        if ratio < 0.999:
            m["hold_current"] = round(m["run_current"] * ratio, 3)
