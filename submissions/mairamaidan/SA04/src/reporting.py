"""Точные показатели и детерминированный текст отчёта."""

from decimal import MAX_EMAX, MIN_EMIN, Decimal, localcontext


def summarize(clean_rows, categories):
    amounts = [Decimal(row["amount"]) for row in clean_rows]
    # Сохраняем все десятичные разряды даже при сумме длиннее контекста Decimal.
    if amounts:
        highest = max(amount.adjusted() for amount in amounts)
        lowest = min(amount.as_tuple().exponent for amount in amounts)
        precision = max(1, highest - lowest + 1 + len(str(len(amounts))))
    else:
        precision = 1
    with localcontext() as context:
        context.prec = precision
        context.Emax = MAX_EMAX
        context.Emin = MIN_EMIN
        totals = {category: Decimal(0) for category in categories.values()}
        for row, amount in zip(clean_rows, amounts):
            totals[row["category"]] += amount
        total = sum(amounts, Decimal(0))
    return {"clean_rows": len(clean_rows), "total": total, "category_totals": totals}


def render_report(clean_rows, stats, sources, rules):
    summary = summarize(clean_rows, rules["categories"])
    lines = ["# Отчёт", "", "## Источники"]
    lines.extend("- " + source for source in sources)
    if not sources:
        lines.append("- Нет")
    lines.extend(
        [
            "",
            "## Показатели",
            "- Уникальных операций: {}".format(summary["clean_rows"]),
            "- Общая сумма: {} KZT".format(format(summary["total"], "f")),
            "",
            "| Категория | Сумма, KZT |",
            "| --- | ---: |",
        ]
    )
    for category, amount in summary["category_totals"].items():
        lines.append("| {} | {} |".format(category, format(amount, "f")))
    lines.extend(
        [
            "",
            "## Баланс строк",
            "- Исходных строк: {}".format(stats["source_rows"]),
            "- Корректных уникальных строк: {}".format(stats["clean_rows"]),
            "- Полных повторов: {}".format(stats["duplicate_rows"]),
            "- Отклонённых строк: {}".format(stats["rejected_rows"]),
            "",
            "## Допущения",
            "- Валидация предшествует исключению повторов: проверяются поля, реальная дата, категория и конечная неотрицательная сумма.",
            "- Полный повтор совпадает по всем четырём исходным полям; повтор неверной записи отклоняется.",
            "- При конфликте id с другими значениями сохраняется первая корректная запись, последующая отклоняется.",
            "",
        ]
    )
    return "\n".join(lines)
