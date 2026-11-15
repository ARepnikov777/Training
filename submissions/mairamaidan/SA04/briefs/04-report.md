# T4 / #105 — показатели и отчёт

Роль worker, один владелец worktree SA04-report. Прочитай interfaces.md первым: API и поля обязательны. Разрешены только src/reporting.py, tests/test_reporting.py, evidence/reporting-* внутри submissions/mairamaidan/SA04/.

Реализуй summarize(clean_rows, categories) и render_report(clean_rows, stats, sources, rules). Не импортировать cleaning и не ждать его реализации: независимые ручные fixture. Тесты: 4 записи/1000 KZT/500,200,300; точность 0.1+0.2=0.3, ноль/пустой набор, источники/баланс/допущения/все категории, детерминизм. Не округлять произвольно. Выходная структура — interfaces.md.

TDD: сначала тест поведения и минимальный вызываемый каркас для ожидаемого AssertionError, фактический RED сохранить; затем GREEN. evidence/reporting-red.txt, reporting-green.txt, reporting-report.md. Команда `python3 -m unittest discover -s tests -v`.

Без новых runtime-зависимостей, переделегирования и commit/push. Не менять общий контракт, другие файлы, materials/downloads. Полный отчёт в файле; ответ статус, файлы, проверки, блокеры. Перед ответом прекрати запись и передай владение координатору.
