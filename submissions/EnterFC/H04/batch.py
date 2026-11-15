"""Local PDF extraction. Outputs raw text, rendered pages, tables and errors."""

import argparse
import csv
import hashlib
import json
import subprocess
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parent
DPI = 240


def write_json(path, data):
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def groups(values):
    """Collapse consecutive dark pixel positions into line center positions."""
    runs = []
    for value in values:
        if runs and value == runs[-1][-1] + 1:
            runs[-1].append(value)
        else:
            runs.append([value])
    return [sum(run) / len(run) for run in runs]


def raster_grid(page):
    """Find the single rectangular ruled table used by this input package.

    Projections require long dark lines; text alone cannot define a table.
    Coordinates returned in points on the page normalized to rotation zero.
    """
    pix = page.get_pixmap(dpi=DPI, colorspace=pymupdf.csGRAY, alpha=False)
    binary = pix.samples.translate(bytes(1 if v < 70 else 0 for v in range(256)))
    width, height = pix.width, pix.height
    ys = groups(
        y
        for y in range(height)
        if sum(binary[y * width : (y + 1) * width]) > width * 0.6
    )
    if len(ys) < 3:
        return []
    xs = groups(x for x in range(width) if sum(binary[x::width]) > height * 0.15)
    if len(xs) < 3:
        return []
    factor = 72 / DPI
    return [
        [
            [
                (xs[c] * factor, ys[r] * factor, xs[c + 1] * factor, ys[r + 1] * factor)
                for c in range(len(xs) - 1)
            ]
            for r in range(len(ys) - 1)
        ]
    ]


