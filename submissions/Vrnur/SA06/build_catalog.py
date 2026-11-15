#!/usr/bin/env python3
"""Build the A4 product catalog from a CSV and its PNG files."""
import argparse
import csv
from pathlib import Path
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parent

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, default=ROOT / 'source/H11/input')
    parser.add_argument('--output', type=Path, default=ROOT / 'result/catalog.pdf')
    args = parser.parse_args()
    with (args.input / 'products.csv').open(encoding='utf-8', newline='') as f:
        rows = list(csv.DictReader(f))
    if len(rows) != 5 or len({r['id'] for r in rows}) != 5:
        raise ValueError('Expected five unique products')
    pdfmetrics.registerFont(TTFont('DejaVu', str(ROOT / 'fonts/DejaVuSans.ttf')))
    pdfmetrics.registerFont(TTFont('DejaVu-Bold', str(ROOT / 'fonts/DejaVuSans-Bold.ttf')))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(args.output), pagesize=A4, pageCompression=1)
    width, height = A4
    for page in range(3):
        c.setFillColor(HexColor('#172c35'))
        c.setFont('DejaVu-Bold', 19)
        c.drawString(40, height - 52, 'Точка идеи')
        c.setStrokeColor(HexColor('#bdd5d5'))
        c.line(40, height - 68, width - 40, height - 68)
        for slot, row in enumerate(rows[page * 2:page * 2 + 2]):
            top = height - 96 - slot * 320
            c.setFillColor(HexColor('#f2f7f6'))
            c.roundRect(40, top - 280, width - 80, 280, 12, fill=1, stroke=0)
            c.drawImage(str(args.input / row['image']), 55, top - 230, width=240, height=192)
            c.setFillColor(HexColor('#172c35'))
            c.setFont('DejaVu', 10)
            c.drawString(310, top - 49, row['id'])
            c.setFont('DejaVu-Bold', 17)
            c.drawString(310, top - 78, row['name'])
            c.setFont('DejaVu', 10)
            # Wrap at words, preserving the source text for PDF extraction.
            words = row['description'].split()
            lines, line = [], ''
            for word in words:
                candidate = (line + ' ' + word).strip()
                if pdfmetrics.stringWidth(candidate, 'DejaVu', 10) > 225 and line:
                    lines.append(line)
                    line = word
                else:
                    line = candidate
            lines.append(line)
            for i, text in enumerate(lines):
                c.drawString(310, top - 108 - i * 15, text)
            c.setFont('DejaVu-Bold', 14)
            c.drawString(310, top - 166, row['price_KZT'] + ' KZT')
        c.setFont('DejaVu', 9)
        c.setFillColor(HexColor('#587077'))
        c.drawRightString(width - 40, 32, str(page + 1))
        c.showPage()
    c.save()

if __name__ == '__main__':
    main()
