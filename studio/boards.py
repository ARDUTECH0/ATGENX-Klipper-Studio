# -*- coding: utf-8 -*-
"""Board database (boards/*.json) and applying a board's pins to a project."""
import io
import json
import os
import re
from collections import OrderedDict

from . import BOARDS_DIR
from .model import AXIS_SECTION, SERIAL_PLACEHOLDER, SPI_KEYS, UART_KEYS

_cache = None

Z1_SLOT_ORDER = ("stepper_z1", "stepper_", "extruder1", "stepper_z2", "extruder2", "extruder3", "extruder4")


def board_dirs():
    from .appdata import BOARDS_USER_DIR
    return [BOARDS_DIR, BOARDS_USER_DIR]


def load_boards(dirs=None, reload=False):
    """id -> board dict, sorted by vendor then name. User boards override bundled ones."""
    global _cache
    if _cache is not None and dirs is None and not reload:
        return _cache
    found = {}
    for d in dirs or board_dirs():
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            if not f.endswith(".json"):
                continue
            try:
                with io.open(os.path.join(d, f), encoding="utf-8") as fh:
                    b = json.load(fh, object_pairs_hook=OrderedDict)
                if b.get("schema") == 1 and b.get("id") and b.get("drivers"):
                    found[b["id"]] = b
            except (OSError, ValueError):
                continue
    out = OrderedDict(sorted(found.items(), key=lambda kv: (kv[1].get("vendor", "").lower(), kv[1]["name"].lower())))
    if dirs is None:
        _cache = out
    return out


def get_board(board_id, boards=None):
    return (boards or load_boards()).get(board_id)


def board_label(b):
    vendor = b.get("vendor", "").split(" (")[0]
    if not vendor or vendor == "Other" or b["name"].lower().startswith(vendor.lower()):
        return b["name"]
    return "%s %s" % (vendor, b["name"])


def slots(board):
    return OrderedDict((d["slot"], d) for d in board["drivers"])


def default_z1_slot(board):
    s = slots(board)
    for name in Z1_SLOT_ORDER:
        if name in s:
            return name
    used = set(AXIS_SECTION.values())
    for name in s:
        if name not in used:
            return name
    return ""


def strip_mods(pin):
    return re.sub(r"^[\^~!\s]+", "", (pin or "").strip())


def apply_board(P, board, z1_slot=None, keep_inversion=True):
    """Fills P['pins'] / P['tmc'] from a board. Returns a list of (i18n key, kwargs) notes."""
    notes = []
    s = slots(board)
    pins, tmc = P["pins"], P["tmc"]
    z1_slot = z1_slot or default_z1_slot(board)
    mapping = {"x": "stepper_x", "y": "stepper_y", "z": "stepper_z", "e": "extruder", "z1": z1_slot}

    for ax, slot in mapping.items():
        d = s.get(slot)
        if not d:
            if ax == "z1":
                notes.append(("note.no_z1_slot", {}))
            for suffix in ("_step", "_dir", "_en"):
                pins[ax + suffix] = ""
            tmc[ax] = OrderedDict()
            continue
        pins[ax + "_step"] = d.get("step_pin", "")
        dir_pin = d.get("dir_pin", "")
        pins[ax + "_dir"] = dir_pin.lstrip("!")
        if not keep_inversion and ax != "z1":
            P["inv_" + ax] = dir_pin.startswith("!")
        pins[ax + "_en"] = d.get("enable_pin", "")
        if ax in ("x", "y", "z"):
            pins[ax + "_stop"] = d.get("endstop_pin", "")
        tmc[ax] = OrderedDict((k, v) for k, v in d.get("tmc", {}).items() if k in UART_KEYS + SPI_KEYS)

    heaters = board.get("heaters", {})
    ext = heaters.get("extruder", {})
    bed = heaters.get("heater_bed", {})
    pins["e_heater"], pins["e_sensor"] = ext.get("heater_pin", ""), ext.get("sensor_pin", "")
    pins["bed_heater"], pins["bed_sensor"] = bed.get("heater_pin", ""), bed.get("sensor_pin", "")

    fans = board.get("fans", [])
    part = next((f["pin"] for f in fans if f["name"] == "fan"), "")
    others = [f for f in fans if f["name"] != "fan" and f["pin"] != part]
    hot = next((f["pin"] for f in others if f["name"].startswith("heater_fan")), "")
    hot = hot or next((f["pin"] for f in others), "")
    if not hot:
        spare = [h for n, h in heaters.items() if n not in ("extruder", "heater_bed")
                 and h.get("heater_pin") and strip_mods(h["heater_pin"]) != strip_mods(part)]
        if spare:
            hot = spare[0]["heater_pin"]
            notes.append(("note.hotend_fan_on_heater", {"pin": hot}))
    pins["fan"], pins["hotend_fan"] = part, hot

    probe = board.get("probe", {})
    z_stop = s.get("stepper_z", {}).get("endstop_pin", "")
    pins["probe"] = probe.get("pin") or z_stop
    pins["bl_sensor"] = probe.get("bl_sensor") or ("^" + strip_mods(z_stop) if z_stop else "")
    pins["bl_control"] = probe.get("bl_control") or board.get("servo", "")
    pins["neopixel"] = board.get("neopixel", "")

    fil = (board.get("filament_sensors") or [""])[0]
    if not fil:
        e_diag = s.get("extruder", {}).get("tmc", {})
        diag = e_diag.get("diag1_pin") or e_diag.get("diag_pin") or ""
        if diag:
            fil = "^" + strip_mods(diag)
            notes.append(("note.fil_sensor_guess", {"pin": fil}))
    pins["fil_sensor"] = fil

    P["board"] = board["id"]
    procs = board.get("mcu", {}).get("processors") or []
    if "XXXX" in P.get("mcu_serial", "") or not P.get("mcu_serial"):
        P["mcu_serial"] = SERIAL_PLACEHOLDER.replace("Klipper_XXXX", "Klipper_%s_XXXX" % procs[0]) if procs else SERIAL_PLACEHOLDER
    return notes


