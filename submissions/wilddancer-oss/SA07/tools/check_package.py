#!/usr/bin/env python3
"""SA07 package check (coordinator gate). Stdlib only.

Usage: python3 -I tools/check_package.py <solution_root> [path/to/notes.md]
Exit: 0 no findings, 1 findings, 2 usage/read error.
Mechanical checks only; meaning of timecodes is checked by the reviewer by audio.
"""
import csv
import json
import re
import sys
from pathlib import Path

DURATION = 685.73
TOPICS = {"date", "room", "start_time", "archives", "stand", "files_check",
          "coffee", "stickers", "budget", "audience", "other"}
KINDS = {"proposal", "decision", "change", "cancellation", "question", "info"}
TASK_STATUS = {"подтверждено записью", "срок не указан в записи",
               "ответственный не указан в записи", "требует уточнения"}
CONTR_KIND = {"дата", "место", "время", "срок", "ответственный", "сумма",
              "отмена", "обязательность", "нет в записи"}
CONTR_STATUS = {"разрешено по записи", "не разрешено"}
HEADERS = {
    "extract/audio-events.csv": "event_id,start,end,speaker,kind,topic,value,owner,deadline,statement,asr_quote",
    "extract/notes-claims.csv": "claim_id,notes_ref,notes_text,topic,field,value,owner,deadline",
    "result/tasks.csv": "task_id,action,topic,owner,deadline,source_timecode,source_quote,confirmation_status",
    "result/contradictions.csv": "contradiction_id,topic,notes_ref,notes_fragment,audio_timecode,audio_fragment,kind,resolution,resolution_status",
}
MINUTES_SECTIONS = ["## Реквизиты встречи", "## Действующие решения",
                    "## История изменений", "## Открытые вопросы", "## Источники"]
TC = re.compile(r"^(\d{2}):(\d{2})$")
TOLERANCE = 3.0  # seconds around an event range

findings = []


def bad(msg):
    findings.append(msg)


def tc_seconds(s, where):
    m = TC.match(s.strip())
    if not m:
        bad(f"{where}: таймкод '{s}' не в формате MM:SS")
        return None
    sec = int(m.group(1)) * 60 + int(m.group(2))
    if int(m.group(2)) > 59 or sec > DURATION:
        bad(f"{where}: таймкод '{s}' вне записи (0-685 с)")
        return None
    return sec


def tc_points(field, where):
    """'MM:SS', 'MM:SS-MM:SS', several joined by '; ' -> list of (a, b)."""
    out = []
    for part in [p for p in field.split(";") if p.strip()]:
        ends = part.strip().split("-")
        if len(ends) > 2:
            bad(f"{where}: диапазон '{part}' некорректен")
            continue
        secs = [tc_seconds(e, where) for e in ends]
        if None in secs:
            continue
        a, b = secs[0], secs[-1]
        if b < a:
            bad(f"{where}: конец диапазона раньше начала '{part}'")
            continue
        out.append((a, b))
    if not out:
        bad(f"{where}: нет корректного таймкода")
    return out


def read_csv(root, rel):
    p = root / rel
    if not p.is_file():
        bad(f"{rel}: файл отсутствует")
        return []
    raw = p.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        bad(f"{rel}: не UTF-8")
        return []
    lines = text.splitlines()
    header = lines[0].lstrip("﻿") if lines else ""
    if header != HEADERS[rel]:
        bad(f"{rel}: заголовок '{header}' не совпадает с интерфейсом")
        return []
    rows = list(csv.DictReader(text.lstrip("﻿").splitlines()))
    for i, r in enumerate(rows, start=2):
        if None in r or any(v is None for v in r.values()):
            bad(f"{rel}:{i}: число полей не совпадает с заголовком")
    if not rows:
        bad(f"{rel}: нет строк данных")
    return rows


