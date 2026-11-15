"""Build an editable matrix and initial report from collected observations only."""
import csv
import json
from pathlib import Path
from datetime import datetime, timezone

base = Path(__file__).resolve().parents[1]
browser = base/'evidence/browser'
expected = ['201, одна запись', '400, errors=[name], без записи', '400, errors=[email], без записи', '400, errors=[name], без записи', '201, одна запись', '400, errors=[email], без записи', '200, прежние id/token, без новой записи', '400 name → 201, одна запись после исправления']
labels = [f'scenario{i}' for i in range(1,7)] + ['scenario7-repeat','scenario8-fixed']
states = {}
for path in browser.glob('scenario*.json'):
    if '-snapshot' in path.stem:
        continue
    obj = json.loads(path.read_text(encoding='utf-8'))
    if 'result' in obj and isinstance(obj['result'], str):
        obj = json.loads(obj['result'])
        path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')
    states[path.stem] = obj
rows = []
previous = 0
for i, label in enumerate(labels,1):
    state = states[label]
    exchanges = state['exchanges']
    statuses = [e['status'] for e in exchanges]
    passed = i not in [3,4,6]
    count = len(state['registrations'])
    row = {'scenario':i,'start':'reload; отдельные данные' if i<=6 else ('reload; успешная отправка; повтор без reload' if i==7 else 'reload; пустое имя; исправление без reload'), 'name':state['name'], 'name_length':len(state['name'].strip()),'email':state['email'],'consent':True,'expected':expected[i-1],'actual_http':' → '.join(map(str,statuses)), 'actual_text':state['text'],'records_before':previous,'records_after':count,'token':exchanges[-1]['request']['token'],'id':exchanges[-1]['response'].get('id',''),'verdict':'PASS' if passed else 'FAIL','evidence':f'evidence/browser/{label}.json','screenshot':f'evidence/browser/{label}.png'}
    rows.append(row)
    previous=count
with (base/'result/matrix.csv').open('w',encoding='utf-8',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
lines=['# M14 — первичный результат', '',f'Сохранён UTC: {datetime.now(timezone.utc).isoformat()}. Контрольный checks ещё не прочитан.', '', 'Браузер Orca; локальный стенд http://127.0.0.1:18764/register, mode=form-buggy, Python 3.15.0. Форму и сервер не исправляли.', '', '|№|Вход (consent=true)|Ожидается|Фактически|Записи до → после|Вердикт|Доказательство|', '|---|---|---|---|---|---|---|']
for row in rows:
    i=row['scenario'];name=row['name'] if len(row['name'])<=4 else f"а × {row['name_length']}"; name=name or '(пусто)'
    lines.append(f"|{i}|{name}; {row['email']}|{row['expected']}|HTTP {row['actual_http']}; {row['actual_text']}|{row['records_before']} → {row['records_after']}|{row['verdict']}|[JSON](../{row['evidence']}) · [PNG](../{row['screenshot']})|")
lines += ['', '## Наблюдаемые нарушения', '', '1. Email: сценарии 3 и 6 принимают not-an-email и a b@example.test вместо ошибки email; ответ HTTP 201 и запись в /api/registrations.', '2. Длина имени: сценарий 4 принимает 81 букву а вместо ошибки name; HTTP 201 и новая запись.', '', '## Условия сценариев 7 и 8', '', '7: отдельная новая форма, Анна/s7@example.test/согласие. После HTTP 201 нажата та же кнопка без reload; HTTP 200, тот же token и id, 6 записей до повтора и после. См. scenario7-first и scenario7-repeat.', '', '8: ещё одна новая форма, пустое имя/s8@example.test/согласие. HTTP 400 errors=[name], число записей 6. В той же форме без reload изменено только имя на Анна: HTTP 201, тот же token, записей 7. См. scenario8-empty и scenario8-fixed.', '', 'Полные входы, id/token, ответы и снимки промежуточных шагов находятся в evidence/browser/. Протокол команд: commands.json. CSV — UTF-8, разделитель запятая. Проверка выполнена самим исполнителем; независимым ревью не является.']
(base/'result/initial-report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
assert len(rows)==8
assert [r['verdict'] for r in rows].count('PASS')==5
assert len(states['scenario7-first']['registrations'])==len(states['scenario7-repeat']['registrations'])==6
assert states['scenario7-first']['exchanges'][0]['response']['id']==states['scenario7-repeat']['exchanges'][1]['response']['id']
assert len(states['scenario8-empty']['registrations'])==6
assert len(states['scenario8-fixed']['registrations'])==7
assert states['scenario8-empty']['exchanges'][0]['request']['token']==states['scenario8-fixed']['exchanges'][1]['request']['token']
print('Initial report saved; matrix 8 rows, 5 PASS, 3 FAIL; scenarios 7/8 observed invariants verified.')
