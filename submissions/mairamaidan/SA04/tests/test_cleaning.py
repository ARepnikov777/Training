import json
import tempfile
import unittest
from pathlib import Path

from src.cleaning import clean_files

ROOT = Path(__file__).resolve().parents[1]
RULES = {"categories": {"Food": "Еда", "Travel": "Транспорт", "Office": "Канцелярия"}}


class CleaningTests(unittest.TestCase):
    def test_h07(self):
        rules = json.loads((ROOT / "input/rules.json").read_text(encoding="utf-8"))
        result = clean_files(
            [ROOT / "input/nov-1.csv", ROOT / "input/nov-2.csv"], rules
        )
        self.assertEqual(
            result["stats"],
            {
                "source_rows": 8,
                "clean_rows": 4,
                "duplicate_rows": 1,
                "rejected_rows": 3,
            },
        )
        self.assertEqual(
            [row["id"] for row in result["clean"]], ["A1", "A2", "A3", "A4"]
        )
        self.assertEqual([row["id"] for row in result["rejected"]], ["A5", "A6", "A7"])

    def test_validation_duplicates_and_exact_raw_record(self):
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.csv"
            second = Path(directory) / "second.csv"
            first.write_text(
                "id,date,category,amount\n"
                "a,2024-02-29,Food,0\n"
                "b,2024-01-01,Travel,1.25\n"
                "c,2024-01-01,Food,1e2\n"
                "bad,2023-02-29,Food,1\n"
                "bad2,2024-2-01,Food,1\n"
                "bad3,2024-01-01,Unknown,1\n"
                "bad4,2024-01-01,Food,-1\n"
                "bad5,2024-01-01,Food,NaN\n"
                "bad6,2024-01-01,Food,Infinity\n"
                ",2024-01-01,Food,1\n"
                "short,2024-01-01,Food\n"
                '"quoted,id",2024-01-01,Unknown,1\n',
                encoding="utf-8",
            )
            second.write_text(
                "id,date,category,amount\n"
                "a,2024-02-29,Food,0\n"
                "a,2024-02-29,Food,2\n"
                "bad,2023-02-29,Food,1\n",
                encoding="utf-8",
            )
            result = clean_files([first, second], RULES)
        self.assertEqual(
            result["clean"],
            [
                {"id": "a", "date": "2024-02-29", "category": "Еда", "amount": "0"},
                {
                    "id": "b",
                    "date": "2024-01-01",
                    "category": "Транспорт",
                    "amount": "1.25",
                },
                {"id": "c", "date": "2024-01-01", "category": "Еда", "amount": "100"},
            ],
        )
        self.assertEqual(
            result["stats"],
            {
                "source_rows": 15,
                "clean_rows": 3,
                "duplicate_rows": 1,
                "rejected_rows": 11,
            },
        )
        rejected = result["rejected"]
        self.assertEqual(
            [row["id"] for row in rejected],
            [
                "bad",
                "bad2",
                "bad3",
                "bad4",
                "bad5",
                "bad6",
                "",
                "short",
                "quoted,id",
                "a",
                "bad",
            ],
        )
        self.assertEqual(rejected[8]["raw_line"], '"quoted,id",2024-01-01,Unknown,1')
        self.assertEqual(
            (rejected[8]["source"], rejected[8]["line_number"]), ("first.csv", 13)
        )
        self.assertEqual(
            (rejected[9]["source"], rejected[9]["line_number"]), ("second.csv", 3)
        )
        self.assertEqual(
            [row["reason"] for row in rejected],
            [
                "Неверная дата",
                "Неверная дата",
                "Неизвестная категория",
                "Неверная сумма",
                "Неверная сумма",
                "Неверная сумма",
                "Пустой id",
                "Неверное число полей",
                "Неизвестная категория",
                "Конфликт id",
                "Неверная дата",
            ],
        )

    def test_bad_header_and_broken_csv_raise(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.csv"
            for contents in (
                "date,id,category,amount\n",
                'id,date,category,amount\n"unclosed\n',
            ):
                with self.subTest(contents=contents):
                    path.write_text(contents, encoding="utf-8")
                    with self.assertRaises((ValueError, OSError)):
                        clean_files([path], RULES)

    def test_extra_fields_and_missing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "extra.csv"
            path.write_text(
                "id,date,category,amount\nx,2024-01-01,Food,1,extra\n", encoding="utf-8"
            )
            rejected = clean_files([path], RULES)["rejected"]
            self.assertEqual(rejected[0]["reason"], "Неверное число полей")
            with self.assertRaises(OSError):
                clean_files([Path(directory) / "missing.csv"], RULES)

    def test_multiline_record_keeps_raw_text_and_first_line(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "multi.csv"
            path.write_text(
                'id,date,category,amount\n"a\nb",2024-01-01,Unknown,1\n',
                encoding="utf-8",
            )
            rejected = clean_files([path], RULES)["rejected"]
        self.assertEqual(rejected[0]["raw_line"], '"a\nb",2024-01-01,Unknown,1')
        self.assertEqual(
            (rejected[0]["source"], rejected[0]["line_number"]), ("multi.csv", 2)
        )