def match_score(P, board):
    """How many step/dir/enable/heater pins of P match this board."""
    s = slots(board)
    pins = P["pins"]
    score = 0
    for ax, slot in (("x", "stepper_x"), ("y", "stepper_y"), ("z", "stepper_z"), ("e", "extruder")):
        d = s.get(slot, {})
        for suffix, key in (("_step", "step_pin"), ("_dir", "dir_pin"), ("_en", "enable_pin")):
            if pins.get(ax + suffix) and strip_mods(pins[ax + suffix]) == strip_mods(d.get(key, "")):
                score += 1
    h = board.get("heaters", {})
    for role, sec in (("e_heater", "extruder"), ("bed_heater", "heater_bed")):
        if pins.get(role) and strip_mods(pins[role]) == strip_mods(h.get(sec, {}).get("heater_pin", "")):
            score += 1
    return score


def detect_board(P, boards=None, serial=""):
    """Best matching board id for imported pins (or '' when unsure)."""
    boards = boards or load_boards()
    best, best_score = "", 0
    for bid, b in boards.items():
        sc = match_score(P, b) * 10
        procs = b.get("mcu", {}).get("processors") or []
        if serial and any(p in serial.lower() for p in procs):
            sc += 5
        if sc > best_score:
            best, best_score = bid, sc
    return best if best_score >= 90 else ""


def boards_for_mcu(mcu_name, boards=None):
    """Board ids whose processor list contains mcu_name (e.g. 'lpc1769', 'stm32f446xx')."""
    boards = boards or load_boards()
    name = (mcu_name or "").lower()
    out = []
    for bid, b in boards.items():
        for p in b.get("mcu", {}).get("processors") or []:
            if p and (name.startswith(p) or p.startswith(name.replace("xx", ""))):
                out.append(bid)
                break
    return out


def build_hint(board):
    """Human readable make menuconfig summary (values only, no prose)."""
    m = board.get("mcu", {})
    parts = []
    fam = {"lpc176x": "LPC176x", "stm32": "STMicroelectronics STM32", "avr": "Atmega AVR",
           "atsam": "SAM3/SAM4/SAM E70", "rp2040": "Raspberry Pi RP2040/RP235x",
           "hc32f460": "Huada Semiconductor HC32F460", "pru": "Beaglebone PRU"}.get(m.get("family"), m.get("family") or "?")
    parts.append(("Micro-controller", fam))
    if m.get("processors"):
        parts.append(("Processor", " / ".join(p.upper() if p.startswith("stm32") else p for p in m["processors"])))
    if m.get("bootloader"):
        parts.append(("Bootloader offset", " / ".join(m["bootloader"])))
    if m.get("crystal"):
        parts.append(("Clock reference", " / ".join(m["crystal"])))
    if m.get("interfaces"):
        parts.append(("Communication", " / ".join(m["interfaces"])))
    return parts
