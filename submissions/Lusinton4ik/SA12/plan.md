# SA12 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Ограниченные задания ниже, без переделегирования.

**Goal:** Восстановимый браузерный сбор 50 товаров по SA12/H13 с независимой проверкой.
**Architecture:** Python stdlib запускает Orca CLI и читает DOM каталога/карточек. Один JSON checkpoint является источником прогресса. Отдельный validator не импортирует collector и сверяет готовый результат с эталонами только после первого результата.
**Tech Stack:** Python 3.10+, Orca browser, GitHub MCP/CLI, Mermaid.
**Spec:** sources/issue-74.json, sources/issue-49.json, kit/H13/input/scenario.md; workflow.md.

## Global Constraints

- Запись только submissions/Lusinton4ik/SA12/, исходные materials/downloads и чужие решения сохранены.
- Сбор выполняй через браузер на локальном стенде; не заменяй его прямой выгрузкой исходного JSON.
- /catalog.json не читать для сбора, только для итоговой сверки.
- Сначала сохранить страницы 1–2 (20 записей), зарегистрировать HTTP 503 страницы 3 с fail=1, завершить процесс, продолжить новым процессом без fail=1.
- Поля: id,name,category,price,currency,supplier,availability,ram_GB,ssd_GB,screen_inches,source_url.
- Уточнение после первого результата (10:50Z): availability, ram_GB, ssd_GB, screen_inches могут быть null. В DOM это строка None, в JSON сохраняется null, в CSV пустое поле. Обязательные ключи сохраняются. screen_inches — float при наличии, остальные числовые поля — int.
- source_url — абсолютная ссылка на карточку /product?id=…; CSV UTF-8, запятая, десятичная точка.
- Не делать merge и не закрывать исходный H13. Субагенты не публикуют и не переделегируют.

## Review Focus

- Обрыв после атомарного checkpoint: сохранённые id не теряются.
- Повтор завершённого запуска: ни дублей, ни повторного добавления.
- Ошибка страницы: отметка неполноты и журнал URL/status, следующий запуск восстанавливает её.
- Повреждённый/чужой checkpoint: явная ошибка вместо фиктивного успеха.
- Набор с пропуском/дублем/неверным полем: независимая проверка отклоняет.

## Декомпозиция и приёмка

Пять задач обоснованы пятью отдельно проверяемыми выходами: контракт, сборщик,
валидатор, предметный прогон, независимое ревью. Одна задача не дублирует другую.

1. **Explore (`explorer`, read-only текущего checkout)**: прочитать входы, вернуть контракт и ссылки; никаких файлов/публикаций. Координатор сохраняет отчёт.
2. **Build (`worker`, student/Lusinton4ik/SA12-worker, SA12-worker)**: только collector.py, tests/test_collector.py, evidence/collector-tests.txt, collector-report.md. Сначала поведенческий тест resume/503/dedupe и ожидаемый RED, затем минимальный код и GREEN. Не читать catalog.json/checks. CLI `collector.py --base-url URL --output DIR [--fail-third] [--page ID]`; exit 2 = управляемое прерывание, 0 = полный набор.
3. **Validate_build (отдельный `worker`, student/Lusinton4ik/SA12-validator, SA12-validator)**: только validate.py, tests/test_validate.py, evidence/validator-tests.txt, validator-report.md. Контракт: `validate.py --data FILE --expected-ids FILE --catalog FILE`; exit 0 при точном совпадении 50 id и всех полей, иначе 1. Тесты RED → GREEN для пропуска, дубля, неверного поля и source_url. Не импортировать collector. Эталоны читать при реальной проверке после первого результата.
4. **Run (координатор)**: интеграция по diff и повтор тестов; отдельные процессы fail/resume/rerun, evidence checkpoint20/503/50/недублей. Копия с удалённой записью отвергается validator, восстановленная принимается. Повторить по README в новой папке.
5. **Review (`reviewer`, read-only интеграционного checkout)**: получить spec, отчёты и diff package, проверить соответствие и качество, вернуть отдельные вердикты. До 2 исправлений первоначальным владельцем файлов. Координатор сохраняет reviewer-report.md, README с полным DoD, проверяет gitleaks staged/history и создаёт один PR в main.

Граф и его рендер проверяются до запуска Explore. Приёмка каждого этапа по наблюдаемым артефактам; run-log — журнал переходов и идентификаторов. GitHub-веха и native sub-issues создаются до реализации. Вся работа разрешена поручением выполнить issue целиком; дополнительные согласования способа исполнения не требуются.
