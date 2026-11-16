# Первое независимое ревью сборщика

Reviewer `/root/sa12_review`, тип reviewer, read-only. Около 10:44 UTC.
Spec compliance: **FAIL**. Code quality: **FAIL**.

P2, collector.py:101: `goto` может вернуть `result.effects.loading=true`, а
сборщик сразу вызывает eval. Orca browser reference требует `wait --load load`.
Узкое воспроизведение in-memory: незавершённый goto, старый DOM каталога вместо
карточки, затем `Card has unexpected fields`; вызовы только goto/eval, без wait.
Нужен регрессионный тест и ожидание завершения загрузки перед чтением DOM.

Проверены diff, код, тесты, RED/GREEN и координаторские 7 tests OK. Сам reviewer
не повторял suite. git diff --check успешен. Других подтверждённых дефектов нет.
Подозрение о top-level effects снято: наблюдаемый контракт result.effects.
Абсолютный путь Orca — ограничение переносимости согласно брифу, не blocker текущего run.
Реальный сбор, catalog/checks, validator и итоговый DoD в этом ревью не проверялись.
