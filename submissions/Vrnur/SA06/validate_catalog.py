#!/usr/bin/env python3
"""Validate content and decoded PDF image pixels against trusted input."""
import argparse
import csv
import io
import sys
from pathlib import Path
import pdfplumber
from PIL import Image, ImageChops
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent

def validate(input_dir, pdf):
    with (input_dir / 'products.csv').open(encoding='utf-8', newline='') as f:
        rows = list(csv.DictReader(f))
    if len(rows) != 5 or len({r['id'] for r in rows}) != 5 or len({r['image'] for r in rows}) != 5:
        raise ValueError('CSV must contain five unique IDs and images')
    reader = PdfReader(pdf)
    layout = pdfplumber.open(pdf)
    if len(reader.pages) != 3:
        raise ValueError('Expected three pages')
    all_lines = [line.strip() for p in reader.pages for line in p.extract_text().splitlines()]
    all_text = ' '.join(all_lines)
    report = []
    for page_number, page in enumerate(reader.pages, 1):
        if abs(float(page.mediabox.width) - 595.276) > .1 or abs(float(page.mediabox.height) - 841.890) > .1:
            raise ValueError(f'Page {page_number} is not A4')
        page_lines = [line.strip() for line in page.extract_text().splitlines()]
        page_text = ' '.join(page_lines)
        expected = rows[(page_number - 1) * 2:page_number * 2]
        images = list(page.images)
        placements = sorted(layout.pages[page_number - 1].images, key=lambda item: item['top'])
        if len(images) != len(expected) or len(placements) != len(expected):
            raise ValueError(f'Page {page_number}: expected {len(expected)} embedded images, got {len(images)}')
        for row, placement in zip(expected, placements):
            for value in (row['id'], row['name'], row['price_KZT'] + ' KZT'):
                if page_lines.count(value) != 1 or all_lines.count(value) != 1:
                    raise ValueError(f"{row['id']}: text missing or duplicated: {value}")
            if page_text.count(row['description']) != 1 or all_text.count(row['description']) != 1:
                raise ValueError(f"{row['id']}: description missing or duplicated")
            with Image.open(input_dir / row['image']) as image:
                source = image.convert('RGB')
            matches = []
            for embedded in images:
                if embedded.name != placement['name'] + '.png':
                    continue
                with Image.open(io.BytesIO(embedded.data)) as image:
                    actual = image.convert('RGB')
                if source.size == actual.size and not ImageChops.difference(source, actual).getbbox():
                    matches.append(embedded)
            if len(matches) != 1:
                raise ValueError(f"{row['id']}: embedded image differs from {row['image']}")
            images.remove(matches[0])
            report.append((row['id'], rows.index(row) + 2, row['image'], page_number, 'OK'))
    layout.close()
    return report

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, default=ROOT / 'source/H11/input', help='Trusted CSV and images')
    parser.add_argument('--pdf', type=Path, default=ROOT / 'result/catalog.pdf')
    args = parser.parse_args()
    try:
        report = validate(args.input, args.pdf)
    except Exception as error:
        print(f'FAIL: {error}', file=sys.stderr)
        return 1
    print('id,csv_line,image,page,result')
    for item in report:
        print(','.join(map(str, item)))
    return 0

if __name__ == '__main__':
    sys.exit(main())
