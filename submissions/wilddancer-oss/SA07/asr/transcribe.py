"""Первый проход распознавания meeting.mp3 через faster-whisper.

Запуск (из корня репозитория):
    ASR_MODELS=<папка моделей> $ASR_PY submissions/wilddancer-oss/SA07/asr/transcribe.py \
        materials/H06/input/meeting.mp3 submissions/wilddancer-oss/SA07/asr

Пишет first-pass.json (сегменты {id, start, end, text}) и first-pass.md
([MM:SS-MM:SS] текст). Текст не правится вручную.
"""

import json
import os
import sys
import time

from faster_whisper import WhisperModel, __version__ as fw_version

MODEL = "medium"
LANGUAGE = "ru"
DEVICE = "cpu"
COMPUTE_TYPE = "int8"
BEAM_SIZE = 5


def mmss(seconds: float) -> str:
    total = int(seconds)
    return f"{total // 60:02d}:{total % 60:02d}"


def load_audio(path: str, rate: int = 16000):
    """Декодирует MP3 в моно float32 16 кГц через PyAV.

    Встроенный decode_audio из faster-whisper 1.2.1 передаёт в av.open()
    аргумент metadata_errors, которого нет в PyAV 19, поэтому декодируем сами
    тем же способом (ресемплинг в s16 mono, деление на 32768).
    """
    import av
    import numpy as np

    resampler = av.AudioResampler(format="s16", layout="mono", rate=rate)
    chunks = []
    with av.open(path, mode="r") as container:
        for frame in container.decode(audio=0):
            for out in resampler.resample(frame):
                chunks.append(out.to_ndarray().reshape(-1))
        for out in resampler.resample(None):
            chunks.append(out.to_ndarray().reshape(-1))
    return np.concatenate(chunks).astype(np.float32) / 32768.0


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: transcribe.py <input.mp3> <out_dir>", file=sys.stderr)
        return 2
    src, out_dir = sys.argv[1], sys.argv[2]
    models = os.environ.get("ASR_MODELS")
    if not models:
        print("env ASR_MODELS is not set", file=sys.stderr)
        return 2

    t0 = time.time()
    model = WhisperModel(MODEL, device=DEVICE, compute_type=COMPUTE_TYPE,
                         download_root=models)
    audio = load_audio(src)
    segments, info = model.transcribe(audio, language=LANGUAGE,
                                      beam_size=BEAM_SIZE, vad_filter=False)
    result = [
        {"id": i, "start": round(s.start, 2), "end": round(s.end, 2),
         "text": s.text.strip()}
        for i, s in enumerate(segments)
    ]
    elapsed = time.time() - t0

    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "first-pass.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
        f.write("\n")
    with open(os.path.join(out_dir, "first-pass.md"), "w", encoding="utf-8") as f:
        f.write("# Первый проход распознавания (без правок)\n\n")
        for s in result:
            f.write(f"[{mmss(s['start'])}-{mmss(s['end'])}] {s['text']}\n")

    print(f"faster-whisper {fw_version}, model={MODEL}, lang={info.language}, "
          f"duration={info.duration:.2f}s, segments={len(result)}, "
          f"elapsed={elapsed:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
