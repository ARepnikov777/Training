"""Local OCR extraction; grid detection adapted from H04 batch.py."""

import csv
import json
import re
import subprocess
import tempfile
from pathlib import Path

import pymupdf

DPI = 240


def _groups(values):
    runs = []
    for value in values:
        if runs and value == runs[-1][-1] + 1:
            runs[-1].append(value)
        else:
            runs.append([value])
    return [sum(run) / len(run) for run in runs]


def _grid(page):
    pix = page.get_pixmap(dpi=DPI, colorspace=pymupdf.csGRAY, alpha=False)
    binary = pix.samples.translate(bytes(1 if v < 70 else 0 for v in range(256)))
    width, height = pix.width, pix.height
    ys = _groups(
        y
        for y in range(height)
        if sum(binary[y * width : (y + 1) * width]) > width * 0.6
    )
    xs = _groups(x for x in range(width) if sum(binary[x::width]) > height * 0.15)
    if len(ys) < 3 or len(xs) < 3:
        return []
    f = 72 / DPI
    return [
        [
            (xs[c] * f, ys[r] * f, xs[c + 1] * f, ys[r + 1] * f)
            for c in range(len(xs) - 1)
        ]
        for r in range(len(ys) - 1)
    ]


def _value(text):
    value = text.strip()
    return value.replace(",", ".") if re.fullmatch(r"[+-]?\d+,\d+", value) else value


def extract_ocr(source: Path, output_dir: Path) -> list[dict]:
    source, output_dir = Path(source).resolve(), Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=False)
    pages = []
    with pymupdf.open(source) as pdf:
        for number, page in enumerate(pdf, 1):
            folder = output_dir / f"page-{number:03}"
            folder.mkdir()
            rotation = page.rotation
            page.get_pixmap(dpi=130).save(folder / "source.png")
            page.set_rotation(0)
            page.get_pixmap(dpi=DPI).save(folder / "normalized.png")
            grid = _grid(page)
            jobs = [
                {
                    "image": str(folder / "normalized.png"),
                    "output": str(folder / "ocr.json"),
                    "psm": 3,
                }
            ]
            for ri, row in enumerate(grid, 1):
                for ci, box in enumerate(row, 1):
                    name = f"table-1-r{ri}-c{ci}"
                    page.get_pixmap(
                        clip=pymupdf.Rect(box) + (2, 2, -2, -2), dpi=DPI
                    ).save(folder / f"{name}.png")
                    jobs.append(
                        {
                            "image": str(folder / f"{name}.png"),
                            "output": str(folder / f"{name}.json"),
                            "psm": 7,
                        }
                    )
            (folder / "jobs.json").write_text(
                json.dumps(jobs, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            with tempfile.TemporaryDirectory(prefix="sa11-tessdata-") as cache:
                process = subprocess.run(
                    [
                        "node",
                        str(Path(__file__).with_suffix(".cjs")),
                        str(folder / "jobs.json"),
                        cache,
                    ],
                    check=False,
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
            ocr = json.loads((folder / "ocr.json").read_text(encoding="utf-8"))
            text = ocr["text"]
            if not text.strip():
                raise ValueError("OCR returned no text; manual inspection required")
            (folder / "text.txt").write_text(text, encoding="utf-8")
            (folder / "page.json").write_text(
                json.dumps({"source_rotation": rotation, "dpi": DPI}, indent=2),
                encoding="utf-8",
            )
            tables = []
            if grid:
                rows = []
                with (folder / "table-1-cells.csv").open(
                    "w", encoding="utf-8", newline=""
                ) as cells:
                    writer = csv.writer(cells)
                    writer.writerow(
                        [
                            "source",
                            "page",
                            "table",
                            "row",
                            "column",
                            "value",
                            "bbox_pdf_points",
                            "method",
                            "confidence",
                            "raw_path",
                            "manual_review",
                        ]
                    )
                    for ri, row in enumerate(grid, 1):
                        values = []
                        for ci, box in enumerate(row, 1):
                            raw = f"table-1-r{ri}-c{ci}.json"
                            cell = json.loads(
                                (folder / raw).read_text(encoding="utf-8")
                            )
                            value = _value(cell["text"])
                            values.append(value)
                            writer.writerow(
                                [
                                    source.name,
                                    number,
                                    1,
                                    ri,
                                    ci,
                                    value,
                                    json.dumps(box),
                                    "ocr",
                                    cell["confidence"],
                                    f"page-{number:03}/{raw}",
                                    True,
                                ]
                            )
                        rows.append(values)
                with (folder / "table-1.csv").open(
                    "w", encoding="utf-8", newline=""
                ) as handle:
                    csv.writer(handle).writerows(rows)
                tables.append({"columns": rows[0], "rows": rows[1:]})
            pages.append(
                {
                    "source": source.name,
                    "page": number,
                    "method": "ocr",
                    "text": text,
                    "tables": tables,
                    "uncertainty": [
                        "OCR и все ячейки таблиц требуют ручной проверки; confidence не гарантирует точность."
                    ],
                }
            )
    return pages
