"""Browser evidence collector. Run with an existing Orca page and clean local stand."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from datetime import datetime, timezone

BASE = Path(__file__).resolve().parents[1]
EVIDENCE = BASE / 'evidence' / 'browser'
EVIDENCE.mkdir(parents=True, exist_ok=True)
parser = argparse.ArgumentParser()
parser.add_argument('--page', required=True)
parser.add_argument('--orca', default='orca')
args = parser.parse_args()
history = []

def command(*parts):
    proc = subprocess.run([args.orca, *parts, '--page', args.page, '--json'], capture_output=True, encoding='utf-8')
    data = json.loads(proc.stdout)
    history.append({'utc': datetime.now(timezone.utc).isoformat(), 'args': parts, 'response': data})
    (EVIDENCE / 'commands.json').write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding='utf-8')
    if proc.returncode or not data.get('ok'):
        raise RuntimeError(data)
    return data['result']

def evaluate(expression):
    result = command('eval', '--expression', expression)
    value = result.get('result', result)
    return json.loads(value) if isinstance(value, str) else value

def reset():
    command('reload')
    snap = command('snapshot')
    refs = {value.get('name', '').strip(): '@' + key for key, value in snap['refs'].items()}
    evaluate("window.__observed=[];const originalFetch=window.fetch;window.fetch=async(...a)=>{const r=await originalFetch(...a);if(a[0]==='/api/register'){const body=await r.clone().json();window.__observed.push({request:JSON.parse(a[1].body),status:r.status,response:body});}return r;};true")
    return refs

def submit(refs, name, email, initial=True):
    command('fill', '--element', refs['Имя'], '--value', name)
    command('fill', '--element', refs['Email'], '--value', email)
    if initial:
        command('check', '--element', refs['Согласен с учебной обработкой'])
    command('click', '--element', refs['Отправить'])
    command('wait', '--selector', '#result:not(:empty)')

def save(label):
    state = evaluate("(async()=>({url:location.href,name:document.getElementById('name').value,email:document.getElementById('email').value,consent:document.getElementById('consent').checked,text:document.getElementById('result').textContent,exchanges:window.__observed,registrations:await(await fetch('/api/registrations')).json()}))()")
    (EVIDENCE / f'{label}.json').write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
    snapshot = command('snapshot')
    (EVIDENCE / f'{label}-snapshot.json').write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding='utf-8')
    screenshot = command('screenshot')
    print(label, json.dumps(state, ensure_ascii=False), 'SCREENSHOT', screenshot, flush=True)
    # The screenshot response shape is retained in commands.json.
    for key in ('path', 'filePath', 'screenshotPath'):
        if key in screenshot:
            shutil.copyfile(screenshot[key], EVIDENCE / f'{label}.png')
            break
    else:
        raise RuntimeError(('Unknown screenshot response', screenshot))
    return state

checksums = json.loads((BASE/'kit/M14/checksums.json').read_text(encoding='utf-8'))
hashes = {p: hashlib.sha256((BASE/'kit/M14'/p).read_bytes()).hexdigest() for p in checksums if not p.startswith('checks/')}
assert all(checksums[p] == digest for p, digest in hashes.items())
(BASE/'evidence/input-hashes-before.json').write_text(json.dumps(hashes, indent=2), encoding='utf-8')
cases = [(1,'Анна','anna@example.test'),(2,'','s2@example.test'),(3,'Анна','not-an-email'),(4,'а'*81,'s4@example.test'),(5,'а'*80,'s5@example.test'),(6,'Анна','a b@example.test')]
for number, name, email in cases:
    refs = reset()
    submit(refs, name, email)
    save(f'scenario{number}')
refs = reset()
submit(refs, 'Анна', 's7@example.test')
save('scenario7-first')
command('click', '--element', refs['Отправить'])
save('scenario7-repeat')
refs = reset()
submit(refs, '', 's8@example.test')
save('scenario8-empty')
submit(refs, 'Анна', 's8@example.test', initial=False)
save('scenario8-fixed')
print('Eight scenarios collected. Checks have not been read.', flush=True)
