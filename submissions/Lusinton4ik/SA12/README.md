# SA12 — восстановимый браузерный сбор каталога

Задание: [#74](https://github.com/ARepnikov777/Training/issues/74), исполнитель Lusinton4ik.
Сдача: [единый draft PR #139 в main](https://github.com/ARepnikov777/Training/pull/139).
Локальная приёмка завершена; преподавательская приёмка и merge остаются человеку.
Предметные уточнения: [H13 #49](https://github.com/ARepnikov777/Training/issues/49).
[Веха SA12](https://github.com/ARepnikov777/Training/milestone/6), нативные подзадачи
[#110](https://github.com/ARepnikov777/Training/issues/110),
[#111](https://github.com/ARepnikov777/Training/issues/111),
[#112](https://github.com/ARepnikov777/Training/issues/112),
[#113](https://github.com/ARepnikov777/Training/issues/113),
[#114](https://github.com/ARepnikov777/Training/issues/114).

## Результат и источники

`collector.py` собирает таблицы и карточки через DOM Orca, сохраняет прогресс по id
в атомарном `result/checkpoint.json` и экспортирует `products.json`, `products.csv`,
`errors.json`, `events.jsonl`. `validate.py` независимо сравнивает готовые JSON/CSV
с 50 ожидаемыми id и всеми исходными полями. Он не импортирует сборщик.
Итог: 50 уникальных товаров, JSON и CSV полностью совпали с эталоном по всем полям.
Повторный запуск сохранил SHA-256 данных и checkpoint. Контролируемое удаление P050
отклонено независимой проверкой, восстановленная копия принята.

Закреплённый [H13.zip](sources/H13.zip) распакован в `kit/H13/`, SHA-256
`278186e77b56325fbe1bd2e23dd4d317e162569ee1e1e6a0fbd7b311331637e7`.
Исходники не исправлялись. Снимки постановок и уточнений: `sources/issue-74.json`,
`sources/issue-49.json`; правила курса: `sources/course-AGENTS.md`.
Полный JSON каталога/checks разрешены только для сверки после первого результата.

## Как воспроизвести

Нужны Python 3.10+ и работающий Orca с доступным встроенным браузером.
В данном запуске использован временный официальный Python 3.12.10 embedded,
поскольку `python` в PATH оказался системным псевдонимом без runtime.
В PowerShell вместо `python` можно использовать полный путь к рабочему python.exe.
Фактические команды/версии сохранены в evidence и run-log.
Сторонние Python-пакеты не нужны. Пример ниже из этой папки (`SA12`).

1. В отдельном терминале запустите неизменённый стенд:

   ```powershell
   python -X utf8 kit/H13/input/site/serve.py --port 8875
   ```

2. Из новой рабочей папки/с новым `--output` запустите сбор:

   ```powershell
   python -X utf8 collector.py --base-url http://127.0.0.1:8875 --output result --fail-third
   ```

   Ожидается **exit 2**: страницы 1–2 сохранены (20 товаров), HTTP 503 страницы 3
   записан, процесс завершён. Это ожидаемый неполный результат, не успешный полный сбор.
   Сохраните копию checkpoint до продолжения; серверный `_state.json` прогрессом не является.

3. Новым процессом продолжите тот же output без флага отказа:

   ```powershell
   python -X utf8 collector.py --base-url http://127.0.0.1:8875 --output result
   ```

   Ожидается exit 0 и 50 уникальных id; страницы 1–2 не собираются снова,
   ошибка страницы 3 остаётся в журнале с `resolved: true`.

   Null в исходном стенде отображается строкой `None`: в результате это JSON null
   и пустая CSV-ячейка. Ключи nullable-полей сохраняются. При восстановлении старого
   checkpoint сборщик исправляет собственную прежнюю сериализацию availability.

4. Повторите последнюю команду: exit 0, данные не меняются и дубли не добавляются.
   Встроенные события содержат UTC, PID и run_id каждого процесса.

5. После получения результата выполните обе независимые сверки:

   ```powershell
   python -X utf8 validate.py --data result/products.json --expected-ids kit/H13/checks/expected-ids.json --catalog kit/H13/input/site/catalog.json
   python -X utf8 validate.py --data result/products.csv --expected-ids kit/H13/checks/expected-ids.json --catalog kit/H13/input/site/catalog.json
   python -X utf8 -m unittest discover -s tests -v
   python -X utf8 sources/graph_check.py workflow.md
   ```

   Ожидается `ok: true`, `count: 50`, `unique_count: 50`, `errors: []` и exit 0.
   Validator на копии с удалённой записью или дубликатом обязан вернуть exit 1.
   Не удаляйте действительный результат для отрицательного сценария.

При незавершённой операции сначала проверьте процессы, checkpoint и events.
Повреждённый или чужой checkpoint сборщик отклоняет без перезаписи. Для другого
порта нужен новый output: base_url входит в контракт checkpoint.
Сервер останавливается Ctrl+C в его терминале.

## Граф, исполнители и проверки

[workflow.md](workflow.md) сохранён до реализации, отрендерен и просмотрен:
[состояния PNG](evidence/workflow.png), [SVG](evidence/workflow.svg),
[зависимости PNG](evidence/dependencies.png). [Структурная проверка](evidence/graph-check.txt)
не заменяет смысловую проверку, контроль счётчиков и фактические evidence.
[Первый рендер до реализации](evidence/workflow-before-build.png) и
[метаданные времени](evidence/graph-render-provenance.json): 10:28:53Z, до создания
collector.py в worktree (10:33:35Z). Полная версия PNG улучшает масштаб изображения.
[plan.md](plan.md), [briefs](briefs/), [run-log.md](run-log.md),
[свидетельство ролей](evidence/agents.json).

- `explorer` `/root/sa12_explore`: read-only контракт и смысловая проверка графа,
  [отчёт](explorer-report.md); координатор сверил ссылки на строки.
- `worker` `/root/sa12_collector`: только сборщик/его тесты/отчёт в SA12-worker,
  [отчёт](collector-report.md), [RED/GREEN](evidence/collector-tests.txt).
- Другой `worker` `/root/sa12_validator`: отдельный валидатор и синтетические тесты
  в SA12-validator, [отчёт](validator-report.md), [RED/GREEN](evidence/validator-tests.txt).
- `reviewer` `/root/sa12_review`: отдельная read-only проверка; первичное замечание
  о loading:true сохранено в [первом ревью](reviewer-collector-initial.md).
  [Scoped loading review](reviewer-collector-fix.md),
  [nullable collector review](reviewer-null-collector.md),
  [nullable validator review](reviewer-null-validator.md) — PASS.
  [Итоговое независимое ревью](reviewer-report.md): локальный spec PASS, quality PASS,
  открытых замечаний нет; публикацию подтверждает координатор отдельно.
- Координатор интегрирует разрешённые файлы, повторяет проверки и владеет
  единственным реальным браузерным сбором/checkpoint. Субагенты не публикуют и не переделегируют.

## Definition of Done SA12 — дословно из issue

- [x] Предметный результат удовлетворяет **всем** предметным критериям и формату раздела «Что передать заказчику»; в README для каждого есть отдельное доказательство, исходные материалы сохранены.
- [x] Создана персональная GitHub-веха с результатом и критериями приёмки; это issue и нативно связанные подзадачи включены в неё, зависимости/владельцы/области записи определены и доступны по ссылкам.
- [x] До реализации сохранён и проверен граф с минимум тремя типами субагентов, обоснованной параллельностью, наблюдаемыми условиями, ограниченными повторами, локальной приёмкой и эскалацией. Mermaid отрендерен и просмотрен; структурная проверка записана с её ограничениями.
- [x] Журнал и артефакты подтверждают реальные запуски `explorer`, `worker`, отдельного `reviewer`, успешную интеграцию и выбранный отрицательный сценарий; замечания reviewer исправлены либо явно оставлены как блокеры, локальный успех не объявлен при невыполненных критериях.
- [x] В одном PR в `main` переданы результат, исходники, `workflow.md`, брифы, `run-log.md`, отчёт reviewer и README с командами/порядком повторения. Ссылки на веху, подзадачи и PR добавлены в это issue; объединение PR оставлено преподавателю.

| Критерий SA12 | Фактический результат и доказательство |
|---|---|
| Предметный результат / исходники | `result/products.json`, `products.csv`, checkpoint/errors/events; предметные доказательства ниже; [11 исходных файлов совпали с ZIP](evidence/source-integrity.json) |
| Персональная веха / native sub-issues | [Веха](https://github.com/ARepnikov777/Training/milestone/6), #110–#114; [parent](evidence/tracker-parent.json), [native children](evidence/tracker-children.json); входы/зависимости/владельцы/files/branches в briefs |
| Граф до реализации / пределы | workflow/plan, ранний Explore PASS в run-log, `graph-check.txt`, PNG/SVG; N=2, T=120мин от 10:26:17Z, до3 агентов; кодовые writers последовательно |
| Реальные роли / интеграция / отрицательный сценарий | `agents.json`, run-log, отчёты и scoped review; [27 tests OK](evidence/integrated-tests.txt), negative validation ниже; итоговое независимое ревью дополняет этот набор |
| Единый PR / ссылки / без merge | [PR139](https://github.com/ARepnikov777/Training/pull/139), base main, head student/Lusinton4ik/SA12, OPEN draft/MERGEABLE; [обратные ссылки в #74](https://github.com/ARepnikov777/Training/issues/74#issuecomment-6893546899), [проверка публикации](evidence/publication.json). Merge не выполнялся |

## Предметный DoD H13 — дословно из issue

- [x] Выполнение прервано после сохранения части записей и продолжено из сохранённого состояния; есть доказательства обоих запусков.
- [x] При доступности всех целевых страниц итог содержит ровно 50 уникальных записей без пропусков.
- [x] Недоступные страницы перечислены в отчёте, частичный набор не объявлен полным; после восстановления страницы пропуск восполнен.
- [x] Повторный запуск не дублирует уже собранные записи; переданы данные, состояние и инструкция воспроизведения.

| Критерий H13 | Фактический результат и доказательство |
|---|---|
| Прерывание и новый процесс | [PID25520 exit2, count20](evidence/run-1.json), [checkpoint20](evidence/checkpoint-after-20.json); [PID25248 exit0, count50](evidence/run-3-resumed.json) |
| 50 без пропусков | [JSON: 50/50, errors=[]](evidence/validation-json.json), [CSV: 50/50, errors=[]](evidence/validation-csv.json); сверены все исходные поля и URL карточки |
| Недоступность и восстановление | [HTTP503](evidence/http-503.json), [скриншот](evidence/http-503.png), [HTTP200 страницы3](evidence/page-3-restored.json), [скриншот](evidence/page-3-restored.png); `result/errors.json` содержит прежний503 с resolved=true. checkpoint20 имеет complete=false |
| Повтор без дублей / переданные данные | [Повтор exit0 и неизменные hashes](evidence/run-4-idempotent.json), `result/` и инструкция выше |

Дополнительно: [испорченная копия49](evidence/negative-missing.json) получила
[exit1, missing P050](evidence/negative-missing-validation.json);
[исправленная копия50](evidence/negative-repaired.json) получила
[exit0](evidence/negative-repaired-validation.json). Запись восстановлена из собственного
браузерного результата. Полнота частичного набора не заявлялась.

Первое продолжение до исправления null завершилось явной ошибкой без потери20 записей:
[run-2-null-failure.json](evidence/run-2-null-failure.json),
[наблюдение DOM P021](evidence/null-card-observation.json),
[поздняя проверка схемы](evidence/schema-verification.json).
Ошибка исправлена по RED→GREEN, затем ревью приняло исправление. Этот неуспешный
запуск сохранён в журнале; успешное продолжение — run-3-resumed.json.
Повтор из полностью чистой рабочей папки завершён: отдельные PID12748/37464/12368,
exit2/0/0, 20/50/50, обе сверки JSON/CSV PASS. [Отчёт и точные команды](evidence/clean-replay.json),
[события](evidence/clean-replay-events.jsonl), [финальный checkpoint](evidence/clean-replay-checkpoint.json).
SHA-256 collector совпал с финальным исходником; в validator после прогона удалена
только пустая строка EOF, равенство AST подтверждено, обе сверки повторены уже его
финальным файлом, SHA-256 обновлён в отчёте. Это форматирование без изменения логики.

## Ограничения

Сборщик предназначен для данного синтетического пятистраничного стенда, не для
произвольных сайтов. Путь Orca в collector.py сейчас соответствует среде исполнителя;
на другой машине потребуется указать её путь. Изображения SVG/PNG графа доступны
офлайн, повторный рендер HTML использует Mermaid CDN.
Общие проверки организаторского проекта pytest/ruff не выполнялись для сдачи SA12;
попытка worker запустить pytest показала отсутствие пакета. Проверяются собственные
поведенческие unittest и реальный браузерный сценарий.

Gitleaks истории вернул exit 1 на SHA-256 исходного H09; контрольная сумма
пересчитана и совпала с файлом, см. [диагностику](evidence/gitleaks-history.md).
Это не зелёный результат сканера; исключения и подавление не применялись.
Staged scan завершился **exit 0, no leaks found**:
[лог](evidence/gitleaks-staged.txt); после изменения индекса проверка повторяется.
Преподавательская приёмка и merge не выполняются агентом.
