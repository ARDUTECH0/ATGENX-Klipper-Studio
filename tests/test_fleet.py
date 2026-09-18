# -*- coding: utf-8 -*-
"""Printers, parallel sync, dry run and the print-safety rules - against the fake Moonraker."""
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("ATGENX_STUDIO_HOME", os.path.join(ROOT, "tests", ".studio_home"))

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from studio import printers as P  # noqa: E402
from studio import sync as S  # noqa: E402
from studio.moonraker import Moonraker  # noqa: E402
from fake_moonraker import FakeMoonraker  # noqa: E402


def gcode(dirpath, name, size=2048):
    path = os.path.join(dirpath, name)
    if not os.path.isdir(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write("G1 X1\n" * (size // 6))
    return path


class TestPrinterStore(unittest.TestCase):
    def test_crud_and_reorder(self):
        a = P.new_printer("A", "10.0.0.1")
        b = P.new_printer("B", "10.0.0.2", port=7126, ssh_port=2222, remote_path="shelf")
        items = P.save_printers([a, b])
        self.assertEqual([p["name"] for p in items], ["A", "B"])
        items = P.move_printer(items, b["id"], -1)
        self.assertEqual([p["name"] for p in items], ["B", "A"])
        items = P.update_printer(items, a["id"], name="A2", host="10.0.0.9")
        self.assertEqual(P.load_printers()[1]["name"], "A2")
        self.assertEqual(P.load_printers()[0]["port"], 7126)       # the override survived
        self.assertEqual(P.load_printers()[0]["ssh_port"], 2222)
        items = P.delete_printer(items, b["id"])
        self.assertEqual([p["name"] for p in items], ["A2"])
        P.save_printers([])

    def test_defaults_are_filled_in(self):
        p = P._clean({"host": "10.0.0.3"})
        self.assertEqual(p["port"], P.DEFAULT_PORT)
        self.assertEqual(p["ssh_port"], P.DEFAULT_SSH_PORT)
        self.assertEqual(p["name"], "10.0.0.3")
        self.assertTrue(p["id"])


class TestSync(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.events = []

    def emit(self, kind, pid, data):
        self.events.append((kind, data))

    def printer(self, server, name="p"):
        return P.new_printer(name, "127.0.0.1", port=server.port)

    def test_local_files_walks_folders_and_filters(self):
        gcode(self.tmp, "a.gcode")
        gcode(self.tmp, os.path.join("sub", "b.gcode"))
        gcode(self.tmp, "notes.txt")
        found = sorted(rel for _, rel, _ in S.local_files([self.tmp]))
        self.assertEqual(found, ["a.gcode", "sub/b.gcode"])

    def test_plan_marks_new_replace_and_same(self):
        server = FakeMoonraker(gcodes={"old.gcode": "x" * 2046, "same.gcode": "y" * 2046}).start()
        try:
            gcode(self.tmp, "new.gcode")
            gcode(self.tmp, "old.gcode", size=4096)
            gcode(self.tmp, "same.gcode")
            files = S.local_files([self.tmp])
            m = Moonraker("127.0.0.1", server.port)
            kinds = dict((a[2], a[0]) for a in S.plan(m, files, S.Options()))
            self.assertEqual(kinds["new.gcode"], S.UPLOAD)
            self.assertEqual(kinds["old.gcode"], S.REPLACE)
            self.assertEqual(kinds["same.gcode"], S.SAME)
        finally:
            server.stop()

    def test_dry_run_changes_nothing(self):
        server = FakeMoonraker().start()
        try:
            gcode(self.tmp, "a.gcode")
            files = S.local_files([self.tmp])
            res = S.sync_one(self.printer(server), files, S.Options(dry_run=True), self.emit)
            self.assertEqual(res["sent"], 1)
            self.assertEqual(server.gcodes, {})
            self.assertFalse([c for c in server.calls if c[0] == "UPLOAD"])
            self.assertTrue(any(d.get("dry") for k, d in self.events if k == "file"))
        finally:
            server.stop()

    def test_the_file_being_printed_is_never_overwritten(self):
        server = FakeMoonraker(gcodes={"benchy.gcode": "old"}, print_state="printing",
                               printing="benchy.gcode").start()
        try:
            gcode(self.tmp, "benchy.gcode")
            res = S.sync_one(self.printer(server), S.local_files([self.tmp]), S.Options(), self.emit)
            self.assertEqual(res["busy"], 1)
            self.assertEqual(res["sent"], 0)
            self.assertEqual(server.gcodes["benchy.gcode"], "old")
            self.assertIn(("skip", {"name": "benchy.gcode", "why": "busy"}), self.events)
        finally:
            server.stop()

    def test_a_queued_file_is_protected_too(self):
        server = FakeMoonraker(gcodes={"next.gcode": "old"}, queued=["next.gcode"]).start()
        try:
            gcode(self.tmp, "next.gcode")
            res = S.sync_one(self.printer(server), S.local_files([self.tmp]), S.Options(), self.emit)
            self.assertEqual(res["busy"], 1)
            self.assertEqual(server.gcodes["next.gcode"], "old")
        finally:
            server.stop()

    def test_uploads_in_parallel_with_progress(self):
        s1, s2 = FakeMoonraker().start(), FakeMoonraker().start()
        try:
            gcode(self.tmp, "a.gcode", size=40000)
            gcode(self.tmp, "b.gcode", size=40000)
            files = S.local_files([self.tmp])
            fleet = [self.printer(s1, "one"), self.printer(s2, "two")]
            res = S.sync(fleet, files, S.Options(workers=2), self.emit)
            self.assertEqual(sorted(s1.gcodes), ["a.gcode", "b.gcode"])
            self.assertEqual(sorted(s2.gcodes), ["a.gcode", "b.gcode"])
            self.assertEqual(sum(r["sent"] for r in res.values()), 4)
            speeds = [d["speed"] for k, d in self.events if k == "progress"]
            self.assertTrue(speeds and all(s > 0 for s in speeds))
            self.assertTrue(any(d["eta"] >= 0 for k, d in self.events if k == "progress"))
        finally:
            s1.stop(), s2.stop()

    def test_remote_folder_and_per_printer_override(self):
        server = FakeMoonraker().start()
        try:
            gcode(self.tmp, "a.gcode")
            p = self.printer(server)
            p["remote_path"] = "shelf"
            S.sync_one(p, S.local_files([self.tmp]), S.Options(), self.emit)
            self.assertEqual(list(server.gcodes), ["shelf/a.gcode"])
        finally:
            server.stop()

    def test_an_unreachable_printer_reports_and_does_not_raise(self):
        p = P.new_printer("dead", "127.0.0.1", port=9)
        res = S.sync_one(p, [], S.Options(), self.emit)
        self.assertTrue(res["error"])
        self.assertTrue(any(k == "error" for k, _ in self.events))


class TestRemoteFiles(unittest.TestCase):
    def test_browse_delete_and_thumbnails(self):
        server = FakeMoonraker(gcodes={"a.gcode": "x", "sub/b.gcode": "y", "sub/c.gcode": "z"},
                               thumbs={"a.gcode": b"\x89PNG\r\n\x1a\nfake"}).start()
        try:
            m = Moonraker("127.0.0.1", server.port)
            top = m.list_dir("gcodes")
            self.assertEqual([d["dirname"] for d in top["dirs"]], ["sub"])
            self.assertEqual([f["filename"] for f in top["files"]], ["a.gcode"])
            inner = m.list_dir("gcodes/sub")
            self.assertEqual(sorted(f["filename"] for f in inner["files"]), ["b.gcode", "c.gcode"])
            self.assertTrue(m.thumbnail("a.gcode").startswith(b"\x89PNG"))
            self.assertEqual(m.thumbnail("sub/b.gcode"), b"")
            m.delete_gcode("a.gcode")
            self.assertNotIn("a.gcode", server.gcodes)
            m.delete_dir("sub")
            self.assertEqual(server.gcodes, {})
        finally:
            server.stop()

    def test_busy_files_lists_printing_and_queued(self):
        server = FakeMoonraker(print_state="printing", printing="now.gcode", queued=["later.gcode"]).start()
        try:
            self.assertEqual(Moonraker("127.0.0.1", server.port).busy_files(), {"now.gcode", "later.gcode"})
        finally:
            server.stop()


if __name__ == "__main__":
    unittest.main()
