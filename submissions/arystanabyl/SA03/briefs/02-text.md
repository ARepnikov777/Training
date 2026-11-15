# Бриф SA03-2 — worker: текст шагов S1–S6

Подзадача: #63. Тип субагента: `general-purpose`. Состояние графа: `Authoring` (ветвь text).

## Рабочий каталог
Worktree `C:/Users/abylaikhan.a/Training-SA03/text`, ветка `student/arystanabyl/SA03-text`.
Пиши **только** в `submissions/arystanabyl/SA03/text/` этого worktree.

## Входы (только чтение)
- `submissions/arystanabyl/SA03/interfaces.md` — контракт: шаги, подписи рисунков, канонические команды, структура файла, объём
- `submissions/arystanabyl/SA03/research/process-notes.md` — факты и источники
- `materials/H12/input/process.md`, `materials/E01/README.md`, `materials/E01/input/rules.md`

## Выход
`submissions/arystanabyl/SA03/text/steps.md` — по структуре из interfaces.md, на русском,
900–1500 слов. Аудитория — слушатель, который впервые скачал комплект.

## Правила
- Команды в блоках ```powershell``` — только канонические из interfaces.md, дословно.
- Ссылки на рисунки — «см. рисунок N», номера и смысл совпадают с таблицей interfaces.md.
- В S5 не давай готовый скрипт решения E01: опиши процесс и требования rules.md.
- В «Частых ошибках» обязательно: вложенная папка E01 после распаковки, кодировка (`-Encoding UTF8`), правка оригинала вместо копии, SHA-256 не совпал → удалить файл и скачать заново.
- Нет SSH, сервера, облака и покупки программ.
- Проверь объём: `python -I -c "import re;t=open('submissions/arystanabyl/SA03/text/steps.md',encoding='utf-8').read();print(len(re.findall(r'\w+',t)))"`.

## Завершение
Закоммить только свою папку: `git add submissions/arystanabyl/SA03/text && git commit -m "[SA03-text] Текст шагов S1–S6"`.
Не делай push, merge и ничего на GitHub. Не передавай работу другим агентам. Не трогай
файлы вне своей папки, в том числе `figures/` и `materials/`.

Верни: путь к файлу, хэш коммита, число слов, список разделов и любые расхождения
между interfaces.md и фактами, которые ты заметил (не исправляй interfaces.md, сообщи).

## DoD
S1–S6 в порядке process.md, у каждого шага есть разделы «Зачем», «Сделай», «Проверь», «Если не так»
и ссылка на рисунок. Команды совпадают с каноническими. 900–1500 слов. Коммит только в `text/`.
