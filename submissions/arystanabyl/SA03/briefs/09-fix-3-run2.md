# Бриф Fix, запуск 2 — круг 3 (N' = 1, решение слушателя после Escalate_human)

Источник: `reviews/review-4.md` (R-5, R-6). Контракт: `interfaces.md` v1.4. Тип: `general-purpose`, Sonnet.
Fix-text и Fix-figures работают параллельно, затем пересборка. Счётчики запуска 1 не обнуляются.

## Fix-text — R-5
Worktree `C:/Users/abylaikhan.a/Training-SA03/text`, пишет только `submissions/arystanabyl/SA03/text/steps.md`, правка инструментом Edit.
В «Что приложить к сдаче» п. 1 добавь блок ```bash``` с командами создания ветки дословно по v1.4
и одну фразу: clone и `cd Training` нужны только при первом клонировании. Остальное не меняй. Не больше 1800 слов.
Коммит: `[SA03-text] Круг 3: R-5`.

## Fix-figures — R-6
Worktree `C:/Users/abylaikhan.a/Training-SA03/figures`, пишет только `figures/fig-07.svg`, `fig-07.png` и `PROVENANCE.md`.
В «Не класть» четыре перечёркнутые метки по v1.4, кегль не меньше 52 px, без наложений. Экспорт PNG 1600×900 через
headless Edge с `--user-data-dir=<новая папка в %TEMP%>` и `timeout 60`. Открой PNG и проверь.
Коммит: `[SA03-figures] Круг 3: R-6`.

## Build
Worktree `C:/Users/abylaikhan.a/Training-SA03/build`: перенеси блок R-5 в `guide.html` и пересобери по `build.md`.
Страниц 4–6, кегль 10/9 pt, поля чистые. Открой все страницы и обнови `layout-check.md` (раздел «Пересборка, запуск 2»).
Коммит: `[SA03-build] Пересборка, запуск 2`.

## Для всех
Без push, merge и GitHub, работу не передавай. Верни хэш коммита и итог проверки.
