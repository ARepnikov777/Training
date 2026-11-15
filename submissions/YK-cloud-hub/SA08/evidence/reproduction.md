# Повторение проверок из чистой копии

Рабочий каталог — `submissions/YK-cloud-hub/SA08/`. Достаточно Python 3 со стандартной библиотекой; macOS PDFKit и Quick Look использовались для предметной/визуальной проверки. Исполняемая логика продукта не создавалась, TDD к документам не применялся.

```sh
python3 - <<'PY'
from pathlib import Path
import csv, hashlib, json
r = Path('.')
inventory = json.loads((r/'evidence/input-hashes.json').read_text())
for f in inventory['files']:
    assert hashlib.sha256((r/f['path']).read_bytes()).hexdigest() == f['sha256']
rows = list(csv.DictReader((r/'comparison.csv').open(encoding='utf-8', newline='')))
assert len(rows) == 12
by_key = {x['parameter']: x for x in rows}
assert {x['parameter'] for x in rows if x['classification'] == 'contradiction'} == {
    'quantity', 'total_price', 'delivery_date', 'ram', 'warranty'}
assert all(by_key[k]['classification'] == 'uncertainty' for k in ['vat', 'initial_setup'])
assert all(by_key[k]['classification'] == 'match' for k in ['contract_id', 'model', 'storage', 'location'])
assert by_key['contract_id']['contract_value'] == 'C-17'
assert by_key['contract_id']['appendix_value'] == 'C-17'
assert by_key['contract_id']['specification_value'] == 'C-17'
for doc in ['contract', 'appendix', 'specification']:
    extracted = list(csv.DictReader((r/'extractions'/str(doc+'.csv')).open(encoding='utf-8')))
    evidence = (r/'evidence'/str(doc+'-verification.md')).read_text()
    assert len(extracted) == 11
    for x in extracted:
        assert x['source_file'] == doc+'.pdf' and x['page'] == '1'
        if x['value'] == 'NOT_STATED':
            assert not x['quote']
        else:
            assert x['quote'] and x['quote'] in evidence
print('PASS: source hashes, matrix contract, required cases and extraction citations')
PY
```

Это проверка полноты и структуры сохранённого результата, а не независимый парсер PDF. Предметную точность подтверждают просмотр трёх PDF, рендеры, отдельный reviewer и точные фрагменты. Для самостоятельного повторения открыть исходники и сопоставить каждый вывод по странице 1.

`evidence/first-result/` — неизменная первая версия до контроля. В итоговой матрице добавлено совпадение C-17 после первого ревью; исходные 11 строк сохранены. Локальный `.gitattributes` отключает преобразование переводов строк для CSV, чтобы хеши первой версии воспроизводились после checkout.

Граф: выполнить `python3 scripts/graph_check.py workflow.md`, где scripts/ — каталог скилла agent-behavior-graph; нужен Python 3.10+. В этой среде доступен Python 3.9, поэтому координатор выполнил тот же файл с `from __future__ import annotations`, добавленным в памяти. Результат и ограничения — graph-verification.md. Сохранённый workflow.svg открывается без сети; повторный HTML-рендер использует Mermaid 11 из CDN.
