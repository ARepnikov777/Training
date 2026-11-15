# Метод первого прохода распознавания (T2, worker audio)

## Инструмент

- faster-whisper 1.2.1 (CTranslate2 4.9.0, PyAV 19.0.2, Python 3.14.7).
- Модель `medium` (многоязычная), заранее скачана в `$ASR_MODELS`.
- Устройство `cpu`, `compute_type=int8`.
- Параметры `transcribe`: `language="ru"`, `beam_size=5`, `vad_filter=False`,
  остальные по умолчанию (temperature fallback, `condition_on_previous_text=True`).
- `word_timestamps` не используются.

## Декодирование звука

Встроенный `decode_audio` из faster-whisper 1.2.1 падает на PyAV 19:
`TypeError: open() got an unexpected keyword argument 'metadata_errors'`
(первый запуск, код выхода 1, ничего не записано). Ничего не переустанавливали.
В `transcribe.py` звук декодируется тем же способом вручную: PyAV,
ресемплинг в s16 mono 16 кГц, деление на 32768, массив передаётся в
`model.transcribe`.

## Команда

Из корня репозитория:

```
ASR_MODELS=$ASR_MODELS $ASR_PY submissions/wilddancer-oss/SA07/asr/transcribe.py \
    materials/H06/input/meeting.mp3 submissions/wilddancer-oss/SA07/asr
```

`$ASR_PY` - интерпретатор окружения с faster-whisper, `$ASR_MODELS` - папка
моделей (`download_root`). Пути выдаёт координатор, в репозиторий не пишутся.

## Запуск

- Начало: 2026-11-15 13:10:41 +0500.
- Конец: 2026-11-15 13:18:05 +0500.
- Длительность: 444 с по часам (443,7 с внутри скрипта, включая загрузку модели).
- Код выхода: 0.
- Вывод скрипта: `faster-whisper 1.2.1, model=medium, lang=ru, duration=685.73s, segments=170, elapsed=443.7s`.

## Входы и выходы

| Файл | SHA-256 |
| --- | --- |
| `materials/H06/input/meeting.mp3` | `9de06cc4759ca8b3e9e22154d0fba44a1587ff307bac72c32a0905d743015343` |
| `asr/first-pass.json` | `cef56332a84f0e54a70a45b412b1e7d5260e0e290400c05fc5256b681b3a7928` |

- Сегментов: 170 (id 0-169), последний кончается на 685,0 с.
- `first-pass.md` - те же 170 сегментов в виде `[MM:SS-MM:SS] текст`
  (секунды отброшены вниз до целых).
- Текст не правился вручную. Эталон (`checks/`) не открывался.
