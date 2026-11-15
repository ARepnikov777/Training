# Сборка руководства SA03

Исходник — `guide.html` (один файл, стили внутри). Его правят руками. Текст взят из
`../text/steps.md` без смысловых правок, подписи рисунков — дословно из `../interfaces.md` (v1.3),
рисунки подключены относительными путями `../figures/fig-0N.png`.

Вёрстка: `@page { size: A4 landscape; margin: 0 }`, каждая страница — блок `.page` 297×210 мм
с полями 12 мм сверху, 14 мм слева и справа, 18,5 мм снизу. Номер «N / всего» стоит внизу,
внутри нижнего поля, на 12 мм от края листа. Основной текст 10 pt, на обложке 11,5 pt, код 9 pt.
В коде включён `white-space: pre-wrap`, а параметры вида `-Recurse` обёрнуты в
`<span class="nb">`, чтобы перенос не шёл по дефису. При копировании текст команды не меняется.
У последней `.page` нет `page-break-after`.

Если меняется число страниц, поправь вручную «N / всего» в каждом `<footer class="pno">`.

## Окружение

- Windows 11, Git Bash, Microsoft Edge (headless), Python 3 с Pillow.
- Все команды ниже запускаются из Git Bash. Корень — каталог `submissions/arystanabyl/SA03`.
- Edge всегда получает свежий `--user-data-dir` во `%TEMP%` и запускается через `timeout 60`.
  Без этого он может подключиться к уже открытому браузеру и зависнуть.

```bash
cd submissions/arystanabyl/SA03
EDGE="/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
HTML="$(cygpath -m "$PWD/guide/guide.html")"
```

## 1. PDF

```bash
T=$(mktemp -d "$TEMP/sa03pdf-XXXX")
timeout 60 "$EDGE" --headless=new --disable-gpu --no-pdf-header-footer \
  --user-data-dir="$(cygpath -w "$T/prof")" \
  --print-to-pdf="$(cygpath -w "$PWD/guide/guide.pdf")" "file:///$HTML"
```

Проверка числа страниц. Должно выйти 6, и у каждой страницы MediaBox 841.92×594.96 pt (A4 альбомная):

```bash
python -I -c "import re,sys;print(len(re.findall(rb'/Type\s*/Page[^s]',open(sys.argv[1],'rb').read())))" guide/guide.pdf
grep -ao "/MediaBox *\[[^]]*\]" guide/guide.pdf | sort | uniq -c
```

## 2. PNG страниц (`evidence/pages/page-N.png`)

Способ: снимок HTML в headless Edge. Окно шириной 1123 CSS px (297 мм) и высотой 794×N
(N — число страниц), масштаб 2. Получается одна длинная картинка 2246×(1588·N). Pillow
режет её на N кусков с шагом 793,70 CSS px (210 мм) × 2. Вёрстка на экране и в печати одна
и та же: стили не зависят от `@media`, страница — блок фиксированного размера в мм.

```bash
N=6
T=$(mktemp -d "$TEMP/sa03shot-XXXX")
timeout 60 "$EDGE" --headless=new --disable-gpu --hide-scrollbars \
  --user-data-dir="$(cygpath -w "$T/prof")" --force-device-scale-factor=2 \
  --window-size=1123,$((794*N)) --screenshot="$(cygpath -w "$T/all.png")" "file:///$HTML"
python -I -c "
import sys; from PIL import Image
im = Image.open(sys.argv[1]); n = int(sys.argv[3]); s = im.width / 1122.52
for k in range(n):
    top = round(k * 793.70 * s); bot = round((k + 1) * 793.70 * s)
    im.crop((0, top, im.width, bot)).save(sys.argv[2] + '/page-%d.png' % (k + 1))
print(im.size)
" "$(cygpath -w "$T/all.png")" evidence/pages $N
```

Результат: `evidence/pages/page-1.png` … `page-6.png`, каждый 2246×1588 px.

## 3. Проверка вёрстки

Каждый `page-N.png` просматривается глазами, итог — в `../evidence/layout-check.md`.
Дополнительно перед сдачей можно измерить вёрстку в той же копии Edge. Для этого нужна
временная копия `guide.html` с `<base href>` на каталог `guide/`. Перед `</body>` в неё
вставляют скрипт: он для каждой `.page` считает запас до нижнего поля, минимальный кегль
текста, горизонтальные прокрутки и загрузку рисунков. Результат снимается через `--dump-dom`.
В репозиторий эта копия не кладётся. Цифры последнего прогона приведены в `layout-check.md`.
