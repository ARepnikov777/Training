import unittest
from decimal import Decimal, localcontext

from src.reporting import render_report, summarize

CATEGORIES = {"Food": "Еда", "Travel": "Транспорт", "Office": "Канцелярия"}
RULES = {"categories": CATEGORIES}
ROWS = [
    {"id": "1", "date": "2024-11-01", "category": "Еда", "amount": "200"},
    {"id": "2", "date": "2024-11-02", "category": "Еда", "amount": "300"},
    {"id": "3", "date": "2024-11-03", "category": "Транспорт", "amount": "200"},
    {"id": "4", "date": "2024-11-04", "category": "Канцелярия", "amount": "300"},
]
STATS = {"source_rows": 8, "clean_rows": 4, "duplicate_rows": 1, "rejected_rows": 3}


class ReportingTests(unittest.TestCase):
    def test_summarize_counts_and_totals(self):
        self.assertEqual(
            summarize(ROWS, CATEGORIES),
            {
                "clean_rows": 4,
                "total": Decimal(1000),
                "category_totals": {
                    "Еда": Decimal(500),
                    "Транспорт": Decimal(200),
                    "Канцелярия": Decimal(300),
                },
            },
        )

    def test_decimal_precision_and_zero_categories(self):
        rows = [dict(ROWS[0], amount="0.1"), dict(ROWS[1], amount="0.2")]
        result = summarize(rows, CATEGORIES)
        self.assertEqual(result["total"], Decimal("0.3"))
        self.assertEqual(
            result["category_totals"],
            {"Еда": Decimal("0.3"), "Транспорт": Decimal(0), "Канцелярия": Decimal(0)},
        )
        rows = [
            dict(ROWS[0], amount="123456789012345678901234567890.1"),
            dict(ROWS[1], amount="0.2"),
        ]
        self.assertEqual(
            summarize(rows, CATEGORIES)["total"],
            Decimal("123456789012345678901234567890.3"),
        )

    def test_summarize_is_independent_of_caller_exponent_limits(self):
        with localcontext() as context:
            context.Emax = 6
            context.Emin = -6
            small = summarize([dict(ROWS[0], amount="0.00000001")], CATEGORIES)
            self.assertEqual(small["total"], Decimal("0.00000001"))
            self.assertEqual(small["category_totals"]["Еда"], Decimal("0.00000001"))
            large = summarize([dict(ROWS[0], amount="10000000")], CATEGORIES)
            self.assertEqual(large["total"], Decimal(10000000))
            self.assertEqual(large["category_totals"]["Еда"], Decimal(10000000))

    def test_empty_rows(self):
        self.assertEqual(
            summarize([], CATEGORIES),
            {
                "clean_rows": 0,
                "total": Decimal(0),
                "category_totals": {
                    "Еда": Decimal(0),
                    "Транспорт": Decimal(0),
                    "Канцелярия": Decimal(0),
                },
            },
        )

    def test_report_contains_sources_totals_balance_and_assumptions(self):
        report = render_report(ROWS, STATS, ["nov-1.csv", "nov-2.csv"], RULES)
        for value in (
            "nov-1.csv",
            "nov-2.csv",
            "1000",
            "KZT",
            "Еда",
            "500",
            "Транспорт",
            "200",
            "Канцелярия",
            "300",
            "8",
            "4",
            "1",
            "3",
            "валидац",
            "повтор",
            "конфликт",
        ):
            self.assertIn(value.lower(), report.lower())
        for line in (
            "Исходных строк: 8",
            "Корректных уникальных строк: 4",
            "Полных повторов: 1",
            "Отклонённых строк: 3",
            "| Еда | 500 |",
            "| Транспорт | 200 |",
            "| Канцелярия | 300 |",
        ):
            self.assertIn(line, report)
        self.assertEqual(
            report, render_report(ROWS, STATS, ["nov-1.csv", "nov-2.csv"], RULES)
        )

    def test_report_empty_rows_keeps_all_categories(self):
        report = render_report(
            [],
            {
                "source_rows": 0,
                "clean_rows": 0,
                "duplicate_rows": 0,
                "rejected_rows": 0,
            },
            [],
            RULES,
        )
        for category in CATEGORIES.values():
            self.assertIn(category, report)
        self.assertIn("0", report)


if __name__ == "__main__":
    unittest.main()
