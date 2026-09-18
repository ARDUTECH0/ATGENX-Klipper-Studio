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
from studio.boards import apply_board, assign_slot, load_boards, slots  # noqa: E402
from studio.doctor import RULES, diagnose, last_session  # noqa: E402
from studio.model import enabled_motors, project_from_dict  # noqa: E402
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


def page_builders():
    """Page builder names from the GUI source (without importing Qt)."""
    with io.open(os.path.join(os.path.dirname(HERE), "studio", "gui", "pages.py"), encoding="utf-8") as fh:
        src = fh.read()
    return re.findall(r'\("nav\.[a-z]+", "(page_[a-z]+)"\)', src)


def errors(R):
    return [r[1] for r in R if r[0] == "error"]


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
        self.assertEqual(P["motors"]["y"]["bus"]["uart_address"], "2")
        self.assertEqual(P["motors"]["y"]["slot"], "stepper_y")

    def test_apply_keeps_inversion(self):
        P = new_params()
        P["motors"]["z"]["invert"] = True
        P["motors"]["z1"]["enabled"] = True
        apply_board(P, self.boards["bigtreetech-skr-v1.4"], keep_inversion=True)
        self.assertTrue(P["motors"]["z"]["invert"])
        self.assertEqual(P["motors"]["z1"]["slot"], "extruder1")
        self.assertEqual(P["motors"]["z1"]["step_pin"], "P1.15")
        self.assertEqual(P["motors"]["x"]["bus"]["uart_pin"], "P1.10")

    def test_any_motor_on_any_socket(self):
        b = self.boards["bigtreetech-octopus-v1.1"]
        P = new_params()
        for mid in ("z1", "z2", "z3"):
            P["motors"][mid]["enabled"] = True
        apply_board(P, b)
        used = [P["motors"][m]["slot"] for m in enabled_motors(P)]
        self.assertEqual(len(used), len(set(used)))  # 7 motors on 7 different sockets
        assign_slot(P, "e", b, "extruder3")
        self.assertEqual(P["motors"]["e"]["step_pin"], slots(b)["extruder3"]["step_pin"])


class TestMerge(unittest.TestCase):
    def setUp(self):
        i18n.set_lang("en")
        self.text = read("simple_printer.cfg")
        self.P, self.notes = import_config(self.text)

    def test_import_reads_save_config(self):
        self.assertAlmostEqual(self.P["pid_e_kp"], 21.527)
        self.assertAlmostEqual(self.P["pa"], 0.045)
        self.assertEqual(self.P["motors"]["x"]["driver"], "tmc2209")

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


