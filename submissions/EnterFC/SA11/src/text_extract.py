import csv
import json
from pathlib import Path

import fitz


def extract_text(source: Path, output_dir: Path) -> list[dict]:
    output_dir.mkdir(parents=True, exist_ok=False)
    pages = []
    with fitz.open(source) as document:
        for number, page in enumerate(document, start=1):
            text = page.get_text()
            tables = []
            for index, table in enumerate(page.find_tables().tables, start=1):
                rows = [[cell or "" for cell in row] for row in table.extract()]
                if not rows:
                    continue
                tables.append({"columns": rows[0], "rows": rows[1:]})
                with (output_dir / f"page-{number}-table-{index}.csv").open(
                    "x", encoding="utf-8", newline=""
                ) as file:
                    csv.writer(file).writerows(rows)
            record = {
                "source": source.name,
                "page": number,
                "method": "text",
                "text": text,
                "tables": tables,
                "uncertainty": [],
            }
            (output_dir / f"page-{number}.txt").write_text(text, encoding="utf-8")
            page.get_pixmap().save(output_dir / f"page-{number}.png")
            (output_dir / f"page-{number}.json").write_text(
                json.dumps(record, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            pages.append(record)
    return pages
