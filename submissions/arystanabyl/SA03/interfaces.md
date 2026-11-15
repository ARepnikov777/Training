# SA03 — утверждённые интерфейсы (Freeze)

Утверждено координатором 2026-11-15 10:56 +05:00 после `explore_check`.
Источник фактов — `research/process-notes.md`. Канонические команды ниже
координатор прогнал на свежей копии E01 в Windows PowerShell 5.1.26100:
S1 хэш 006F40B1… и размер 62162, S2 — 17 файлов, S4 — 12 файлов, сверка с
checksums.json — 12 проверено, 0 расхождений, сверка с expected.json на пустом
result даёт MISMATCH по трём категориям. Ветви Authoring читают только этот
файл и `research/`. Друг друга они не читают.

## Пути (относительно `submissions/arystanabyl/SA03/`)

| Владелец | Пишет | Формат |
|---|---|---|
| SA03-text | `text/steps.md` | Markdown, UTF-8 |
| SA03-figures | `figures/fig-01.svg` … `fig-06.svg`, `figures/fig-01.png` … `fig-06.png`, `figures/PROVENANCE.md` | SVG и PNG ровно 1600×900 |
| SA03-build | `guide/guide.html`, `guide/guide.pdf`, `guide/build.md`, `evidence/pages/page-N.png`, `evidence/layout-check.md` | HTML + PDF |
| SA03-review | `reviews/review-K.md` | Markdown |

## Шаги и рисунки

Порядок и смысл шагов — по `materials/H12/input/process.md`. Пример — комплект
E01. Рабочие папки в руководстве: `$HOME\Course\E01-kit` (распакованный
комплект, только чтение) и `$HOME\Course\E01-work` (рабочая копия).

| ID | Заголовок шага | Рисунок | Подпись (дословно) | Что обязательно изображено |
|---|---|---|---|---|
| S1 | Скачай ZIP задания из issue | fig-01 | Рисунок 1. Скачай E01.zip из issue и сверь SHA-256 | окно браузера со страницей issue и кнопкой «Скачать комплект» → стрелка → файл E01.zip → бейдж SHA-256 с галочкой |
| S2 | Распакуй в новую папку | fig-02 | Рисунок 2. Распакуй архив в новую папку E01-kit | E01.zip → стрелка → папка E01-kit, внутри вложенная папка E01 с README.md, input, checks |
| S3 | Прочитай README и правила | fig-03 | Рисунок 3. Прочитай README.md и input/rules.md | два документа README.md и rules.md, круг-лупа над rules.md, три категории documents · images · tables |
| S4 | Скопируй исходники в рабочую папку | fig-04 | Рисунок 4. Работай в копии E01-work, оригинал не трогай | папка E01-kit (с замком или отметкой «только чтение») → стрелка «копия» → папка E01-work |
| S5 | Выполни задание, результат отдельно | fig-05 | Рисунок 5. Результат — в отдельной папке result | E01-work/input/files (12 файлов) → стрелка → result с тремя папками documents, images, tables. Исходники остаются на месте |
| S6 | Проверь по checks и запиши повтор | fig-06 | Рисунок 6. Сверь result с checks/expected.json и запиши команду повтора | expected.json ↔ result, три зелёные галочки, документ README решения с блоком команды |

Все надписи на рисунках — на русском, кроме имён файлов. Высота кегля надписей
на холсте 1600×900 — не меньше 36 px, чтобы на странице PDF их можно было прочесть.
Одна палитра на все рисунки — цвета `elements.svg`: `#172b3a`, `#1d8794`,
`#f1b34a`, `#7063a3`, фон `#f5f7fa`. Галочка «OK» — `#1d8794`.

## Канонические команды (PowerShell 5.1, проверены)

