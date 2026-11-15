"""M11: пять карточек 1200x1200 из input/product-N.png.
Запуск: python build_cards.py <папка input> <папка результата>
Предмет = все пиксели, цвет которых не равен трём цветам фона (фон, диагональные линии, тень)."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image

BG_CLASSES = [(0xE8, 0xDC, 0xCC), (0xD9, 0xC8, 0xB2), (0xC5, 0xB3, 0x99)]  # фон, линии, тень
CARD, BG, TARGET, PAD = 1200, (0xF5, 0xF7, 0xFA), 900, 6


def object_mask(arr):
    m = np.ones(arr.shape[:2], bool)
    for c in BG_CLASSES:
        m &= ~np.all(arr == c, axis=2)
    return m


def fill_outside(arr, mask, steps=8):
    """Цвета вне предмета заменяем ближайшим цветом предмета: в края не попадёт цвет исходного фона."""
    out, known = arr.copy(), mask.copy()
    for _ in range(steps):
        pad_o = np.pad(out, ((1, 1), (1, 1), (0, 0)))
        pad_k = np.pad(known, 1)
        new = known.copy()
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            src_k = pad_k[1 + dy:1 + dy + known.shape[0], 1 + dx:1 + dx + known.shape[1]]
            src_o = pad_o[1 + dy:1 + dy + known.shape[0], 1 + dx:1 + dx + known.shape[1]]
            take = ~new & src_k
            out[take] = src_o[take]
            new |= take
        known = new
    return out


def smoothstep(x):
    x = np.clip((x - 0.35) / 0.3, 0, 1)
    return x * x * (3 - 2 * x)


def build(src, dst):
    arr = np.asarray(Image.open(src).convert("RGB"))
    mask = object_mask(arr)
    ys, xs = np.where(mask)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    w, h = x1 - x0, y1 - y0
    s = TARGET / max(w, h)
    rgb = fill_outside(arr, mask)
    box = (x0 - PAD, y0 - PAD, x1 + PAD, y1 + PAD)
    size = (round((w + 2 * PAD) * s), round((h + 2 * PAD) * s))
    rgb_big = Image.fromarray(rgb).crop(box).resize(size, Image.LANCZOS)
    m_big = Image.fromarray((mask * 255).astype(np.uint8)).crop(box).resize(size, Image.LANCZOS)
    alpha = smoothstep(np.asarray(m_big, float) / 255)
    ox = round(CARD / 2 - (PAD + w / 2) * s)
    oy = round(CARD / 2 - (PAD + h / 2) * s)
    card = np.empty((CARD, CARD, 3), float)
    card[:] = BG
    big = np.asarray(rgb_big, float)
    region = card[oy:oy + size[1], ox:ox + size[0]]
    region[:] = region * (1 - alpha[..., None]) + big * alpha[..., None]
    Image.fromarray(np.rint(card).astype(np.uint8)).save(dst)
    return dict(src_bbox=(int(x0), int(y0), int(x1), int(y1)), scale=round(float(s), 4))


if __name__ == "__main__":
    inp, outp = Path(sys.argv[1]), Path(sys.argv[2])
    outp.mkdir(parents=True, exist_ok=True)
    for i in range(1, 6):
        print(i, build(inp / f"product-{i}.png", outp / f"card-{i}.png"))
