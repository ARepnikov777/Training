import collections
import csv
import hashlib
import json
import sys
import zipfile
from decimal import Decimal
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from src.contract import validate_batch

batch = json.loads((root / "result/batch/batch.json").read_text("utf-8"))
validate_batch(batch)
candidate = json.loads((root / "evidence/negative/candidate.json").read_text("utf-8"))
corrected = json.loads((root / "evidence/negative/corrected.json").read_text("utf-8"))
try:
    validate_batch(candidate)
except ValueError as error:
    assert "page" in str(error)
else:
    raise AssertionError("Negative candidate was accepted")
validate_batch(corrected)
assert corrected == batch
fixed = json.loads(json.dumps(corrected))
assert fixed["pages"][0].pop("page") == 1
assert fixed == candidate
counts = dict(collections.Counter(page["source"] for page in batch["pages"]))
assert counts == {"01-text.pdf": 1, "02-scan.pdf": 3, "03-rotated-table.pdf": 1}
assert [e["source"] for e in batch["errors"]] == ["04-broken.pdf"]
assert batch["errors"][0]["continued"] is True
table = next(p for p in batch["pages"] if p["source"] == "03-rotated-table.pdf")[
    "tables"
][0]
rows = table["rows"]
assert len(table["columns"]) == 5 and len(rows) == 5
assert sum(Decimal(row[2]) for row in rows[:-1]) == Decimal(rows[-1][2]) == 20
assert sum(Decimal(row[4]) for row in rows[:-1]) == Decimal(rows[-1][4]) == 128000
assert all(Decimal(row[2]) * Decimal(row[3]) == Decimal(row[4]) for row in rows[:-1])
for p in batch["pages"]:
    compact = "".join(p["text"].split())
    if p["source"] == "01-text.pdf" or (
        p["source"] == "02-scan.pdf" and p["page"] == 1
    ):
        assert (
            "017" in compact
            and "12" in compact
            and "245000" in compact
            and "2940000" in compact
        )
    if p["source"] == "02-scan.pdf" and p["page"] == 2:
        assert "OR-2026-11" in compact and "36" in compact
    if p["source"] == "02-scan.pdf" and p["page"] == 3:
        assert "90" in compact and "18500" in compact
inputs = json.loads((root / "result/batch/inputs.json").read_text("utf-8"))
assert all(
    i["sha256"]
    == hashlib.sha256((root / "kit/H04/input" / i["source"]).read_bytes()).hexdigest()
    for i in inputs
)
archive = root.parents[2] / "downloads/H04.zip"
assert (
    hashlib.sha256(archive.read_bytes()).hexdigest()
    == "25a5e3236b6a1490ffcad7a54b51ff370f573d1551e9501d587eae042a194910"
)
kit_files = list((root / "kit/H04").rglob("*"))
with zipfile.ZipFile(archive) as zipped:
    for f in kit_files:
        if f.is_file():
            rel = f.relative_to(root / "kit/H04").as_posix()
            name = next(
                n for n in zipped.namelist() if n == rel or n.endswith("/" + rel)
            )
            assert zipped.read(name) == f.read_bytes(), rel
cells = root / "result/batch/03-rotated-table/page-001/table-1-cells.csv"
with cells.open(encoding="utf-8", newline="") as handle:
    records = list(csv.DictReader(handle))
assert len(records) == 30
assert all(r["source"] == "03-rotated-table.pdf" and r["page"] == "1" for r in records)
assert all((cells.parents[1] / r["raw_path"]).exists() for r in records)
out = {
    "negative_candidate_rejected": True,
    "corrected_accepted_and_equals_main": True,
    "pages": counts,
    "errors": [e["source"] for e in batch["errors"]],
    "table_shape_including_header": [6, 5],
    "cells": 30,
    "quantity": 20,
    "total_kzt": 128000,
    "row_products_match": True,
    "control_fragments_match": True,
    "archive_hash_matches": True,
    "kit_files_equal_archive": sum(f.is_file() for f in kit_files),
    "raw_cell_paths_exist": True,
    "note": "OCR textual discrepancies are documented separately; numeric agreement is not full textual accuracy.",
}
(root / "evidence/verification.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(json.dumps(out, ensure_ascii=False))