```powershell
# S1
$zip = "$HOME\Downloads\E01.zip"
Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/ARepnikov777/Training/22aad84cc6666d2b0abca011e95a96b12e69c9cd/downloads/E01.zip" -OutFile $zip
(Get-FileHash $zip -Algorithm SHA256).Hash   # 006F40B11AB7BCFD7DF2A326D45E4D97787A940D47FBED5E39A19207F1BF1382

# S2
New-Item -ItemType Directory -Path "$HOME\Course\E01-kit" | Out-Null
Expand-Archive -Path $zip -DestinationPath "$HOME\Course\E01-kit"
(Get-ChildItem "$HOME\Course\E01-kit\E01" -Recurse -File).Count   # 17

# S3
Get-Content "$HOME\Course\E01-kit\E01\input\rules.md" -Encoding UTF8

# S4
Copy-Item -Path "$HOME\Course\E01-kit\E01" -Destination "$HOME\Course\E01-work" -Recurse
(Get-ChildItem "$HOME\Course\E01-work\input\files" -File).Count   # 12

# S6 — состав result по категориям
$exp = Get-Content "$HOME\Course\E01-work\checks\expected.json" -Encoding UTF8 -Raw | ConvertFrom-Json
foreach ($cat in 'documents','images','tables') {
  $act = @((Get-ChildItem "$HOME\Course\E01-work\result\$cat" -File).Name | Sort-Object)
  if (Compare-Object @($exp.$cat | Sort-Object) $act) { "$cat : РАСХОЖДЕНИЕ" } else { "$cat : OK" }
}
# S6 — исходники не изменились
$ref = Get-Content "$HOME\Course\E01-kit\E01\checksums.json" -Encoding UTF8 -Raw | ConvertFrom-Json
$ref.PSObject.Properties | Where-Object Name -like 'input/files/*' |
  Where-Object { (Get-FileHash (Join-Path "$HOME\Course\E01-work" $_.Name)).Hash.ToLower() -ne $_.Value } |
  ForEach-Object { "ИЗМЕНЁН: $($_.Name)" }   # пустой вывод = исходники целы
# S6 — содержимое result совпадает с исходниками (добавлено в v1.1)
(Get-ChildItem "$HOME\Course\E01-work\result" -Recurse -File).Count   # 12
Get-ChildItem "$HOME\Course\E01-work\result" -Recurse -File |
  Where-Object { (Get-FileHash $_.FullName).Hash -ne (Get-FileHash "$HOME\Course\E01-work\input\files\$($_.Name)").Hash } |
  ForEach-Object { "НЕ СОВПАДАЕТ: $($_.Name)" }   # пустой вывод = содержимое совпадает
```

### Изменения после Freeze

- **v1.1, 2026-11-15 11:03.** Причина: на `join_check` ветвь text сообщила, а координатор подтвердил, что
  канон S6 не покрывает п. 1 DoD E01 «содержимое файлов совпадает с исходниками».
  Добавлены две команды выше. Координатор прогнал их на ручной раскладке E01:
  12 файлов, пустой вывод; после порчи `table-1.csv` — `НЕ СОВПАДАЕТ: table-1.csv`.
  Таблица рисунков не менялась: fig-06 показывает сверку категорий, это не противоречит
  добавленной проверке.
- **v1.2, 2026-11-15 11:20, Fix круг 1 по `reviews/review-2.md`.**
  - R-2: третья рабочая папка `$HOME\Course\E01-solution` — скрипт решения и README решения.
    Она вне `E01-kit` и `E01-work`, поэтому не ломает проверку `result` и не удаляется при свежей копии.
    Скрипт запускается из неё и работает с `E01-work`; конкретную команду руководство не даёт (это решение E01).
  - R-1: все надписи внутри рисунков — не меньше 52 px на холсте 1600×900 (≈8 pt при ширине 90 мм);
    расширения на fig-03 — тёмным цветом `#172b3a`, не светло-бирюзовым.
  - R-3: кнопка на fig-01 — «Скачать полный комплект E01.zip», как в issue #7 и в тексте S1.

S5 руководство описывает как процесс: поручить агенту или написать скрипт по
rules.md и положить результат в `E01-work\result`. Готовый скрипт решения E01 в
руководство не входит: это решение другого задания.

## Структура `text/steps.md`

```
# <заголовок руководства>
## Введение            — аудитория, что понадобится (Windows, PowerShell 5.1, браузер), 6 шагов списком, без SSH/сервера/покупок
## S1 — <заголовок>    — по одному разделу на шаг, порядок S1…S6
**Зачем.** 1–2 предложения
**Сделай.** нумерованный список действий + блок ```powershell``` из канонических команд
**Проверь.** наблюдаемый результат (число, хэш, вывод)
**Если не так.** 1–3 типичные проблемы и их решение
Ссылка на рисунок: «см. рисунок N»
## Частые ошибки        — вложенная папка E01, кодировка UTF-8, правка оригинала, SHA не совпал
## Журнал прохождения   — шаблон таблицы: шаг, что сделано, наблюдаемый результат, ок/замечание
```

Объём `steps.md` — 900–1500 слов, чтобы вместе с шестью рисунками уложиться в
4–6 страниц.

## Разбивка страниц (A4 альбомная, 297×210 мм)

1. Обложка-введение: заголовок, аудитория, что понадобится, список S1–S6.
2. S1 и S2 с рисунками 1 и 2.
3. S3 и S4 с рисунками 3 и 4.
4. S5 и S6 с рисунками 5 и 6.
5. Частые ошибки и журнал прохождения.

Допустимо 4–6 страниц. Последний блок без `page-break-after`: проверено, что
лишний разрыв даёт пустую страницу.