class TestMotorsAndDrivers(unittest.TestCase):
    def setUp(self):
        i18n.set_lang("en")
        self.board = load_boards()["bigtreetech-octopus-v1.1"]
        P = new_params()
        P["probe"], P["probe_z"], P["pa"] = "inductive", 1.0, 0.04
        P["mcu_serial"] = "/dev/serial/by-id/usb-Klipper_stm32f446xx_TEST-if00"
        for mid in ("z1", "z2", "z3"):
            P["motors"][mid]["enabled"] = True
        apply_board(P, self.board)
        P["pins"]["probe"] = "^PB7"
        self.P = P

    def gen(self):
        return build(self.P, None, board=self.board)

    def test_quad_z_generates_z_tilt_with_4_positions(self):
        out = self.gen()
        for sec in ("stepper_z1", "stepper_z2", "stepper_z3", "tmc2209 stepper_z3"):
            self.assertIn("[%s]" % sec, out)
        z_tilt = out.split("[z_tilt]")[1].split("\n[")[0]
        self.assertEqual(z_tilt.split("points:")[0].count(","), 4)
        self.assertEqual(errors(validate(self.P, out, self.board)), [])

    def test_quad_gantry_level(self):
        self.P["kinematics"], self.P["z_leveling"] = "corexy", "quad_gantry_level"
        out = self.gen()
        self.assertIn("[quad_gantry_level]", out)
        self.assertNotIn("[z_tilt]", out)
        self.P["motors"]["z3"]["enabled"] = False
        self.assertTrue(any("exactly 4" in m for m in errors(validate(self.P, self.gen(), self.board))))

    def test_sensorless_homing(self):
        m = self.P["motors"]["x"]
        m["sensorless"], m["sg"], m["hold_current"] = True, 90, 0.0
        out = self.gen()
        self.assertIn("endstop_pin: tmc2209_stepper_x:virtual_endstop", out)
        self.assertIn("homing_retract_dist: 0", out)
        tmc = out.split("[tmc2209 stepper_x]")[1].split("\n[")[0]
        self.assertIn("diag_pin: ^", tmc)
        self.assertIn("driver_SGTHRS: 90", tmc)
        P2, _ = import_config(out)
        self.assertTrue(P2["motors"]["x"]["sensorless"])
        self.assertEqual(P2["motors"]["x"]["sg"], 90)
        m["driver"] = "tmc2208"
        self.assertTrue(any("StallGuard" in e for e in errors(validate(self.P, self.gen(), self.board))))

    def test_mixed_drivers_and_features(self):
        x = self.P["motors"]["x"]
        x["driver"], x["bus"] = "tmc5160", {"cs_pin": "PC4", "spi_bus": "spi1"}
        x["sense_resistor"], x["interpolate"], x["full_steps"] = 0.075, False, 400
        x["autotune"], x["tuning_goal"] = "ldo-42sth48-2504ac", "performance"
        out = self.gen()
        tmc = out.split("[tmc5160 stepper_x]")[1].split("\n[")[0]
        for line in ("cs_pin: PC4", "spi_bus: spi1", "sense_resistor: 0.075", "interpolate: False"):
            self.assertIn(line, tmc)
        self.assertIn("full_steps_per_rotation: 400", out)
        self.assertIn("[autotune_tmc stepper_x]\nmotor: ldo-42sth48-2504ac\ntuning_goal: performance", out)
        self.assertIn("[tmc2209 stepper_y]", out)
        P2, _ = import_config(out)
        self.assertEqual(P2["motors"]["x"]["driver"], "tmc5160")
        self.assertEqual(P2["motors"]["x"]["full_steps"], 400)
        self.assertEqual(P2["motors"]["x"]["autotune"], "ldo-42sth48-2504ac")

    def test_socket_conflict_is_an_error(self):
        self.P["motors"]["z3"]["slot"] = self.P["motors"]["z"]["slot"]
        self.assertTrue(any("is used by both" in e for e in errors(validate(self.P, self.gen(), self.board))))

    def test_addons_and_macros(self):
        P = self.P
        P["retraction"], P["idle_timeout_min"], P["host_temp"], P["mcu_temp"] = True, 30, True, True
        P["print_macros"] = True
        out = self.gen()
        for s in ("[firmware_retraction]", "timeout: 1800", "sensor_type: temperature_host",
                  "sensor_type: temperature_mcu", "[gcode_macro START_PRINT]", "BED_MESH_CALIBRATE ADAPTIVE=1",
                  "Z_TILT_ADJUST", "[gcode_macro M600]"):
            self.assertIn(s, out)
        cfg_parser(out)
        P2, _ = import_config(out)
        self.assertTrue(P2["retraction"] and P2["host_temp"] and P2["mcu_temp"] and P2["print_macros"])
        self.assertEqual(P2["idle_timeout_min"], 30)
        lpc = load_boards()["bigtreetech-skr-v1.4"]
        self.assertTrue(any("processors" in e for e in errors(validate(P, out, lpc))))

    def test_user_macro_is_never_replaced(self):
        base = read("simple_printer.cfg").replace("[gcode_macro HELLO]", "[gcode_macro START_PRINT]")
        P, _ = import_config(base)
        P["print_macros"] = True
        out = build(P, base, "merge")
        self.assertEqual(out.count("[gcode_macro START_PRINT]"), 1)
        self.assertIn('RESPOND MSG="hello"', out)
        self.assertIn("[gcode_macro END_PRINT]", out)
        P2, _ = import_config(out)
        P2["print_macros"] = False
        out2 = build(P2, out, "merge")
        self.assertIn("[gcode_macro START_PRINT]", out2)
        self.assertNotIn("[gcode_macro END_PRINT]", out2)

    def test_schema1_project_is_converted(self):
        old = {"kind": "atgenx-klipper-studio", "version": "1.0.0-beta.1", "driver": "tmc2208", "dual_z": True,
               "cur_z": 0.65, "inv_z": True, "rd_z": 8, "microsteps": 16, "hold_ratio": 0.5, "cur_xy": 0.8,
               "pins": {"z1_step": "P1.15", "x_step": "P2.2", "fan": "P2.3"}, "tmc": {"z1": {"uart_pin": "P1.1"}}}
        P = project_from_dict(old)
        z1 = P["motors"]["z1"]
        self.assertTrue(z1["enabled"] and z1["invert"])
        self.assertEqual((z1["step_pin"], z1["driver"], z1["run_current"]), ("P1.15", "tmc2208", 0.65))
        self.assertEqual(z1["bus"]["uart_pin"], "P1.1")
        self.assertAlmostEqual(P["motors"]["x"]["hold_current"], 0.4)
        self.assertEqual(P["pins"]["fan"], "P2.3")


