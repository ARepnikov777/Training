# Worker #143 — текстовая ветвь

Ветка `student/EnterFC/SA11-text`, отдельный worktree `Training-SA11-text`. Реализация написана заново с PyMuPDF из окружения H04; готовый результат H04 не копировался. Вход `kit/H04/input/01-text.pdf`, SHA-256 `7ce24c85607c591f31f537d6e4fc63df5ee4f85f2ff001108597ad046bf164e3`. Новый запуск создал `result/text/01-text/page-1.txt`, `page-1.png`, `page-1.json`; SHA-256 raw текста `9bba0ec94a0dcee9b6bc724833213793c1727d4f5072eab6477e8c3f77cbeef2`. Таблиц не обнаружено, поэтому CSV отсутствует. Данные извлечены до чтения `kit/H04/checks/expected.md`.

После сохранения raw сверка с checks: одна страница, акт А-017, 12 ноутбуков, цена 245 000 и сумма 2 940 000 совпадают. Расхождений по указанным контрольным значениям нет. Содержательная точность всего текста и таблиц иных PDF этой проверкой не установлена; извлечение таблиц зависит от распознавания линий PyMuPDF.

Проверки (из корня worktree):

- `../Training-H04/submissions/EnterFC/H04/.venv/Scripts/python.exe -m pytest submissions/EnterFC/SA11/tests/test_text_extract.py -q -p no:cacheprovider`: RED, exit 1, 2 failed — заглушка вернула пустой список вместо страниц; импорт работал. Первый запуск до этого завершился ошибками доступа pytest к временному каталогу, не считался RED; повтор выполнен с разрешением.
- Та же команда после реализации: GREEN, exit 0, 2 passed. Проверки исходного PDF и двух страниц с запретом перезаписи.
- После добавления проверки синтетической таблицы и CSV: та же команда, exit 0, 3 passed. Эта дополнительная проверка написана после реализации таблиц, отдельный RED для неё не проводился.
- `../Training-H04/submissions/EnterFC/H04/.venv/Scripts/python.exe -m pytest submissions/EnterFC/SA11/tests -q -p no:cacheprovider`: exit 0, 3 passed, 1 предупреждение PyMuPDF о deprecated `typing.ByteString`.
- Новый запуск `extract_text` на входном PDF: exit 0, pages=1, tables=0; метод `text`, нумерация с 1. Тест проверяет контракт страницы, JSON и PNG.

Коммит, push и публикация не выполнялись. Общие счётчики не менялись.


## Дополнительный цикл TDD для таблиц

Первоначально тест таблиц был написан после кода, как указано выше. Затем реализация извлечения таблиц была удалена, оставлен `tables=[]`. Команда `../Training-H04/submissions/EnterFC/H04/.venv/Scripts/python.exe -m pytest submissions/EnterFC/SA11/tests/test_text_extract.py::test_table_is_returned_and_saved_as_csv -q -p no:cacheprovider` вернула exit 1: ожидаемый RED, `tables` равен `[]` вместо таблицы с Item, Count и Pen, 12. После этого обработка таблиц реализована заново. Команда `../Training-H04/submissions/EnterFC/H04/.venv/Scripts/python.exe -m pytest submissions/EnterFC/SA11/tests/test_text_extract.py -q -p no:cacheprovider` вернула exit 0: 3 passed, 1 предупреждение PyMuPDF о deprecated `typing.ByteString`. SHA-256 raw `page-1.txt` после цикла остался `9bba0ec94a0dcee9b6bc724833213793c1727d4f5072eab6477e8c3f77cbeef2`; raw входного документа не перезапускался и не изменялся.
