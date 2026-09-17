# -*- coding: utf-8 -*-
"""
Build boards/*.json from Klipper's official board files.

    python tools/import_klipper_boards.py  <klipper>/config  [boards_dir]

Only factual pin data is extracted (pins, MCU, bootloader offset, clock,
interfaces). Each board keeps a link to the original Klipper file, which
remains the reference for flashing instructions.

Commented-out sections such as "#[tmc2209 stepper_x]" or "#[bltouch]" are
parsed too, because that is where most boards document their optional pins.
"""
import io
import json
import os
import re
import sys
from collections import OrderedDict

SOURCE_URL = "https://github.com/Klipper3d/klipper/blob/master/config/%s"

VENDORS = OrderedDict([
    ("bigtreetech", "BIGTREETECH"), ("fysetc", "FYSETC"), ("mks", "Makerbase (MKS)"),
    ("mellow", "Mellow"), ("creality", "Creality"), ("duet", "Duet3D"), ("ldo", "LDO"),
    ("prusa", "Prusa"), ("einsy", "Prusa"), ("mini-rambo", "Ultimachine"), ("rambo", "Ultimachine"),
    ("th3d", "TH3D"), ("ultimaker", "Ultimaker"), ("printrboard", "Printrbot"),
    ("azteeg", "Panucatt"), ("smoothieboard", "Smoothieware"), ("re-arm", "Panucatt"),
    ("alligator", "Alligator"), ("archim", "Ultimachine"), ("I3DBEEZ9", "I3DBEEZ"),
])

SPECIAL_NAMES = {
    "ramps": "RAMPS 1.4", "re-arm": "Re-ARM", "cramps": "CRAMPS", "melzi": "Melzi",
    "gt2560": "Geeetech GT2560", "rumba": "RUMBa", "radds": "RADDS", "remram": "RemRam",
    "replicape": "Replicape", "flyboard": "FlyBoard", "mightyboard": "MightyBoard",
    "minitronics1": "Minitronics 1.0", "simulavr": "SimulAVR (testing)",
    "I3DBEEZ9": "I3DBEEZ9",
}

# Sections whose pins become board "resources"
STEPPER_RE = re.compile(r"^(stepper_[a-z]\d*|stepper_|extruder\d*)$")
TMC_RE = re.compile(r"^(tmc\d+)\s+(\S+)$")
TMC_KEYS = ("uart_pin", "tx_pin", "uart_address", "cs_pin", "spi_bus",
            "spi_software_miso_pin", "spi_software_mosi_pin", "spi_software_sclk_pin",
            "diag_pin", "diag1_pin")

# Active sections the board needs to work correctly (USB pull-ups,
# digipots, stepper current PWM, second MCU, ...). They are copied as-is.
EXTRA_TYPES = {"static_digital_output", "output_pin", "mcp4018", "mcp4451", "mcp4728",
               "ad5206", "dac084", "adc_scaled", "replicape", "sx1509", "pca9533",
               "temperature_sensor", "thermistor", "temperature_fan", "controller_fan", "mcu"}
EXTRA_SKIP_NAMES = {"output_pin beeper_pin", "temperature_sensor k_therm"}

MCU_PATTERNS = [
    (r"\bLPC1769\b", "lpc176x", "lpc1769"), (r"\bLPC1768\b", "lpc176x", "lpc1768"),
    (r"\bSTM32([A-Z]\d[A-Z0-9]{2,})", "stm32", None),
    (r"\b(atmega\d+\w*|at90usb\d+)", "avr", None),
    (r"\b(?:AT)?(SAM3X8E|SAM4E8E|SAM4S8C|SAME70Q20B|SAMD51\w*|SAMD21\w*)\b", "atsam", None),
    (r"\b(Arduino Due)\b", "atsam", "sam3x8e"),
    (r"\bRP2040\b", "rp2040", "rp2040"), (r"\bHC32F460\b", "hc32f460", "hc32f460"),
    (r"\b(Beaglebone|PRU)\b", "pru", None),
]


def board_name(fname):
    base = fname[len("generic-"):-len(".cfg")]
    vendor = ""
    for key, v in VENDORS.items():
        if base.lower().startswith(key.lower()):
            vendor = v
            break
    if base in SPECIAL_NAMES:
        return vendor or SPECIAL_NAMES[base], SPECIAL_NAMES[base]
    rest = base
    for pre in ("bigtreetech-", "fysetc-", "mks-", "mellow-", "creality-", "ldo-", "th3d-", "prusa-"):
        if rest.startswith(pre):
            rest = rest[len(pre):]
    words = []
    for w in rest.split("-"):
        if re.match(r"^v\d", w):
            words.append("V" + w[1:])
        elif w in ("skr", "e3", "ez", "mz", "cr6", "gtr", "dip", "hv", "sgenl", "rrf", "cdy", "f6", "s6"):
            words.append(w.upper())
        elif re.match(r"^m\d+p$", w):
            words.append(w.upper())
        else:
            words.append(w.capitalize())
    title = " ".join(words)
    short = vendor.split(" (")[0]
    if not vendor or title.lower().startswith(short.lower()):
        return vendor, title
    return vendor, "%s %s" % (short, title)


