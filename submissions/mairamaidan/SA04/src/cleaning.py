"""Validate and deduplicate transaction CSV records."""

import csv
import re
from datetime import date
from decimal import Decimal, InvalidOperation

_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\Z")
_HEADER = ["id", "date", "category", "amount"]


def clean_files(paths, rules):
    clean = []
    rejected = []
    seen_rows = set()
    seen_ids = set()
    source_rows = duplicate_rows = 0
    for path in paths:
        with path.open(encoding="utf-8", newline="") as stream:
            lines = stream.readlines()
        reader = csv.reader(lines, strict=True)
        try:
            if next(reader, None) != _HEADER:
                raise ValueError(f"Неверный заголовок CSV: {path}")
            while True:
                first_line = reader.line_num + 1
                try:
                    row = next(reader)
                except StopIteration:
                    break
                raw = "".join(lines[first_line - 1 : reader.line_num])
                if raw.endswith("\r\n"):
                    raw = raw[:-2]
                elif raw.endswith(("\r", "\n")):
                    raw = raw[:-1]
                source_rows += 1
                row_id = row[0] if row else ""
                reason = None
                if len(row) != 4:
                    reason = "Неверное число полей"
                else:
                    row_id, date_text, category, amount_text = row
                    if not row_id:
                        reason = "Пустой id"
                    elif not _DATE.fullmatch(date_text):
                        reason = "Неверная дата"
                    else:
                        try:
                            date.fromisoformat(date_text)
                        except ValueError:
                            reason = "Неверная дата"
                    if reason is None and category not in rules["categories"]:
                        reason = "Неизвестная категория"
                    if reason is None:
                        try:
                            amount = Decimal(amount_text)
                            if not amount.is_finite() or amount < 0:
                                reason = "Неверная сумма"
                        except InvalidOperation:
                            reason = "Неверная сумма"
                    if reason is None:
                        key = tuple(row)
                        if key in seen_rows:
                            duplicate_rows += 1
                            continue
                        if row_id in seen_ids:
                            reason = "Конфликт id"
                        else:
                            seen_rows.add(key)
                            seen_ids.add(row_id)
                            clean.append(
                                {
                                    "id": row_id,
                                    "date": date_text,
                                    "category": rules["categories"][category],
                                    "amount": format(amount, "f"),
                                }
                            )
                if reason is not None:
                    rejected.append(
                        {
                            "source": path.name,
                            "line_number": first_line,
                            "raw_line": raw,
                            "id": row_id,
                            "reason": reason,
                        }
                    )
        except csv.Error as exc:
            raise ValueError(f"Ошибка CSV в {path}: {exc}") from exc
    return {
        "clean": clean,
        "rejected": rejected,
        "stats": {
            "source_rows": source_rows,
            "clean_rows": len(clean),
            "duplicate_rows": duplicate_rows,
            "rejected_rows": len(rejected),
        },
    }
