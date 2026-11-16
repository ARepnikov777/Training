"""Reproducible local extraction of the SA11 PDF package."""

import argparse
import csv
import hashlib
import json
import subprocess
from pathlib import Path

import pymupdf
from src.contract import validate_batch, validate_page

ROOT = Path(__file__).resolve().parent


def write_json(path, payload):
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def run_batch(input_dir, output_dir, text_extractor=None, ocr_extractor=None):
    input_dir, output_dir = Path(input_dir), Path(output_dir)
    sources = sorted(input_dir.glob("*.pdf"))
    if not sources:
        raise ValueError(f"No PDF files in {input_dir}")
    output_dir.mkdir(parents=True, exist_ok=False)
    if text_extractor is None:
        from src.text_extract import extract_text

        text_extractor = extract_text
    if ocr_extractor is None:
        from src.ocr_extract import extract_ocr

        ocr_extractor = extract_ocr
    payload = {"pages": [], "errors": []}
    inventory = []
    for source in sources:
        inventory.append(
            {
                "source": source.name,
                "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            }
        )
        try:
            with pymupdf.open(source) as doc:
                count = len(doc)
                native = all(page.get_text().strip() for page in doc)
            extractor = text_extractor if native else ocr_extractor
            pages = extractor(source, output_dir / source.stem)
            for page in pages:
                validate_page(page)
            if [p["page"] for p in pages] != list(range(1, count + 1)) or any(
                p["source"] != source.name for p in pages
            ):
                raise ValueError(
                    "Extractor returned incomplete pages or mismatched source"
                )
            payload["pages"].extend(pages)
        except (RuntimeError, ValueError, OSError, subprocess.SubprocessError) as error:
            payload["errors"].append(
                {
                    "source": source.name,
                    "error": f"{type(error).__name__}: {error}",
                    "continued": True,
                }
            )
    validate_batch(payload)
    write_json(output_dir / "batch.json", payload)
    write_json(output_dir / "inputs.json", inventory)
    with (output_dir / "errors.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["source", "error", "continued"])
        writer.writeheader()
        writer.writerows(payload["errors"])
    return payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "kit/H04/input")
    parser.add_argument(
        "--output", type=Path, required=True, help="New directory; never overwrites raw"
    )
    args = parser.parse_args()
    result = run_batch(args.input, args.output)
    print(
        json.dumps(
            {"pages": len(result["pages"]), "errors": result["errors"]},
            ensure_ascii=False,
        )
    )
    raise SystemExit(1 if result["errors"] else 0)
