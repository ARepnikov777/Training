import csv
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(module, *args):
    return subprocess.run(
        [sys.executable, "-m", "src." + module, *map(str, args)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class PipelineTests(unittest.TestCase):
    def test_outputs_and_repeat(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "fresh"
            args = ("--input", ROOT / "input", "--output", output)
            result = run("pipeline", *args)
            self.assertEqual(result.returncode, 0, result.stderr)
            first = {p.name: p.read_bytes() for p in output.iterdir()}
            self.assertEqual(set(first), {"clean.csv", "rejected.csv", "report.md"})
            with (output / "clean.csv").open(encoding="utf-8", newline="") as f:
                self.assertEqual(
                    list(csv.DictReader(f)),
                    [
                        {
                            "id": "A1",
                            "date": "2026-11-01",
                            "category": "Еда",
                            "amount": "100",
                        },
                        {
                            "id": "A2",
                            "date": "2026-11-01",
                            "category": "Транспорт",
                            "amount": "200",
                        },
                        {
                            "id": "A3",
                            "date": "2026-11-02",
                            "category": "Канцелярия",
                            "amount": "300",
                        },
                        {
                            "id": "A4",
                            "date": "2026-11-03",
                            "category": "Еда",
                            "amount": "400",
                        },
                    ],
                )
            self.assertEqual(run("pipeline", *args).returncode, 0)
            self.assertEqual(first, {p.name: p.read_bytes() for p in output.iterdir()})

    def test_missing_input_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            result = run(
                "pipeline",
                "--input",
                Path(temp) / "missing",
                "--output",
                Path(temp) / "out",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertTrue(result.stderr)

    def test_bad_header_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            inputs = Path(temp) / "input"
            shutil.copytree(ROOT / "input", inputs)
            (inputs / "nov-1.csv").write_text("wrong,header\n", encoding="utf-8")
            result = run("pipeline", "--input", inputs, "--output", Path(temp) / "out")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("заголовок", result.stderr)
