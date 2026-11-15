# Scoped re-review: исправление 1/2

Reviewer `/root/sa12_review`, read-only. P2 **ADDRESSED**, spec **PASS**, quality **PASS**.
При effects.loading=true теперь wait --page ID --load load предшествует eval.
Таймаут и закреплённый page ID сохранены, несовпадающий URL вызывает CollectorError.
Новые NavigationTests подтверждают goto → wait → eval и отказ чужого URL.
RED: 9 tests, 2 ожидаемых отказа; GREEN: 9 OK; координатор: 17 integrated OK.
Новых находок в fix diff нет, suite reviewer не повторял. Реальный сценарий и
весь DoD этим scoped review ещё не подтверждены.
