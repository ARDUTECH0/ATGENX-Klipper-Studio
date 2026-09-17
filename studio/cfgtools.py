# -*- coding: utf-8 -*-
"""Low level helpers for Klipper config text."""
import configparser
import re

SAVE_RE = re.compile(r"^#\*# <-+ SAVE_CONFIG -+>", re.M)
SECTION_RE = re.compile(r"^\[([^\]\n]+)\]")
KEY_RE = re.compile(r"^([A-Za-z0-9_]+)\s*[:=]\s?(.*)$")
INLINE_COMMENT_RE = re.compile(r"\s+[#;].*$")


def split_save(text):
    """(main part, SAVE_CONFIG block) - the block starts at the SAVE_CONFIG marker."""
    text = text.replace("\r\n", "\n")
    m = SAVE_RE.search(text)
    if not m:
        return text, ""
    return text[:m.start()], text[m.start():]


def cfg_parser(text):
    c = configparser.ConfigParser(strict=False, interpolation=None, allow_no_value=True,
                                  inline_comment_prefixes=("#", ";"), comment_prefixes=("#", ";"))
    c.optionxform = str.lower
    c.read_string(text)
    return c


def save_as_cfg(save):
    """SAVE_CONFIG block -> plain config text."""
    out = []
    for ln in save.split("\n"):
        if ln.startswith("#*#"):
            s = ln[3:]
            out.append(s[1:] if s.startswith(" ") else s)
    return "\n".join(out)


def num(v, cast=float):
    if v is None:
        return None
    v = INLINE_COMMENT_RE.sub("", str(v)).strip()
    try:
        return cast(float(v)) if cast is int else cast(v)
    except ValueError:
        return None


def fmt(v, nd=3):
    """Compact number formatting: 40.0 -> '40', 0.8500 -> '0.85'."""
    if isinstance(v, bool):
        return "True" if v else "False"
    if isinstance(v, int):
        return str(v)
    try:
        v = float(v)
    except (TypeError, ValueError):
        return str(v)
    if abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    s = ("%.*f" % (nd, v)).rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s


def block(name, rows):
    """Section text from [(key, value)] - None values are skipped, multi-line values indented."""
    out = ["[%s]" % name]
    for k, v in rows:
        if v is None:
            continue
        v = str(v)
        if "\n" in v:
            out.append(k + ":")
            out += ["    " + ln for ln in v.strip("\n").split("\n")]
        else:
            out.append("%s: %s" % (k, v))
    return "\n".join(out)


def parse_blocks(main):
    """(head lines, [{'lead': [...], 'name': str, 'body': [...]}]).

    Comment / blank lines right above a section belong to that section ('lead'),
    so moving or dropping a section keeps its description with it.
    """
    head, blocks, cur = [], [], None
    for ln in main.split("\n"):
        m = SECTION_RE.match(ln)
        if m:
            lead = []
            if cur is not None:
                body = cur["body"]
                while len(body) > 1 and (body[-1].strip() == "" or body[-1].startswith(("#", ";"))):
                    lead.insert(0, body.pop())
            cur = {"lead": lead, "name": m.group(1).strip(), "body": [ln]}
            blocks.append(cur)
        elif cur is None:
            head.append(ln)
        else:
            cur["body"].append(ln)
    return head, blocks


def body_items(lines):
    """Groups section body lines into key items (with continuation lines) and other lines."""
    items = []
    for i, ln in enumerate(lines):
        m = KEY_RE.match(ln)
        last_key = items and items[-1]["kind"] == "key"
        if m and not ln[:1].isspace():
            items.append({"kind": "key", "key": m.group(1).lower(), "lines": [ln]})
        elif last_key and ln[:1].isspace() and ln.strip():
            items[-1]["lines"].append(ln)
        elif last_key and not ln.strip() and _next_indented(lines, i):
            items[-1]["lines"].append(ln)
        else:
            items.append({"kind": "other", "lines": [ln]})
    return items


def _next_indented(lines, i):
    for ln in lines[i + 1:]:
        if ln.strip():
            return ln[:1].isspace()
    return False


def item_value(item):
    m = KEY_RE.match(item["lines"][0])
    parts = [INLINE_COMMENT_RE.sub("", m.group(2)).strip()]
    for ln in item["lines"][1:]:
        s = INLINE_COMMENT_RE.sub("", ln).strip()
        if s and not s.startswith(("#", ";")):
            parts.append(s)
    return "\n".join(p for p in parts if p)


def values_equal(a, b):
    """Compares config values token by token; numbers compare numerically (0.850 == 0.85)."""
    ta = [t for t in re.split(r"[\s,]+", a or "") if t]
    tb = [t for t in re.split(r"[\s,]+", b or "") if t]
    if len(ta) != len(tb):
        return False
    for x, y in zip(ta, tb):
        if x == y or x.lower() == y.lower():
            continue
        try:
            if abs(float(x) - float(y)) < 1e-9:
                continue
        except ValueError:
            pass
        return False
    return True


# keys that the generator owns inside SAVE_CONFIG (None = whole section)
SAVE_OWNED = {
    "extruder": {"control", "pid_kp", "pid_ki", "pid_kd"},
    "heater_bed": {"control", "pid_kp", "pid_ki", "pid_kd"},
    "probe": {"z_offset"},
    "bltouch": {"z_offset"},
    "input_shaper": None,
}


def clean_save(save, owned=None):
    """Removes from SAVE_CONFIG the values now written in the main file, so they take effect."""
    owned = SAVE_OWNED if owned is None else owned
    if not save:
        return ""
    header, secs, cur = [], [], None
    for ln in save.rstrip("\n").split("\n"):
        if not ln.startswith("#*#"):
            continue
        content = ln[3:]
        stripped = content.strip()
        m = re.match(r"^\[([^\]]+)\]$", stripped)
        if m:
            cur = {"name": m.group(1), "items": []}
            secs.append(cur)
            continue
        if cur is None:
            header.append(ln)
            continue
        if stripped == "":
            continue
        rest = content[1:] if content.startswith(" ") else content
        km = re.match(r"^([A-Za-z0-9_]+)\s*[=:]", rest)
        if km and not rest.startswith(("\t", " ")):
            cur["items"].append({"key": km.group(1).lower(), "lines": [ln]})
        elif cur["items"]:
            cur["items"][-1]["lines"].append(ln)
    out, kept = [], 0
    for s in secs:
        if s["name"] in owned and owned[s["name"]] is None:
            continue
        drop = owned.get(s["name"], set())
        items = [it for it in s["items"] if it["key"] not in drop]
        if not items:
            continue
        kept += 1
        out.append("#*# [%s]" % s["name"])
        for it in items:
            out += it["lines"]
        out.append("#*#")
    if not kept:
        return ""
    hdr = [h for h in header if h.strip() != "#*#"] or [
        "#*# <---------------------- SAVE_CONFIG ---------------------->",
        "#*# DO NOT EDIT THIS BLOCK OR BELOW. The contents are auto-generated."]
    return "\n".join(hdr + ["#*#"] + out) + "\n"
