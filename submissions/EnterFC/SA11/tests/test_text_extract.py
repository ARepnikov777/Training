import json
import sys
from pathlib import Path

import fitz
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from contract import validate_page
from text_extract import extract_text


def test_real_pdf_extracts_text_and_source(tmp_path):
    source = ROOT / "kit/H04/input/01-text.pdf"
    output = tmp_path / "document"
    pages = extract_text(source, output)
    assert len(pages) == 1
    assert pages[0]["source"] == "01-text.pdf"
    assert pages[0]["page"] == 1
    assert "Акт приёмки оборудования" in pages[0]["text"]
    validate_page(pages[0])
    assert "Акт приёмки оборудования" in (output / "page-1.txt").read_text(
        encoding="utf-8"
    )
    assert json.loads((output / "page-1.json").read_text(encoding="utf-8")) == pages[0]
    assert (output / "page-1.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n")


def test_multiple_pages_and_existing_output_are_preserved(tmp_path):
    source = tmp_path / "two.pdf"
    with fitz.open() as document:
        for text in ("First page", "Second page"):
            document.new_page().insert_text((72, 72), text)
        document.save(source)
    output = tmp_path / "document"
    pages = extract_text(source, output)
    assert [(p["page"], p["text"].strip()) for p in pages] == [
        (1, "First page"),
        (2, "Second page"),
    ]
    before = (output / "page-1.txt").read_bytes()
    with pytest.raises(FileExistsError):
        extract_text(source, output)
    assert (output / "page-1.txt").read_bytes() == before


def test_table_is_returned_and_saved_as_csv(tmp_path):
    source = tmp_path / "table.pdf"
    with fitz.open() as document:
        page = document.new_page()
        for x in (50, 150, 250):
            page.draw_line((x, 50), (x, 110))
        for y in (50, 80, 110):
            page.draw_line((50, y), (250, y))
        for point, text in [
            ((60, 70), "Item"),
            ((160, 70), "Count"),
            ((60, 100), "Pen"),
            ((160, 100), "12"),
        ]:
            page.insert_text(point, text)
        document.save(source)
    output = tmp_path / "output"
    pages = extract_text(source, output)
    assert pages[0]["tables"] == [
        {"columns": ["Item", "Count"], "rows": [["Pen", "12"]]}
    ]
    import csv

    with (output / "page-1-table-1.csv").open(encoding="utf-8", newline="") as file:
        assert list(csv.reader(file)) == [["Item", "Count"], ["Pen", "12"]]
