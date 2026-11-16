import json
import sys
from pathlib import Path

import pymupdf
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_batch import run_batch


def native_extractor(source, output_dir):
    output_dir.mkdir()
    with pymupdf.open(source) as doc:
        return [
            {
                "source": source.name,
                "page": n,
                "method": "native",
                "text": p.get_text(),
                "tables": [],
                "uncertainty": [],
            }
            for n, p in enumerate(doc, 1)
        ]


def test_broken_first_does_not_lose_later_document(tmp_path):
    inputs = tmp_path / "input"
    inputs.mkdir()
    (inputs / "00-broken.pdf").write_bytes(b"not a PDF")
    with pymupdf.open() as doc:
        doc.new_page().insert_text((72, 72), "Survives damaged input")
        doc.save(inputs / "01-valid.pdf")
    result = run_batch(inputs, tmp_path / "out", native_extractor, native_extractor)
    assert [p["source"] for p in result["pages"]] == ["01-valid.pdf"]
    assert "Survives damaged input" in result["pages"][0]["text"]
    assert [e["source"] for e in result["errors"]] == ["00-broken.pdf"]
    assert result["errors"][0]["continued"] is True
    assert result["errors"][0]["error"]
    assert json.loads((tmp_path / "out" / "batch.json").read_text("utf-8")) == result


def test_empty_input_is_explicit_failure(tmp_path):
    with pytest.raises(ValueError, match="No PDF"):
        run_batch(tmp_path, tmp_path / "out", native_extractor, native_extractor)


def test_failed_extractor_is_reported_without_losing_other_files(tmp_path):
    inputs = tmp_path / "input"
    inputs.mkdir()
    for name in ["01-fail.pdf", "02-ok.pdf"]:
        with pymupdf.open() as doc:
            doc.new_page().insert_text((72, 72), name)
            doc.save(inputs / name)

    def extract(source, out):
        if source.name == "01-fail.pdf":
            raise RuntimeError("controlled extractor failure")
        return native_extractor(source, out)

    result = run_batch(inputs, tmp_path / "out", extract, extract)
    assert [p["source"] for p in result["pages"]] == ["02-ok.pdf"]
    assert "controlled extractor failure" in result["errors"][0]["error"]


def test_existing_output_is_preserved(tmp_path):
    inputs = tmp_path / "input"
    inputs.mkdir()
    with pymupdf.open() as doc:
        doc.new_page()
        doc.save(inputs / "scan.pdf")
    out = tmp_path / "out"
    out.mkdir()
    marker = out / "raw.txt"
    marker.write_text("original")
    with pytest.raises(FileExistsError):
        run_batch(inputs, out, native_extractor, native_extractor)
    assert marker.read_text() == "original"


@pytest.mark.parametrize("defect", ["missing_page", "wrong_source"])
def test_incomplete_or_wrong_source_is_document_error(tmp_path, defect):
    inputs = tmp_path / "input"
    inputs.mkdir()
    with pymupdf.open() as doc:
        doc.new_page().insert_text((72, 72), "First page")
        doc.new_page().insert_text((72, 72), "Second page")
        doc.save(inputs / "two.pdf")

    def extract(source, out):
        pages = native_extractor(source, out)
        if defect == "missing_page":
            return pages[:1]
        pages[0]["source"] = "unrelated.pdf"
        return pages

    result = run_batch(inputs, tmp_path / "out", extract, extract)
    assert result["pages"] == []
    assert [e["source"] for e in result["errors"]] == ["two.pdf"]
    assert "incomplete pages or mismatched source" in result["errors"][0]["error"]
