"""Независимая проверка карточек по условиям M11. Запуск: python measure_cards.py <input> <result>"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image

BG = np.array([0xF5, 0xF7, 0xFA])
OLD = [(0xE8, 0xDC, 0xCC), (0xD9, 0xC8, 0xB2), (0xC5, 0xB3, 0x99)]
inp, res = Path(sys.argv[1]), Path(sys.argv[2])
ok_all = True
for i in range(1, 6):
    im = Image.open(res / f"card-{i}.png")
    a = np.asarray(im.convert("RGB")).astype(int)
    diff = np.abs(a - BG).max(axis=2)
    ys, xs = np.where(diff > 40)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    w, h = x1 - x0, y1 - y0
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    margins = (x0, y0, 1200 - x1, 1200 - y1)
    src = np.asarray(Image.open(inp / f"product-{i}.png").convert("RGB")).astype(int)
    sm = np.ones(src.shape[:2], bool)
    for c in OLD:
        sm &= ~np.all(src == c, axis=2)
    sy, sx = np.where(sm)
    sw, sh = sx.max() + 1 - sx.min(), sy.max() + 1 - sy.min()
    ratio_err = abs(w / h - sw / sh) / (sw / sh)
    old_left = sum(int((np.abs(a - np.array(c)).max(axis=2) < 6).sum()) for c in OLD)
    checks = {
        "size_1200x1200": im.size == (1200, 1200),
        "corner_bg": all(tuple(a[y, x]) == tuple(BG) for y in (0, 1199) for x in (0, 1199)),
        "long_side_900±20": abs(max(w, h) - 900) <= 20,
        "center_±20": abs(cx - 600) <= 20 and abs(cy - 600) <= 20,
        "margins>=100": min(margins) >= 100,
        "aspect_err<1%": ratio_err < 0.01,
        "no_old_bg_pixels": old_left == 0,
    }
    ok_all &= all(checks.values())
    print(f"card-{i}: bbox=({x0},{y0},{x1},{y1}) w×h={w}×{h} centre=({cx:.1f},{cy:.1f}) margins={margins} "
          f"aspect_err={ratio_err*100:.2f}% old_bg_px={old_left}")
    for k, v in checks.items():
        print("   ", "OK " if v else "FAIL", k)
print("ALL OK" if ok_all else "SOME FAILED")
