<!-- Отчёт explorer (SA03-1, тип Explore), сохранён координатором из сообщения агента без смысловых правок. 2026-11-15 10:52 +05:00 -->

# Заметки по процессу H12 и комплекту E01 (explorer, SA03-1)

Корень: `C:/Users/abylaikhan.a/Training-SA03/integration` (дальше пути даны относительно него). Всё ниже я только читал. Решение E01 не запускал, на GitHub выполнял только `gh issue view 7` и `gh issue view 48`.

Обозначения:
- **[Факт]** — значение взято из источника или проверено командой только для чтения.
- **[Предложение]** — команда PowerShell, которую можно дать в руководстве. Я её **не запускал** (работал в режиме только чтения). Синтаксис стандартный для Windows PowerShell 5.1, но перед публикацией её нужно прогнать.

---

## 0. Ключевые факты о комплекте E01

| Факт | Значение | Источник |
|---|---|---|
| Ссылка «Скачать полный комплект E01.zip» | `https://raw.githubusercontent.com/ARepnikov777/Training/22aad84cc6666d2b0abca011e95a96b12e69c9cd/downloads/E01.zip` | issue #7, раздел «Готовые материалы» |
| Ссылка «Открыть инструкцию» | `https://github.com/ARepnikov777/Training/blob/22aad84cc6666d2b0abca011e95a96b12e69c9cd/materials/E01/README.md` | issue #7 |
| SHA-256 ZIP | `006f40b11ab7bcfd7df2a326d45e4d97787a940d47fbed5e39a19207f1bf1382` | issue #7 |
| Совпадает ли с локальной копией | Да: `certutil -hashfile downloads/E01.zip SHA256` выдал тот же хеш | проверка `downloads/E01.zip` |
| Размер ZIP | 62 162 байт | `ls -la downloads` |
| Ссылка закреплена за коммитом | `22aad84` («Добавить полные материалы для 45 учебных заданий»), это последний коммит, менявший `downloads/E01.zip` | `git log -- downloads/E01.zip`, issue #7 |
| Корневая папка внутри ZIP | **Есть: `E01/`**. Все 17 записей начинаются с `E01/`, отдельных записей-каталогов в архиве нет | `zipfile.ZipFile('downloads/E01.zip').infolist()` |
| Заголовок комплекта | `[E01] Порядок в папке` (README и manifest); заголовок issue #7 — «[E01] Разложить файлы по категориям без изменения исходников» | `materials/E01/README.md`, `manifest.json`, issue #7 |
| Ориентир времени | 15–25 минут, уровень easy | issue #7 |

**Содержимое ZIP (17 файлов, размер в байтах)** — источник `downloads/E01.zip`:

```
E01/README.md                  2726
E01/checks/expected.json        291
E01/checksums.json             1522
E01/input/files/manual.pdf    26845
E01/input/files/notes.md          8
E01/input/files/picture-1.png 12262
E01/input/files/picture-2.png 12057
E01/input/files/picture-3.png 12181
E01/input/files/picture-4.png 12571
E01/input/files/readme.txt        8
E01/input/files/record.json      10
E01/input/files/table-1.csv      14
E01/input/files/table-2.csv      14
E01/input/files/table-3.csv      14
E01/input/files/table-4.csv      14
E01/input/rules.md              298
E01/manifest.json               853
```

Тот же состав лежит в `materials/E01/`. Для 16 файлов в `materials/E01/checksums.json` записаны SHA-256; самого `checksums.json` в этом списке нет. Я выборочно сверил `README.md`, `input/rules.md`, `checks/expected.json`, `manifest.json` и `input/files/table-1.csv` через `sha256sum` — все пять совпали с `checksums.json`.

---

## 1. Шаги S1–S6

