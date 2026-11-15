"""Независимая сверка контрольного набора H07, не общий валидатор CSV."""

import argparse
import csv
import json
import sys
from decimal import Decimal
from pathlib import Path


def read_csv(path, fields):
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream, strict=True)
        if reader.fieldnames != fields:
            raise ValueError(f"Неверная схема: {path}")
        rows = list(reader)
        if any(None in row or None in row.values() for row in rows):
            raise ValueError(f"Неверная строка: {path}")
        return rows


def verify(input_dir, output_dir, expected_path):
    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    rules = json.loads((input_dir / "rules.json").read_text(encoding="utf-8"))
    fields = ["id", "date", "category", "amount"]
    rejects = []
    accepted = []
    seen = set()
    source_count = duplicates = 0
    reasons = {
        "A5": "Неверная дата",
        "A6": "Неизвестная категория",
        "A7": "Неверная сумма",
    }
    if set(expected["rejected_ids"]) != set(reasons):
        raise ValueError("Неизвестный набор отклонений H07")
    for name in ("nov-1.csv", "nov-2.csv"):
        path = input_dir / name
        with path.open(encoding="utf-8", newline="") as stream:
            lines = stream.readlines()
        reader = csv.reader(lines, strict=True)
        if next(reader) != fields:
            raise ValueError(f"Неверная схема: {path}")
        while True:
            start = reader.line_num + 1
            try:
                row = next(reader)
            except StopIteration:
                break
            if len(row) != 4:
                raise ValueError("Неизвестная строка H07")
            source_count += 1
            if row[0] in reasons:
                defects = {
                    "A5": (1, "bad-date"),
                    "A6": (2, "Unknown"),
                    "A7": (3, "-20"),
                }
                index, value = defects[row[0]]
                if row[index] != value or (
                    row[0] == "A6" and value in rules["categories"]
                ):
                    raise ValueError("Дефект отклонённой строки H07 изменён")
                rejects.append(
                    {
                        "source": name,
                        "line_number": str(start),
                        "raw_line": "".join(lines[start - 1 : reader.line_num])
                        .removesuffix("\n")
                        .removesuffix("\r"),
                        "id": row[0],
                        "reason": reasons[row[0]],
                    }
                )
            elif tuple(row) in seen:
                duplicates += 1
            else:
                seen.add(tuple(row))
                accepted.append(
                    dict(
                        zip(
                            fields,
                            [
                                row[0],
                                row[1],
                                rules["categories"][row[2]],
                                format(Decimal(row[3]), "f"),
                            ],
                        )
                    )
                )
    clean = read_csv(output_dir / "clean.csv", fields)
    rejected = read_csv(
        output_dir / "rejected.csv",
        ["source", "line_number", "raw_line", "id", "reason"],
    )
    if clean != accepted or len({row["id"] for row in clean}) != len(clean):
        raise ValueError("Расхождение clean.csv")
    if rejected != rejects or sorted(row["id"] for row in rejected) != sorted(
        expected["rejected_ids"]
    ):
        raise ValueError("Расхождение rejected.csv")
    counts = {
        "source_rows": source_count,
        "clean_rows": len(clean),
        "duplicate_rows": duplicates,
        "rejected_rows": len(rejected),
    }
    if any(counts[k] != expected[k] for k in counts) or source_count != len(
        clean
    ) + duplicates + len(rejected):
        raise ValueError("Расхождение баланса")
    totals = {category: Decimal(0) for category in rules["categories"].values()}
    for row in clean:
        totals[row["category"]] += Decimal(row["amount"])
    if totals != {
        k: Decimal(str(v)) for k, v in expected["category_totals"].items()
    } or sum(totals.values()) != Decimal(str(expected["total"])):
        raise ValueError("Расхождение контрольных сумм")
    report = (output_dir / "report.md").read_text(encoding="utf-8").splitlines()
    required = [
        "- nov-1.csv",
        "- nov-2.csv",
        f"- Уникальных операций: {counts['clean_rows']}",
        f"- Общая сумма: {expected['total']} KZT",
        f"- Исходных строк: {source_count}",
        f"- Корректных уникальных строк: {len(clean)}",
        f"- Полных повторов: {duplicates}",
        f"- Отклонённых строк: {len(rejected)}",
    ]
    required += [
        f"| {category} | {amount} |"
        for category, amount in expected["category_totals"].items()
    ]
    if any(report.count(line) != 1 for line in required):
        raise ValueError("Расхождение report.md")
    metric_lines = required[2:8]
    for line in metric_lines:
        prefix = line.split(":", 1)[0] + ":"
        if [item for item in report if item.startswith(prefix)] != [line]:
            raise ValueError("Расхождение report.md")
    for category, amount in expected["category_totals"].items():
        prefix = f"| {category} |"
        if [item for item in report if item.startswith(prefix)] != [
            f"| {category} | {amount} |"
        ]:
            raise ValueError("Расхождение report.md")


def main():
    parser = argparse.ArgumentParser(
        description="Независимая проверка контрольного H07"
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected", type=Path, required=True)
    args = parser.parse_args()
    try:
        verify(args.input, args.output, args.expected)
    except (OSError, ValueError, KeyError, TypeError, StopIteration, csv.Error) as exc:
        print(f"Ошибка проверки H07: {exc}", file=sys.stderr)
        return 1
    print("Контрольный H07 проверен")
    return 0


if __name__ == "__main__":
    sys.exit(main())
