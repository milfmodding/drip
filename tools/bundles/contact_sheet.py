"""Contact sheet of every TSHIRT variant plus vanilla, for identifying which shirt a bot is
actually wearing during smoke test 6.7. The point is that the tester must be able to name the
garment they see, not just judge that it looks fine -- so the fixtures have to be visually
unmistakable, and that is a question about human perception, not pixel deltas.
"""
import os
import sys

from PIL import Image, ImageDraw

import UnityPy

SRC = sys.argv[1]
VANILLA = sys.argv[2]
OUT = sys.argv[3]

TILE = 256
LABEL = 26


def vanilla_tshirt():
    """Pull the vanilla diffuse so 'DRIP silently fell back to vanilla' is recognisable too."""
    env = UnityPy.load(VANILLA)
    for obj in env.objects:
        if obj.type.name != "Texture2D":
            continue
        d = obj.read()
        if "_dif" in d.m_Name or d.m_Name.endswith("_d"):
            return d.m_Name, d.image
    return None, None


tiles = []
vname, vimg = vanilla_tshirt()
if vimg is not None:
    tiles.append(("VANILLA", vimg))
    print(f"vanilla diffuse: {vname} {vimg.size}")
else:
    print("WARNING: no vanilla diffuse found -- sheet will omit it")

for f in sorted(os.listdir(SRC)):
    if f.endswith(".png"):
        tiles.append((f[:-4], Image.open(os.path.join(SRC, f))))

cols = 4
rows = (len(tiles) + cols - 1) // cols
sheet = Image.new("RGB", (cols * TILE, rows * (TILE + LABEL)), (24, 24, 28))
draw = ImageDraw.Draw(sheet)

for i, (name, img) in enumerate(tiles):
    x = (i % cols) * TILE
    y = (i // cols) * (TILE + LABEL)
    sheet.paste(img.convert("RGB").resize((TILE, TILE), Image.LANCZOS), (x, y))
    draw.rectangle([x, y + TILE, x + TILE, y + TILE + LABEL], fill=(24, 24, 28))
    draw.text((x + 5, y + TILE + 7), name, fill=(235, 235, 240))

sheet.save(OUT)
print(f"{len(tiles)} tiles -> {OUT} {sheet.size}")
