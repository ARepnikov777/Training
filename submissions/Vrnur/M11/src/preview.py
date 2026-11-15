import sys
from pathlib import Path
from PIL import Image
res = Path(sys.argv[1]); out = Path(sys.argv[2]); out.mkdir(exist_ok=True)
sheet = Image.new("RGB", (5 * 400, 400), "white")
for i in range(1, 6):
    sheet.paste(Image.open(res / f"card-{i}.png").resize((400, 400), Image.LANCZOS), ((i - 1) * 400, 0))
sheet.save(out / "sheet.png")
# увеличение 4x: (карточка, область 300x300)
zooms = {"mug_handle": (1, (850, 300, 1100, 550)), "lamp_base": (2, (300, 850, 600, 1050)),
         "backpack_pocket": (3, (240, 700, 540, 900)), "notebook_text": (4, (300, 330, 600, 480)),
         "speaker_top": (5, (400, 140, 700, 340))}
for name, (i, box) in zooms.items():
    c = Image.open(res / f"card-{i}.png").crop(box)
    c.resize((c.width * 4, c.height * 4), Image.NEAREST).save(out / f"zoom_{name}.png")
