# Бриф SA03-3 — worker: иллюстрации fig-01…fig-06

Подзадача: #64. Тип субагента: `general-purpose`. Состояние графа: `Authoring` (ветвь figures).

## Рабочий каталог
Worktree `C:/Users/abylaikhan.a/Training-SA03/figures`, ветка `student/arystanabyl/SA03-figures`.
Пиши **только** в `submissions/arystanabyl/SA03/figures/` этого worktree.

## Входы (только чтение)
- `submissions/arystanabyl/SA03/interfaces.md` — таблица «Шаги и рисунки»: подписи и обязательное содержание, палитра, минимальный кегль 36 px
- `materials/H12/input/elements.svg` — элементы document, folder, arrow, circle, leaf (лицензия `materials/H12/input/LICENSE.md`)
- `submissions/arystanabyl/SA03/research/process-notes.md` — точные имена файлов и папок

## Выход
- `figures/fig-01.svg` … `fig-06.svg` — собственные композиции, редактируемый SVG, `width="1600" height="900" viewBox="0 0 1600 900"`. Элементы elements.svg переносите в свой файл (копия группы `<g>` с трансформацией). Внешних ссылок и растровых вставок нет.
- `figures/fig-01.png` … `fig-06.png` — экспорт ровно 1600×900. Команда для экспорта (Edge есть на машине):
  `"/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" --headless=new --disable-gpu --hide-scrollbars --window-size=1600,900 --screenshot="<win-путь png>" "file:///<путь svg>"`
  (в Git Bash пути переводи через `cygpath -w` и `cygpath -m`). Альтернатива — `materials/H12/input/rasterize.html`.
- `figures/PROVENANCE.md` — для каждого рисунка: какие элементы elements.svg использованы (id), что нарисовано заново, шрифт, способ экспорта. AI-генератор не использовался — так и укажи.

## Правила
- Содержание и подпись каждого рисунка — строго по таблице interfaces.md. Имена файлов и папок — как в process-notes (E01.zip, E01-kit, E01-work, README.md, input/rules.md, checks/expected.json, result/documents|images|tables).
- Подпись «Рисунок N. …» на сам рисунок не ставь, её даёт вёрстка. На рисунке — только надписи-метки.
- Кегль меток не меньше 36 px, шрифт `Segoe UI, Arial, sans-serif`. Текст не выходит за холст и не накладывается на фигуры.
- Проверь каждый PNG: размер (`python -I -c "from PIL import Image;print(Image.open(p).size)"`) и визуально, открыв изображение. Исправь наложения и обрезки до сдачи.

## Завершение
`git add submissions/arystanabyl/SA03/figures && git commit -m "[SA03-figures] Иллюстрации fig-01…fig-06"`.
Не делай push, merge и ничего на GitHub. Не передавай работу. Не трогай `text/`, `materials/` и другие файлы.

Верни: список файлов с размерами PNG, хэш коммита, что проверил визуально и найденные и исправленные проблемы.

## DoD
Шесть пар SVG+PNG 1600×900, содержание соответствует таблице interfaces.md, кегль от 36 px,
без наложений и обрезки, PROVENANCE.md заполнен, коммит только в `figures/`.
