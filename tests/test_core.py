# -*- coding: utf-8 -*-
"""Core tests - no network and no Qt needed.

    python -m unittest discover -s tests -v
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
os.environ.setdefault("ATGENX_STUDIO_HOME", os.path.join(HERE, ".studio_home"))

from studio import i18n  # noqa: E402
from studio.boards import apply_board, detect_board, load_boards  # noqa: E402
from studio.cfgtools import cfg_parser, split_save, values_equal  # noqa: E402
from studio.configset import ConfigSet, restart_kind  # noqa: E402
from studio.importer import import_config  # noqa: E402
from studio.merge import build  # noqa: E402
from studio.model import new_params  # noqa: E402
from studio.validate import validate  # noqa: E402

FIX = os.path.join(HERE, "fixtures")


def read(*parts):
    with io.open(os.path.join(FIX, *parts), encoding="utf-8") as f:
        return f.read()


def errors(R):
    return [m for k, m in R if k == "error"]


class TestCfgTools(unittest.TestCase):
    def test_values_equal(self):
        self.assertTrue(values_equal("0.850", "0.85"))
        self.assertTrue(values_equal("200, 110", "200,110"))
        self.assertTrue(values_equal("True", "true"))
        self.assertFalse(values_equal("0.45", "0.5"))
        self.assertFalse(values_equal("P1.29", "^P1.29"))


class TestBoards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        i18n.set_lang("en")
        cls.boards = load_boards()

    def test_database_loaded(self):
        self.assertGreater(len(self.boards), 70)
        for bid, b in self.boards.items():
            slots = {d["slot"] for d in b["drivers"]}
            for s in ("stepper_x", "stepper_y", "stepper_z", "extruder"):
                self.assertIn(s, slots, "%s has no %s" % (bid, s))

    def test_every_board_generates_a_valid_file(self):
        for bid, b in self.boards.items():
            P = new_params()
            apply_board(P, b)
            P["mcu_serial"] = "/dev/serial/by-id/usb-Klipper_test-if00"
            text = build(P, None, board=b)
            cfg_parser(text)  # must parse
            names = re.findall(r"^\[([^\]\n]+)\]", text, re.M)
            self.assertEqual(len(names), len(set(names)), bid)
            conflicts = [m for m in errors(validate(P, text, b)) if "used twice" in m]
            self.assertEqual(conflicts, [], bid)

    def test_detect_board_from_imported_pins(self):
        P, _ = import_config(read("simple_printer.cfg"), self.boards)
        self.assertEqual(P["board"], "bigtreetech-skr-mini-e3-v3.0")
        self.assertEqual(P["tmc"]["y"]["uart_address"], "2")

    def test_apply_keeps_inversion(self):
        P = new_params()
        P["inv_z"] = True
        apply_board(P, self.boards["bigtreetech-skr-v1.4"], keep_inversion=True)
        self.assertTrue(P["inv_z"])
        self.assertEqual(P["pins"]["z1_step"], "P1.15")  # extruder1 slot
        self.assertEqual(P["tmc"]["x"]["uart_pin"], "P1.10")


class TestMerge(unittest.TestCase):
    def setUp(self):
        i18n.set_lang("en")
        self.text = read("simple_printer.cfg")
        self.P, self.notes = import_config(self.text)

    def test_import_reads_save_config(self):
        self.assertAlmostEqual(self.P["pid_e_kp"], 21.527)
        self.assertAlmostEqual(self.P["pa"], 0.045)
        self.assertEqual(self.P["driver"], "tmc2209")

    def test_merge_keeps_user_lines(self):
        out = build(self.P, self.text, "merge")
        main, save = split_save(out)
        # inline comments and formatting of unchanged values survive
        self.assertIn("max_accel: 3000       # tuned with ringing tower", main)
        self.assertIn("pressure_advance: 0.045   # measured with PA tower", main)
        self.assertIn("rotation_distance: 40.000", main)
        # soft defaults keep the user's value and are not added to existing sections
        self.assertIn("off_below: 0.15", main)
        self.assertNotIn("kick_start_time", main)
        # macros and includes untouched
        self.assertIn("[gcode_macro HELLO]", main)
        self.assertIn("[include macros.cfg]", main)
        # PID moved out of SAVE_CONFIG (so the main file wins), mesh kept
        self.assertIn("pid_Kp: 21.527", main)
        self.assertNotIn("pid_kp", save)
        self.assertIn("[bed_mesh default]", save)

    def test_merge_is_idempotent(self):
        once = build(self.P, self.text, "merge")
        P2, _ = import_config(once)
        twice = build(P2, once, "merge")
        self.assertEqual(once, twice)

    def test_changed_value_is_replaced(self):
        self.P["max_accel"] = 2500
        out = build(self.P, self.text, "merge")
        self.assertIn("max_accel: 2500", out)
        self.assertNotIn("max_accel: 3000", out)

    def test_switched_off_feature_is_removed(self):
        self.P["probe"] = "bltouch"
        self.P["pins"]["bl_sensor"], self.P["pins"]["bl_control"] = "^PC14", "PA1"
        out = build(self.P, self.text, "merge")
        self.assertIn("endstop_pin: probe:z_virtual_endstop", out)
        stepper_z = out.split("[stepper_z]")[1].split("\n[")[0]
        self.assertNotIn("position_endstop", stepper_z)
        self.assertIn("[bltouch]", out)

    def test_full_mode_keeps_macros(self):
        out = build(self.P, self.text, "full", keep_custom=True)
        self.assertIn("[gcode_macro HELLO]", out)
        self.assertEqual(errors(validate(self.P, out))[:1], [])

    def test_validation_catches_common_mistakes(self):
        self.P["max_z_accel"] = 5000
        self.P["pins"]["fan"] = "PC9"  # same as bed heater
        R = validate(self.P, build(self.P, self.text, "merge"))
        msgs = " | ".join(errors(R))
        self.assertIn("max_z_accel", msgs)
        self.assertIn("PC9", msgs)


class TestConfigSet(unittest.TestCase):
    def load(self):
        folder = os.path.join(FIX, "modular")
        listing = []
        for dp, _, files in os.walk(folder):
            for f in files:
                rel = os.path.relpath(os.path.join(dp, f), folder).replace(os.sep, "/")
                listing.append((rel, 10))

        def fetch(p):
            return read("modular", *p.split("/"))
        return ConfigSet.load(fetch, listing)

    def test_include_tree(self):
        cs = self.load()
        self.assertEqual(cs.included[0], "printer.cfg")
        self.assertIn("parts/steppers.cfg", cs.included)
        self.assertIn("parts/macros.cfg", cs.included)
        self.assertEqual(cs.missing, ["missing.cfg"])
        self.assertIn("moonraker.conf", cs.files)
        self.assertEqual(cs.section_files()["stepper_x"], "parts/steppers.cfg")

    def test_modular_import(self):
        cs = self.load()
        P, _ = import_config(cs.files["printer.cfg"], includes_text=cs.includes_text())
        self.assertEqual(P["kinematics"], "corexy")
        self.assertEqual(P["microsteps"], 32)
        self.assertEqual(P["pins"]["x_step"], "P2.2")

    def test_restart_kind(self):
        self.assertEqual(restart_kind("printer.cfg"), "klipper")
        self.assertEqual(restart_kind("moonraker.conf"), "moonraker")
        self.assertEqual(restart_kind("crowsnest.conf"), "crowsnest")
        self.assertEqual(restart_kind("notes.txt"), "")


class TestI18n(unittest.TestCase):
    def test_all_used_keys_exist_in_every_language(self):
        root = os.path.join(os.path.dirname(HERE), "studio")
        used = set()
        for dp, _, files in os.walk(root):
            for f in files:
                if f.endswith(".py") and f != "i18n.py":
                    with io.open(os.path.join(dp, f), encoding="utf-8") as fh:
                        src = fh.read()
                    used |= set(re.findall(r"""tr\(\s*["']([a-z_0-9]+\.[a-z_0-9]+)["']""", src))
                    used |= set(re.findall(r"""\(\s*["']((?:note|val|pin)\.[a-z_0-9]+)["']""", src))
        used = {k for k in used if not k.endswith("_")}  # dynamic prefixes like "up.busy_" + state
        used |= {"up.busy_printing", "up.busy_paused", "state.printing", "state.paused"}
        missing = sorted(k for k in used if k not in i18n.STRINGS)
        self.assertEqual(missing, [])
        for key, entry in i18n.STRINGS.items():
            for lang in i18n.LANGS:
                self.assertTrue(entry.get(lang), "%s has no %s text" % (key, lang))
            ph = {lang: sorted(set(re.findall(r"\{(\w+)\}", entry[lang]))) for lang in i18n.LANGS}
            self.assertEqual(ph["en"], ph["ar"], "placeholders differ in " + key)


if __name__ == "__main__":
    unittest.main()
