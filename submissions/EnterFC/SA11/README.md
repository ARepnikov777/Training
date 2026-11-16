# SA11 — EnterFC — пакет PDF по графу нативных субагентов

Задание: [#73](https://github.com/ARepnikov777/Training/issues/73). Предметная основа: [H04 #40](https://github.com/ARepnikov777/Training/issues/40). Новое выполнение SA11; исходное решение H04 не изменялось. Локальная приёмка преподавателем и merge здесь не заявляются.

Получены 5 страниц трёх пригодных PDF, raw OCR и таблица CSV с provenance; повреждённый четвёртый PDF отражён отдельно в errors. [Отчёт заказчику](report.md) содержит числовую сверку, конкретные расхождения и места ручной проверки.

## Результат и источники

- [Итоговый пакет](result/batch/batch.json), [ошибки CSV](result/batch/errors.csv), [SHA256 входов](result/batch/inputs.json). В каждой записи source/page/method/text/tables/uncertainty; страницы нумеруются с 1.
- [Текст](result/batch/01-text/page-1.txt), OCR [страница 1](result/batch/02-scan/page-001/text.txt), [2](result/batch/02-scan/page-002/text.txt), [3](result/batch/02-scan/page-003/text.txt).
- Таблица: [raw CSV](result/batch/03-rotated-table/page-001/table-1.csv), [30 ячеек с provenance/confidence](result/batch/03-rotated-table/page-001/table-1-cells.csv), [нормализованное изображение](result/batch/03-rotated-table/page-001/normalized.png). [Сверенная копия первого OCR-прогона](result/ocr/03-rotated-table/page-001/verified-table.csv) исправляет две визуально пустые ячейки; журнал исправлений — [отчёт OCR](evidence/ocr/worker.md). Raw не переписывался.
- Первый новый raw двух worker отдельно сохранён в result/text/ и result/ocr/. result/batch/ получен повторным общим запуском интегратора. Готовые результаты прежнего H04 не копировались. Детектор сетки и runner Tesseract адаптированы из собственного H04; provenance — [inventory](inventory.md), [архив](evidence/provenance.json), отчёты worker.

Все исходные kit/H04 и downloads/H04.zip сохранены. SHA256 архива повторно совпал с закреплённым значением issue. Checks прочитаны после нового raw, используются для сверки, а не подстановки ответа.

## Веха, задачи и владельцы

[Milestone SA11 — EnterFC](https://github.com/ARepnikov777/Training/milestone/10); родитель #73 и все пять задач включены в неё, имеют subagents и assignee EnterFC. Нативные sub-issues проверены обратным API-чтением: [снимок](evidence/github-subissues.json), [ID и URL](evidence/github-tasks.json).

| Задача | Владелец / роль | Зависимость | Ветка / запись |
|---|---|---|---|
| [#141](https://github.com/ARepnikov777/Training/issues/141) инвентаризация | explorer, только чтение; координатор сохраняет отчёт | Capability_check | SA11, inventory.md |
| [#142](https://github.com/ARepnikov777/Training/issues/142) контракт | worker | #141 | SA11, contract.md/schema.json/src/contract.py/tests/test_contract.py |
| [#143](https://github.com/ARepnikov777/Training/issues/143) текст | worker | #142 | SA11-text, text_extract/test_text_extract/result/text/evidence/text |
| [#144](https://github.com/ARepnikov777/Training/issues/144) OCR | worker | #142, параллельно #143 | SA11-ocr, ocr_extract/test_ocr_extract/result/ocr/evidence/ocr и npm manifests |
| [#145](https://github.com/ARepnikov777/Training/issues/145) интеграция/ревью | координатор и отдельный reviewer | #143, #144 | SA11, batch/общие отчёты/negative evidence |

Пять задач разделяют пять реальных границ приёмки. Полные ветки: student/EnterFC/SA11[-text/-ocr]. Параллельные worker работали в отдельных Training-SA11-text/Training-SA11-ocr; общий отчёт/интегратор пишет только координатор. Контракт согласован до параллельной записи. Промежуточные ветки не публикуются. Задачи не закрываются автоматически.

## Как повторить

Проверено: Windows, Python 3.15.0, PyMuPDF 1.26.7, Node 26.13.1, npm 11.20.0, tesseract.js 6.0.1, локальные rus/eng 1.0.0, pytest 9.2.0, Ruff 0.17.5. Python-пакеты закреплены в requirements*.txt; npm — src/package-lock.json. Платных API, ключей и SSH нет.

Из каталога submissions/EnterFC/SA11 в PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
npm.cmd ci --prefix src --ignore-scripts --no-audit --no-fund
.\.venv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider
.\.venv\Scripts\python.exe run_batch.py --output result/repeat-NEW
```

Каталог result/repeat-NEW должен отсутствовать. Повторный запуск требует нового имени; raw защищён от перезаписи. На Linux используйте .venv/bin/python и npm вместо npm.cmd. Установка Python-зависимостей в новой venv отдельно не проверялась: фактические прогоны использовали уже установленный Python H04; npm ci выполнен в чистом локальном src/node_modules SA11. Модели OCR берутся из установленных пакетов, временные копии очищаются и в Git не входят.

Для полного комплекта ожидается **exit 1**: 04-broken.pdf непригоден. Сверяйте batch.json: 5 страниц, единственная ошибка source=04-broken.pdf, continued=true. На ошибках вывод не объявляется успешным кодом 0. Ошибка одного документа не удаляет результаты остальных. Пустой вход, неполные страницы и несовпадение source тоже явно проверяются.

## Граф и проверки

[workflow.md](workflow.md) подготовлен до реализации; N=2 общих исправления, T=3600 секунд, max_parallel=3, два параллельных пишущих worker. Новый started_at и счётчик — [run-log](run-log.md). Реальные роли выбирались явным agent_type, fork_turns=none; имена задач роль не заменяют. Модели ролей не переопределялись.

Брифы: [контракт](brief-contract.md), [текст](brief-text.md), [OCR](brief-ocr.md), [интеграция](brief-integration.md), [ревью](brief-review.md), [отрицательный сценарий](evidence/negative/brief.md). [Контракт](contract.md), [JSON Schema](schema.json). Результаты worker: [text](evidence/text/worker.md), [OCR](evidence/ocr/worker.md). [Независимый reviewer](reviewer-report.md) принял основной результат, фактически отклонил [кандидат без page](evidence/negative/candidate.json), затем принял [исправление](evidence/negative/corrected.json). [Отчёт исправления](evidence/negative/repair-report.md). Done_accepted зафиксирован локально 2026-11-16 до исходного дедлайна, attempts=1 из N=2. Приёмка преподавателя и merge остаются ему.

Повторная структурная проверка: graph_check.py, exit 0, 17 состояний/33 перехода. [Сохранённый результат](evidence/graph-check.txt), [state SVG](evidence/workflow-state.svg), [параллельные ветви SVG](evidence/workflow-parallel.svg), [просмотренный PNG](evidence/workflow-render.png). Checker — эвристика, не доказательство реальных запусков; исходные визуальные evidence сохранены.

TDD: [contract RED/GREEN](evidence/contract/commands.txt), [batch RED/GREEN](evidence/integration/commands.txt), отчёты text/OCR с честной хронологией дополнительных циклов. Итоговый общий прогон: [40 passed](evidence/integration/all-tests.txt), включая 9 базовых и 31 SA11; одно предупреждение зависимости PyMuPDF о deprecated ByteString. Ruff check/format прошли для tools/tests и кода SA11. [Новый batch](evidence/integration/batch-run.txt): 5 страниц, ошибка broken, exit 1 ожидаемый и сохранён.

[Проверка чисел, полноты и архива](evidence/verification.json) воспроизводится командой `python evidence/verify_results.py` из каталога SA11 (при установленном PyMuPDF/зависимостях). [Повтор из чистой cwd](evidence/integration/clean-replay.txt) дал идентичный batch: [сверка](evidence/integration/replay-check.json). Локальный .gitattributes сохраняет точные байты raw, включая CRLF. `git diff --check` отмечает исходные окончания строк и пустые строки OCR; raw не нормализуется ради этой проверки, исходники проверяются отдельно.

[Gitleaks](evidence/gitleaks-review.md): staged scan без находок, history scan exit 1 на унаследованной контрольной сумме H09. Она независимо пересчитана из того же commit, значение не публикуется; автоматическая history scan не объявляется зелёной. Перед каждым commit/push стандартные проверки повторяются без исключений и подавления ошибок.

## Definition of Done (DoD)

- [x] Предметный результат удовлетворяет **всем** предметным критериям и формату раздела «Что передать заказчику»; в README для каждого есть отдельное доказательство, исходные материалы сохранены. Доказательства: result/batch/, report.md и provenance; буквенные неоднозначности перечислены для ручной проверки.
- [x] Создана персональная GitHub-веха с результатом и критериями приёмки; это issue и нативно связанные подзадачи включены в неё, зависимости/владельцы/области записи определены и доступны по ссылкам. Доказательства: веха №10, #141–145, API evidence и таблица выше.
- [x] До реализации сохранён и проверен граф с минимум тремя типами субагентов, обоснованной параллельностью, наблюдаемыми условиями, ограниченными повторами, локальной приёмкой и эскалацией. Mermaid отрендерен и просмотрен; структурная проверка записана с её ограничениями. Доказательства: workflow.md и SVG/PNG/check.
- [x] Журнал и артефакты подтверждают реальные запуски `explorer`, `worker`, отдельного `reviewer`, успешную интеграцию и выбранный отрицательный сценарий; замечания reviewer исправлены либо явно оставлены как блокеры, локальный успех не объявлен при невыполненных критериях. Доказательства: run-log.md, reviewer-report.md, candidate/corrected и repair-report; независимый цикл accept → reject → исправление worker → accept, общий attempts=1.
- [ ] В одном PR в `main` переданы результат, исходники, `workflow.md`, брифы, `run-log.md`, отчёт reviewer и README с командами/порядком повторения. Ссылки на веху, подзадачи и PR добавлены в это issue; объединение PR оставлено преподавателю. Публикация после приёмки и Gitleaks.

Предметные DoD H04: тексты/таблица с page — result/batch; контрольные фрагменты/суммы — report; повреждённый файл/продолжение — errors.csv и test_batch; ручные страницы/ячейки — report/cells CSV/uncertainty; способ запуска и результаты — команды выше. OCR не представлен как точная транскрипция. Детектор таблиц рассчитан на одну линованную таблицу этого комплекта; произвольные PDF требуют новой предметной проверки.
