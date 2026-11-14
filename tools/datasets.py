"""Небольшие CSV и эталоны с фиксированными ожидаемыми числами."""

from content import jsn, table, text

EXPENSES = [
    ["X01", "2026-11-01", "Площадка", 120000],
    ["X02", "2026-11-01", "Питание", 45000],
    ["X03", "2026-11-02", "Печать", 12000],
    ["X04", "2026-11-02", "Питание", 15000],
    ["X05", "2026-11-03", "Транспорт", 8000],
    ["X06", "2026-11-03", "Печать", 3000],
    ["X07", "2026-11-04", "Транспорт", 2000],
    ["X08", "2026-11-04", "Площадка", 30000],
]


def make(root):
    p = root / "E07"
    table(
        p / "input/dirty.csv",
        ["id", "date", "category", "amount"],
        [
            ["1", "2026-11-01", "Food", "100"],
            ["2", "01.11.2026", "еда", "200"],
            ["2", "01.11.2026", "еда", "200"],
            ["3", "31.02.2026", "Food", "300"],
            ["4", "2026/11/02", "Transport", "150"],
            ["5", "02-11-2026", "транспорт", "50"],
            ["6", "2026-11-03", "office", "80"],
            ["7", "2026-11-03", "Unknown", "90"],
        ],
    )
    jsn(
        p / "input/rules.json",
        {
            "key": "id",
            "dates": ["YYYY-MM-DD", "DD.MM.YYYY", "YYYY/MM/DD", "DD-MM-YYYY"],
            "output_date": "YYYY-MM-DD",
            "category_aliases": {
                "Food": "Еда",
                "еда": "Еда",
                "Transport": "Транспорт",
                "транспорт": "Транспорт",
                "office": "Канцелярия",
            },
            "duplicate_rule": "Первую корректную строку id сохранить; полностью совпадающий повтор удалить. Конфликтующий id — в exceptions; неверная дата/неизвестная категория — в exceptions.",
        },
    )
    table(
        p / "checks/clean.csv",
        ["id", "date", "category", "amount"],
        [
            ["1", "2026-11-01", "Еда", 100],
            ["2", "2026-11-01", "Еда", 200],
            ["4", "2026-11-02", "Транспорт", 150],
            ["5", "2026-11-02", "Транспорт", 50],
            ["6", "2026-11-03", "Канцелярия", 80],
        ],
    )
    jsn(
        p / "checks/expected.json",
        {
            "input": 8,
            "output": 5,
            "duplicates_removed": 1,
            "exceptions": 2,
            "total_amount": 580,
            "exception_ids": ["3", "7"],
        },
    )
    p = root / "E08"
    table(p / "input/expenses.csv", ["id", "date", "category", "amount_KZT"], EXPENSES)
    jsn(
        p / "checks/expected.json",
        {
            "Площадка": 150000,
            "Питание": 60000,
            "Печать": 15000,
            "Транспорт": 10000,
            "total": 235000,
        },
    )
    text(
        p / "input/rules.md",
        "Валюта KZT. Группировка по category, итог SUM по суммам. Диаграмма — суммы по категориям. Измените X08 с 30000 на 35000: общий итог должен стать 240000; затем верните исходное значение.",
    )
    p = root / "M07"
    table(
        p / "input/a.csv",
        ["id", "date", "category", "amount"],
        [
            ["1", "2026-11-01", "Food", 100],
            ["2", "2026-11-01", "Travel", 200],
            ["3", "2026-11-02", "Food", 300],
            ["4", "2026-11-02", "Office", 400],
        ],
    )
    table(
        p / "input/b.csv",
        ["operation_id", "day", "type", "sum"],
        [
            ["3", "02.11.2026", "еда", 300],
            ["5", "03.11.2026", "дорога", 500],
            ["6", "03.11.2026", "офис", 600],
            ["7", "04.11.2026", "еда", 700],
        ],
    )
    table(
        p / "input/c.csv",
        ["ID", "timestamp", "group", "value"],
        [
            ["5", "2026/11/03", "Travel", 550],
            ["8", "2026/11/04", "Office", 800],
            ["9", "2026/11/05", "Food", 900],
            ["10", "2026/11/05", "Travel", 1000],
        ],
    )
    jsn(
        p / "input/rules.json",
        {
            "schema": ["id", "date", "category", "amount"],
            "mapping": {
                "a.csv": ["id", "date", "category", "amount"],
                "b.csv": ["operation_id", "day", "type", "sum"],
                "c.csv": ["ID", "timestamp", "group", "value"],
            },
            "category_aliases": {
                "Food": "Еда",
                "еда": "Еда",
                "Travel": "Транспорт",
                "дорога": "Транспорт",
                "Office": "Канцелярия",
                "офис": "Канцелярия",
            },
            "date_format": "YYYY-MM-DD",
            "key": "id",
            "same_id_same_fields": "одна итоговая запись; указать все источники",
            "conflict": "все варианты id вывести в conflicts.csv, в итог не включать",
        },
    )
    jsn(
        p / "checks/expected.json",
        {
            "source_rows": 12,
            "clean_ids": ["1", "2", "3", "4", "6", "7", "8", "9", "10"],
            "conflict_id": "5",
            "conflict_values": [500, 550],
            "duplicates_collapsed": 1,
            "clean_rows": 9,
            "clean_amount": 5000,
            "balance": "12 = 9 итоговых + 1 схлопнутый повтор + 2 конфликтующих варианта",
        },
    )
    p = root / "M08"
    table(
        p / "input/plan.csv",
        ["category", "plan_KZT"],
        [["Площадка", 140000], ["Питание", 70000], ["Печать", 10000], ["Транспорт", 0]],
    )
    table(p / "input/actual.csv", ["id", "date", "category", "amount_KZT"], EXPENSES)
    text(
        p / "input/rules.md",
        "Отклонение = факт − план. Превышение выделить, если отклонение >0. Процент = отклонение/план*100; при нулевом плане вывести «нет базы», без деления. Категории брать из объединения плана и факта. Диаграмма: план и факт по категориям.",
    )
    jsn(
        p / "checks/expected.json",
        {
            "total_plan": 220000,
            "total_actual": 235000,
            "total_delta": 15000,
            "category_deltas": {
                "Площадка": 10000,
                "Питание": -10000,
                "Печать": 5000,
                "Транспорт": 10000,
            },
            "zero_base": "Транспорт",
        },
    )
    p = root / "H07"
    for name, header, rows in [
        (
            "nov-1.csv",
            ["id", "date", "category", "amount"],
            [
                ["A1", "2026-11-01", "Food", 100],
                ["A2", "2026-11-01", "Travel", 200],
                ["A3", "2026-11-02", "Office", 300],
            ],
        ),
        (
            "nov-2.csv",
            ["id", "date", "category", "amount"],
            [
                ["A3", "2026-11-02", "Office", 300],
                ["A4", "2026-11-03", "Food", 400],
                ["A5", "bad-date", "Food", 500],
                ["A6", "2026-11-04", "Unknown", 600],
                ["A7", "2026-11-05", "Travel", -20],
            ],
        ),
    ]:
        table(p / "input" / name, header, rows)
    jsn(
        p / "input/rules.json",
        {
            "key": "id",
            "dates": "YYYY-MM-DD only; реальная календарная дата",
            "categories": {
                "Food": "Еда",
                "Travel": "Транспорт",
                "Office": "Канцелярия",
            },
            "amount": "число >=0",
            "duplicate": "полный повтор id схлопнуть",
            "metrics": [
                "число корректных уникальных операций",
                "общая сумма",
                "суммы по категориям",
            ],
            "output": "clean.csv, rejected.csv с причиной и исходной строкой, report.md; один документированный запуск",
        },
    )
    jsn(
        p / "checks/expected.json",
        {
            "source_rows": 8,
            "clean_rows": 4,
            "duplicate_rows": 1,
            "rejected_rows": 3,
            "rejected_ids": ["A5", "A6", "A7"],
            "total": 1000,
            "category_totals": {"Еда": 500, "Транспорт": 200, "Канцелярия": 300},
        },
    )
    p = root / "H08"
    table(
        p / "input/scenarios.csv",
        [
            "scenario",
            "ticket_KZT",
            "participants",
            "fixed_cost_KZT",
            "variable_per_person_KZT",
        ],
        [
            ["базовый", 25000, 30, 300000, 5000],
            ["оптимистичный", 27000, 40, 300000, 4500],
            ["пессимистичный", 22000, 20, 330000, 6000],
        ],
    )
    text(
        p / "input/rules.md",
        "Выручка = цена билета × участники. Затраты = постоянные + переменные на участника × участники. Прибыль = выручка − затраты. Точка безубыточности = округление вверх(постоянные/(цена−переменные)), если маржа >0; иначе «недостижима». Чувствительность: в базовом сценарии менять число участников 10/20/30/40 и цену 20000/25000/30000, остальные параметры фиксированы. Только учебная модель, не прогноз.",
    )
    jsn(
        p / "checks/expected.json",
        {
            "базовый": {
                "revenue": 750000,
                "cost": 450000,
                "profit": 300000,
                "break_even": 15,
            },
            "оптимистичный": {
                "revenue": 1080000,
                "cost": 480000,
                "profit": 600000,
                "break_even": 14,
            },
            "пессимистичный": {
                "revenue": 440000,
                "cost": 450000,
                "profit": -10000,
                "break_even": 21,
            },
            "edge_case": {"ticket": 5000, "variable": 5000, "expected": "недостижима"},
            "sensitivity_base_at_10_participants": -100000,
        },
    )