def run_batch(input_dir, output_dir, ocr_languages="rus+eng"):
    input_dir, output_dir = Path(input_dir).resolve(), Path(output_dir).resolve()
    # A new output folder protects the first tool result from accidental overwrite.
    output_dir.mkdir(parents=True, exist_ok=False)
    result = {
        "dpi": DPI,
        "ocr_languages": ocr_languages,
        "documents": [],
        "coordinate_system": "PDF points, top-left origin, source page normalized to rotation 0",
    }
    errors = []
    for source in sorted(input_dir.glob("*.pdf")):
        document = {
            "document": source.name,
            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "status": "ok",
            "pages": [],
        }
        result["documents"].append(document)
        try:
            with pymupdf.open(source) as pdf:
                document["page_count"] = len(pdf)
                for number, page in enumerate(pdf, 1):
                    folder = output_dir / source.stem / f"page-{number:03}"
                    folder.mkdir(parents=True)

                    def relative(name, folder=folder):
                        return (folder / name).relative_to(output_dir).as_posix()

                    record = {
                        "page": number,
                        "source_rotation": page.rotation,
                        "tables": [],
                    }
                    document["pages"].append(record)
                    try:
                        page.get_pixmap(dpi=130).save(folder / "source.png")
                        record["source_image"] = relative("source.png")
                        page.set_rotation(0)
                        page.get_pixmap(dpi=DPI).save(folder / "normalized.png")
                        record["normalized_image"] = relative("normalized.png")
                        text = page.get_text(sort=True)
                        (folder / "native.txt").write_text(text, encoding="utf-8")
                        record["native_text_path"] = relative("native.txt")
                        native = bool(text.strip())
                        record.update(
                            method="native" if native else "ocr",
                            confidence=None,
                            manual_review=not native,
                            status="ok",
                        )
                        raw_tables = []
                        if native:
                            for table in page.find_tables().tables:
                                raw_tables.append(
                                    (table.extract(), [r.cells for r in table.rows])
                                )
                            write_json(folder / "words.json", page.get_text("words"))
                        else:
                            jobs = [
                                {
                                    "image": str(folder / "normalized.png"),
                                    "output": str(folder / "ocr.json"),
                                    "psm": 3,
                                }
                            ]
                            grids = raster_grid(page)
                            for ti, grid in enumerate(grids, 1):
                                for ri, row in enumerate(grid, 1):
                                    for ci, box in enumerate(row, 1):
                                        name = f"table-{ti}-r{ri}-c{ci}"
                                        # Exclude the dark ruling from OCR crops.
                                        clip = pymupdf.Rect(box) + (2, 2, -2, -2)
                                        page.get_pixmap(clip=clip, dpi=DPI).save(
                                            folder / f"{name}.png"
                                        )
                                        jobs.append(
                                            {
                                                "image": str(folder / f"{name}.png"),
                                                "output": str(folder / f"{name}.json"),
                                                "psm": 7,
                                            }
                                        )
                            write_json(folder / "ocr-jobs.json", jobs)
                            process = subprocess.run(
                                [
                                    "node",
                                    str(ROOT / "ocr.cjs"),
                                    str(folder / "ocr-jobs.json"),
                                    ocr_languages,
                                ],
                                check=False,
                                cwd=ROOT,
                                capture_output=True,
                                text=True,
                                encoding="utf-8",
                                timeout=300,
                            )
                            (folder / "ocr-process.log").write_text(
                                process.stdout + process.stderr, encoding="utf-8"
                            )
                            if process.returncode:
                                raise RuntimeError(
                                    f"OCR exited {process.returncode}: {process.stderr.strip()}"
                                )
                            ocr = json.loads((folder / "ocr.json").read_text("utf-8"))
                            text = ocr["text"]
                            if not text.strip():
                                raise ValueError(
                                    "OCR returned no text; manual inspection required"
                                )
                            record.update(
                                confidence=ocr["confidence"],
                                ocr_json_path=relative("ocr.json"),
                            )
                            for ti, grid in enumerate(grids, 1):
                                rows = []
                                for ri, row in enumerate(grid, 1):
                                    rows.append(
                                        [
                                            json.loads(
                                                (
                                                    folder
                                                    / f"table-{ti}-r{ri}-c{ci}.json"
                                                ).read_text("utf-8")
                                            )["text"].strip()
                                            for ci in range(1, len(row) + 1)
                                        ]
                                    )
                                raw_tables.append((rows, grid))
                        (folder / "text.txt").write_text(text, encoding="utf-8")
                        record["text_path"] = relative("text.txt")
                        for ti, (rows, boxes) in enumerate(raw_tables, 1):
                            csv_name, cells_name = (
                                f"table-{ti}.csv",
                                f"table-{ti}-cells.csv",
                            )
                            with (folder / csv_name).open(
                                "w", encoding="utf-8", newline=""
                            ) as handle:
                                csv.writer(handle).writerows(rows)
                            with (folder / cells_name).open(
                                "w", encoding="utf-8", newline=""
                            ) as handle:
                                writer = csv.DictWriter(
                                    handle,
                                    fieldnames=[
                                        "document",
                                        "page",
                                        "table",
                                        "row",
                                        "column",
                                        "value",
                                        "bbox",
                                        "method",
                                        "confidence",
                                        "manual_review",
                                        "raw_path",
                                    ],
                                )
                                writer.writeheader()
                                for ri, row in enumerate(rows, 1):
                                    for ci, value in enumerate(row, 1):
                                        raw_name = f"table-{ti}-r{ri}-c{ci}.json"
                                        confidence = (
                                            ""
                                            if native
                                            else json.loads(
                                                (folder / raw_name).read_text("utf-8")
                                            )["confidence"]
                                        )
                                        writer.writerow(
                                            {
                                                "document": source.name,
                                                "page": number,
                                                "table": ti,
                                                "row": ri,
                                                "column": ci,
                                                "value": value or "",
                                                "bbox": json.dumps(
                                                    boxes[ri - 1][ci - 1]
                                                ),
                                                "method": record["method"],
                                                "confidence": confidence,
                                                "manual_review": not native,
                                                "raw_path": relative(
                                                    "words.json" if native else raw_name
                                                ),
                                            }
                                        )
                            record["tables"].append(
                                {
                                    "csv_path": relative(csv_name),
                                    "cells_path": relative(cells_name),
                                    "rows": len(rows),
                                    "columns": len(rows[0]),
                                }
                            )
                    except (
                        RuntimeError,
                        ValueError,
                        OSError,
                        subprocess.SubprocessError,
                    ) as error:
                        record.update(
                            status="error",
                            error=f"{type(error).__name__}: {error}",
                            manual_review=True,
                        )
                        document["status"] = "partial"
                        errors.append(
                            {
                                "document": source.name,
                                "page": number,
                                "error": record["error"],
                            }
                        )
        except (RuntimeError, ValueError, OSError) as error:
            document.update(status="error", error=f"{type(error).__name__}: {error}")
            errors.append(
                {"document": source.name, "page": "", "error": document["error"]}
            )
    write_json(output_dir / "manifest.json", result)
    with (output_dir / "errors.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["document", "page", "error"])
        writer.writeheader()
        writer.writerows(errors)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "kit/H04/input")
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="New directory; existing results are never overwritten",
    )
    parser.add_argument(
        "--languages",
        default="rus+eng",
        help="Tesseract language list, e.g. rus+eng or eng",
    )
    args = parser.parse_args()
    report = run_batch(args.input, args.output, args.languages)
    print(
        json.dumps(
            {d["document"]: d["status"] for d in report["documents"]},
            ensure_ascii=False,
        )
    )
    raise SystemExit(1 if any(d["status"] != "ok" for d in report["documents"]) else 0)
