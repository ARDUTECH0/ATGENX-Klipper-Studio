# -*- coding: utf-8 -*-
"""Builds the wiring map: which device sits on which board pin, and what is wrong with it.

Pure data (no Qt) so it can be tested and reused: studio/gui/map_page.py draws it.
"""
import re
from collections import OrderedDict

from .boards import strip_mods
from .cfgtools import SECTION_RE, split_save
from .features import COMMENTED_SECTION_RE
from .i18n import tr
from .model import MOTOR_LABEL, MOTOR_SECTION, bus_keys, enabled_motors

PIN_KEY_RE = re.compile(r"^([a-z_0-9]*pin)\s*[:=]\s*(.+?)\s*$")
MCU_PREFIX_RE = re.compile(r"^[\^~!]*([a-z][a-z0-9_]*):")
NON_MCU_PREFIX = ("probe", "neopixel", "led", "host")

GROUPS = ("motors", "heat", "fans", "sensors", "lights", "other")


def _pin_board(pin, boards):
    """Which board a pin belongs to ('pico:gpio1' -> 'pico'), or the main MCU."""
    m = MCU_PREFIX_RE.match(pin or "")
    if m and m.group(1) in boards:
        return m.group(1)
    if m and "_stepper_" in (pin or ""):
        return None  # a virtual endstop inside a driver, not a wire
    return "mcu"


def _node(nid, group, label, icon, pins, page, board="mcu", off=False, note=""):
    return OrderedDict(id=nid, group=group, label=label, icon=icon, pins=pins, page=page,
                       board=board, off=off, note=note, issues=[])


def _pin(role, pin, label):
    return OrderedDict(role=role, pin=pin or "", label=label)


def secondary_boards(text):
    """[mcu name] sections in the file: extra boards (Pico for an ADXL, a toolhead board, ...)."""
    out = OrderedDict()
    main, _ = split_save(text or "")
    for ln in main.split("\n"):
        m = SECTION_RE.match(ln) or COMMENTED_SECTION_RE.match(ln)
        if m and m.group(1).strip().startswith("mcu "):
            name = m.group(1).strip().split(None, 1)[1]
            out[name] = bool(SECTION_RE.match(ln))
    return out


def other_devices(text, is_managed, boards):
    """Nodes for sections the app does not manage but that use pins (ADXL, chamber sensor, case light...)."""
    main, _ = split_save(text or "")
    nodes, current, commented = [], None, False
    for ln in main.split("\n"):
        m = SECTION_RE.match(ln)
        c = COMMENTED_SECTION_RE.match(ln)
        if m or c:
            name = (m or c).group(1).strip()
            commented = c is not None
            current = None
            if is_managed(name) or name.startswith(("mcu", "gcode_macro", "include", "delayed_gcode",
                                                    "gcode_shell_command", "menu ", "display_template")):
                continue
            current = _node("section:" + name, "other", "[%s]" % name, "🧩", [], "page_features",
                            off=commented)
            nodes.append(current)
            continue
        if current is None:
            continue
        body = re.sub(r"^#\s?", "", ln, count=1) if commented else ln
        pm = PIN_KEY_RE.match(body.strip()) if body.strip() else None
        if pm and "virtual_endstop" not in pm.group(2):
            current["pins"].append(_pin(pm.group(1), pm.group(2).split("#")[0].strip(), pm.group(1)))
    return [n for n in nodes if n["pins"]]