### S1. Скачай ZIP задания из issue
- **Что делает слушатель.** Открывает issue #7 (`https://github.com/ARepnikov777/Training/issues/7`), в разделе «Готовые материалы» нажимает «Скачать полный комплект E01.zip» и сверяет SHA-256. *Источник: `materials/H12/input/process.md` п.1; issue #7.*
- **Имена.** Файл `E01.zip`. *Источник: issue #7.*
- **[Предложение] PowerShell:**
  ```powershell
  $zip = "$HOME\Downloads\E01.zip"
  Invoke-WebRequest -Uri "https://raw.githubusercontent.com/ARepnikov777/Training/22aad84cc6666d2b0abca011e95a96b12e69c9cd/downloads/E01.zip" -OutFile $zip
  (Get-FileHash $zip -Algorithm SHA256).Hash
  ```
- **Как понять, что шаг выполнен.** Файл весит 62 162 байт. `Get-FileHash` выводит `006F40B11AB7BCFD7DF2A326D45E4D97787A940D47FBED5E39A19207F1BF1382` — PowerShell печатает хеш в верхнем регистре, значение то же, что в issue. *Источник: issue #7; хеш и размер проверены на `downloads/E01.zip`.*
- **Замечание.** В issue сказано: «просмотр файлов в GitHub не заменяет скачивание». Кроме того, уточнения из issue нужно сохранить вместе с комплектом и README решения: «Уточнения в этом issue — часть условий: сохрани их вместе с README решения». *Источник: issue #7.*

### S2. Распакуй в новую папку
- **Что делает слушатель.** Создаёт новую пустую папку и распаковывает в неё ZIP. *Источник: process.md п.2; `materials/E01/README.md` «Как начать»: «Распакуй ZIP в отдельную папку».*
- **Структура после распаковки.** Внутри появляется вложенная папка `E01\`, а в ней `README.md`, `manifest.json`, `checksums.json`, `input\rules.md`, `input\files\` (12 файлов) и `checks\expected.json`. *Источник: список ZIP.*
- **[Предложение] PowerShell:**
  ```powershell
  New-Item -ItemType Directory -Path "$HOME\Course\E01-kit" | Out-Null
  Expand-Archive -Path "$HOME\Downloads\E01.zip" -DestinationPath "$HOME\Course\E01-kit"
  Get-ChildItem "$HOME\Course\E01-kit\E01" -Recurse -File | Measure-Object   # ожидаемо Count = 17
  ```
- **Как понять, что шаг выполнен.** Есть `...\E01-kit\E01\README.md`, найдено 17 файлов, в `input\files` их 12. *Источник: список ZIP.*

### S3. Прочитай README и input/rules.md или input/SPEC.md
- **Что делает слушатель.** Читает `E01\README.md`, `E01\input\rules.md`, а также `manifest.json`. README комплекта просит прочитать «все файлы .md/.json в input». Кроме того, слушатель читает DoD и уточнения в issue #7. *Источник: process.md п.3; `materials/E01/README.md`.*
- **Факт.** В E01 есть только `input/rules.md`, **файла `input/SPEC.md` нет**. *Источник: `find materials/E01`, список ZIP.*
- **[Предложение] PowerShell:**
  ```powershell
  Get-Content "$HOME\Course\E01-kit\E01\README.md" -Encoding UTF8
  Get-Content "$HOME\Course\E01-kit\E01\input\rules.md" -Encoding UTF8
  ```
- **Ловушка с кодировкой** (вывод мой, не из источника). Файлы набраны кириллицей в UTF-8 без BOM: `rules.md` начинается с байтов `d0 a0`, `README.md` — с `# [`. Windows PowerShell 5.1 без `-Encoding UTF8` прочитает их в кодировке ANSI и покажет кракозябры. Можно и просто открыть файлы в Блокноте или VS Code.
- **Как понять, что шаг выполнен.** Слушатель может пересказать правило: «.txt/.md/.json/.pdf → documents; .png → images; .csv → tables; input/files не менять; result создаётся отдельно; все 12 файлов учтены». *Источник: `materials/E01/input/rules.md`.*