def main():
    if len(sys.argv) not in (2, 3):
        print(__doc__)
        return 2
    root = Path(sys.argv[1]).resolve()
    # optional 2nd arg: path to notes.md (for copies outside the repo)
    if len(sys.argv) == 3:
        notes_path = Path(sys.argv[2])
    else:
        notes_path = root.parents[2] / "materials/H06/input/notes.md"
    if not notes_path.is_file():
        print(f"ERROR: не найден {notes_path}")
        return 2
    notes = notes_path.read_text(encoding="utf-8").splitlines()

    # first pass ASR
    fp = root / "asr/first-pass.json"
    if not fp.is_file():
        bad("asr/first-pass.json: файл отсутствует")
    else:
        try:
            segs = json.loads(fp.read_text(encoding="utf-8"))
            if not isinstance(segs, list) or not segs or not all(
                    {"id", "start", "end", "text"} <= set(s) for s in segs):
                bad("asr/first-pass.json: ожидается список сегментов id/start/end/text")
        except json.JSONDecodeError as e:
            bad(f"asr/first-pass.json: не JSON ({e})")
    for rel in ["asr/first-pass.md", "asr/method.md", "asr/corrections.md"]:
        if not (root / rel).is_file():
            bad(f"{rel}: файл отсутствует")

    # audio events
    events = read_csv(root, "extract/audio-events.csv")
    ev_ranges = []
    for i, e in enumerate(events, start=2):
        w = f"extract/audio-events.csv:{i}"
        if e.get("kind") not in KINDS:
            bad(f"{w}: kind '{e.get('kind')}' вне словаря")
        if e.get("topic") not in TOPICS:
            bad(f"{w}: topic '{e.get('topic')}' вне словаря")
        a = tc_seconds(e.get("start") or "", w)
        b = tc_seconds(e.get("end") or "", w)
        for f in ("owner", "deadline", "speaker", "statement", "asr_quote"):
            if not (e.get(f) or "").strip():
                bad(f"{w}: пустое поле {f} (нужно значение или 'не указан')")
        if a is not None and b is not None:
            ev_ranges.append((a, b, e.get("kind"), e.get("topic"), e.get("event_id")))

    # notes claims
    claims = read_csv(root, "extract/notes-claims.csv")
    for i, c in enumerate(claims, start=2):
        check_notes_ref(c.get("notes_ref", ""), c.get("notes_text", ""), notes,
                        f"extract/notes-claims.csv:{i}")
        if c.get("topic") not in TOPICS:
            bad(f"extract/notes-claims.csv:{i}: topic '{c.get('topic')}' вне словаря")

    # cancelled topics = last event of the topic is a cancellation
    last = {}
    for a, b, kind, topic, eid in sorted(ev_ranges):
        last[topic] = kind
    cancelled = {t for t, k in last.items() if k == "cancellation"}

    # tasks
    tasks = read_csv(root, "result/tasks.csv")
    for i, t in enumerate(tasks, start=2):
        w = f"result/tasks.csv:{i}"
        topic = t.get("topic")
        if topic not in TOPICS:
            bad(f"{w}: topic '{topic}' вне словаря")
        if topic in cancelled:
            bad(f"{w}: тема '{topic}' отменена в записи (последнее событие cancellation), "
                f"но есть в действующих поручениях")
        if t.get("confirmation_status") not in TASK_STATUS:
            bad(f"{w}: confirmation_status '{t.get('confirmation_status')}' вне словаря")
        for f in ("action", "owner", "deadline", "source_quote"):
            if not (t.get(f) or "").strip():
                bad(f"{w}: пустое поле {f}")
        for a, b in tc_points(t.get("source_timecode") or "", w):
            ok = any(ea - TOLERANCE <= a and b <= eb + TOLERANCE and k in ("decision", "change")
                     and et == topic for ea, eb, k, et, _ in ev_ranges)
            if not ok:
                bad(f"{w}: таймкод {t.get('source_timecode')} не попадает в событие "
                    f"decision/change темы '{topic}' в audio-events.csv")

    # contradictions
    contr = read_csv(root, "result/contradictions.csv")
    for i, c in enumerate(contr, start=2):
        w = f"result/contradictions.csv:{i}"
        check_notes_ref(c.get("notes_ref", ""), c.get("notes_fragment", ""), notes, w)
        if c.get("kind") not in CONTR_KIND:
            bad(f"{w}: kind '{c.get('kind')}' вне словаря")
        if c.get("resolution_status") not in CONTR_STATUS:
            bad(f"{w}: resolution_status '{c.get('resolution_status')}' вне словаря")
        if c.get("topic") not in TOPICS:
            bad(f"{w}: topic '{c.get('topic')}' вне словаря")
        if c.get("kind") != "нет в записи" or (c.get("audio_timecode") or "").strip():
            tc_points(c.get("audio_timecode") or "", w)
        for f in ("audio_fragment", "resolution"):
            if not (c.get(f) or "").strip():
                bad(f"{w}: пустое поле {f}")
    covered = {int(m) for c in contr for m in re.findall(r":(\d+)$", c.get("notes_ref", ""))}
    claim_lines = {int(m) for c in claims for m in re.findall(r":(\d+)$", c.get("notes_ref", ""))}
    if claims and contr:
        missing = sorted(claim_lines - covered)
        if missing:
            print(f"INFO: строки заметок без расхождений: {missing} (должны совпадать с записью)")

    # minutes
    mp = root / "result/minutes.md"
    if not mp.is_file():
        bad("result/minutes.md: файл отсутствует")
    else:
        md = mp.read_text(encoding="utf-8")
        pos = [md.find(s) for s in MINUTES_SECTIONS]
        if -1 in pos or pos != sorted(pos):
            bad("result/minutes.md: разделы отсутствуют или не в порядке интерфейса")
        else:
            active = md[pos[1]:pos[2]]
            history = md[pos[2]:pos[3]]
            if not re.search(r"\d{2}:\d{2}", active):
                bad("result/minutes.md: в «Действующих решениях» нет таймкодов")
            for t in cancelled:
                words = {"coffee": "кофе"}.get(t)
                if words and words in active.lower() and "отмен" not in active.lower():
                    bad(f"result/minutes.md: отменённая тема '{t}' в «Действующих решениях»")
                if words and words not in history.lower():
                    bad(f"result/minutes.md: отменённая тема '{t}' не описана в «Истории изменений»")

    if findings:
        print(f"FINDINGS: {len(findings)}")
        for f in findings:
            print(" -", f)
        return 1
    print(f"OK: events={len(events)} claims={len(claims)} tasks={len(tasks)} "
          f"contradictions={len(contr)} cancelled_topics={sorted(cancelled)}")
    return 0


def check_notes_ref(ref, fragment, notes, where):
    m = re.fullmatch(r"input/notes\.md:(\d+)", (ref or "").strip())
    if not m:
        bad(f"{where}: ссылка на заметку '{ref}' не в формате input/notes.md:N")
        return
    n = int(m.group(1))
    if not 1 <= n <= len(notes):
        bad(f"{where}: строки {n} нет в notes.md")
        return
    if not fragment.strip() or fragment.strip() not in notes[n - 1]:
        bad(f"{where}: фрагмент '{fragment}' не найден в input/notes.md:{n}")


if __name__ == "__main__":
    sys.exit(main())
