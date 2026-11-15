# SA06 — каталог «Точка идеи»

Задание: [#57](https://github.com/ARepnikov777/Training/issues/57). Исполнитель: Vrnur. [Веха SA06 · Vrnur](https://github.com/ARepnikov777/Training/milestone/8). Локальная приёмка `Done_accepted` подтверждена координатором и независимым reviewer; merge и приёмка преподавателем отдельно.

Результат: [трёхстраничный PDF](result/catalog.pdf), [ведомость сверки](result/reconciliation.csv), редактируемые [сборка](build_catalog.py) и [валидатор](validate_catalog.py). Формат A4, карточки 2+2+1. Пять названий, описаний, цен KZT и изображений перенесены из CSV без рекламных дополнений.

## Повторение

Python 3.12+, зависимости [requirements.txt](requirements.txt). В установленном окружении:

```sh
cd submissions/Vrnur/SA06
python3 -m venv /tmp/sa06-venv
/tmp/sa06-venv/bin/pip install -r requirements.txt
/tmp/sa06-venv/bin/python build_catalog.py
/tmp/sa06-venv/bin/python validate_catalog.py
/tmp/sa06-venv/bin/python -m unittest discover -s tests -v
python3 tools/graph_check.py workflow.md
pdftoppm -scale-to 1400 -png result/catalog.pdf /tmp/sa06-page
```

На машине выполнения использован готовый Python `/Users/arnursain/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3`, дополнительных Python-пакетов не устанавливалось. Чистая пересборка из отдельной временной папки с копией исходников проверена: [команды и exit codes](evidence/coordinator-checks.txt). Исходные шрифты входят в fonts/. Отсутствие сетевого доступа не мешает сборке при уже установленных зависимостях. Валидатор `--input` должен получать доверенные неизменённые входы; проверка пикселей не устанавливает семантику произвольного нового изображения, поэтому исходные пять PNG также проверены визуально.

## Источники и сохранность

Исходный [комплект H11](source/H11/README.md) извлечён из downloads/H11.zip. SHA256 ZIP: `2a9f183818f89c5b37282d57b6d411e64ef5f37dd253d273fd229e562503f113`, совпадает с [сохранённым #47](source/issue-47.md). Все 15 файлов совпадают побайтно с ZIP, 14 внутренних SHA256 из checksums.json подтверждены координатором. [Полное условие SA06](source/issue-57.md) сохранено. [Происхождение изображений и шрифтов](materials-provenance.md), [лицензия шрифтов](fonts/LICENSE-DejaVu.html), [CC0 входов](source/H11/input/LICENSE.md). materials/, downloads/ и чужие решения не изменены.

## Граф, задачи и реальные роли

[Граф](workflow.md), [рендер](evidence/workflow.png), [структурная проверка](evidence/graph-check.txt), [preflight и ограничения проверки](evidence/preflight.md), [декомпозиция](decomposition.md), [журнал](run-log.md), [брифы](briefs/), [идентификаторы запусков](evidence/native-agents.json).

Шесть нативных sub-issues: [граф #124](https://github.com/ARepnikov777/Training/issues/124), [данные #125](https://github.com/ARepnikov777/Training/issues/125), [изображения #126](https://github.com/ARepnikov777/Training/issues/126), [сборка #127](https://github.com/ARepnikov777/Training/issues/127), [ревью #128](https://github.com/ARepnikov777/Training/issues/128), [сдача #129](https://github.com/ARepnikov777/Training/issues/129). Через API подтверждены нативные связи с #57, milestone 8, assignee Vrnur и subagents у всех. N=3 исправления, T до 17:35 15.11.2026 Asia/Almaty, не более 3 субагентов; параллельно два read-only explorer, предметный worker один. Native explorer/worker/reviewer реально запускались с явным agent_type и без model override; [отчёты данных](evidence/explorer-data.md) и [изображений](evidence/explorer-images.md). docs_researcher доступен в интерфейсе, не требовался и не запускался.

## Предметные критерии H11 и SA06

- [x] Все товары представлены в PDF ровно по одному разу с верными изображением, названием, описанием и ценой — [ведомость 5/5 OK](result/reconciliation.csv), пиксельная и текстовая проверка [exit 0](evidence/coordinator-checks.txt).
- [x] Каталог имеет единый стиль, читаемые подписи; нет обрезанного текста, наложений и потерянных изображений — [визуальная проверка координатора](evidence/coordinator-visual.md), рендеры [1](evidence/catalog-page-1.png), [2](evidence/catalog-page-2.png), [3](evidence/catalog-page-3.png).
- [x] Проверена каждая страница и соответствие каждой карточки исходной строке CSV — [визуальная проверка пяти карточек](evidence/coordinator-visual.md), [исходный CSV](source/H11/input/products.csv).
- [x] Переданы PDF, редактируемый исходник/сценарий сборки и список использованных материалов с происхождением — ссылки на результат выше, [происхождение](materials-provenance.md). [pdfinfo](evidence/pdfinfo.txt) подтверждает A4 / 3 страницы.

## Definition of Done из #57

- [x] Предметный результат удовлетворяет **всем** предметным критериям и формату раздела «Что передать заказчику»; в README для каждого есть отдельное доказательство, исходные материалы сохранены. Доказательства — четыре пункта выше и source/.
- [x] Создана персональная GitHub-веха с результатом и критериями приёмки; это issue и нативно связанные подзадачи включены в неё, зависимости/владельцы/области записи определены и доступны по ссылкам. [Декомпозиция](decomposition.md), [сохранённые ID](evidence/github.json), веха и шесть ссылок выше.
- [x] До реализации сохранён и проверен граф с минимум тремя типами субагентов, обоснованной параллельностью, наблюдаемыми условиями, ограниченными повторами, локальной приёмкой и эскалацией. Mermaid отрендерен и просмотрен; структурная проверка записана с её ограничениями. [Граф](workflow.md), [preflight](evidence/preflight.md), [журнал](run-log.md).
- [x] Журнал и артефакты подтверждают реальные запуски `explorer`, `worker`, отдельного `reviewer`, успешную интеграцию и выбранный отрицательный сценарий; замечания reviewer исправлены либо явно оставлены как блокеры, локальный успех не объявлен при невыполненных критериях. [Независимый отчёт](reviewer-report.md), [отрицательный прогон](evidence/negative-report.json) и [команды](evidence/negative-commands.txt) подтверждают выполнение; замечаний нет, исправления не требовались.
- [x] В одном PR в `main` переданы результат, исходники, `workflow.md`, брифы, `run-log.md`, отчёт reviewer и README с командами/порядком повторения. Ссылки на веху, подзадачи и PR добавлены в это issue; объединение PR оставлено преподавателю. [PR #137](https://github.com/ARepnikov777/Training/pull/137), [комментарий сдачи в #57](https://github.com/ARepnikov777/Training/issues/57#issuecomment-6893410776), [проверенное живое состояние](evidence/github-verified.json).

## Проверки и ограничения

[Red: exit 1](evidence/test-red.txt) из-за ещё не реализованного поведения, затем [Green: exit 0](evidence/test-green.txt). Тест включает сборку, проверку, подмену P01 изображением P02 на временной копии, отказ валидатора и восстановление. Отдельный контроль координатора выполнен после положительного reviewer: [плохой PDF](evidence/negative-bad.pdf) отклонён exit 1 с P01 image differs; [восстановленный PDF](evidence/negative-restored.pdf) принят exit 0. [Рендер подмены](evidence/negative-page1.png) просмотрен координатором и reviewer. [JSON](evidence/negative-report.json) подтверждает неизменность финального PDF. Повторно reviewer подтвердил эту ветвь. Полный тестовый набор общего репозитория не запускался: общие инструменты и материалы не менялись. Независимое ревью положительное, [отчёт](reviewer-report.md); проверки секретов выполняются перед каждым коммитом и push, результаты указаны в [журнале](run-log.md) и [PR #137](https://github.com/ARepnikov777/Training/pull/137). Внешней рассылки, сайта или production нет.

Рендер графа выполнен Mermaid CLI 12.2.0 (зависимость установлена только в /tmp):

```sh
npm install --prefix /tmp/sa06-mermaid @mermaid-js/mermaid-cli@12.2.0
/tmp/sa06-mermaid/node_modules/.bin/mmdc -i evidence/workflow.mmd -o /tmp/sa06-workflow.png -p evidence/puppeteer.json --size 1800
```

В puppeteer.json указан локальный Chrome на macOS; на другой машине замените путь своим браузером. Это вспомогательный инструмент проверки, не зависимость сборки PDF. graph_check.py сохранён из mbk-dev/ai-learning/skills/agent-behavior-graph/scripts/graph_check.py (2026-11-15); ограничений полноты checker не скрываем. Финалы недоступного входа/таймаута/эскалации и петля исправлений в этом успешном запуске не проходились. attempts=0/3, recoveries=0/1, общий срок не сбрасывался.
