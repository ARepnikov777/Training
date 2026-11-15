"""Проверки артефактов M04; запуск из любой папки, только Python 3."""

import csv
import hashlib
import json
from decimal import Decimal
from pathlib import Path


solution = Path(__file__).resolve().parents[1]
repo = solution.parents[2]
source = repo / "materials/M04"
archive = repo / "downloads/M04.zip"
assert hashlib.sha256(archive.read_bytes()).hexdigest() == (
    "3e82f7197d3c54c2b454a62c5e4dd31ea456fbbca14a5116fad6b89fb50bef2d"
), "SHA-256 ZIP не совпадает с issue #25"
for name, checksum in json.loads((source / "checksums.json").read_text()).items():
    assert hashlib.sha256((source / name).read_bytes()).hexdigest() == checksum, name
print("PASS: SHA-256 ZIP и всех 4 исходных файлов совпадают")

expected = json.loads((source / "checks/expected.json").read_text())
initial = json.loads((solution / "evidence/initial-transcription.json").read_text())
assert len(initial["pages"]) == 3
for page in range(1, 4):
    path = solution / f"result/page-{page}.csv"
    with path.open(encoding="utf-8", newline="") as file:
        rows = list(csv.reader(file))
    assert len(rows) == 7 and all(len(row) == 5 for row in rows), path.name
    assert rows[0] == [f"Ведомость №{page}; цены и суммы в KZT", "", "", "", ""]
    assert rows[1] == expected["columns"], path.name
    assert [row[0] for row in rows[2:]] == expected["row_order"], path.name
    assert rows[2:] == initial["pages"][page - 1]["rows"], path.name
    assert rows[-1][1] == rows[-1][3] == "", path.name
    for row in rows[2:-1]:
        assert int(row[2]) > 0
        assert Decimal(row[2]) * Decimal(row[3]) == Decimal(row[4]), row[0]
    quantity = sum(int(row[2]) for row in rows[2:-1])
    amount = sum(Decimal(row[4]) for row in rows[2:-1])
    assert quantity == int(rows[-1][2]) == expected[f"page{page}"]["quantity_total"]
    assert amount == Decimal(rows[-1][4]) == expected[f"page{page}"]["amount_total_KZT"]
    print(f"PASS: {path.name}: структура, первичная транскрипция, 4 произведения; "
          f"итог {quantity} шт., {amount} KZT")
print("PASS: все 3 CSV открыты в UTF-8; все проверки пройдены")
