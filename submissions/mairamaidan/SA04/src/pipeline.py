"""Воспроизводимый запуск обработки двух выгрузок."""

import argparse
import csv
import json
import sys
from pathlib import Path

from .cleaning import clean_files
from .reporting import render_report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        paths = [args.input / "nov-1.csv", args.input / "nov-2.csv"]
        rules = json.loads((args.input / "rules.json").read_text(encoding="utf-8"))
        data = clean_files(paths, rules)
        report = render_report(
            data["clean"], data["stats"], [p.name for p in paths], rules
        )
        args.output.mkdir(parents=True, exist_ok=True)
        for name, fields, rows in (
            ("clean.csv", ["id", "date", "category", "amount"], data["clean"]),
            (
                "rejected.csv",
                ["source", "line_number", "raw_line", "id", "reason"],
                data["rejected"],
            ),
        ):
            with (args.output / name).open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows)
        (args.output / "report.md").write_text(report, encoding="utf-8")
    except (OSError, ValueError, KeyError, TypeError, csv.Error) as exc:
        print(f"Ошибка обработки: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