class TestDoctor(unittest.TestCase):
    def test_common_errors_are_recognised(self):
        samples = {
            "mcu 'mcu': Unable to connect": "serial",
            "Lost communication with MCU 'mcu'": "lost_comm",
            "MCU 'mcu' shutdown: Timer too close": "timer",
            "Unable to read tmc uart 'stepper_x' register IFCNT": "tmc_comm",
            "ADC out of range": "adc",
            "Heater extruder not heating at expected rate": "heater_rate",
            "Endstop x still triggered after retract": "endstop_triggered",
            "Probe triggered prior to movement": "probe_prior",
            "Option 'uart_address' is not valid in section 'tmc2208 stepper_x'": "option_invalid",
            "Section 'led_effect heating' is not a valid config section": "section_invalid",
            "MCU temperature not supported on lpc1769": "mcu_temp",
        }
        for text, rid in samples.items():
            self.assertIn(rid, [h[0] for h in diagnose(text)], text)

    def test_log_config_dump_is_ignored(self):
        log = ("Start printer at Mon\n===== Config file =====\n# ADC out of range happened once\n"
               "=======================\nLost communication with MCU 'mcu'\n")
        self.assertEqual([h[0] for h in diagnose(last_session(log))], ["lost_comm"])


class TestHelpAndLayout(unittest.TestCase):
    def test_every_setting_has_help_in_every_language(self):
        from studio.help import HELP, PAGE_GUIDE
        root = os.path.join(os.path.dirname(HERE), "studio", "gui")
        keys = set()
        for f in os.listdir(root):
            if f.endswith(".py"):
                with io.open(os.path.join(root, f), encoding="utf-8") as fh:
                    src = fh.read()
                keys |= set(re.findall(r'self\.(?:spin|check|combo|line|_multi_line)\("([a-z_0-9]+)"', src))
                keys |= set(re.findall(r'register_help\([^,]+, "([a-z_0-9.]+)"', src))
                keys |= set(re.findall(r'"(motor\.[a-z_]+)"', src))
        self.assertGreater(len(keys), 60)
        self.assertEqual(sorted(k for k in keys if k not in HELP), [])
        for key, h in HELP.items():
            self.assertTrue(h["en"] and h["ar"], key)
            self.assertIn(h["page"], PAGE_GUIDE, key)
        self.assertEqual([b for b in page_builders() if b not in PAGE_GUIDE], [])

    def test_checks_point_to_a_page(self):
        from studio.validate import check_page
        pages = set(page_builders())
        with io.open(os.path.join(os.path.dirname(HERE), "studio", "validate.py"), encoding="utf-8") as fh:
            src = fh.read()
        for key in set(re.findall(r'"(val\.[a-z_0-9]+)"', src)):
            self.assertIn(check_page(key), pages, key)
        self.assertEqual(check_page("val.slot_conflict"), "page_motors")
        self.assertEqual(check_page("val.parse_ok"), "page_files")
        self.assertEqual(check_page("val.pa_zero"), "page_thermal")

    def test_new_file_is_grouped_and_explained_without_duplicates(self):
        i18n.set_lang("en")
        text = read("simple_printer.cfg")
        P, _ = import_config(text)
        once = build(P, text, "full", keep_custom=True)
        twice = build(import_config(once)[0], once, "full", keep_custom=True)
        for out in (once, twice):
            self.assertEqual(out.count("#  Motors and drivers"), 1)
            self.assertEqual(out.count("# Connection to the controller board"), 1)
            self.assertIn("[gcode_macro HELLO]", out)
            cfg_parser(out)
        main = split_save(once)[0]
        self.assertLess(main.index("[mcu]"), main.index("[printer]"))
        self.assertLess(main.index("[printer]"), main.index("[stepper_x]"))
        self.assertLess(main.index("[extruder]"), main.index("[virtual_sdcard]"))

    def test_merge_explains_only_new_sections(self):
        i18n.set_lang("en")
        text = read("simple_printer.cfg")
        P, _ = import_config(text)
        P["retraction"] = True
        out = build(P, text, "merge")
        self.assertIn("# Firmware retraction for G10/G11", out)
        self.assertNotIn("# Connection to the controller board", out)  # existing sections get no new comments


