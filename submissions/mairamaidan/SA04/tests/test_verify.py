import shutil
import tempfile
import unittest
from pathlib import Path

from test_pipeline import ROOT, run


class VerifyTests(unittest.TestCase):
    def test_original_and_tampering(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "out"
            self.assertEqual(
                run(
                    "pipeline", "--input", ROOT / "input", "--output", output
                ).returncode,
                0,
            )
            args = (
                "--input",
                ROOT / "input",
                "--output",
                output,
                "--expected",
                ROOT / "checks/expected.json",
            )
            self.assertEqual(run("verify", *args).returncode, 0)
            clean = output / "clean.csv"
            original = clean.read_text(encoding="utf-8")
            lines = original.splitlines(keepends=True)
            for changed in (
                "".join(lines[:-1]),
                original + lines[-1],
                original.replace("A1,", "AX,"),
            ):
                clean.write_text(changed, encoding="utf-8")
                self.assertNotEqual(run("verify", *args).returncode, 0)
            clean.write_text(original, encoding="utf-8")
            rejected = output / "rejected.csv"
            original_rejected = rejected.read_text(encoding="utf-8")
            rejected.write_text(
                original_rejected.replace("bad-date", "good-date"), encoding="utf-8"
            )
            self.assertNotEqual(run("verify", *args).returncode, 0)
            rejected.write_text(original_rejected, encoding="utf-8")
            report = output / "report.md"
            original_report = report.read_text(encoding="utf-8")
            report.write_text(
                original_report.replace("1000 KZT", "1001 KZT"), encoding="utf-8"
            )
            self.assertNotEqual(run("verify", *args).returncode, 0)
            report.write_text(original_report, encoding="utf-8")
            self.assertEqual(run("verify", *args).returncode, 0)

    def test_modified_rejected_input_is_not_accepted(self):
        with tempfile.TemporaryDirectory() as temp:
            inputs = Path(temp) / "input"
            shutil.copytree(ROOT / "input", inputs)
            output = Path(temp) / "out"
            self.assertEqual(
                run("pipeline", "--input", inputs, "--output", output).returncode, 0
            )
            source = inputs / "nov-2.csv"
            source.write_text(
                source.read_text(encoding="utf-8").replace("bad-date", "2026-11-04"),
                encoding="utf-8",
            )
            rejected = output / "rejected.csv"
            rejected.write_text(
                rejected.read_text(encoding="utf-8").replace("bad-date", "2026-11-04"),
                encoding="utf-8",
            )
            result = run(
                "verify",
                "--input",
                inputs,
                "--output",
                output,
                "--expected",
                ROOT / "checks/expected.json",
            )
            self.assertNotEqual(result.returncode, 0)

    def test_conflicting_report_values_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "out"
            shutil.copytree(ROOT / "result", output)
            args = (
                "--input",
                ROOT / "input",
                "--output",
                output,
                "--expected",
                ROOT / "checks/expected.json",
            )
            report = output / "report.md"
            original = report.read_text(encoding="utf-8")
            for correct, wrong in (
                ("- Общая сумма: 1000 KZT", "- Общая сумма: 1001 KZT"),
                ("| Еда | 500 |", "| Еда | 501 |"),
            ):
                with self.subTest(correct=correct):
                    self.assertIn(correct, original)
                    report.write_text(
                        original.replace(correct, wrong + "\n" + correct),
                        encoding="utf-8",
                    )
                    self.assertNotEqual(run("verify", *args).returncode, 0)
            report.write_text(original, encoding="utf-8")
            self.assertEqual(run("verify", *args).returncode, 0)