### S4. Скопируй исходники в отдельную рабочую папку
- **Что делает слушатель.** Копирует распакованный комплект в отдельную рабочую папку и работает только с этой копией. *Источники: process.md п.4; README E01: «Работай в отдельной рабочей папке»; issue #7: «Исходные файлы сохраняйте без перезаписи; работу выполняйте на копии».*
- **Куда класть.** По issue #7: «копии проекта, результат и evidence сохраняй в `submissions/LOGIN/E01/`». В README репозитория, раздел «2. Выполни и проверь»: «Работай с копией исходных материалов. Выданные `materials/`, `downloads/` … не изменяй». Если руководство пишется для внешнего читателя без git, подойдёт любая отдельная папка — это мой вывод.
- **[Предложение] PowerShell:**
  ```powershell
  Copy-Item -Path "$HOME\Course\E01-kit\E01" -Destination "$HOME\Course\E01-work" -Recurse
  Get-ChildItem "$HOME\Course\E01-work\input\files" -File | Measure-Object   # Count = 12
  ```
  Чтобы потом доказать, что исходники не изменились, стоит снять «снимок» хешей до работы. Для этого есть готовый эталон `checksums.json`:
  ```powershell
  $ref = Get-Content "$HOME\Course\E01-kit\E01\checksums.json" -Encoding UTF8 -Raw | ConvertFrom-Json
  ```
- **Как понять, что шаг выполнен.** В рабочей папке лежат те же 12 файлов в `input\files`, а распакованный комплект (`E01-kit`) больше не трогается.

