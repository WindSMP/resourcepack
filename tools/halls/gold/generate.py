#!/usr/bin/env python3
"""The `gold` hall behind Core's /chasinggold dialog: a mine lit by lanterns, gold veins in the rock, rails, and a
minecart heaped with gold where the figure stands in the other halls.

Draws the three sets every hall has (see tools/halls/README.md) in the same dark style, cuts them into tiles and
adds their glyphs to assets/golbg/font/hall.json after the last hall:

    python3 tools/halls/gold/generate.py

Deterministic (fixed seed). Copy the new assets/golbg/font/hall.json to Core's dialog/hall.json afterwards.
Needs Pillow.
"""
import json
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

PACK = Path(__file__).resolve().parents[3]
HALL = "gold"
TEXTURES = PACK / "assets/golbg/textures/hall"
FONT = PACK / "assets/golbg/font/hall.json"

PLAIN_W, PLAIN_H = 800, 320
WINDOW_W, WINDOW_H = 322, 187
WINDOW_X, WINDOW_Y = (316 + 640) // 4, 232 // 4
BACKDROP_W, BACKDROP_H = 640, 360
TILE_W, TILE_H = 120, 240
FLOOR_Y = 214

ROCK_TOP = (8, 7, 6)
ROCK_LOW = (24, 18, 12)
ROCK_FACE = (30, 23, 16)
FLOOR = (14, 11, 8)
WOOD = (58, 38, 20)
WOOD_DARK = (36, 23, 12)
GOLD = (255, 202, 98)
GOLD_DEEP = (196, 132, 30)
GOLD_LIGHT = (255, 240, 180)
STEEL = (70, 74, 82)


def lerp(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def glow(img, box, colour, strength, blur):
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).ellipse(box, fill=strength)
    img.paste(colour, mask=mask.filter(ImageFilter.GaussianBlur(blur)))


