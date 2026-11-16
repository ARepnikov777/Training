# Независимое ревью SA11

Агент `/root/sa11_review`, явный `agent_type=reviewer`, fork_turns=none. Исполнители и координатор код писали отдельно; reviewer только читал. Ниже его фактические выводы, сохранённые координатором.

## Review основного результата — 2026-11-16

**Verdict: accept основного предметного результата и кода для данного учебного комплекта.** Блокирующих дефектов не обнаружено. Отрицательный сценарий и публикация PR этим выводом не принимаются.

Проверенные факты:

- `result/batch/batch.json`: сохранены все 5 страниц с корректными `source/page`; единственная ошибка — `04-broken.pdf`, `continued=true`. Проверки полноты и источника выполняются до добавления страниц в пакет (`run_batch.py:51–59`).
- Независимо сверены SHA256 входов, архива и содержимое kit. Сохранённые source/normalized PNG совпали по пикселям с новым рендером соответствующих исходных PDF; текстовая страница совпала с текстовым слоем.
- Визуально просмотрены три страницы скана и таблица. Проверены 30 связей ячеек с raw JSON и сами значения. Арифметика верна: 20 предметов, 128000 KZT, произведения всех четырёх строк совпадают.
- Ошибки OCR раскрыты в `report.md:21–25`: А/A, №1/Nel, ложные «В»/«ВО» в пустых ячейках. Raw и verified разделены; verified исправляет только две указанные ячейки. Числовая сверка не выдана за точную транскрипцию.
- В исполняемом коде нет чтения checks или подстановки контрольных ответов.
- Независимый повтор contract/batch/text: **29 passed**, exit 0. Первый запуск получил ошибки доступа pytest к temp; разрешённый повтор прошёл. Полный OCR повторно не запускался; сохранённый общий протокол подтверждает 40 passed.

Пробелы доказательств, не блокирующие этот этап: установка Python-зависимостей в новой venv не проверена, что честно указано в `README.md:44`; Linux отдельно не проверен. Хронология чтения checks подтверждается журналом и отчётами исполнителей, но одним итоговым diff её независимо доказать нельзя.

Ревью ограничено основным результатом SA11. Отрицательный сценарий, финальная приёмка всего упражнения, Gitleaks перед публикацией и PR остаются отдельными этапами. Файлы не изменял.

## Negative_review — фактическое отклонение

**Negative_review: reject.**

В `submissions/EnterFC/SA11/evidence/negative/candidate.json:4` запись `pages[0]` для `01-text.pdf` лишена обязательного поля `page`. Это нарушает контракт и теряет явную привязку текста к странице. По исходному PDF ожидается `[1]`, кандидат содержит `[None]`. Остальные документы имеют ожидаемые номера `[1,2,3]` и `[1]`.

Фактически выполненная команда из корня checkout:

```powershell
../Training-H04/submissions/EnterFC/H04/.venv/Scripts/python.exe -c "import json,sys; from pathlib import Path; r=Path('submissions/EnterFC/SA11'); sys.path.insert(0,str(r.resolve())); from src.contract import validate_batch; validate_batch(json.loads((r/'evidence/negative/candidate.json').read_text('utf-8')))"
```

Результат: **exit 1**.

```text
ValueError: page: expected fields source, page, method, text, tables, uncertainty
```

Для исправления требуется восстановить `pages[0].page = 1` по исходному PDF и повторить проверку. Файлы не изменял; основной accept сохраняется.

## Final_review — исправление принято

**Final_review: accept исправления отрицательного сценария.** Предметные критерии основного результата и цикл reject → исправление → accept подтверждены для локального `Done_accepted`.

Независимая проверка установила:

- `evidence/negative/corrected.json` проходит `validate_batch`.
- Единственное смысловое изменение относительно `candidate.json` — добавление `pages[0].page = 1`; остальные поля сохранены.
- Исправленный JSON семантически равен принятому `result/batch/batch.json`.
- Исходный `01-text.pdf` содержит одну страницу; её текст полностью совпадает с исправленной записью.
- Привязки всех документов соответствуют исходникам: `[1]`, `[1,2,3]`, `[1]`. Сохранены 5 страниц и единственная ошибка `04-broken.pdf`, `continued=true`.
- Исходный кандидат продолжает отклоняться из-за отсутствия `page`.

Повторяемая команда из корня checkout:

```powershell
../Training-H04/submissions/EnterFC/H04/.venv/Scripts/python.exe -c "import json,sys; from pathlib import Path; r=Path('submissions/EnterFC/SA11'); sys.path.insert(0,str(r.resolve())); from src.contract import validate_batch; c=json.loads((r/'evidence/negative/candidate.json').read_text('utf-8')); x=json.loads((r/'evidence/negative/corrected.json').read_text('utf-8')); b=json.loads((r/'result/batch/batch.json').read_text('utf-8')); validate_batch(x); assert x==b; assert x['pages'][0].pop('page')==1 and x==c; print('PASS: contract, main batch equality, only page=1 restored')"
```

Фактическая независимая проверка завершилась **exit 0**; вывод: `CORRECTED CONTRACT: ACCEPT`, `CANDIDATE CONTRACT: REJECT`, `CORRECTED == MAIN BATCH: true`.

Файлы не изменял. Сохраняются ограничения основного ревью: новая Python venv и Linux отдельно не проверены. Публикация PR, Gitleaks перед публикацией и merge в этот вывод не входят.
