# [SA12] Lusinton4ik — реализовать браузерный сборщик с checkpoint

Родитель: #74. Веха SA12 · Lusinton4ik. Входы: #74, уточнения #49, закреплённый H13.zip SHA-256 278186e77b56325fbe1bd2e23dd4d317e162569ee1e1e6a0fbd7b311331637e7; plan.md и workflow.md.

Роль: worker. Ответственный: Lusinton4ik. Зависимости: Подзадача explore: подтверждённый контракт.
Ветка/worktree: C:/Users/lyudm/orca/workspaces/Training/SA12-worker / student/Lusinton4ik/SA12-worker.
Область записи относительно submissions/Lusinton4ik/SA12/: collector.py, tests/test_collector.py, evidence/collector-tests.txt, collector-report.md

Результат: Рабочий CLI collector.py и поведенческие тесты Red → Green.

## Ограничения

Только локальный синтетический стенд. Не менять materials/, downloads/, чужие решения. Сбор через DOM браузера; catalog.json/checks только для проверки после первого результата. Один владелец checkpoint. Субагентам запрещены делегирование, push, merge и внешняя публикация. N=2, общий T=120 минут, максимум 3 субагента.

## Definition of Done (DoD)

- [ ] DOM через Orca, атомарный checkpoint по id, журнал 503, новый процесс resume, idempotent rerun; RED и GREEN записаны.
- [ ] Отчёт содержит фактические команды, результаты и ссылки; координатор проверил артефакты.

## Точный технический контракт

Уточнение после реального первого результата: DOM P021 имеет None в ram_GB/ssd_GB/screen_inches.
Поздняя независимая проверка типов источника подтвердила nullable availability и эти 3 характеристики.
Сохранять Python None/JSON null, CSV пустое поле. Ключи обязательны, null разрешён только
для этих 4 полей. При наличии screen_inches сохранить float (включая 14.0), остальные числа int.
Исходное предположение о всегда числовых характеристиках ниже заменено этим уточнением.

Read this first: это требования реализации. Прочти также ../plan.md и explorer-report.md после его появления.
Работай в явном SA12-worker checkout; область записи только перечисленные файлы.
Исходники/отчёт сдавать без коммита: координатор проверяет diff и интегрирует файлы.
Не запускать реальный сбор: предметные запуски принадлежат координатору после интеграции.
Python: C:/Users/lyudm/AppData/Local/Temp/sa12-python-3.12.10/python.exe, UTF-8 mode.
Orca: C:/Users/lyudm/AppData/Local/Programs/orca/resources/bin/orca.exe, обычный exe.
Используй subprocess argv без shell=True и таймаут для каждого Orca вызова.
Перед реальным браузером загрузи orca skill и references/browser.md, если потребуется.
Известный API: `orca goto --page ID --url URL --json`; `orca eval --page ID --expression JS --json`.
eval JSON envelope: {ok:true,result:{result:"JSON-строка значения",origin:"…"}}.
goto JSON имеет effects или result, извлекай HTTP статус через browser performance navigation responseStatus.
Пример eval: ({status:performance.getEntriesByType('navigation')[0].responseStatus,rows:document.querySelectorAll('tr').length}).
Таблицу и карточки читай DOM после navigation, не fetch HTML и не catalog.json.
Карточки имеют dl/dt/dd; получить пары ключ-значение, числовые поля преобразовать в числа.
source_url — абсолютный URL реально открытой карточки. В JSON 10 полей каталога + source_url.

CLI: `collector.py --base-url URL --output DIR [--fail-third] [--page ID]`.
Создать Orca tab при отсутствии --page; каждый browser вызов адресует закреплённый page ID.
Файлы в DIR: products.json (массив), products.csv, checkpoint.json, errors.json, events.jsonl.
Checkpoint — один атомарно заменяемый файл, включает schema_version, base_url, records по id,
completed_pages, pending_pages, errors с URL/status/resolved, complete. Экспорт пересоздаётся из checkpoint.
При первом запуске --fail-third: сохранить страницы 1 и 2 по 10 карточек, запросить страницу 3 с fail=1,
зарегистрировать наблюдаемый HTTP 503 в checkpoint/errors/events и вернуть exit 2 (неполный).
Новый процесс без флага читает checkpoint, не повторяет completed_pages, собирает страницы 3–5,
помечает прежнюю ошибку resolved, возвращает 0 только при 50 уникальных id/5 страницах.
Повтор готового checkpoint — 0, данные не меняются и дубли не добавляются.
В events: timestamp UTC, PID/run_id, URL, status, количество, завершение страницы, resume, exit.
При неверном checkpoint явный ненулевой exit, без перезаписи исходных файлов. Атомарность progress,
resume и отсутствие двойной записи по id важнее универсальных абстракций.

TDD: сначала реальные behavioral tests с минимальным рабочим каркасом функций (не import error),
затем ожидаемый RED, затем реализация и GREEN. Сохрани точные команды и оба вывода в
evidence/collector-tests.txt. Тестируй через fake browser boundary 503 после 20, resume только 3–5,
повтор без дублей и отказ повреждённого checkpoint. Не копируй алгоритм в ожидания тестов.
Только stdlib unittest, никаких новых зависимостей. Бюджет 20 минут, deadline всего run 12:26:17Z.
Не переделегировать, не делать push/merge и внешние сообщения. Вернуть статус, список файлов,
точную команду тестов, число тестов, ограничения; полный отчёт в collector-report.md.
