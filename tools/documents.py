"""Создание собственных учебных PDF и предметных иллюстраций."""

import ctypes
import json
import math
import textwrap
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
pdfmetrics.registerFont(TTFont("Course", FONT))


def pdf(path, pages, scan=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(path), pagesize=(595, 842), invariant=1)
    c.setTitle("Вымышленные материалы учебного курса")
    for n, paragraphs in enumerate(pages, 1):
        if scan:
            image = Image.new("RGB", (1190, 1684), "#fffef9")
            draw = ImageDraw.Draw(image)
            font = ImageFont.truetype(FONT, 22)
            y = 95
            for para in paragraphs:
                for line in textwrap.wrap(para, width=83) or [""]:
                    draw.text((90, y), line, fill="#222222", font=font)
                    y += 34
                y += 14
            draw.text(
                (90, 1590), f"Учебный скан · страница {n}", fill="#444444", font=font
            )
            c.drawImage(ImageReader(image), 0, 0, 595, 842)
        else:
            c.setFont("Course", 11)
            y = 790
            for para in paragraphs:
                for line in textwrap.wrap(para, width=83) or [""]:
                    c.drawString(45, y, line)
                    y -= 17
                y -= 9
            c.setFont("Course", 9)
            c.drawString(45, 28, f"Синтетический учебный документ · страница {n}")
        c.showPage()
    c.save()


SCAN_PAGES = [
    [
        "УЧЕБНАЯ МАСТЕРСКАЯ «ОРИОН»",
        "Акт приёмки оборудования № А-017 от 12.11.2026.",
        "Ответственный: Анна Петрова. Получатель: Илья Смирнов.",
        "Переданы 12 ноутбуков по цене 245 000 тенге. Общая стоимость: 2 940 000 тенге.",
        "Поставка принята без замечаний. Срок проверки комплектации — 14.11.2026.",
    ],
    [
        "ВЕДОМОСТЬ КОМПЛЕКТАЦИИ",
        "Партия: OR-2026-11. Место приёмки: аудитория 305.",
        "Каждый комплект: ноутбук, блок питания, инструкция.",
        "Ноутбуки: 12 штук. Блоки питания: 12 штук. Инструкции: 12 штук.",
        "Всего предметов: 36. Проверил: Михаил Волков. Дата: 13.11.2026.",
    ],
    [
        "ГРАФИК ПОДГОТОВКИ",
        "Мария Соколова готовит рабочие места до 15.11.2026.",
        "Техническая проверка проводится 16.11.2026 в 09:30.",
        "На проверку выделено 90 минут. Контрольный бюджет расходных материалов: 18 500 тенге.",
        "При обнаружении повреждения оформить запись с номером комплекта и фотографией.",
    ],
]
TABLE_ROWS = [
    ["Артикул", "Наименование", "Кол-во, шт.", "Цена, KZT", "Сумма, KZT"],
    ["A101", "Кабель USB", "8", "2500", "20000"],
    ["A102", "Мышь", "5", "6000", "30000"],
    ["A103", "Клавиатура", "4", "9000", "36000"],
    ["A104", "Наушники", "3", "14000", "42000"],
    ["ИТОГО", "", "20", "", "128000"],
]


def table_pdf(path):
    c = canvas.Canvas(str(path), pagesize=(595, 842), invariant=1)
    widths = [90, 160, 85, 85, 85]
    for page_no in range(3):
        image = Image.new("RGB", (1190, 1684), "#fffef9")
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype(FONT, 20)
        draw.text(
            (90, 90),
            f"Ведомость №{page_no + 1}; цены и суммы в KZT",
            font=font,
            fill="black",
        )
        y = 200
        rows = [row[:] for row in TABLE_ROWS]
        factor = page_no + 1
        for row in rows[1:-1]:
            row[2], row[4] = str(int(row[2]) * factor), str(int(row[4]) * factor)
        rows[-1][2], rows[-1][4] = str(20 * factor), str(128000 * factor)
        for row in rows:
            x = 65
            for width, value in zip(widths, row, strict=True):
                draw.rectangle((x, y, x + width * 2, y + 60), outline="black", width=2)
                draw.text((x + 8, y + 16), value, font=font, fill="black")
                x += width * 2
            y += 60
        c.drawImage(ImageReader(image), 0, 0, 595, 842)
        c.showPage()
    c.save()