class TestFeatures(unittest.TestCase):
    def setUp(self):
        i18n.set_lang("en")

    def test_every_feature_and_catalog_item_is_translated(self):
        from studio.features import BUILTIN, CATALOG
        cats = {spec[1] for spec in BUILTIN.values()} | {spec[1] for spec in CATALOG.values()}
        keys = ["feat.%s.%s" % (f, p) for f in BUILTIN for p in ("title", "desc")]
        keys += ["cat.%s.%s" % (c, p) for c in CATALOG for p in ("title", "desc")]
        keys += ["fcat." + c for c in cats]
        self.assertEqual([k for k in keys if k not in i18n.STRINGS], [])

    def test_dependencies_are_switched_together(self):
        from studio.features import feature_on, set_feature
        P = new_params()
        changed = set_feature(P, "adaptive_mesh", True)
        self.assertTrue(feature_on(P, "probe") and P["print_macros"] and P["exclude_object"] and P["adaptive_mesh"])
        self.assertIn("probe", changed)
        set_feature(P, "probe", False)
        self.assertFalse(feature_on(P, "adaptive_mesh"))
        set_feature(P, "led_effects", True)
        self.assertTrue(P["leds"] and P["led_effects"])
        set_feature(P, "multi_z", True)
        self.assertTrue(P["motors"]["z1"]["enabled"] and P["probe"] != "none")

    def test_catalog_templates_are_valid_klipper_config(self):
        from studio.features import CATALOG, fill_template, section_names
        P = new_params()
        for cid, spec in CATALOG.items():
            text = fill_template(P, spec[3])
            self.assertTrue(section_names(text), cid)
            cfg_parser(text)

    def test_switch_sections_off_and_on_again(self):
        from studio.features import apply_section_toggles, list_sections
        from studio.merge import is_managed
        text = read("simple_printer.cfg").replace("#*# <", "#[adxl345]\n#cs_pin: rpi:None\n# # an inner note\n#spi_speed: 2000000\n\n#*# <", 1)
        P, _ = import_config(text)
        secs = dict(list_sections(text, lambda n: is_managed(n, P)))
        self.assertTrue(secs["gcode_macro HELLO"])
        self.assertFalse(secs["adxl345"])
        on = apply_section_toggles(text, disable=["gcode_macro HELLO"], enable=["adxl345"])
        c = cfg_parser(split_save(on)[0])
        self.assertEqual(c.get("adxl345", "spi_speed"), "2000000")
        self.assertFalse(c.has_section("gcode_macro HELLO"))
        self.assertIn('#    RESPOND MSG="hello"', on)
        back = apply_section_toggles(on, disable=["adxl345"], enable=["gcode_macro HELLO"])
        c2 = cfg_parser(split_save(back)[0])
        self.assertTrue(c2.has_section("gcode_macro HELLO") and not c2.has_section("adxl345"))

    def test_added_features_and_missing_mcu_check(self):
        from studio.features import CATALOG, fill_template
        text = read("simple_printer.cfg")
        P, _ = import_config(text)
        P["custom_sections"] = [{"id": "adxl_pico", "text": fill_template(P, CATALOG["adxl_pico"][3]), "enabled": True},
                                {"id": "skew_correction", "text": "[skew_correction]", "enabled": False}]
        out = build(P, text, "merge")
        self.assertIn("[mcu adxl]", out)
        self.assertNotIn("[skew_correction]", out)
        self.assertLess(out.index("[adxl345]"), out.index("SAVE_CONFIG"))
        self.assertEqual(build(import_config(out)[0], out, "merge").count("[adxl345]"), 1)
        P["custom_sections"][0]["text"] = "[adxl345]\ncs_pin: pico:gpio1\n"
        msgs = errors(validate(P, build(P, text, "merge")))
        self.assertTrue(any("mcu pico" in m for m in msgs), msgs)


