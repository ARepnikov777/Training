# Scoped re-review nullable validator, раунд 2/2

Reviewer `/root/sa12_review`, read-only. **ADDRESSED**, spec **PASS**, quality **PASS**.
Null в эталоне разрешён только для четырёх nullable полей. JSON null и CSV пустое
значение принимаются только против null. Missing key, строка None, подстановка числа
и null вместо непустого эталона отвергаются. ID и source_url checks сохранены.
RED12/9 отказов → GREEN12 OK, интеграция координатора27 OK. Новых находок нет,
suite reviewer не повторял. Numeric-type риск снят уточнённым контрактом.
Реальное продолжение и итоговая сверка должны подтверждаться отдельными evidence.
