import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from starter import copy_files


class SorterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.source = self.base / "input"
        self.output = self.base / "output"
        self.source.mkdir()

    def put(self, relative, content):
        path = self.source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    def snapshot(self, root):
        return {
            str(p.relative_to(root)): p.read_bytes()
            for p in root.rglob("*")
            if p.is_file()
        }

    def test_default_preview_preserves_source_and_existing_output(self):
        self.put("a/report.txt", "first")
        self.put("b/report.txt", "second")
        self.output.mkdir()
        (self.output / "keep.txt").write_text("keep")
        before = self.snapshot(self.base)
        records = copy_files(self.source, self.output)
        self.assertEqual(self.snapshot(self.base), before)
        self.assertEqual([r["action"] for r in records], ["would_copy"] * 2)
        self.assertEqual(
            [Path(r["target"]).name for r in records], ["report.txt", "report__2.txt"]
        )

    def test_preview_does_not_create_output(self):
        self.put("report.txt", "first")
        copy_files(self.source, self.output)
        self.assertFalse(self.output.exists())

    def test_recursive_categories_conflicts_and_source_preserved(self):
        self.put("b/report.txt", "second")
        self.put("a/report.txt", "first")
        self.put("c/data.csv", "value\n1\n")
        self.put("c/note.md", "# Note")
        before = self.snapshot(self.source)
        records = copy_files(self.source, self.output, dry_run=False)
        self.assertEqual(
            self.snapshot(self.output),
            {
                "documents/report.txt": b"first",
                "documents/report__2.txt": b"second",
                "documents/note.md": b"# Note",
                "tables/data.csv": b"value\n1\n",
            },
        )
        self.assertEqual(self.snapshot(self.source), before)
        self.assertTrue(all(r["action"] == "copied" for r in records))

    def test_existing_files_and_natural_suffix_are_not_overwritten(self):
        self.put("a/report.txt", "first")
        self.put("b/report.txt", "second")
        self.put("c/report__2.txt", "natural")
        target = self.output / "documents"
        target.mkdir(parents=True)
        (target / "report.txt").write_text("existing")
        copy_files(self.source, self.output, dry_run=False)
        self.assertEqual(
            self.snapshot(self.output),
            {
                "documents/report.txt": b"existing",
                "documents/report__2.txt": b"first",
                "documents/report__3.txt": b"second",
                "documents/report__2__2.txt": b"natural",
            },
        )

    def test_skips_are_explained_in_journal(self):
        self.put("photo.png", "image")
        self.put("note.md", "note")
        (self.source / "linked.txt").symlink_to(self.source / "note.md")
        records = copy_files(self.source, self.output, dry_run=False)
        skips = [r for r in records if r["action"] == "skipped"]
        self.assertEqual(len(skips), 2)
        self.assertTrue(
            all(r["source"] and r["reason"] and r["target"] is None for r in skips)
        )
        self.assertEqual(self.snapshot(self.output), {"documents/note.md": b"note"})

    def test_missing_source_and_nested_output_fail_without_writes(self):
        with self.assertRaises(FileNotFoundError):
            copy_files(self.base / "missing", self.output)
        with self.assertRaises(ValueError):
            copy_files(self.source, self.source / "sorted", dry_run=False)
        self.assertFalse(self.output.exists())
        self.assertFalse((self.source / "sorted").exists())

    def test_cli_preview_apply_and_error_exit(self):
        self.put("nested/note.md", "note")
        script = str(Path(__file__).with_name("starter.py"))
        args = [sys.executable, script, str(self.source), str(self.output)]
        preview = subprocess.run(args, capture_output=True, text=True, check=False)
        self.assertEqual(preview.returncode, 0, preview.stderr)
        self.assertEqual(json.loads(preview.stdout)[0]["action"], "would_copy")
        self.assertFalse(self.output.exists())
        applied = subprocess.run(
            args + ["--apply"], capture_output=True, text=True, check=False
        )
        self.assertEqual(applied.returncode, 0, applied.stderr)
        self.assertEqual((self.output / "documents/note.md").read_text(), "note")
        failed = subprocess.run(
            [sys.executable, script, str(self.base / "missing"), str(self.output)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(failed.returncode, 0)
        self.assertIn("missing", failed.stderr)

    def test_read_error_is_propagated_even_in_preview(self):
        self.put("note.md", "note")
        # Permission bits are unreliable when tests run with elevated privileges.
        with (
            patch.object(Path, "open", side_effect=PermissionError("denied")),
            self.assertRaises(PermissionError),
        ):
            copy_files(self.source, self.output)
        self.assertFalse(self.output.exists())

    def test_output_ancestor_cannot_copy_back_into_source(self):
        source = self.base / "documents"
        source.mkdir()
        (source / "note.md").write_text("note")
        before = self.snapshot(source)
        with self.assertRaises(ValueError):
            copy_files(source, self.base, dry_run=False)
        self.assertEqual(self.snapshot(source), before)


if __name__ == "__main__":
    unittest.main()