def plain():
    rnd = random.Random(2811)
    img = Image.new("RGB", (PLAIN_W, PLAIN_H), ROCK_TOP)
    d = ImageDraw.Draw(img)
    for y in range(FLOOR_Y):
        d.line([(0, y), (PLAIN_W, y)], fill=lerp(ROCK_TOP, ROCK_LOW, (y / FLOOR_Y) ** 1.3))
    # Rough rock: blotches of a lighter face.
    for _ in range(420):
        x, y = rnd.randrange(PLAIN_W), rnd.randrange(FLOOR_Y)
        r = rnd.randrange(2, 7)
        d.ellipse([x - r, y - r // 2, x + r, y + r // 2], fill=lerp(ROCK_LOW, ROCK_FACE, rnd.random()))
    # Stalactites along the ceiling.
    for x in range(0, PLAIN_W, 6):
        h = rnd.choice([3, 4, 6, 9, 14, 20])
        d.polygon([(x, 0), (x + 6, 0), (x + 3, h)], fill=ROCK_TOP)
    # Gold veins: little clusters in the rock, some catching the light.
    for _ in range(46):
        cx, cy = rnd.randrange(PLAIN_W), rnd.randrange(30, FLOOR_Y - 20)
        for _ in range(rnd.randrange(3, 9)):
            x, y = cx + rnd.randrange(-6, 7), cy + rnd.randrange(-4, 5)
            d.rectangle([x, y, x + 1, y], fill=rnd.choice([GOLD, GOLD_DEEP, GOLD_DEEP]))
        if rnd.random() < 0.4:
            d.point((cx, cy - 1), fill=GOLD_LIGHT)
    # Floor and rails.
    d.rectangle([0, FLOOR_Y, PLAIN_W, PLAIN_H], fill=FLOOR)
    d.line([(0, FLOOR_Y), (PLAIN_W, FLOOR_Y)], fill=ROCK_FACE)
    for x in range(-4, PLAIN_W, 12):
        d.rectangle([x, FLOOR_Y + 9, x + 7, FLOOR_Y + 11], fill=WOOD_DARK)
    for y in (FLOOR_Y + 8, FLOOR_Y + 12):
        d.line([(0, y), (PLAIN_W, y)], fill=STEEL)
    # Mine supports with lanterns, warm light on the rock and floor.
    for x in range(40, PLAIN_W, 150):
        glow(img, [x - 50, 40, x + 50, FLOOR_Y + 30], (70, 46, 14), 110, 18)
    d = ImageDraw.Draw(img)
    for x in range(40, PLAIN_W, 150):
        d.rectangle([x - 34, 60, x - 29, FLOOR_Y], fill=WOOD)
        d.rectangle([x + 29, 60, x + 34, FLOOR_Y], fill=WOOD)
        d.rectangle([x - 40, 54, x + 40, 61], fill=WOOD)
        d.line([(x - 40, 61), (x + 40, 61)], fill=WOOD_DARK)
        d.rectangle([x - 33, 60, x - 32, FLOOR_Y], fill=WOOD_DARK)
        d.line([(x, 61), (x, 70)], fill=STEEL)
        d.rectangle([x - 3, 70, x + 3, 79], fill=STEEL)
        d.rectangle([x - 2, 72, x + 2, 77], fill=GOLD_LIGHT)
    # A minecart heaped with gold where the figure stands in the other halls.
    cart(img, 222, FLOOR_Y + 8)
    # Dust in the lantern light.
    d = ImageDraw.Draw(img)
    for _ in range(140):
        x, y = rnd.randrange(PLAIN_W), rnd.randrange(30, FLOOR_Y)
        d.point((x, y), fill=lerp(ROCK_FACE, GOLD, rnd.random() * 0.5))
    return img


def cart(img, cx, rail):
    glow(img, [cx - 80, rail - 70, cx + 80, rail + 14], (90, 64, 18), 130, 14)
    d = ImageDraw.Draw(img)
    top, bottom = rail - 34, rail - 6
    d.polygon([(cx - 36, top), (cx + 36, top), (cx + 30, bottom), (cx - 30, bottom)], fill=(64, 68, 76))
    d.polygon([(cx - 36, top), (cx + 36, top), (cx + 34, top + 4), (cx - 34, top + 4)], fill=(96, 100, 110))
    for x in (cx - 20, cx, cx + 20):
        d.line([(x, top + 6), (x, bottom - 2)], fill=(48, 50, 58))
    for wx in (cx - 20, cx + 20):
        d.ellipse([wx - 6, bottom - 4, wx + 6, bottom + 8], fill=(30, 30, 34))
        d.ellipse([wx - 2, bottom, wx + 2, bottom + 4], fill=STEEL)
    # The heap: stacked ingots and nuggets, rising in the middle.
    rnd = random.Random(7)
    for i in range(70):
        t = rnd.random()
        x = cx - 32 + 64 * t
        h = 14 * math.sin(math.pi * t)
        y = top - rnd.random() * h
        d.rectangle([round(x) - 2, round(y) - 1, round(x) + 2, round(y) + 1], fill=rnd.choice([GOLD, GOLD_DEEP, GOLD]))
        if rnd.random() < 0.2:
            d.point((round(x), round(y) - 1), fill=GOLD_LIGHT)
    # Sparkles over the heap.
    for sx, sy in [(cx - 18, top - 20), (cx + 12, top - 24), (cx + 26, top - 10)]:
        d.line([(sx - 2, sy), (sx + 2, sy)], fill=GOLD_LIGHT)
        d.line([(sx, sy - 2), (sx, sy + 2)], fill=GOLD_LIGHT)


def window(src):
    crop = src.crop((WINDOW_X, WINDOW_Y, WINDOW_X + WINDOW_W, WINDOW_Y + WINDOW_H)).convert("RGB")
    d = ImageDraw.Draw(crop)
    d.rectangle([0, 0, WINDOW_W - 1, WINDOW_H - 1], outline=(4, 3, 2))
    d.rectangle([1, 1, WINDOW_W - 2, WINDOW_H - 2], outline=(58, 44, 26))
    return crop


def backdrop(src):
    wide = src.resize((BACKDROP_W, round(PLAIN_H * BACKDROP_W / PLAIN_W)), Image.LANCZOS)
    out = Image.new("RGB", (BACKDROP_W, BACKDROP_H), FLOOR)
    out.paste(wide, (0, 0))
    out = out.filter(ImageFilter.GaussianBlur(3))
    return Image.blend(out, Image.new("RGB", out.size, (3, 2, 1)), 0.45)


def tiles(name, img):
    names = []
    for y in range(0, img.height, TILE_H):
        for x in range(0, img.width, TILE_W):
            tile = img.crop((x, y, min(x + TILE_W, img.width), min(y + TILE_H, img.height))).convert("RGBA")
            file = f"{HALL}_{name}_{x}_{y}.png"
            tile.save(TEXTURES / file, optimize=True)
            names.append((file, tile.height))
    return names


def main():
    picture = plain()
    cut = tiles("backdrop", backdrop(picture)) + tiles("plain", picture) + tiles("window", window(picture))
    font = json.loads(FONT.read_text(encoding="utf-8"))
    providers = [p for p in font["providers"] if not p["file"].startswith(f"golbg:hall/{HALL}_")]
    last = max(ord(p["chars"][0]) for p in providers)
    for i, (file, height) in enumerate(cut):
        providers.append({"type": "bitmap", "file": f"golbg:hall/{file}", "height": height, "ascent": 0, "chars": [chr(last + 1 + i)]})
    font["providers"] = providers
    # The same compact one-line form as the rest of the file, so the diff is only the new glyphs.
    FONT.write_text(json.dumps(font, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
    print(f"{len(cut)} tiles, glyphs U+{last + 1:04X}..U+{last + len(cut):04X}")


if __name__ == "__main__":
    main()
