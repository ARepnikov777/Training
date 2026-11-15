# Бриф SA03-4 — worker: сборка руководства и проверка вёрстки

Подзадача: #65. Тип субагента: `general-purpose`. Состояние графа: `Build` (и `Fix` для вёрстки).

## Рабочий каталог
Worktree `C:/Users/abylaikhan.a/Training-SA03/build`, ветка `student/arystanabyl/SA03-build`.
Там уже влиты `text/` и `figures/`. Пиши **только** в `submissions/arystanabyl/SA03/guide/`,
`submissions/arystanabyl/SA03/evidence/pages/` и `submissions/arystanabyl/SA03/evidence/layout-check.md`.

## Входы (только чтение)
- `submissions/arystanabyl/SA03/text/steps.md` — весь текст руководства
- `submissions/arystanabyl/SA03/figures/fig-0N.png` — рисунки
- `submissions/arystanabyl/SA03/interfaces.md` — подписи рисунков (дословно) и разбивка страниц

## Выход
1. `guide/guide.html` — самодостаточный редактируемый исходник. Текст переносится из steps.md без смысловых правок. Рисунки подключаются относительными путями `../figures/fig-0N.png`. Формат A4 альбомный: `@page { size: A4 landscape; margin: 0 }`, каждая страница — блок 297×210 мм с полями не меньше 12 мм. У последней страницы нет `page-break-after`, иначе появится пустая страница. Основной текст не меньше 10 pt, код не меньше 9 pt. На странице внизу — номер «N / всего».
2. `guide/guide.pdf` — печать из Edge:
   `"/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" --headless=new --disable-gpu --no-pdf-header-footer --print-to-pdf="<win-путь pdf>" "file:///<путь html>"`
3. `guide/build.md` — как пересобрать PDF и PNG (точные команды).
4. `evidence/pages/page-N.png` — PNG каждой страницы. Способ: Edge `--screenshot` по HTML с окном 1123×(794×страниц) и нарезка PIL по 794 px, либо другой воспроизводимый способ. Опиши его в build.md.
5. `evidence/layout-check.md` — таблица по каждой странице: что на странице, мин. кегль, наложения (да/нет), обрезка (да/нет), рисунок и подпись на месте. Плюс число страниц PDF, посчитанное командой, например `python -I -c "import re;print(len(re.findall(rb'/Type\s*/Page[^s]',open(p,'rb').read())))"`.

## Правила
- Страниц 4–6, ориентир — разбивка из interfaces.md.
- Открой каждый page-N.png (инструмент Read показывает изображения) и проверь сам: текст не выходит за страницу, блоки кода не обрезаны справа (длинные строки переносятся через `white-space: pre-wrap`), рисунок не перекрывает текст. Найденное исправь и пересобери до сдачи.
- Не меняй `text/` и `figures/`. Если ошибка в них — опиши её в отчёте, но не исправляй.

## Завершение
`git add` только своих путей и `git commit -m "[SA03-build] Сборка руководства"`. Не делай push, merge и ничего на GitHub. Не передавай работу.
Верни: число страниц PDF, пути, хэш коммита, итог layout-check, замечания к тексту и рисункам (если есть).

## DoD
PDF 4–6 страниц. Все S1–S6 и шесть рисунков с подписями из interfaces.md на месте. PNG всех страниц. layout-check без открытых находок. Коммит только в разрешённых путях.
