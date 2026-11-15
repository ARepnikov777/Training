# T5 / #106 — интеграция

Рабочее дерево `student/mairamaidan/SA04-integrate`. Реализованы CLI `src/pipeline.py`, независимый `src/verify.py`, тесты, README и три файла `result/`. Verifier рассчитан на фиксированный H07 и не импортирует cleaning/reporting: он выводит ожидаемые записи из входов и проверяет поля, уникальность, источники, номера, сырой текст, причины, суммы и баланс по эталону.

RED: `python3 -m unittest discover -s tests -p test_pipeline.py -v` — 1 (ожидаемый AssertionError о нереализованном CLI); затем аналогичный запуск `test_verify.py` — 1 (ожидаемый неверный код verifier). Дополнительный тест подмены и входа, и реестра сначала ошибочно проходил, затем скорректированный тест показал RED 1; после проверки дефектов H07 — GREEN. Полные выводы и коды — `integration-red.txt`.

GREEN: `python3 -m unittest discover -s tests -v` — 0, 16 тестов; полный вывод — `integration-green.txt`. `python3 -m src.pipeline --input input --output result` дважды — 0, три SHA-256 до и после совпадают. `python3 -m src.verify --input input --output result --expected checks/expected.json` — 0. На отдельной копии результата заменили в отчёте 1000 KZT на 1001 KZT: verifier — 1, «Расхождение report.md»; после восстановления — 0. Копия удалена, исходные input не менялись. Все команды и вывод — `integration-green.txt`.

`/tmp/sa04-checks-20261115/bin/ruff check --fix` и `ruff format` применены только к четырём файлам pipeline/verify и их тестов; затем `ruff check` тех же файлов — 0, `All checks passed!`. Проверка финального diff и статуса выполнена исполнителем; независимое итоговое ревью и приёмка остаются координатору. Коммит, публикация и PR не выполнялись. Право записи возвращено координатору.

## Fix 2 — противоречивые значения отчёта

Независимый reviewer обнаружил, что verifier принимал правильную строку даже при наличии второй строки того же показателя с неверным значением. Регрессионный тест добавляет одновременно правильное и неверное значение общей суммы и, отдельно, категории «Еда». До исправления оба случая дали ожидаемый AssertionError: `python3 -m unittest discover -s tests -p test_verify.py -v`, exit 1, два FAIL (`integration-fix2-red.txt`). Теперь каждый показатель и каждая категория должны встречаться единожды с ожидаемым значением.

После исправления `python3 -m unittest discover -s tests -v` — exit 0, 17 тестов; Ruff четырёх файлов интеграции — exit 0, `All checks passed!`; выводы — `integration-fix2-green.txt`. `ruff check --fix` и `ruff format` применены к тем же четырём файлам. Повторное независимое ревью и приёмка остаются координатору. Право записи передано координатору.
