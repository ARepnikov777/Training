# Исправление отрицательного сценария

После фактического `Negative_review: reject` в отдельной копии `corrected.json` восстановлено только `pages[0].page = 1` для `01-text.pdf`. Исходный PDF содержит одну страницу; её текст совпадает с текстом первой записи принятого `result/batch/batch.json`, где указан номер 1. `candidate.json`, основной batch и raw не изменялись. Общие условия: attempts уже 1 из N=2, начало 2026-11-16T10:08:31+05:00, дедлайн 11:08:31; исправление ожидает независимого повторного ревью.

Команды из корня checkout (Python — существующее окружение H04):

```powershell
../Training-H04/submissions/EnterFC/H04/.venv/Scripts/python.exe -c "import json,sys; from pathlib import Path; r=Path('submissions/EnterFC/SA11'); sys.path.insert(0,str(r.resolve())); from src.contract import validate_batch; validate_batch(json.loads((r/'evidence/negative/candidate.json').read_text('utf-8')))"
```

Exit 1: `ValueError: page: expected fields source, page, method, text, tables, uncertainty`.

```powershell
../Training-H04/submissions/EnterFC/H04/.venv/Scripts/python.exe -c "import fitz,json; from pathlib import Path; r=Path('submissions/EnterFC/SA11'); d=fitz.open(r/'kit/H04/input/01-text.pdf'); b=json.loads((r/'result/batch/batch.json').read_text('utf-8')); print('pdf page count:',len(d)); print('batch first source/page:',b['pages'][0]['source'],b['pages'][0]['page']); print('pdf text equals batch:',d[0].get_text().strip()==b['pages'][0]['text'].strip())"
```

Exit 0: `pdf page count: 1`, `batch first source/page: 01-text.pdf 1`, `pdf text equals batch: True`.

```powershell
../Training-H04/submissions/EnterFC/H04/.venv/Scripts/python.exe -c "import json; from pathlib import Path; r=Path('submissions/EnterFC/SA11/evidence/negative'); p=json.loads((r/'candidate.json').read_text('utf-8')); assert p['pages'][0]['source']=='01-text.pdf' and 'page' not in p['pages'][0]; p['pages'][0]['page']=1; (r/'corrected.json').write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')"
```

Exit 0.

```powershell
../Training-H04/submissions/EnterFC/H04/.venv/Scripts/python.exe -c "import json,sys; from pathlib import Path; r=Path('submissions/EnterFC/SA11'); sys.path.insert(0,str(r.resolve())); from src.contract import validate_batch; c=json.loads((r/'evidence/negative/candidate.json').read_text('utf-8')); x=json.loads((r/'evidence/negative/corrected.json').read_text('utf-8')); b=json.loads((r/'result/batch/batch.json').read_text('utf-8')); print('corrected validate_batch:',validate_batch(x)); assert x==b; print('corrected equals batch: True'); assert x['pages'][0].pop('page')==1 and x==c; print('only change: pages[0].page added as 1')"
```

Exit 0: `corrected validate_batch: None`, `corrected equals batch: True`, `only change: pages[0].page added as 1`. Сравнения семантические, после разбора JSON.
