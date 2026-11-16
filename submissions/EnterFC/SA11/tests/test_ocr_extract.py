import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from ocr_extract import extract_ocr


def test_rotated_document_produces_oriented_page_and_preserves_raw(tmp_path):
    source = ROOT / "kit/H04/input/03-rotated-table.pdf"
    output = tmp_path / "ocr"
    pages = extract_ocr(source, output)
    assert len(pages) == 1
    assert pages[0]["source"] == source.name
    assert pages[0]["page"] == 1
    assert pages[0]["method"] == "ocr"
    assert pages[0]["text"].strip()
    assert pages[0]["tables"]
    assert pages[0]["uncertainty"]
    import pymupdf

    image = pymupdf.Pixmap(str(output / "page-001/normalized.png"))
    assert image.height > image.width
    assert list(output.rglob("*.png"))
    assert list(output.rglob("ocr.json"))
    assert list(output.rglob("*.csv"))
    assert not (output / "tessdata").exists()
    before = {p: p.read_bytes() for p in output.rglob("*") if p.is_file()}
    with pytest.raises(FileExistsError):
        extract_ocr(source, output)
    assert all(p.read_bytes() == contents for p, contents in before.items())


def test_decimal_comma_is_normalized_without_changing_text():
    from ocr_extract import _value

    assert _value("12,50") == "12.50"
    assert _value("Цена, KZT") == "Цена, KZT"
