# -*- coding: utf-8 -*-
"""Troubleshooter: turns Klipper error messages and klippy.log lines into causes and fixes."""
import re
from collections import OrderedDict

from .i18n import tr

# (id, regex, page to open). Texts are doc.<id>.title / .cause / .fix in i18n.
RULES = [
    ("serial", r"Unable to open serial port|Serial connection closed|mcu '[^']+': Unable to connect|"
               r"No such file or directory: '/dev/serial", "page_board"),
    ("protocol", r"Command format mismatch|MCU Protocol error|mcu '[^']+' has version", "page_board"),
    ("lost_comm", r"Lost communication with MCU", "page_board"),
    ("timer", r"Timer too close|Rescheduled timer in the past|Stepper too far in past|Move queue overflow", "page_motors"),
    ("tmc_comm", r"Unable to (read|write) tmc (uart|spi)|Unable to obtain '[^']+' response|"
                 r"TMC stepper driver.*not responding|tmc.*(IFCNT|ifcnt)", "page_motors"),
    ("tmc_fault", r"TMC '[^']+' reports error: .*(ot=1|otpw|s2ga|s2gb|s2vsa|s2vsb|uv_cp|drv_err|GSTAT)", "page_motors"),
    ("adc", r"ADC out of range", "page_thermal"),
    ("heater_rate", r"Heater \S+ not heating at expected rate", "page_thermal"),
    ("heater_range", r"(Extrude below minimum temp|Heater \S+ temperature .* (above|below)|exceeds (min|max)_temp)", "page_thermal"),
    ("out_of_range", r"Move out of range", "page_machine"),
    ("must_home", r"Must home axis first", "page_machine"),
    ("endstop_triggered", r"Endstop \S+ still triggered after retract", "page_pins"),
    ("no_trigger", r"No trigger on \S+ after full movement", "page_motors"),
    ("probe_prior", r"Probe triggered prior to movement", "page_probe"),
    ("bltouch", r"BLTouch failed to (raise|verify|deploy)", "page_probe"),
    ("probe_tolerance", r"Probe samples exceed samples_tolerance", "page_probe"),
    ("z_tilt_range", r"Retries: \d+/\d+ Probed points range: .* (increasing|exceeds)|"
                     r"Too many retries|max_adjust", "page_motors"),
    ("mesh_range", r"bed_mesh: (Probe|mesh) .* (out of range|outside)|Unable to generate coordinates", "page_probe"),
    ("option_invalid", r"Option '([^']+)' is not valid in section '([^']+)'", "page_files"),
    ("section_invalid", r"Section '([^']+)' is not a valid config section", "page_files"),
    ("option_missing", r"Option '([^']+)' in section '([^']+)' must be specified", "page_files"),
    ("option_limit", r"Option '([^']+)' in section '([^']+)' must have (maximum|minimum) of", "page_machine"),
    ("pin_twice", r"pin \S+ used multiple times in config|Pin '[^']+' used multiple times", "page_pins"),
    ("pin_invalid", r"Unknown pin chip name|Invalid pin description|Unable to parse pin", "page_board"),
    ("duplicate_command", r"(gcode command|macro) \S+ already registered|is already registered", "page_files"),
    ("save_conflict", r"SAVE_CONFIG section '([^']+)' option '([^']+)' conflicts with included value", "page_files"),
    ("include_missing", r"Include file '([^']+)' does not exist", "page_files"),
    ("mcu_temp", r"MCU temperature not supported", "page_extras"),
    ("webhooks", r"Shutdown due to webhooks request", None),
    ("thermal_runaway", r"Thermal Runaway|Heater \S+ not heating", "page_thermal"),
    ("undervoltage", r"Undervoltage|under-voltage", None),
]
_COMPILED = [(rid, re.compile(rx, re.I), page) for rid, rx, page in RULES]


def diagnose(text):
    """Returns [(rule id, matched line, page)] - one entry per rule, most recent match."""
    found = OrderedDict()
    for line in (text or "").splitlines():
        line = line.strip()
        if not line:
            continue
        for rid, rx, page in _COMPILED:
            if rx.search(line):
                found.pop(rid, None)
                found[rid] = (line[:300], page)
    # the heater_rate rule is more specific than thermal_runaway
    if "heater_rate" in found:
        found.pop("thermal_runaway", None)
    return [(rid, line, page) for rid, (line, page) in reversed(list(found.items()))]


def last_session(log_text, max_lines=4000):
    """The part of klippy.log since Klipper last started (errors from old sessions are noise)."""
    lines = (log_text or "").splitlines()
    start = 0
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].startswith("Start printer at"):
            start = i
            break
    out, in_config = [], False
    for ln in lines[start:]:
        # klippy.log repeats the whole config - its comments must not trigger rules
        if "===== Config file =====" in ln:
            in_config = True
            continue
        if in_config:
            if ln.startswith("======================="):
                in_config = False
            continue
        out.append(ln)
    return "\n".join(out[-max_lines:])


def card(rid):
    return tr("doc.%s.title" % rid), tr("doc.%s.cause" % rid), tr("doc.%s.fix" % rid)
