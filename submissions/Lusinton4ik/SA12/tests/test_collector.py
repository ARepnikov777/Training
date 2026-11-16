import csv
import json
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import collector

BASE = "http://localhost:8000"

class FakeBrowser:
    def __init__(self):
        self.pages = []

    def navigate(self, url):
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        if parsed.path == "/catalog":
            page = int(query["page"][0])
            self.pages.append(page)
            if query.get("fail") == ["1"]:
                return {"status": 503, "url": url, "links": []}
            return {"status": 200, "url": url, "links": [f"{BASE}/product?id=p{i}" for i in range((page-1)*10+1, page*10+1)]}
        if parsed.path == "/product":
            ident = query["id"][0]
            return {"status": 200, "url": url, "fields": {"id": ident, "name": "Item " + ident, "category": "laptop", "price": "12", "currency": "USD", "supplier": "A", "availability": "yes", "ram_GB": "16", "ssd_GB": "512", "screen_inches": "15.6"}}
        raise AssertionError(url)

class CollectorTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name)

    def read(self, name):
        return json.loads((self.output / name).read_text(encoding="utf-8"))

    def test_interruption_resume_and_idempotent_rerun(self):
        first = FakeBrowser()
        self.assertEqual(collector.collect(BASE, self.output, first, True), 2)
        cp = self.read("checkpoint.json")
        self.assertEqual(first.pages, [1, 2, 3])
        self.assertEqual(len(cp["records"]), 20)
        self.assertEqual(cp["completed_pages"], [1, 2])
        self.assertEqual(cp["pending_pages"], [3, 4, 5])
        self.assertFalse(cp["complete"])
        self.assertEqual(cp["errors"][0]["status"], 503)
        self.assertFalse(cp["errors"][0]["resolved"])
        self.assertIn("fail=1", cp["errors"][0]["url"])
        self.assertEqual(self.read("errors.json"), cp["errors"])
        second = FakeBrowser()
        self.assertEqual(collector.collect(BASE, self.output, second), 0)
        self.assertEqual(second.pages, [3, 4, 5])
        cp = self.read("checkpoint.json")
        self.assertTrue(cp["complete"])
        self.assertTrue(cp["errors"][0]["resolved"])
        products = self.read("products.json")
        self.assertEqual(len(products), 50)
        self.assertEqual(len({p["id"] for p in products}), 50)
        self.assertEqual(products[0]["source_url"], BASE + "/product?id=p1")
        self.assertEqual(products[0]["price"], 12)
        self.assertEqual(products[0]["ram_GB"], 16)
        with (self.output / "products.csv").open(encoding="utf-8", newline="") as f:
            self.assertEqual(len(list(csv.DictReader(f))), 50)
        third = FakeBrowser()
        self.assertEqual(collector.collect(BASE, self.output, third), 0)
        self.assertEqual(third.pages, [])
        self.assertEqual(self.read("products.json"), products)
        events = [json.loads(line) for line in (self.output / "events.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertTrue(any(e.get("status") == 503 and "fail=1" in e.get("url", "") for e in events))
        self.assertTrue(any(e.get("event") == "resume" for e in events))
        self.assertTrue(any(e.get("event") == "exit" and e.get("code") == 0 for e in events))
        self.assertTrue(all("timestamp" in e and "pid" in e and "run_id" in e for e in events))

    def test_corrupt_checkpoint_leaves_all_files_unchanged(self):
        (self.output / "checkpoint.json").write_text('{broken', encoding="utf-8")
        (self.output / "products.json").write_text('untouched', encoding="utf-8")
        before = {p.name: p.read_bytes() for p in self.output.iterdir()}
        browser = FakeBrowser()
        self.assertNotEqual(collector.collect(BASE, self.output, browser), 0)
        self.assertEqual({p.name: p.read_bytes() for p in self.output.iterdir()}, before)
        self.assertEqual(browser.pages, [])

    def test_wrong_base_checkpoint_leaves_files_unchanged(self):
        self.assertEqual(collector.collect(BASE, self.output, FakeBrowser(), True), 2)
        before = {p.name: p.read_bytes() for p in self.output.iterdir()}
        self.assertNotEqual(collector.collect("http://other.test", self.output, FakeBrowser()), 0)
        self.assertEqual({p.name: p.read_bytes() for p in self.output.iterdir()}, before)

class BoundaryTests(unittest.TestCase):
    def test_duplicate_id_does_not_commit_invalid_completed_checkpoint(self):
        class DuplicateBrowser(FakeBrowser):
            def navigate(self, url):
                result = super().navigate(url)
                if url.endswith("id=p50"):
                    result["fields"]["id"] = "p1"
                return result
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            self.assertEqual(collector.collect(BASE, output, DuplicateBrowser()), 1)
            cp = json.loads((output / "checkpoint.json").read_text(encoding="utf-8"))
            self.assertEqual(cp["pending_pages"], [5])
            self.assertEqual(cp["completed_pages"], [1, 2, 3, 4])
            self.assertEqual(cp["records"]["p1"]["name"], "Item p1")

class ProcessAndOrcaTests(unittest.TestCase):
    def test_resume_in_a_new_python_process(self):
        import subprocess
        script = '''import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from test_collector import FakeBrowser, BASE
import collector
browser = FakeBrowser()
code = collector.collect(BASE, Path(sys.argv[2]), browser, sys.argv[3] == "fail")
print("PAGES:", browser.pages)
sys.exit(code)
'''
        test_dir = str(Path(__file__).resolve().parent)
        with tempfile.TemporaryDirectory() as directory:
            def run(mode):
                return subprocess.run([sys.executable, "-X", "utf8", "-c", script, test_dir, directory, mode], capture_output=True, text=True, encoding="utf-8")
            first = run("fail")
            second = run("resume")
            third = run("resume")
            self.assertEqual((first.returncode, second.returncode, third.returncode), (2, 0, 0), (first.stderr, second.stderr, third.stderr))
            self.assertIn("PAGES: [1, 2, 3]", first.stdout)
            self.assertIn("PAGES: [3, 4, 5]", second.stdout)
            self.assertIn("PAGES: []", third.stdout)
            events = [json.loads(line) for line in (Path(directory) / "events.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertGreaterEqual(len({e["pid"] for e in events}), 2)
            self.assertEqual(len(json.loads((Path(directory) / "products.json").read_text(encoding="utf-8"))), 50)

    def test_orca_commands_use_page_id_and_parse_eval_envelope(self):
        from unittest.mock import patch
        import subprocess
        calls = []
        responses = [
            {"ok": True, "result": {"browserPageId": "page-42"}},
            {"ok": True, "result": {"effects": {}}},
            {"ok": True, "result": {"result": json.dumps({"status": 503, "url": BASE + "/catalog?page=3&fail=1", "links": [], "fields": {}}), "origin": BASE}},
        ]
        def run(argv, **kwargs):
            calls.append((argv, kwargs))
            return subprocess.CompletedProcess(argv, 0, json.dumps(responses.pop(0)), "")
        with patch.object(collector.subprocess, "run", side_effect=run):
            browser = collector.OrcaBrowser()
            result = browser.navigate(BASE + "/catalog?page=3&fail=1")
        self.assertEqual(result["status"], 503)
        self.assertEqual(calls[0][0][1:3], ["tab", "create"])
        self.assertEqual(calls[1][0][1:4], ["goto", "--page", "page-42"])
        self.assertEqual(calls[2][0][1:4], ["eval", "--page", "page-42"])
        self.assertTrue(all(call[1].get("timeout") and not call[1].get("shell", False) for call in calls))

class CheckpointValidationTests(unittest.TestCase):
    def test_checkpoint_with_invalid_record_is_rejected_without_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            self.assertEqual(collector.collect(BASE, output, FakeBrowser(), True), 2)
            path = output / "checkpoint.json"
            cp = json.loads(path.read_text(encoding="utf-8"))
            cp["records"]["p1"]["price"] = "not-a-number"
            path.write_text(json.dumps(cp), encoding="utf-8")
            before = {p.name: p.read_bytes() for p in output.iterdir()}
            self.assertEqual(collector.collect(BASE, output, FakeBrowser()), 1)
            self.assertEqual({p.name: p.read_bytes() for p in output.iterdir()}, before)

class NavigationTests(unittest.TestCase):
    def test_loading_goto_waits_before_reading_card_dom(self):
        from unittest.mock import patch
        import subprocess
        target = BASE + "/product?id=p1"
        commands = []
        loaded = False
        def run(argv, **kwargs):
            nonlocal loaded
            command = argv[1]
            commands.append(argv)
            if command == "goto":
                result = {"effects": {"loading": True}}
            elif command == "wait":
                loaded = True
                result = {}
            elif command == "eval":
                value = {"status": 200, "url": target if loaded else BASE + "/catalog?page=1", "fields": {"id": "p1"} if loaded else {}, "links": []}
                result = {"result": json.dumps(value), "origin": BASE}
            else:
                self.fail("Unexpected command: " + command)
            return subprocess.CompletedProcess(argv, 0, json.dumps({"ok": True, "result": result}), "")
        with patch.object(collector.subprocess, "run", side_effect=run):
            result = collector.OrcaBrowser("page-42").navigate(target)
        self.assertEqual(result["url"], target)
        self.assertEqual(result["fields"]["id"], "p1")
        self.assertEqual([cmd[1] for cmd in commands], ["goto", "wait", "eval"])
        self.assertEqual(commands[1][1:6], ["wait", "--page", "page-42", "--load", "load"])

    def test_mismatched_loaded_url_is_rejected(self):
        from unittest.mock import patch
        import subprocess
        target = BASE + "/product?id=p1"
        def run(argv, **kwargs):
            result = {"effects": {}} if argv[1] == "goto" else {"result": json.dumps({"status": 200, "url": BASE + "/product?id=p2", "fields": {}}), "origin": BASE}
            return subprocess.CompletedProcess(argv, 0, json.dumps({"ok": True, "result": result}), "")
        with patch.object(collector.subprocess, "run", side_effect=run):
            with self.assertRaises(collector.CollectorError):
                collector.OrcaBrowser("page-42").navigate(target)

class NullableFieldTests(unittest.TestCase):
    def test_dom_nulls_survive_checkpoint_resume_and_csv_export(self):
        class NullableBrowser(FakeBrowser):
            def navigate(self, url):
                result = super().navigate(url)
                if url.endswith("id=p1"):
                    result["fields"].update(availability="None", ram_GB="None", ssd_GB="None", screen_inches="None")
                if url.endswith("id=p2"):
                    result["fields"]["screen_inches"] = "14.0"
                return result
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            self.assertEqual(collector.collect(BASE, output, NullableBrowser(), True), 2)
            checkpoint = json.loads((output / "checkpoint.json").read_text(encoding="utf-8"))
            for field in ("availability", "ram_GB", "ssd_GB", "screen_inches"):
                self.assertIn(field, checkpoint["records"]["p1"])
                self.assertIsNone(checkpoint["records"]["p1"][field])
            self.assertIs(type(checkpoint["records"]["p2"]["screen_inches"]), float)
            self.assertEqual(checkpoint["records"]["p2"]["screen_inches"], 14.0)
            resumed = NullableBrowser()
            self.assertEqual(collector.collect(BASE, output, resumed), 0)
            self.assertEqual(resumed.pages, [3, 4, 5])
            products = json.loads((output / "products.json").read_text(encoding="utf-8"))
            self.assertIsNone(products[0]["availability"])
            self.assertIsNone(products[0]["ram_GB"])
            with (output / "products.csv").open(encoding="utf-8", newline="") as stream:
                row = next(csv.DictReader(stream))
            for field in ("availability", "ram_GB", "ssd_GB", "screen_inches"):
                self.assertEqual(row[field], "")

    def test_resume_loads_checkpoint_with_null_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            self.assertEqual(collector.collect(BASE, output, FakeBrowser(), True), 2)
            path = output / "checkpoint.json"
            checkpoint = json.loads(path.read_text(encoding="utf-8"))
            for field in ("availability", "ram_GB", "ssd_GB", "screen_inches"):
                checkpoint["records"]["p1"][field] = None
            path.write_text(json.dumps(checkpoint), encoding="utf-8")
            browser = FakeBrowser()
            self.assertEqual(collector.collect(BASE, output, browser), 0)
            self.assertEqual(browser.pages, [3, 4, 5])
            products = json.loads((output / "products.json").read_text(encoding="utf-8"))
            self.assertIsNone(products[0]["availability"])
            self.assertIsNone(products[0]["screen_inches"])

    def test_legacy_checkpoint_is_canonicalized_on_resume(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            self.assertEqual(collector.collect(BASE, output, FakeBrowser(), True), 2)
            path = output / "checkpoint.json"
            checkpoint = json.loads(path.read_text(encoding="utf-8"))
            checkpoint["records"]["p1"]["availability"] = "None"
            checkpoint["records"]["p1"]["screen_inches"] = 14
            path.write_text(json.dumps(checkpoint), encoding="utf-8")
            browser = FakeBrowser()
            self.assertEqual(collector.collect(BASE, output, browser), 0)
            self.assertEqual(browser.pages, [3, 4, 5])
            checkpoint = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(len(checkpoint["records"]), 50)
            self.assertIsNone(checkpoint["records"]["p1"]["availability"])
            self.assertIs(type(checkpoint["records"]["p1"]["screen_inches"]), float)
            self.assertEqual(checkpoint["records"]["p1"]["screen_inches"], 14.0)

    def test_invalid_legacy_checkpoint_is_not_rewritten(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            self.assertEqual(collector.collect(BASE, output, FakeBrowser(), True), 2)
            path = output / "checkpoint.json"
            checkpoint = json.loads(path.read_text(encoding="utf-8"))
            checkpoint["records"]["p1"]["availability"] = "None"
            checkpoint["records"]["p2"]["price"] = None
            path.write_text(json.dumps(checkpoint), encoding="utf-8")
            before = {p.name: p.read_bytes() for p in output.iterdir()}
            self.assertEqual(collector.collect(BASE, output, FakeBrowser()), 1)
            self.assertEqual({p.name: p.read_bytes() for p in output.iterdir()}, before)

    def test_non_nullable_and_invalid_values_are_rejected(self):
        card = FakeBrowser().navigate(BASE + "/product?id=p1")
        for field in ("id", "name", "category", "price", "currency", "supplier"):
            with self.subTest(field=field):
                invalid = {"url": card["url"], "fields": dict(card["fields"])}
                invalid["fields"][field] = "None"
                with self.assertRaises(collector.CollectorError):
                    collector.normalize_record(invalid)
        for field, value in (("price", "12.5"), ("ram_GB", "1.5"), ("screen_inches", "invalid")):
            with self.subTest(field=field):
                invalid = {"url": card["url"], "fields": dict(card["fields"])}
                invalid["fields"][field] = value
                with self.assertRaises(collector.CollectorError):
                    collector.normalize_record(invalid)

    def test_checkpoint_rejects_null_in_required_fields_without_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            self.assertEqual(collector.collect(BASE, output, FakeBrowser(), True), 2)
            path = output / "checkpoint.json"
            original = json.loads(path.read_text(encoding="utf-8"))
            for field in ("id", "name", "category", "price", "currency", "supplier", "source_url"):
                with self.subTest(field=field):
                    checkpoint = json.loads(json.dumps(original))
                    checkpoint["records"]["p1"][field] = None
                    path.write_text(json.dumps(checkpoint), encoding="utf-8")
                    before = {p.name: p.read_bytes() for p in output.iterdir()}
                    self.assertEqual(collector.collect(BASE, output, FakeBrowser()), 1)
                    self.assertEqual({p.name: p.read_bytes() for p in output.iterdir()}, before)

if __name__ == "__main__":
    unittest.main()