### S5. Выполни задание, сохрани результат отдельно от исходников
- **Что делает слушатель.** Пишет (или поручает агенту) скрипт, который **копирует** 12 файлов из `input/files` в папки `documents`, `images`, `tables` внутри отдельной папки `result`. *Источники: README E01 «Что сделать»; rules.md; README E01 «результат сохрани в result».*
- **Имена выходных папок.** `result\documents`, `result\images`, `result\tables`. Названия трёх категорий даны в README и rules.md, а то, что они лежат внутри `result`, следует из README («результат сохрани в result») и из rules.md («Выходная папка result создаётся отдельно»). Где именно находится `result`, не сказано; по issue #7 это `submissions/LOGIN/E01/`.
- **Ограничения.** Без перемещения или удаления исходников: в rules.md — «Каталоги input/files не менять», в README — «Не перезаписывай выданные исходники». Новых возможностей сверх условия не добавлять (issue #7). Готовое решение здесь не приводится.
- **Как понять, что шаг выполнен.** Есть папка `result` с тремя подпапками, в сумме 12 файлов, а `input\files` по-прежнему содержит 12 файлов. *Источник: DoD в issue #7.*

### S6. Проверь результат по checks и запиши способ повторения
- **Что делает слушатель.** Сверяет `result` с `checks/expected.json`: проверяет состав по категориям, совпадение содержимого с исходниками и неизменность исходной папки. Затем записывает в README решения команду запуска и повторяет её на свежей копии. *Источники: process.md п.6; DoD в issue #7.*
- **Состав `checks/expected.json`** — объект с тремя ключами по 4 имени файла в каждом: `documents`, `images`, `tables`. Конкретные имена слушатель видит в самом файле. Это эталон для сверки, «не готовое решение» (README E01); по issue #7 checks используют «после первого результата».
- **[Предложение] PowerShell:**
  ```powershell
  $exp = Get-Content "$HOME\Course\E01-work\checks\expected.json" -Encoding UTF8 -Raw | ConvertFrom-Json
  foreach ($cat in 'documents','images','tables') {
    $act = (Get-ChildItem "$HOME\Course\E01-work\result\$cat" -File).Name | Sort-Object
    $diff = Compare-Object ($exp.$cat | Sort-Object) $act
    if ($diff) { "$cat : РАСХОЖДЕНИЕ"; $diff } else { "$cat : OK" }
  }
  # содержимое: хеш копии = хеш исходника
  Get-ChildItem "$HOME\Course\E01-work\result" -Recurse -File | ForEach-Object {
    $src = "$HOME\Course\E01-work\input\files\$($_.Name)"
    "{0} {1}" -f $_.Name, ((Get-FileHash $_.FullName).Hash -eq (Get-FileHash $src).Hash)
  }
  # неизменность исходников: сверка с checksums.json
  $ref.PSObject.Properties | Where-Object Name -like 'input/files/*' | ForEach-Object {
    $p = Join-Path "$HOME\Course\E01-work" $_.Name
    "{0} {1}" -f $_.Name, ((Get-FileHash $p).Hash.ToLower() -eq $_.Value)
  }
  ```
- **Как понять, что шаг выполнен.** По трём категориям выводится `OK`, а все 12 сравнений содержимого и 12 сверок исходников с `checksums.json` дают `True`. В README решения записаны команда запуска и результат повторного запуска на свежей копии. *Источник: DoD в issue #7.*

---

## 2. Что требует E01

- **Правило из `materials/E01/input/rules.md`, дословно:** «Распределите копии файлов: .txt/.md/.json/.pdf → documents; .png → images; .csv → tables. Каталоги input/files не менять. Выходная папка result создаётся отдельно. Все 12 файлов должны быть учтены.»
- **Число файлов.** 12: 4 документа (pdf, md, txt, json), 4 png и 4 csv. *Источник: README E01, manifest.json.*
- **`checks/expected.json`.** JSON с ключами `documents`, `images`, `tables`, в каждом массив из 4 имён файлов. Размер 291 байт, SHA-256 `c9f25550…481d`. *Источник: файл, `checksums.json`.*
- **DoD из issue #7, дословно:**
  1. «В выходной папке находятся все 12 файлов в категориях из задания; содержимое файлов совпадает с исходниками.»
  2. «Исходная папка не изменена; ни один исходный файл не удалён и не перезаписан.»
  3. «Переданы скрипт и инструкция запуска; повторный запуск на свежей копии даёт ожидаемое распределение.»
- **Ловушка с расширениями** (мой вывод). Файл `notes.md` — это документ, а не «исходник для чтения». `record.json` тоже относится к documents, хотя слушатель может принять JSON за «данные/таблицы». Сами `rules.md`, `manifest.json` и `checksums.json` в раскладку **не входят**: раскладываются только файлы из `input/files`.

---

## 3. Расхождения и ловушки (process.md против фактического E01)

1. **«input/rules.md или input/SPEC.md».** В E01 есть только `input/rules.md`, `SPEC.md` отсутствует. *Источник: список ZIP.* В руководстве лучше написать «правила в `input/rules.md` (в других комплектах может быть `input/SPEC.md`)».
2. **Вложенная корневая папка в ZIP.** Есть: все пути начинаются с `E01/`. После `Expand-Archive -DestinationPath X` файлы окажутся в `X\E01\...`, а не в `X\...`. Отдельных записей-каталогов в ZIP нет, на распаковку это не влияет. *Источник: `ZipFile.infolist()`.*
3. **SHA-256.** Указан в issue #7 (`006f40b1…1382`) и совпадает с `downloads/E01.zip`. Внутри ZIP хеша самого архива нет. Есть только `checksums.json` с хешами 16 файлов комплекта (без самого `checksums.json`), его удобно использовать для проверки «исходники не изменились».
4. **Папка result.** README E01: «результат сохрани в result». rules.md: «Выходная папка result создаётся отдельно». Точное расположение не задано; по issue #7 копии, результат и evidence лежат в `submissions/LOGIN/E01/`. Папки `result` в ZIP нет, её создаёт слушатель.
5. **«Скопируй исходники в отдельную рабочую папку» (S4)** — ни README, ни rules.md не называют этой папки. В README E01 есть только «Работай в отдельной рабочей папке». Имя папки выбирает автор руководства.
6. **Заголовки расходятся.** «[E01] Порядок в папке» (README, manifest) против «[E01] Разложить файлы по категориям без изменения исходников» (issue #7).
7. **Кодировка.** Файлы в UTF-8 без BOM; в Windows PowerShell 5.1 нужен `Get-Content -Encoding UTF8`, иначе кириллица отображается искажённо (мой вывод по байтам файлов). В README E01 про CSV сказано: «UTF-8, разделитель запятая … в Excel используйте импорт „Из текста/CSV“».
8. **process.md против issue #48 о проверке руководства.** process.md требует передать руководство другому слушателю или независимому агенту. Issue #48 эту обязательную независимую проверку заменяет самопроверкой (см. раздел 4).
9. **`materials/H12/checks/checklist.json`** ссылается на `"numeric_reference": "survey.csv или products.csv, если присутствует"`. Таких файлов в H12 нет, и issue #48 прямо говорит: «Общая ссылка графического checklist на отсутствующий CSV не создаёт требования этого файла: применяй конкретный бриф».
10. **Скрипт.** Задание E01 требует именно скрипт и инструкцию запуска (README, DoD). Python 3.10+ без сторонних пакетов упомянут в issue #7 только для «браузерного стенда»; язык скрипта не задан.

---

## 4. Уточнения issue #48, меняющие требования к руководству

Источник всех пунктов — `gh issue view 48 -R ARepnikov777/Training`. Комментариев в issue нет.

- **Руководство проверяется на чистой локальной копии E01 (issue #7).** Нужно пройти по нему скачивание, распаковку, сохранение исходников, копирование и сверку, а замечания и исправления сохранить.
- **Независимая проверка больше не обязательна.** Дословно: «Прежняя обязательная независимая проверка в process.md заменена этой самопроверкой». Другой слушатель или агент «не являются предусловиями». Нужно указать фактический способ проверки, «не называя собственный прогон независимым». В DoD: «Другой слушатель/агент не обязателен».
- **Предметный checklist:** 4–6 страниц, все шесть шагов, читаемые иллюстрации, неизменные исходники, журнал прохождения.
- **DoD H12:**
  1. 4–6 страниц с редактируемым текстом и иллюстрациями ко всем значимым шагам.
  2. Порядок и содержание действий соответствуют process.md, изображения не противоречат тексту.
  3. Процесс выполнен на чистой копии E01; записаны способ проверки, замечания и их учёт либо оставшиеся ограничения.
  4. Все страницы проверены на читаемость, наложения и обрезки; переданы итоговый файл, исходник и сведения о происхождении изображений.
- **Без SSH, сервера и покупки программ.** Для графики допустим вариант без платного генератора. Элементы для иллюстраций — `materials/H12/input/elements.svg`, растеризатор — `materials/H12/input/rasterize.html`, лицензия — `materials/H12/input/LICENSE.md`.
- **Сдача.** Работа кладётся в `submissions/<логин>/H12/`, ветка `student/<логин>/H12`, в PR указать `Задание: #48` без `Closes`. В README решения — DoD с доказательствами по каждому пункту; уточнения issue сохранить вместе с README.
- **Комплект H12.** SHA-256 H12.zip: `36ad9564b9c75ad123e99c4e40fa4e2049fb06bd5379e911ef93878e1aeae0c1`, ссылка закреплена за тем же коммитом `22aad84`.

---

## 5. Источники

- `materials/H12/input/process.md`, `materials/H12/README.md`, `materials/H12/checks/checklist.json`
- `materials/E01/README.md`, `materials/E01/input/rules.md`, `materials/E01/checks/expected.json`, `materials/E01/manifest.json`, `materials/E01/checksums.json`
- `downloads/E01.zip` (только список содержимого и SHA-256)
- `README.md` репозитория, раздел «Подготовка и сдача задания»
- Issue #7 и #48 в `ARepnikov777/Training` (`gh issue view`)

Все команды PowerShell в разделе 1 — непроверенные предложения: перед включением в руководство их нужно прогнать на чистой копии.
