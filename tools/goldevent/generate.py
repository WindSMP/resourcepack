#!/usr/bin/env python3
"""Chasing Gold's items: the golden ticket, gold coin, treasure chest and trophy (menu pictures, as items), and the
golden elytra (item and wings).

    python3 tools/goldevent/generate.py

Reads tools/goldevent/source/ (the event's pixel art, upscaled: the PNGs 16x, the GIFs animated) and writes:
  assets/windsmp/textures/item/<name>.png (+ .mcmeta for animated ones), assets/windsmp/models/item/<name>.json,
  assets/windsmp/items/<name>.json (Core sets item_model windsmp:<name>),
  assets/windsmp/equipment/golden_elytra.json and assets/windsmp/textures/entity/equipment/wings/golden_elytra.png,
  the vanilla wing's outline filled with the item's wing (worn, it shines: tools/goldevent/wings_shine.py).
Dialogs draw the same textures as sprites (windsmp:item/<name>). Needs Pillow. Deterministic.
"""
import json
from pathlib import Path

from PIL import Image, ImageSequence

PACK = Path(__file__).resolve().parents[2]
SOURCE = Path(__file__).resolve().parent / "source"
ASSETS = PACK / "assets/windsmp"


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def downscale(image: Image.Image, cell: int) -> Image.Image:
    """Pixel art drawn at [cell] screen pixels per texel, back to one texel per pixel (sampling each cell's middle)."""
    image = image.convert("RGBA")
    w, h = image.size[0] // cell, image.size[1] // cell
    out = Image.new("RGBA", (w, h))
    src, dst = image.load(), out.load()
    for y in range(h):
        for x in range(w):
            dst[x, y] = src[x * cell + cell // 2, y * cell + cell // 2]
    return out


def still(name: str, cell: int) -> None:
    texture = downscale(Image.open(SOURCE / f"{name}.png"), cell)
    path = ASSETS / f"textures/item/{name}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    texture.save(path, optimize=True)
    item(name)


def animated(name: str, cell: int) -> None:
    """A GIF as an animated item texture: its frames stacked, each shown as long as in the GIF (ticks of 50 ms)."""
    gif = Image.open(SOURCE / f"{name}.gif")
    frames, ticks = [], []
    for frame in ImageSequence.Iterator(gif):
        frames.append(downscale(frame.convert("RGBA"), cell))
        ticks.append(max(1, round((frame.info.get("duration") or 100) / 50)))
    w, h = frames[0].size
    strip = Image.new("RGBA", (w, h * len(frames)))
    for i, f in enumerate(frames):
        strip.paste(f, (0, i * h))
    path = ASSETS / f"textures/item/{name}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    strip.save(path, optimize=True)
    write_json(path.with_suffix(".png.mcmeta"), {"animation": {"frames": [{"index": i, "time": t} for i, t in enumerate(ticks)]}})
    item(name)


def item(name: str) -> None:
    write_json(ASSETS / f"models/item/{name}.json", {"parent": "minecraft:item/generated", "textures": {"layer0": f"windsmp:item/{name}"}})
    write_json(ASSETS / f"items/{name}.json", {"model": {"type": "minecraft:model", "model": f"windsmp:item/{name}"}})


# The golden elytra's equipment tint: green 254 of 255, red and blue full. Invisible, it is the mark the glow shaders'
# wing shine looks for (tools/goldevent/wings_shine.py), as the Christmas kit's red 254 is its mark.
WINGS_MARK = -257  # 0xFFFFFEFF as a signed int


def golden_wings() -> None:
    """The worn wings in the item's golds: the vanilla wing (its texture holds one wing, 12 x 20 texels at 34, 2,
    which both wings use) keeps its feathers' light and shade, mapped onto the icon's palette with more contrast, an
    orange rim along its edges and a pale gleam across its upper part."""
    wings = Image.open(SOURCE / "vanilla_elytra_wings.png").convert("RGBA")
    palette = [(0.00, (92, 42, 0)), (0.22, (176, 82, 0)), (0.42, (232, 132, 8)), (0.62, (255, 184, 28)),
               (0.80, (255, 218, 74)), (1.00, (255, 246, 170))]

    def gold(v: float):
        v = min(1.0, max(0.0, v))
        for (a, ca), (b, cb) in zip(palette, palette[1:]):
            if v <= b:
                t = (v - a) / (b - a)
                return tuple(round(x + (y - x) * t) for x, y in zip(ca, cb))
        return palette[-1][1]

    px = wings.load()
    solid = {(x, y) for x in range(wings.width) for y in range(wings.height) if px[x, y][3]}
    lum = {xy: 0.299 * px[xy][0] + 0.587 * px[xy][1] + 0.114 * px[xy][2] for xy in solid}
    mean = sum(lum.values()) / len(lum)
    spread = max(abs(v - mean) for v in lum.values()) or 1.0
    out = {}
    for (x, y) in solid:
        a = px[x, y][3]
        fx, fy = x - 34, y - 2
        down = min(1.0, max(0.0, fy / 19))
        # Bright gold at the root, richer towards the tips; the vanilla feathers only as fine shading.
        v = 0.86 - 0.36 * down + 0.13 * (lum[(x, y)] - mean) / spread
        # Rows of feathers: a darker line every five texels, slanting like the wing's.
        if 0 <= fx < 12 and fy > 3 and round(fy - fx * 0.3) % 5 == 0:
            v -= 0.16
        # The gleam: a pale diagonal across the upper wing.
        if 0 <= fx < 12 and abs((fx * 0.55 + fy) - 6.5) < 1.0:
            v = max(v, 0.98)
        colour = gold(v)
        edge = any((x + dx, y + dy) not in solid for dx, dy in ((1, 0), (-1, 0), (0, 1)))
        if edge and fy > 1:
            # An orange rim where the wing ends, deeper at the tips.
            colour = gold(0.34 - 0.14 * down)
        out[(x, y)] = (*colour, a)
    for (x, y), c in out.items():
        px[x, y] = c
    path = ASSETS / "textures/entity/equipment/wings/golden_elytra.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    wings.save(path, optimize=True)
    write_json(ASSETS / "equipment/golden_elytra.json", {
        "layers": {"wings": [{"texture": "windsmp:golden_elytra", "dyeable": {"color_when_undyed": WINGS_MARK}}]},
    })


def main() -> None:
    for name in ("golden_ticket", "gold_coin", "treasure_chest"):
        still(name, 16)
    animated("trophy", 4)
    animated("golden_elytra", 8)
    golden_wings()
    print("Chasing Gold items written")


if __name__ == "__main__":
    main()
