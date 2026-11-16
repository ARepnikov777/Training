# [SA12] Lusinton4ik — независимо проверить полноту и поля каталога

Родитель: #74. Веха SA12 · Lusinton4ik. Входы: #74, уточнения #49, закреплённый H13.zip SHA-256 278186e77b56325fbe1bd2e23dd4d317e162569ee1e1e6a0fbd7b311331637e7; plan.md и workflow.md.

Роль: worker (отдельный исполнитель). Ответственный: Lusinton4ik. Зависимости: Контракт explore; реализация после collector, сверка эталонов после первого результата.
Ветка/worktree: C:/Users/lyudm/orca/workspaces/Training/SA12-validator / student/Lusinton4ik/SA12-validator.
Область записи относительно submissions/Lusinton4ik/SA12/: validate.py, tests/test_validate.py, evidence/validator-tests.txt, validator-report.md

Результат: Независимый CLI проверки JSON/CSV, id/полей/source_url, без импорта collector.

## Ограничения

Только локальный синтетический стенд. Не менять materials/, downloads/, чужие решения. Сбор через DOM браузера; catalog.json/checks только для проверки после первого результата. Один владелец checkpoint. Субагентам запрещены делегирование, push, merge и внешняя публикация. N=2, общий T=120 минут, максимум 3 субагента.

## Definition of Done (DoD)

- [ ] 50 уникальных id и значения всех полей совпадают с эталонами; дубликат, пропуск и неверное поле отвергаются; RED/GREEN сохранены.
- [ ] Отчёт содержит фактические команды, результаты и ссылки; координатор проверил артефакты.

## Точный контракт независимого валидатора

Позднее уточнение после первого реального результата (10:50Z): catalog содержит null в availability,
ram_GB,ssd_GB,screen_inches. Поля обязательны, но null — корректное значение, если совпадает
с catalog: JSON None, CSV пустое поле. Пропущенный ключ по-прежнему ошибка. Проверить
nullable synthetic fixtures: null принят, missing rejected, неверная подстановка/число rejected.
Предыдущее предположение 'все значения непусты' ниже заменено этим контрактом.

Read this first — это требования. Рабочий checkout SA12-validator и указанная ветка.
Не читать/импортировать collector.py и не читать реальный catalog.json/checks до первого результата.
Используй синтетические fixtures для TDD. Только Python stdlib unittest, без зависимостей.
CLI `validate.py --data FILE --expected-ids FILE --catalog FILE`, data может быть JSON-массивом
либо CSV. Ожидаемые ids могут быть списком или объектом; фактическую форму узнает координатор
после первого результата и сообщит, если нужна корректировка. catalog — массив объектов.
Сравнить ровно 50 записей, 50 уникальных id, точное множество ожидаемых id, значения всех
10 исходных полей (id,name,category,price,currency,supplier,availability,ram_GB,ssd_GB,screen_inches),
полноту полей и source_url: http(s) URL с /product?id=тот-же-ID на локальном стенде.
Числовые значения CSV нормализовать по типу эталона, не округлять и не скрывать ошибки.
Отклонять дубликат, отсутствующую запись, неожиданную запись, неверную цену/валюту,
неверный или отсутствующий source_url. Exit 0 = полная точная сверка, exit 1 = конкретные
расхождения/ошибки чтения. Напечатать машинно-читаемый JSON отчёт: ok/count/unique_count/errors.
Не сравнивать только число строк. Не создавать коллекцию из эталона вместо проверки.
TDD: minimal callable scaffold, затем поведенческий RED (не import error), реализация и GREEN.
Сохрани команды/оба вывода в evidence/validator-tests.txt. В tests используй 50 простых
явно синтетических строк; проверь valid, missing, duplicate, wrong-field, bad-url и CSV.
Python C:/Users/lyudm/AppData/Local/Temp/sa12-python-3.12.10/python.exe, UTF-8 mode.
Область записи: validate.py, tests/test_validate.py, evidence/validator-tests.txt,
validator-report.md относительно submissions/Lusinton4ik/SA12/ собственного checkout.
Не делегировать, не коммитить, не делать push/merge/внешние сообщения. Реальную сверку
выполнит координатор после браузерного результата. Бюджет 20 минут, deadline 12:26:17Z.
В конце прекратить запись; вернуть статус, файлы, тесты и ограничения.
