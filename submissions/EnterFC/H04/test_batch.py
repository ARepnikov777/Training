"""Behavior tests: continuation, provenance, OCR and rotated tables."""

import csv
import tempfile
import unittest
from pathlib import Path

import pymupdf

from batch import run_batch


class BatchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).parent / ".cache")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.inputs = self.root / "input"
        self.inputs.mkdir()
        self.output = self.root / "output"

    def test_broken_first_does_not_stop_two_text_pages(self):
        # Catches abort-on-error, missing page provenance and missing error reporting.
        (self.inputs / "00-broken.pdf").write_bytes(b"%PDF-1.4\nbroken")
        with pymupdf.open() as doc:
            for text in ["ALPHA 42", "BETA 17"]:
                doc.new_page().insert_text((50, 70), text)
            doc.save(self.inputs / "01-text.pdf")
        result = run_batch(self.inputs, self.output)
        self.assertEqual([d["status"] for d in result["documents"]], ["error", "ok"])
        pages = result["documents"][1]["pages"]
        self.assertEqual([p["page"] for p in pages], [1, 2])
        self.assertIn(
            "ALPHA 42", (self.output / pages[0]["text_path"]).read_text("utf-8")
        )
        self.assertIn(
            "BETA 17", (self.output / pages[1]["text_path"]).read_text("utf-8")
        )
        self.assertTrue(result["documents"][0]["error"])
        self.assertTrue((self.output / "manifest.json").exists())

    def test_image_only_page_uses_real_ocr(self):
        # Catches treating image-only pages as successful empty native extraction.
        with pymupdf.open() as source:
            page = source.new_page(width=400, height=150)
            page.insert_text((35, 70), "ALPHA 42", fontsize=26)
            png = page.get_pixmap(dpi=180).tobytes("png")
        with pymupdf.open() as doc:
            page = doc.new_page(width=400, height=150)
            page.insert_image(page.rect, stream=png)
            doc.save(self.inputs / "scan.pdf")
        result = run_batch(self.inputs, self.output)
        self.assertEqual(len(result["documents"]), 1)
        page = result["documents"][0]["pages"][0]
        self.assertEqual(page["method"], "ocr")
        self.assertIn("ALPHA 42", (self.output / page["text_path"]).read_text("utf-8"))
        self.assertTrue((self.output / page["ocr_json_path"]).exists())
        self.assertTrue(page["manual_review"])

    def make_table(self, raster=False):
        # Catches omission of tables or wrong row/column ordering after rotation.
        with pymupdf.open() as doc:
            page = doc.new_page(width=400, height=300)
            for x in [40, 200, 340]:
                page.draw_line((x, 40), (x, 160))
            for y in [40, 80, 120, 160]:
                page.draw_line((40, y), (340, y))
            for x, y, text in [
                (50, 65, "Item"),
                (210, 65, "Amount"),
                (50, 105, "A"),
                (210, 105, "12.5"),
                (50, 145, "B"),
                (210, 145, "7.5"),
            ]:
                page.insert_text((x, y), text)
            if raster:
                png = page.get_pixmap(dpi=180).tobytes("png")
                with pymupdf.open() as scan:
                    scan.new_page(width=400, height=300).insert_image(
                        page.rect, stream=png
                    )
                    scan[0].set_rotation(90)
                    scan.save(self.inputs / "rotated.pdf")
            else:
                page.set_rotation(90)
                doc.save(self.inputs / "rotated.pdf")

    def test_rotated_grid_exports_table_and_cell_provenance(self):
        self.make_table()
        self.check_table()

    def test_rotated_raster_grid_exports_ocr_cells(self):
        # Catches trying vector-only table extraction on a scanned grid.
        self.make_table(raster=True)
        self.check_table()

    def check_table(self):
        result = run_batch(self.inputs, self.output, ocr_languages="eng")
        self.assertEqual(len(result["documents"]), 1)
        page = result["documents"][0]["pages"][0]
        self.assertEqual(page["source_rotation"], 90)
        table = page["tables"][0]
        with (self.output / table["csv_path"]).open(
            encoding="utf-8", newline=""
        ) as handle:
            self.assertEqual(
                list(csv.reader(handle)),
                [["Item", "Amount"], ["A", "12.5"], ["B", "7.5"]],
            )
        with (self.output / table["cells_path"]).open(
            encoding="utf-8", newline=""
        ) as handle:
            cells = list(csv.DictReader(handle))
        amount = next(c for c in cells if c["value"] == "12.5")
        self.assertEqual(
            (amount["document"], amount["page"], amount["row"], amount["column"]),
            ("rotated.pdf", "1", "2", "2"),
        )
        self.assertTrue(amount["bbox"])


if __name__ == "__main__":
    unittest.main()
