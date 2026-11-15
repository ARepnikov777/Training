# Explorer report

Agent `/root/sa12_explore`, type `explorer`, результат получен 2026-11-15 около 10:32 UTC.
Только чтение, без переделегирования. Контракт подтверждён; граф **PASS** по смыслу.

- Каталог: /catalog, 10 товаров на страницу, таблица ID/name/category/price/currency.
  Название ведёт на /product?id=ID (kit/H13/input/site/serve.py:110).
- Карточка: dl/dt/dd всех исходных полей (serve.py:130). Поля из scenario.md:1:
  id,name,category,price,currency,supplier,availability,ram_GB,ssd_GB,screen_inches + source_url.
  source_url добавляется сборщиком из URL посещённой карточки, среди dt его нет.
- DOM отдаёт строки; типы исходного JSON без чтения catalog.json не подтверждены.
  Координатор выбирает числовое преобразование price/ram_GB/ssd_GB/screen_inches,
  которое затем обязательно проверяется по эталону после первого результата.
- Уточнение #49: сохранить страницы 1–2/20 товаров, запросить 3 с fail=1 и получить 503,
  завершить процесс, новым процессом прочитать checkpoint, собрать без fail=1 и повторить без дублей.
  Условие 503 — serve.py:101. Прогресс по id в result, серверный _state.json им не является.
- Граф: Interrupt → Resume требует 20+503+завершение, Verify требует 50/полную сверку,
  Negative и Review имеют ветви отказа. Это проверка плана, не свидетельство исполнения.

Источники: [scenario](kit/H13/input/scenario.md), [сервер](kit/H13/input/site/serve.py),
[уточнения исходного issue](sources/issue-49.json), [workflow](workflow.md).
catalog.json и checks не читались. Главные риски: source_url отсутствует в dl,
числовые типы требуют поздней сверки, остановка до HTTP 503 не удовлетворяет заданию.

## Повторная проверка схемы после первого результата

/root/sa12_explore подтвердил PASS: nullable availability/ram_GB/ssd_GB/screen_inches, строки DOM None соответствуют null. Источник прочитан только как независимая проверка после сохранения первого результата; сведения не используются для выгрузки товаров. Типы и nullable поля: evidence/schema-verification.json. Обновлённые plan/briefs соответствуют фактической схеме.