def wiring(P, board=None, config_text="", is_managed=None):
    """{'boards': [...], 'nodes': [...], 'issues': [...]} - the whole map."""
    if is_managed is None:
        from .merge import is_managed as _m
        is_managed = lambda name: _m(name, P)  # noqa: E731

    extra = secondary_boards(config_text)
    boards = OrderedDict()
    boards["mcu"] = OrderedDict(id="mcu", name=(board or {}).get("name") or tr("map.custom_board"),
                                mcu=", ".join((board or {}).get("mcu", {}).get("processors") or []) or "",
                                detail=P["mcu_serial"], off=False, main=True)
    for name, on in extra.items():
        boards[name] = OrderedDict(id=name, name="[mcu %s]" % name, mcu="", detail="", off=not on, main=False)

    nodes = []
    for mid in enabled_motors(P):
        m = P["motors"][mid]
        pins = [_pin("step_pin", m["step_pin"], "step"), _pin("dir_pin", m["dir_pin"], "dir"),
                _pin("enable_pin", m["enable_pin"], "enable")]
        if mid in ("x", "y", "z"):
            if m["sensorless"]:
                pins.append(_pin("diag_pin", m["diag_pin"], "diag"))
            elif mid != "z" or P["probe"] == "none":
                pins.append(_pin("endstop_pin", m["endstop_pin"], "endstop"))
        for key in bus_keys(m["driver"], m["bus"]):
            if m["bus"].get(key):
                pins.append(_pin("bus:" + key, m["bus"][key], key))
        label = "%s  ·  %s" % (MOTOR_LABEL[mid], m["slot"] or MOTOR_SECTION[mid])
        note = m["driver"].upper() if m["driver"] != "none" else tr("driver.none")
        nodes.append(_node("motor:" + mid, "motors", label, "⚙️", pins, "page_motors", note=note))

    p = P["pins"]
    nodes.append(_node("heater:e", "heat", tr("pin.e_heater"), "🔥", [_pin("e_heater", p["e_heater"], "heater_pin")],
                       "page_thermal"))
    nodes.append(_node("sensor:e", "heat", tr("pin.e_sensor"), "🌡️", [_pin("e_sensor", p["e_sensor"], "sensor_pin")],
                       "page_thermal", note=P["therm_e"]))
    if p["bed_heater"]:
        nodes.append(_node("heater:bed", "heat", tr("pin.bed_heater"), "🔥",
                           [_pin("bed_heater", p["bed_heater"], "heater_pin")], "page_thermal"))
        nodes.append(_node("sensor:bed", "heat", tr("pin.bed_sensor"), "🌡️",
                           [_pin("bed_sensor", p["bed_sensor"], "sensor_pin")], "page_thermal", note=P["therm_bed"]))
    if p["fan"]:
        nodes.append(_node("fan:part", "fans", tr("pin.fan"), "🌀", [_pin("fan", p["fan"], "pin")], "page_thermal"))
    if p["hotend_fan"]:
        nodes.append(_node("fan:hotend", "fans", tr("pin.hotend_fan"), "🌀",
                           [_pin("hotend_fan", p["hotend_fan"], "pin")], "page_thermal"))
    if P["probe"] == "inductive":
        nodes.append(_node("probe", "sensors", tr("probe.inductive"), "🎯", [_pin("probe", p["probe"], "pin")],
                           "page_probe"))
    elif P["probe"] == "bltouch":
        nodes.append(_node("probe", "sensors", tr("probe.bltouch"), "🎯",
                           [_pin("bl_sensor", p["bl_sensor"], "sensor_pin"),
                            _pin("bl_control", p["bl_control"], "control_pin")], "page_probe"))
    if P["fil_sensor"]:
        nodes.append(_node("fil", "sensors", tr("pin.fil_sensor"), "🧵", [_pin("fil_sensor", p["fil_sensor"], "switch_pin")],
                           "page_extras"))
    if P["leds"]:
        nodes.append(_node("leds", "lights", tr("pin.neopixel"), "💡", [_pin("neopixel", p["neopixel"], "pin")],
                           "page_extras", note="%d x %s" % (P["led_count"], P["led_order"])))
    nodes += other_devices(config_text, is_managed, boards)

    # attach every pin to a board and collect problems
    used, issues = {}, []
    for n in nodes:
        for pin in n["pins"]:
            pin["board"] = _pin_board(pin["pin"], boards)
            if n["off"]:
                continue  # a section that is switched off is not in use, so it cannot be wrong
            if not pin["pin"].strip():
                pin["issue"] = tr("map.issue_empty")
                n["issues"].append(pin["issue"])
                continue
            if pin["board"] and boards[pin["board"]]["off"]:
                pin["issue"] = tr("map.issue_board_off", board=pin["board"])
                n["issues"].append(pin["issue"])
            if pin["role"].startswith("bus:") or n["off"]:
                continue
            base = strip_mods(pin["pin"])
            other = used.get(base)
            share_ok = {"endstop_pin", "probe", "bl_sensor"}
            if other and not (pin["role"] in share_ok and other[1] in share_ok):
                pin["issue"] = tr("map.issue_conflict", other=other[0])
                n["issues"].append(pin["issue"])
                issues.append(tr("map.issue_conflict_full", pin=base, a=other[0], b=n["label"]))
            used.setdefault(base, (n["label"], pin["role"]))
    return OrderedDict(boards=list(boards.values()), nodes=nodes, issues=issues)


def set_pin(P, node_id, role, value):
    """Writes a pin edited on the map back into the project (returns True when it was ours to change)."""
    value = (value or "").strip()
    if node_id.startswith("motor:"):
        m = P["motors"][node_id.split(":", 1)[1]]
        if role.startswith("bus:"):
            key = role.split(":", 1)[1]
            if value:
                m["bus"][key] = value
            else:
                m["bus"].pop(key, None)
        elif role in m:
            m[role] = value.lstrip("!") if role == "dir_pin" else value
        return True
    if role in P["pins"]:
        P["pins"][role] = value
        return True
    return False  # a pin of a section the app does not manage - edit it in All config files