def product_images(folder):
    """Собственные синтетические предметные иллюстрации, не фотографии."""
    folder.mkdir(parents=True, exist_ok=True)
    font = ImageFont.truetype(FONT, 28)
    for i, (name, color) in enumerate(
        [
            ("Чашка", "#1d8794"),
            ("Лампа", "#df9e3a"),
            ("Рюкзак", "#5b5d9f"),
            ("Блокнот", "#b24e58"),
            ("Колонка", "#385e48"),
        ],
        1,
    ):
        image = Image.new("RGB", (1000, 800), "#e8dccc")
        d = ImageDraw.Draw(image)
        for x in range(0, 1000, 80):
            d.line((x, 0, x + 200, 800), fill="#d9c8b2", width=3)
        d.ellipse((250, 620, 790, 690), fill="#c5b399")
        if i == 1:
            d.ellipse((620, 300, 810, 510), outline=color, width=38)
            d.rounded_rectangle((280, 230, 680, 640), radius=60, fill=color)
            d.ellipse((280, 210, 680, 285), fill="#19565e")
        elif i == 2:
            d.ellipse((300, 600, 700, 665), fill=color)
            d.rectangle((480, 290, 520, 625), fill="#373d4b")
            d.polygon([(270, 320), (730, 320), (600, 100), (400, 100)], fill=color)
        elif i == 3:
            d.rounded_rectangle((290, 190, 710, 650), radius=100, fill=color)
            d.rounded_rectangle(
                (400, 120, 600, 260), radius=70, outline=color, width=25
            )
            d.rounded_rectangle(
                (340, 420, 660, 610), radius=30, outline="#dad8ef", width=6
            )
        elif i == 4:
            d.rounded_rectangle((300, 140, 700, 650), radius=20, fill=color)
            d.rectangle((320, 140, 345, 650), fill="#53232b")
            d.text((385, 300), "IDEAS", fill="white", font=font)
        else:
            d.rounded_rectangle((340, 160, 660, 650), radius=70, fill=color)
            for y in range(210, 600, 20):
                d.line((370, y, 630, y), fill="#739985", width=3)
            d.ellipse((475, 180, 500, 205), fill="#dedede")
        image.save(folder / f"product-{i}.png")
    (folder / "provenance.md").write_text(
        "Все пять изображений созданы программно специально для курса. Это синтетические предметные иллюстрации, не фотографии и не реальные товары. Авторские исходники — tools/documents.py; разрешено свободное учебное использование по лицензии CC0.\n"
    )


def synthesize_meeting(folder):
    """Синтезирует русскую учебную запись офлайн через установленный libespeak-ng."""
    paragraphs = json.loads((Path(__file__).parent / "meeting-script.json").read_text())
    lib = ctypes.CDLL("libespeak-ng.so.1")
    lib.espeak_Initialize.argtypes = [
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
    ]
    lib.espeak_Initialize.restype = ctypes.c_int
    rate = lib.espeak_Initialize(2, 0, None, 0)
    if rate <= 0:
        raise RuntimeError("Не удалось инициализировать eSpeak NG")
    callback_type = ctypes.CFUNCTYPE(
        ctypes.c_int, ctypes.POINTER(ctypes.c_short), ctypes.c_int, ctypes.c_void_p
    )
    chunks = []

    @callback_type
    def callback(samples, count, _events):
        if count:
            chunks.append(ctypes.string_at(samples, count * 2))
        return 0

    lib.espeak_SetSynthCallback(callback)
    lib.espeak_SetVoiceByName.argtypes = [ctypes.c_char_p]
    if lib.espeak_SetVoiceByName(b"ru") != 0:
        raise RuntimeError("Русский голос eSpeak NG недоступен")
    lib.espeak_SetParameter(1, 130, 0)
    lib.espeak_Synth.argtypes = [
        ctypes.c_char_p,
        ctypes.c_size_t,
        ctypes.c_uint,
        ctypes.c_int,
        ctypes.c_uint,
        ctypes.c_uint,
        ctypes.c_void_p,
        ctypes.c_void_p,
    ]
    transcript, timeline, all_audio = [], [], bytearray()
    for i, text in enumerate(paragraphs, 1):
        seconds = len(all_audio) / (rate * 2)
        mm, ss = divmod(int(seconds), 60)
        transcript.append(f"{i:02}. [{mm:02}:{ss:02}] {text}")
        timeline.append(
            {"utterance": i, "time_seconds": round(seconds, 2), "text": text}
        )
        chunks.clear()
        encoded = text.encode("utf-8")
        result = lib.espeak_Synth(encoded, len(encoded) + 1, 0, 1, 0, 1, None, None)
        if result != 0:
            raise RuntimeError(f"Ошибка синтеза реплики {i}")
        lib.espeak_Synchronize()
        all_audio.extend(b"".join(chunks))
        all_audio.extend(b"\x00\x00" * math.ceil(rate * 0.5))
    folder.mkdir(parents=True, exist_ok=True)
    with wave.open(str(folder / "meeting.wav"), "wb") as wav:
        wav.setparams((1, 2, rate, 0, "NONE", "not compressed"))
        wav.writeframes(all_audio)
    (folder / "transcript.md").write_text(
        "# Эталонная расшифровка синтетической учебной записи\n\n"
        + "\n\n".join(transcript)
        + "\n"
    )
    (folder / "timeline.json").write_text(
        json.dumps(timeline, ensure_ascii=False, indent=2)
    )
    duration = len(all_audio) / (rate * 2)
    (folder / "audio-info.json").write_text(
        json.dumps(
            {
                "duration_seconds": round(duration, 2),
                "sample_rate": rate,
                "voice": "eSpeak NG ru",
                "synthetic": True,
            },
            indent=2,
        )
    )
    lib.espeak_Terminate()
    return duration
