"""Self-check saved browser evidence, source integrity, links and server shutdown."""
import csv
import hashlib
import json
from pathlib import Path
import re
import socket
from datetime import datetime, timezone

b=Path(__file__).resolve().parents[1]
e=b/'evidence/browser'
s={p.stem:json.loads(p.read_text(encoding='utf-8')) for p in e.glob('scenario*.json') if '-snapshot' not in p.stem}
expected={'scenario1':[201],'scenario2':[400],'scenario3':[201],'scenario4':[201],'scenario5':[201],'scenario6':[201],'scenario7-first':[201],'scenario7-repeat':[201,200],'scenario8-empty':[400],'scenario8-fixed':[400,201]}
for k,v in expected.items():
    assert [x['status'] for x in s[k]['exchanges']]==v,k
    assert (e/(k+'.png')).read_bytes().startswith(b'\x89PNG\r\n\x1a\n'),k
    assert (e/(k+'-snapshot.json')).is_file(),k
    assert s[k]['text'],k
for k in ['scenario2','scenario8-empty']:
    assert s[k]['exchanges'][-1]['response']=={'errors':['name']}
assert len(s['scenario4']['name'])==81
assert len(s['scenario5']['name'])==80
assert len(s['scenario7-first']['registrations'])==len(s['scenario7-repeat']['registrations'])==6
first,repeat=s['scenario7-repeat']['exchanges']
assert first['request']['token']==repeat['request']['token']
assert first['response']['id']==repeat['response']['id']
empty,fixed=s['scenario8-fixed']['exchanges']
assert empty['request']['name']=='' and fixed['request']['name']=='Анна'
assert empty['request']['token']==fixed['request']['token']
assert len(s['scenario8-empty']['registrations'])==6 and len(s['scenario8-fixed']['registrations'])==7
with (b/'result/matrix.csv').open(encoding='utf-8') as f:
    assert len(list(csv.DictReader(f)))==8
checks=json.loads((b/'kit/M14/checksums.json').read_text())
hashes={p:hashlib.sha256((b/'kit/M14'/p).read_bytes()).hexdigest() for p in checks}
assert hashes==checks
assert not (b/'kit/M14/input/site/_state.json').exists()
for p in (b/'result/site').iterdir():
    if p.name!='_state.json':
        assert p.read_bytes()==(b/'kit/M14/input/site'/p.name).read_bytes(),p
links=[]
for p in [b/'README.md',b/'result/initial-report.md',b/'result/defects.md']:
    for link in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
        if not link.startswith('http'):
            # verification.json is this check's output, written below.
            assert (p.parent/link).exists() or link=='evidence/verification.json',(p,link)
            links.append(link)
sock=socket.socket()
stopped=sock.connect_ex(('127.0.0.1',18764))!=0
sock.close()
assert stopped,'own server still running'
commands=json.loads((e/'commands.json').read_text(encoding='utf-8'))
result={'utc':datetime.now(timezone.utc).isoformat(),'scenarios':8,'passed':5,'failed':[3,4,6],'defect_classes':2,'screenshots':10,'browser_commands':len(commands),'all_commands_ok':all(c['response']['ok'] for c in commands),'input_checksums_match':hashes==checks,'working_copy_source_equal':True,'scenario7_same_id_token_no_duplicate':True,'scenario8_fresh_form_then_correction_same_token':True,'local_links_checked':len(links),'own_server_stopped':stopped,'review':'self-check by implementer; not independent'}
assert result['all_commands_ok']
(b/'evidence/verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
