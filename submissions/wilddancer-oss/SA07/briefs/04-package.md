# Бриф T4: worker package, сверка и итоговый пакет

Тип субагента: `general-purpose`. Состояние графа: `Package`.
Worktree: `../SA07-wt/package` (ветка `student/wilddancer-oss/SA07-package`,
в ней уже влиты результаты audio и notes).
Пиши только: `asr/corrections.md`, `result/minutes.md`, `result/tasks.csv`,
`result/contradictions.csv` (в `submissions/wilddancer-oss/SA07/`).

## Входы

- `asr/first-pass.md|json`, `extract/audio-events.csv`, `extract/notes-claims.csv`.
- Теперь разрешено: `materials/H06/checks/transcript.md`, `timeline.json`,
  `expected.json`, `contradictions.md` (эталоны для сверки, не готовый ответ).
- `materials/H06/input/meeting.mp3` (можно переслушать фрагмент через
  `$ASR_PY` и faster-whisper, модели в `$ASR_MODELS`).
- `interfaces.md` v1.0, `tools/check_package.py`.

## Запреты

- Не править `extract/*`, `asr/first-pass*`, `asr/method.md`, `asr/transcribe.py`.
  Нашёл ошибку в них - опиши в отчёте (файл, строка, что не так, таймкод).
- Не придумывать ответственных, сроки и суммы. Нет в записи - `не указан`.
- Не копировать эталон как свой результат: каждое решение опирается на
  таймкод записи; эталон только помогает исправить распознавание.
- Не менять `materials/`, `downloads/`; не делать push/merge; не запускать
  других агентов.

## Шаги

1. Сверить first-pass с `checks/transcript.md` и `timeline.json`. Записать
   `asr/corrections.md` по интерфейсу: таймкод, было, стало, основание,
   влияет ли на решение. Спорное место переслушать (повторно распознать
   фрагмент) и указать это.
2. Составить `result/minutes.md`: реквизиты, действующие решения (Р1…), история
   изменений (предложение → изменение/отмена, с таймкодами всех шагов),
   открытые вопросы, источники. Предложения, решения и вопросы различимы.
3. `result/tasks.csv`: только действующие поручения; таймкод - событие
   decision/change той же темы в audio-events.csv.
4. `result/contradictions.csv`: каждое утверждение заметок, которое не
   совпадает с записью, - строка с обеими версиями, таймкодом, характером и
   решением по записи. Если запись не позволяет решить - `не разрешено`, без
   догадки.
5. `python3 -I tools/check_package.py .` из `submissions/wilddancer-oss/SA07`
   до кода 0. Сверить себя с `checks/expected.json` и `checks/contradictions.md`;
   расхождение с эталоном объяснить в отчёте, а не подгонять молча.
6. Коммит `[SA07] package: minutes, tasks, contradictions, corrections`.

## DoD

Код 0 у `check_package.py`; отменённое не в задачах; у каждого решения и
расхождения таймкод; у расхождений ссылка на строку заметок; изменены только
четыре разрешённых файла; `git status` чистый.

## Отчёт координатору

Хэш коммита, вывод проверки, число исправлений распознавания, найденные
ошибки в `extract/*` (если есть), расхождения с `checks/expected.json`.
