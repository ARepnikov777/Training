"""Check result/laptops.csv: count, duplicates, required fields, match with kit files.

Usage: python3 source/verify.py <path-to-unpacked-M13-kit>
catalog.json and checks/expected-ids.json are used only for checking.
"""

import csv
import json
import sys
from pathlib import Path

FIELDS = ["id", "name", "category", "price", "currency", "supplier",
          "availability", "ram_GB", "ssd_GB", "screen_inches", "source_url"]
REQUIRED = ["id", "name", "category", "price", "currency", "source_url"]

kit = Path(sys.argv[1])
here = Path(__file__).resolve().parent.parent
with open(here / "result" / "laptops.csv", encoding="utf-8", newline="") as f:
    reader = csv.DictReader(f)
    header = reader.fieldnames
    rows = list(reader)

expected = json.loads((kit / "checks" / "expected-ids.json").read_text())
catalog = {r["id"]: r for r in json.loads((kit / "input" / "site" / "catalog.json").read_text())
           if r["category"] == "laptop"}
ids = [r["id"] for r in rows]
problems = []

if header != FIELDS:
    problems.append(f"header {header} != {FIELDS}")
if len(rows) != 20:
    problems.append(f"rows: {len(rows)} != 20")
dups = sorted({i for i in ids if ids.count(i) > 1})
if dups:
    problems.append(f"duplicate ids: {dups}")
if sorted(ids) != sorted(expected):
    problems.append(f"missing {sorted(set(expected) - set(ids))}, extra {sorted(set(ids) - set(expected))}")
for r in rows:
    empty = [k for k in REQUIRED if not r[k]]
    if empty:
        problems.append(f"{r['id']}: empty required {empty}")
    if r["source_url"] != f"http://127.0.0.1:8765/product?id={r['id']}":
        problems.append(f"{r['id']}: source_url {r['source_url']}")
    src = catalog.get(r["id"])
    if src is None:
        continue
    for k in FIELDS[:-1]:
        want = "" if src.get(k) is None else str(src[k])
        if r[k] != want:
            problems.append(f"{r['id']}.{k}: csv={r[k]!r} catalog={want!r}")

print(f"rows={len(rows)} unique_ids={len(set(ids))} expected={len(expected)} "
      f"catalog_laptops={len(catalog)}")
empty_optional = [(r["id"], k) for r in rows for k in FIELDS if k not in REQUIRED and not r[k]]
print(f"empty optional values: {empty_optional}")
print("\n".join(problems) if problems else "OK: all checks passed")
sys.exit(1 if problems else 0)
