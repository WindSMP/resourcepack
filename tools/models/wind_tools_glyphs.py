#!/usr/bin/env python3
"""The wind tools as item pictures for Core's dialogs (the crates screen's ring, list and prize).

Dialogs draw items as glyphs of the `gol:i` font ("glint" in the layout: {name: [glyph, glint glyph]}), made from
vanilla textures by the GUI generator. This adds `wind_pickaxe`, `wind_axe`, ... after them, from the 16 px wind
textures, with a glint glyph in each one's shape. Run it again after the generator rewrote the font or the layout:
it replaces what it added before.

    python3 tools/models/wind_tools_glyphs.py [path/to/Core/dialog/layout.json ...]

Extra paths get the same layout (Core ships a copy of it)."""
import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
FONT = ROOT / "assets/gol/font/i.json"
LAYOUT = ROOT / "assets/windsmp/layout/duels/layout.json"
SHEET = "gol:items/wind_tools.png"
NAMES = ["wind_pickaxe", "wind_axe", "wind_shovel", "wind_sell_axe", "wind_bucket"]
GLINT = (178, 120, 255, 255)


def full_width(im):
    """The game sizes a glyph by its last opaque column: keep the top right pixel barely there."""
    px = im.getpixel((15, 0))
    if px[3] == 0:
        im.putpixel((15, 0), (px[0], px[1], px[2], 1))


def main():
    font = json.loads(FONT.read_text())
    layout = json.loads(LAYOUT.read_text())
    providers = [p for p in font["providers"] if p.get("file") != SHEET]
    items = {k: v for k, v in layout["goliath"]["glint"]["items"].items() if k not in NAMES}
    used = [ord(c) for p in providers for row in p.get("chars", []) for c in row if c != "\u0000"]
    n = max(used) + 1

    sheet = Image.new("RGBA", (16 * len(NAMES), 32), (0, 0, 0, 0))
    rows = ["", ""]
    for i, name in enumerate(NAMES):
        im = Image.open(ROOT / f"assets/windsmp/textures/item/{name}.png").convert("RGBA")
        assert im.size == (16, 16), name
        glint = Image.new("RGBA", im.size, (0, 0, 0, 0))
        for y in range(16):
            for x in range(16):
                if im.getpixel((x, y))[3] > 25:
                    glint.putpixel((x, y), GLINT)
        for k, pic in enumerate((im, glint)):
            full_width(pic)
            sheet.alpha_composite(pic, (i * 16, k * 16))
        item, shine = chr(n + i), chr(n + len(NAMES) + i)
        rows[0] += item
        rows[1] += shine
        items[name] = [item, shine]
    assert n + 2 * len(NAMES) < 0xF8FF

    sheet.save(ROOT / "assets/gol/textures/items/wind_tools.png")
    providers.append({"type": "bitmap", "file": SHEET, "height": 8, "ascent": 0, "chars": rows})
    font["providers"] = providers
    FONT.write_text(json.dumps(font, indent=1, ensure_ascii=False))
    layout["goliath"]["glint"]["items"] = items
    text = json.dumps(layout, ensure_ascii=False)
    for path in [LAYOUT, *map(Path, sys.argv[1:])]:
        path.write_text(text)
    print("glyphs", " ".join(f"{name}=U+{ord(items[name][0]):04X}" for name in NAMES))


if __name__ == "__main__":
    main()
