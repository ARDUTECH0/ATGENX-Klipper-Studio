# -*- coding: utf-8 -*-
"""Project parameters: constants, defaults and project files."""
import io
import json
from collections import OrderedDict

from . import __version__

THERMISTORS = [
    "EPCOS 100K B57560G104F", "Generic 3950", "ATC Semitec 104GT-2", "ATC Semitec 104NT-4-R025H42G",
    "NTC 100K MGB18-104F39050L32", "SliceEngineering 450", "Honeywell 100K 135-104LAG-J01",
    "NTC 100K beta 3950", "PT1000", "PT1000 (MAX31865)",
]

# (klipper section type, label)
DRIVERS = [
    ("tmc2209", "TMC2209 / TMC2226"),
    ("tmc2208", "TMC2208 / TMC2225"),
    ("tmc2130", "TMC2130"),
    ("tmc5160", "TMC5160 / TMC2160"),
    ("tmc2240", "TMC2240"),
    ("none", "Standalone (A4988 / DRV8825 / TMC standalone)"),
]
UART_DRIVERS = {"tmc2208", "tmc2209"}
SPI_DRIVERS = {"tmc2130", "tmc5160", "tmc2240"}
UART_KEYS = ("uart_pin", "tx_pin", "uart_address")
SPI_KEYS = ("cs_pin", "spi_bus", "spi_software_miso_pin", "spi_software_mosi_pin", "spi_software_sclk_pin")

PROBES = ["inductive", "bltouch", "none"]
SHAPERS = ["zv", "mzv", "zvd", "ei", "2hump_ei", "3hump_ei"]
LED_ORDERS = ["GRB", "RGB", "GRBW", "RGBW"]
KINEMATICS = ["cartesian", "corexy"]

AXES = ("x", "y", "z", "z1", "e")
AXIS_SECTION = OrderedDict([("x", "stepper_x"), ("y", "stepper_y"), ("z", "stepper_z"),
                            ("z1", "stepper_z1"), ("e", "extruder")])

# pin role -> i18n label key
PIN_ROLES = OrderedDict([
    ("x_step", "pin.x_step"), ("x_dir", "pin.x_dir"), ("x_en", "pin.x_en"), ("x_stop", "pin.x_stop"),
    ("y_step", "pin.y_step"), ("y_dir", "pin.y_dir"), ("y_en", "pin.y_en"), ("y_stop", "pin.y_stop"),
    ("z_step", "pin.z_step"), ("z_dir", "pin.z_dir"), ("z_en", "pin.z_en"), ("z_stop", "pin.z_stop"),
    ("z1_step", "pin.z1_step"), ("z1_dir", "pin.z1_dir"), ("z1_en", "pin.z1_en"),
    ("e_step", "pin.e_step"), ("e_dir", "pin.e_dir"), ("e_en", "pin.e_en"),
    ("e_heater", "pin.e_heater"), ("e_sensor", "pin.e_sensor"),
    ("bed_heater", "pin.bed_heater"), ("bed_sensor", "pin.bed_sensor"),
    ("fan", "pin.fan"), ("hotend_fan", "pin.hotend_fan"),
    ("probe", "pin.probe"), ("bl_sensor", "pin.bl_sensor"), ("bl_control", "pin.bl_control"),
    ("neopixel", "pin.neopixel"), ("fil_sensor", "pin.fil_sensor"),
])

SERIAL_PLACEHOLDER = "/dev/serial/by-id/usb-Klipper_XXXX-if00"

DEFAULTS = OrderedDict(
    printer_name="My Printer",
    host="", port=7125,
    board="", mcu_serial=SERIAL_PLACEHOLDER, board_extras=True,
    kinematics="cartesian",
    bed_x=220.0, bed_y=220.0, bed_z=250.0,
    x_min=0.0, y_min=0.0, z_min=-2.0, x_endstop=0.0, y_endstop=0.0,
    max_velocity=300, max_accel=3000, max_z_velocity=15, max_z_accel=100, scv=5.0,
    homing_speed=50, microsteps=16, rd_xy=40.0, rd_z=8.0,
    inv_x=False, inv_y=False, inv_z=False, inv_e=False,
    driver="tmc2209", cur_xy=0.8, cur_z=0.8, cur_e=0.6, hold_ratio=1.0,
    stealth_xy=0, stealth_z=0, stealth_e=0,
    dual_z=False, z_tilt_swap=False,
    rd_e=33.5, nozzle=0.4, filament=1.75, bowden=False,
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
)


def new_params():
    p = OrderedDict((k, v) for k, v in DEFAULTS.items())
    p["pins"] = OrderedDict((k, "") for k in PIN_ROLES)
    p["tmc"] = OrderedDict((ax, OrderedDict()) for ax in AXES)
    return p


def driver_bus(driver, tmc_opts):
    """'uart', 'spi' or None for a driver type and its per-axis bus options."""
    if driver in UART_DRIVERS:
        return "uart"
    if driver == "tmc2240":
        return "spi" if tmc_opts.get("cs_pin") or not tmc_opts.get("uart_pin") else "uart"
    if driver in SPI_DRIVERS:
        return "spi"
    return None


PROJECT_KIND = "atgenx-klipper-studio"


def save_project(P, path):
    data = OrderedDict([("kind", PROJECT_KIND), ("version", __version__)])
    data.update(P)
    with io.open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_project(path):
    with io.open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("not a project file")
    P = new_params()
    for k, v in data.items():
        if k in DEFAULTS and v is not None:
            P[k] = type(DEFAULTS[k])(v) if isinstance(DEFAULTS[k], (int, float)) and not isinstance(DEFAULTS[k], bool) else v
    P["pins"].update({k: str(v) for k, v in (data.get("pins") or {}).items()})
    for ax, opts in (data.get("tmc") or {}).items():
        if ax in P["tmc"] and isinstance(opts, dict):
            P["tmc"][ax] = OrderedDict((k, str(v)) for k, v in opts.items())
    return P