def strip_inline(v):
    m = re.search(r"\s[#;]\s*(.*)$", v)
    if m:
        return v[:m.start()].strip(), m.group(1).strip()
    return v.strip(), ""


def parse_sections(text):
    """Returns [(name, commented, OrderedDict(key -> (value, label)), label_above)]."""
    out, cur, prev_comment = [], None, ""
    for raw in text.replace("\r\n", "\n").split("\n"):
        line = raw.rstrip()
        m = re.match(r"^(#\s?)?\[([^\]]*)\]", line)
        if m:
            name = m.group(2).strip()
            cur = (name, bool(m.group(1)), OrderedDict(), prev_comment)
            out.append(cur)
            prev_comment = ""
            continue
        if cur is None:
            continue
        commented = cur[1]
        body = line
        if commented:
            if not body.startswith("#"):
                if body.strip():
                    cur = None
                continue
            body = body[1:]
        elif body.startswith("#"):
            c = body.lstrip("#").strip()
            prev_comment = c if len(c) <= 24 and not c.startswith("[") else ""
            continue
        km = re.match(r"^([A-Za-z0-9_]+)\s*[:=]\s*(.*)$", body)
        if km:
            val, lab = strip_inline(km.group(2))
            cur[2][km.group(1).lower()] = [val, lab]
        elif (not commented and body.startswith((" ", "\t")) and cur[2]
              and not body.strip().startswith(("#", ";"))):
            k = next(reversed(cur[2]))
            cur[2][k][0] = (cur[2][k][0] + "\n" + body.strip()).strip()
        if not line.strip():
            prev_comment = ""
    return out


def header_text(text):
    lines = []
    for ln in text.replace("\r\n", "\n").split("\n"):
        if re.match(r"^#?\s?\[", ln):
            break
        if ln.startswith("#"):
            lines.append(ln[1:].strip())
    return " ".join(lines)


def mcu_info(text, pins):
    head = header_text(text)
    family, procs = None, []
    for pat, fam, proc in MCU_PATTERNS:
        for m in re.finditer(pat, head, re.I):
            family = family or fam
            name = proc or m.group(1)
            if fam == "stm32":
                name = "stm32" + m.group(1).lower()
            name = name.lower()
            if name not in procs:
                procs.append(name)
    if not family:
        sample = " ".join(pins)
        if re.search(r"\bP\d\.\d+", sample):
            family = "lpc176x"
        elif re.search(r"\bgpio\d+", sample):
            family = "rp2040"
        elif re.search(r"\bar\d+", sample):
            family = "avr"
        elif re.search(r"\bP[A-K]\d+", sample):
            family = "atsam" if re.search(r"\bP[A-D]\d{2}\b", sample) and "stm32" not in head.lower() else "stm32"
    boot = sorted(set(m.group(1) + "KiB" for m in re.finditer(r"(\d+)\s*KiB bootloader", head, re.I)),
                  key=lambda s: int(s[:-3]))
    xtal = sorted(set(m.group(1) + "MHz" for m in re.finditer(r"(\d+)\s*MHz\s*crystal", head, re.I)),
                  key=lambda s: int(s[:-3]))
    ifaces = []
    for pat, name in ((r"\bUSB\b", "USB"), (r"\bUSART\d|serial \(on", "UART"), (r"\bCAN\s?bus\b", "CAN")):
        if re.search(pat, head, re.I):
            ifaces.append(name)
    return OrderedDict([("family", family), ("processors", procs), ("bootloader", boot),
                        ("crystal", xtal), ("interfaces", ifaces)])


