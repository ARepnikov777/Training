# Бриф Build, после Fix круг 1 — worker: пересборка

Подзадача: #65. Тип: `general-purpose`, модель Sonnet. Состояние: `Build` (вход из `Fix`, fix_rounds = 1).
Исходный бриф `04-build.md` остаётся в силе. Это **не новая вёрстка**: правь существующий `guide/guide.html`.

## Рабочий каталог
Worktree `C:/Users/abylaikhan.a/Training-SA03/build`, ветка `student/arystanabyl/SA03-build`, в неё влиты
исправленные `text/` и `figures/`. Пиши только `guide/`, `evidence/pages/`, `evidence/layout-check.md`.

## Что сделать
1. `git diff <прежний коммит text> HEAD -- submissions/arystanabyl/SA03/text/steps.md` покажет изменения текста
   (Введение — третья папка E01-solution, S5, S6 п. 4, журнал). Перенеси их в `guide.html` без смысловых правок.
2. Рисунки подтянутся сами: они подключены по относительным путям, PNG уже обновлены.
3. Пересобери PDF и PNG страниц командами из `guide/build.md`: Edge с `--user-data-dir=<новая папка в %TEMP%>` и `timeout 60`.
4. Число страниц 4–6. Если страница переполнилась, сократи интервалы, но кегль не опускай ниже 10 pt для текста и 9 pt для кода.
5. Открой каждый `page-N.png` и обнови `evidence/layout-check.md`: таблица по страницам, число страниц, строка «Пересборка после Fix круг 1».

## Завершение
Коммит `[SA03-build] Пересборка после Fix круг 1`. Без push, merge и GitHub, работу не передавай.
Верни число страниц, хэш коммита и итог layout-check.
