# M14 — первичный результат

Сохранён UTC: 2026-11-15T07:58:30.515305+00:00. Контрольный checks ещё не прочитан.

Браузер Orca; локальный стенд http://127.0.0.1:18764/register, mode=form-buggy, Python 3.15.0. Форму и сервер не исправляли.

|№|Вход (consent=true)|Ожидается|Фактически|Записи до → после|Вердикт|Доказательство|
|---|---|---|---|---|---|---|
|1|Анна; anna@example.test|201, одна запись|HTTP 201; Регистрация сохранена: 905a8378-3d8f-472d-b547-8753316bc176|0 → 1|PASS|[JSON](../evidence/browser/scenario1.json) · [PNG](../evidence/browser/scenario1.png)|
|2|(пусто); s2@example.test|400, errors=[name], без записи|HTTP 400; Ошибки: name|1 → 1|PASS|[JSON](../evidence/browser/scenario2.json) · [PNG](../evidence/browser/scenario2.png)|
|3|Анна; not-an-email|400, errors=[email], без записи|HTTP 201; Регистрация сохранена: a754ccd5-1c94-4c42-b9af-3739aca2d3b4|1 → 2|FAIL|[JSON](../evidence/browser/scenario3.json) · [PNG](../evidence/browser/scenario3.png)|
|4|а × 81; s4@example.test|400, errors=[name], без записи|HTTP 201; Регистрация сохранена: 503bb916-610f-49d7-b713-a3ada065d4e5|2 → 3|FAIL|[JSON](../evidence/browser/scenario4.json) · [PNG](../evidence/browser/scenario4.png)|
|5|а × 80; s5@example.test|201, одна запись|HTTP 201; Регистрация сохранена: f4d90237-1409-4098-9cd2-89a65c0766e1|3 → 4|PASS|[JSON](../evidence/browser/scenario5.json) · [PNG](../evidence/browser/scenario5.png)|
|6|Анна; a b@example.test|400, errors=[email], без записи|HTTP 201; Регистрация сохранена: e98d9a5a-fa69-419c-b7ae-1a0a66b3eb4a|4 → 5|FAIL|[JSON](../evidence/browser/scenario6.json) · [PNG](../evidence/browser/scenario6.png)|
|7|Анна; s7@example.test|200, прежние id/token, без новой записи|HTTP 201 → 200; Регистрация сохранена: 5eb7ca8d-6136-4920-a0f1-56fbd2a71f7d|5 → 6|PASS|[JSON](../evidence/browser/scenario7-repeat.json) · [PNG](../evidence/browser/scenario7-repeat.png)|
|8|Анна; s8@example.test|400 name → 201, одна запись после исправления|HTTP 400 → 201; Регистрация сохранена: 64b5fba6-ab72-48f0-b31a-eec73bcd69e0|6 → 7|PASS|[JSON](../evidence/browser/scenario8-fixed.json) · [PNG](../evidence/browser/scenario8-fixed.png)|

## Наблюдаемые нарушения

1. Email: сценарии 3 и 6 принимают not-an-email и a b@example.test вместо ошибки email; ответ HTTP 201 и запись в /api/registrations.
2. Длина имени: сценарий 4 принимает 81 букву а вместо ошибки name; HTTP 201 и новая запись.

## Условия сценариев 7 и 8

7: отдельная новая форма, Анна/s7@example.test/согласие. После HTTP 201 нажата та же кнопка без reload; HTTP 200, тот же token и id, 6 записей до повтора и после. См. scenario7-first и scenario7-repeat.

8: ещё одна новая форма, пустое имя/s8@example.test/согласие. HTTP 400 errors=[name], число записей 6. В той же форме без reload изменено только имя на Анна: HTTP 201, тот же token, записей 7. См. scenario8-empty и scenario8-fixed.

Полные входы, id/token, ответы и снимки промежуточных шагов находятся в evidence/browser/. Протокол команд: commands.json. CSV — UTF-8, разделитель запятая. Проверка выполнена самим исполнителем; независимым ревью не является.