class TestWiringMap(unittest.TestCase):
    def test_a_switched_off_section_is_not_reported_as_a_problem(self):
        """Found on a real printer: [adxl345] and [mcu pico] both commented out is not an error."""
        P = new_params()
        text = (
            "[stepper_x]\nstep_pin: PA1\n"
            "# [mcu pico]\n# serial: /dev/serial/by-id/usb-Klipper_rp2040_X-if00\n"
            "# [adxl345]\n# cs_pin: pico:gpio1\n"
        )
        from studio.wiring import wiring
        data = wiring(P, None, text)
        adxl = [n for n in data["nodes"] if "adxl345" in n["label"]]
        self.assertTrue(adxl, "the commented section should still be drawn")
        self.assertTrue(adxl[0]["off"])
        self.assertEqual([p.get("issue") for p in adxl[0]["pins"] if p.get("issue")], [])
        self.assertEqual(adxl[0]["issues"], [])

    def setUp(self):
        i18n.set_lang("en")
        self.text = read("simple_printer.cfg")
        self.P, _ = import_config(self.text)
        self.board = load_boards()[self.P["board"]]

    def map(self, text=None):
        from studio.wiring import wiring
        return wiring(self.P, self.board, text if text is not None else self.text)

    def test_every_device_and_pin_is_on_the_map(self):
        from studio.wiring import GROUPS
        data = self.map()
        ids = {n["id"] for n in data["nodes"]}
        for expected in ("motor:x", "motor:y", "motor:z", "motor:e", "heater:e", "sensor:e", "heater:bed", "fan:part"):
            self.assertIn(expected, ids)
        self.assertEqual([g for g in (n["group"] for n in data["nodes"]) if g not in GROUPS], [])
        x = next(n for n in data["nodes"] if n["id"] == "motor:x")
        pins = {p["role"]: p["pin"] for p in x["pins"]}
        self.assertEqual(pins["step_pin"], "PB13")
        self.assertEqual(pins["endstop_pin"], "^PC0")
        self.assertEqual(pins["bus:uart_pin"], "PC11")
        self.assertTrue(all(p["board"] == "mcu" for p in x["pins"]))
        self.assertEqual([n for n in data["nodes"] if n["issues"]], [])

    def test_a_pin_used_twice_shows_on_both_devices(self):
        self.P["pins"]["fan"] = self.P["pins"]["bed_heater"]
        data = self.map()
        bad = [n["label"] for n in data["nodes"] if n["issues"]]
        self.assertEqual(len(bad), 1, bad)
        self.assertTrue(data["issues"] and "used by" in data["issues"][0])

    def test_empty_pin_is_flagged(self):
        self.P["pins"]["e_heater"] = ""
        node = next(n for n in self.map()["nodes"] if n["id"] == "heater:e")
        self.assertTrue(node["issues"])

    def test_second_board_and_added_sections(self):
        text = self.text.replace("#*# <", "[mcu adxl]\nserial: /dev/ttyACM1\n\n[adxl345]\ncs_pin: adxl:gpio1\n\n#*# <", 1)
        data = self.map(text)
        self.assertEqual([b["id"] for b in data["boards"]], ["mcu", "adxl"])
        adxl = next(n for n in data["nodes"] if n["id"] == "section:adxl345")
        self.assertEqual(adxl["pins"][0]["board"], "adxl")
        self.assertFalse(adxl["issues"])
        # the same thing with the board switched off
        off = text.replace("[mcu adxl]\nserial:", "#[mcu adxl]\n#serial:", 1)
        data2 = self.map(off)
        adxl2 = next(n for n in data2["nodes"] if n["id"] == "section:adxl345")
        self.assertTrue(any("switched off" in i for i in adxl2["issues"]), adxl2["issues"])

    def test_editing_a_pin_on_the_map(self):
        from studio.wiring import set_pin
        self.assertTrue(set_pin(self.P, "motor:x", "step_pin", "PA1"))
        self.assertEqual(self.P["motors"]["x"]["step_pin"], "PA1")
        self.assertTrue(set_pin(self.P, "motor:x", "bus:uart_pin", "PB5"))
        self.assertEqual(self.P["motors"]["x"]["bus"]["uart_pin"], "PB5")
        self.assertTrue(set_pin(self.P, "fan:part", "fan", "PC7"))
        self.assertEqual(self.P["pins"]["fan"], "PC7")
        self.assertFalse(set_pin(self.P, "section:adxl345", "cs_pin", "PA0"))
        self.assertIn("PA1", build(self.P, self.text, "merge"))

    def test_map_labels_are_translated(self):
        from studio.wiring import GROUPS
        for key in ["map.group_" + g for g in GROUPS] + ["map.issue_empty", "map.issue_conflict", "map.off",
                                                          "map.side_motors", "map.status"]:
            self.assertIn(key, i18n.STRINGS, key)


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
        self.assertEqual(P["motors"]["x"]["microsteps"], 32)
        self.assertEqual(P["motors"]["x"]["step_pin"], "P2.2")

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
        used = {k for k in used if not k.endswith(("_", "."))}  # dynamic prefixes like "up.busy_" + state
        used |= {"doc.%s.%s" % (r[0], part) for r in RULES for part in ("title", "cause", "fix")}
        used |= {"up.busy_printing", "up.busy_paused", "state.printing", "state.paused"}
        missing = sorted(k for k in used if k not in i18n.STRINGS)
        self.assertEqual(missing, [])
        # The app ships in English. Arabic is kept for the strings that already had it (--lang ar),
        # so it is optional - but where it exists the placeholders must still match.
        for key, entry in i18n.STRINGS.items():
            self.assertTrue(entry.get("en"), "%s has no English text" % key)
            if entry.get("ar"):
                ph = {lang: sorted(set(re.findall(r"\{(\w+)\}", entry[lang]))) for lang in ("en", "ar")}
                self.assertEqual(ph["en"], ph["ar"], "placeholders differ in " + key)


if __name__ == "__main__":
    unittest.main()