def convert(path):
    fname = os.path.basename(path)
    text = io.open(path, encoding="utf-8").read()
    secs = parse_sections(text)
    vendor, name = board_name(fname)
    B = OrderedDict([
        ("schema", 1),
        ("id", fname[len("generic-"):-len(".cfg")].lower()),
        ("name", name),
        ("vendor", vendor or "Other"),
        ("source", SOURCE_URL % fname),
        ("mcu", None),
        ("drivers", []),
        ("heaters", OrderedDict()),
        ("fans", []),
        ("probe", OrderedDict()),
        ("neopixel", ""),
        ("filament_sensors", []),
        ("servo", ""),
        ("extra_sections", []),
        ("aliases", ""),
        ("tmc_types", []),
    ])
    drivers = OrderedDict()
    all_pins = []

    for sname, commented, opts, label in secs:
        v = lambda k: opts[k][0] if k in opts else ""
        stype = sname.split()[0] if sname else ""
        for val, _ in opts.values():
            all_pins.append(val)

        if STEPPER_RE.match(sname):
            if not v("step_pin"):
                continue
            d = drivers.setdefault(sname, OrderedDict([("slot", sname), ("label", label), ("commented", commented)]))
            for k in ("step_pin", "dir_pin", "enable_pin", "endstop_pin"):
                if v(k) and "probe:" not in v(k):
                    d[k] = v(k)
            d.setdefault("tmc", OrderedDict())
            if sname.startswith("extruder") and (v("heater_pin") or v("sensor_pin")):
                B["heaters"][sname] = OrderedDict([("heater_pin", v("heater_pin")), ("sensor_pin", v("sensor_pin")),
                                                   ("label", opts.get("heater_pin", ["", ""])[1])])
            continue

        m = TMC_RE.match(sname)
        if m:
            ttype, target = m.group(1), m.group(2)
            if ttype not in B["tmc_types"]:
                B["tmc_types"].append(ttype)
            d = drivers.setdefault(target, OrderedDict([("slot", target), ("label", ""), ("commented", True), ("tmc", OrderedDict())]))
            for k in TMC_KEYS:
                if v(k) and k not in d["tmc"]:
                    d["tmc"][k] = v(k)
            continue

        if sname == "heater_bed":
            B["heaters"]["heater_bed"] = OrderedDict([("heater_pin", v("heater_pin")), ("sensor_pin", v("sensor_pin")), ("label", "")])
        elif sname == "fan" or stype in ("heater_fan", "controller_fan", "fan_generic"):
            if v("pin"):
                B["fans"].append(OrderedDict([("name", sname), ("pin", v("pin")),
                                              ("label", opts["pin"][1]), ("commented", commented)]))
            # an active controller_fan is also copied as a required section below
            if stype != "controller_fan" or commented:
                continue
        elif sname == "probe" and v("pin"):
            B["probe"]["pin"] = v("pin")
        elif sname == "bltouch":
            if v("sensor_pin"):
                B["probe"]["bl_sensor"] = v("sensor_pin")
            if v("control_pin"):
                B["probe"]["bl_control"] = v("control_pin")
        elif stype == "neopixel" and v("pin") and not B["neopixel"]:
            B["neopixel"] = v("pin")
        elif stype == "filament_switch_sensor" and v("switch_pin"):
            B["filament_sensors"].append(v("switch_pin"))
        elif stype == "servo" and v("pin") and not B["servo"]:
            B["servo"] = v("pin")
        elif sname == "board_pins" and not commented:
            B["aliases"] = v("aliases")

        if (not commented and stype in EXTRA_TYPES and sname != "mcu"
                and sname.lower() not in EXTRA_SKIP_NAMES):
            B["extra_sections"].append(OrderedDict([("name", sname),
                                                    ("options", [[k, val] for k, (val, _) in opts.items()])]))

    order = ["stepper_x", "stepper_y", "stepper_z", "stepper_z1", "stepper_z2", "stepper_z3",
             "extruder", "stepper_"] + ["extruder%d" % i for i in range(1, 8)]
    slots = sorted(drivers.values(), key=lambda d: order.index(d["slot"]) if d["slot"] in order else 99)
    B["drivers"] = [d for d in slots if d.get("step_pin")]
    B["mcu"] = mcu_info(text, all_pins)
    return B


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    src = argv[1]
    dst = argv[2] if len(argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "boards")
    os.makedirs(dst, exist_ok=True)
    files = sorted(f for f in os.listdir(src) if f.startswith("generic-") and f.endswith(".cfg"))
    n = 0
    for f in files:
        if "simulavr" in f:
            continue
        B = convert(os.path.join(src, f))
        if len(B["drivers"]) < 4:
            print("skip %-45s (only %d drivers)" % (f, len(B["drivers"])))
            continue
        with io.open(os.path.join(dst, B["id"] + ".json"), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(B, fh, ensure_ascii=False, indent=1)
            fh.write("\n")
        n += 1
        print("%-42s %-8s drivers=%d tmc=%s extras=%d" % (B["id"], B["mcu"]["family"], len(B["drivers"]),
                                                         ",".join(B["tmc_types"]), len(B["extra_sections"])))
    print("\n%d boards written to %s" % (n, os.path.abspath(dst)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
