#!/usr/bin/env python3
"""The `advent` hall behind Core's /advent dialog: a snowy night with pines, string lights and a lit tree.

Draws the three sets every hall has (see tools/halls/README.md) in the same dark style as the halls the prototype
drew, cuts them into tiles and adds their glyphs to assets/golbg/font/hall.json after the last hall:

    python3 tools/halls/advent/generate.py

Run it from anywhere; it writes into the pack it lives in. Deterministic (fixed seed), so a rerun gives the same files.
Copy the new assets/golbg/font/hall.json to Core's src/main/resources/dialog/hall.json afterwards.
Needs Pillow.
"""
import json
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

PACK = Path(__file__).resolve().parents[3]
HALL = "advent"
TEXTURES = PACK / "assets/golbg/textures/hall"
FONT = PACK / "assets/golbg/font/hall.json"

PLAIN_W, PLAIN_H = 800, 320
WINDOW_W, WINDOW_H = 322, 187
# Where the window sits in the plain picture (scene px 316, 232 at 4 px per texel, the plain starting at -640).
WINDOW_X, WINDOW_Y = (316 + 640) // 4, 232 // 4
BACKDROP_W, BACKDROP_H = 640, 360
TILE_W, TILE_H = 120, 240
FLOOR_Y = 214

SKY_TOP = (6, 9, 18)
SKY_LOW = (14, 26, 46)
FLOOR = (10, 16, 28)
SNOW = (170, 190, 214)
SNOW_DIM = (96, 112, 136)
PINE_FAR = (12, 22, 34)
PINE_NEAR = (16, 34, 40)
LIGHTS = [(232, 72, 82), (255, 202, 98), (87, 229, 154), (59, 212, 232)]


def lerp(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def pine(draw, x, base, height, colour, snow=None):
    """A pine of stacked triangles, its foot at (x, base)."""
    tiers = 4
    width = height * 0.55
    for i in range(tiers):
        top = base - height + i * height / (tiers + 0.6)
        bottom = top + height / 2.2
        half = width / 2 * (0.45 + 0.55 * (i + 1) / tiers)
        draw.polygon([(x, top), (x - half, bottom), (x + half, bottom)], fill=colour)
        if snow:
            draw.line([(x - half * 0.7, bottom - 1), (x + half * 0.7, bottom - 1)], fill=snow)
    draw.rectangle([x - 1, base - height * 0.12, x + 1, base], fill=lerp(colour, (0, 0, 0), 0.3))


def plain():
    rnd = random.Random(1224)
    img = Image.new("RGB", (PLAIN_W, PLAIN_H), SKY_TOP)
    d = ImageDraw.Draw(img)
    for y in range(FLOOR_Y):
        d.line([(0, y), (PLAIN_W, y)], fill=lerp(SKY_TOP, SKY_LOW, (y / FLOOR_Y) ** 1.6))
    # Stars.
    for _ in range(140):
        x, y = rnd.randrange(PLAIN_W), rnd.randrange(150)
        b = rnd.choice([70, 100, 140])
        d.point((x, y), fill=(b, b + 10, b + 30))
    # The moon, soft, high on the right.
    moon = Image.new("L", (PLAIN_W, PLAIN_H), 0)
    ImageDraw.Draw(moon).ellipse([652, 62, 674, 84], fill=255)
    glow = moon.filter(ImageFilter.GaussianBlur(12))
    img.paste((40, 60, 92), mask=glow.point(lambda v: v // 2))
    img.paste((196, 212, 232), mask=moon)
    d = ImageDraw.Draw(img)
    # Far pines along the horizon, then nearer ones.
    for x in range(-10, PLAIN_W + 10, 9):
        pine(d, x + rnd.randrange(-3, 4), FLOOR_Y - 6, rnd.randrange(26, 44), PINE_FAR)
    for x in list(range(10, 230, 34)) + list(range(560, PLAIN_W, 36)):
        pine(d, x + rnd.randrange(-6, 7), FLOOR_Y + 2, rnd.randrange(56, 86), PINE_NEAR, SNOW_DIM)
    # The snowy ground.
    d.rectangle([0, FLOOR_Y, PLAIN_W, PLAIN_H], fill=FLOOR)
    for x in range(0, PLAIN_W, 2):
        h = 3 + 2 * math.sin(x / 23) + math.sin(x / 7)
        d.line([(x, FLOOR_Y - h), (x + 1, FLOOR_Y - h)], fill=SNOW_DIM)
        d.line([(x, FLOOR_Y - h + 1), (x + 1, FLOOR_Y + 2)], fill=lerp(SNOW_DIM, FLOOR, 0.5))
    d.line([(0, FLOOR_Y + 16), (PLAIN_W, FLOOR_Y + 16)], fill=lerp(FLOOR, SNOW_DIM, 0.25))
    # The lit tree, where the figure stands in the other halls (left of the menu).
    tree(img, 222, FLOOR_Y + 4)
    d = ImageDraw.Draw(img)
    # String lights swinging between posts across the top.
    posts = list(range(0, PLAIN_W + 1, 100))
    for a, b in zip(posts, posts[1:]):
        points = [(a + (b - a) * t / 20, 18 + 14 * math.sin(math.pi * t / 20)) for t in range(21)]
        d.line(points, fill=(30, 38, 52))
        for i, (x, y) in enumerate(points[2:-1:3]):
            colour = LIGHTS[(i + a // 100) % len(LIGHTS)]
            halo = lerp(SKY_TOP, colour, 0.35)
            d.ellipse([x - 2, y, x + 2, y + 4], fill=halo)
            d.rectangle([x - 1, y + 1, x, y + 2], fill=colour)
    # Falling snow.
    for _ in range(260):
        x, y = rnd.randrange(PLAIN_W), rnd.randrange(FLOOR_Y)
        d.point((x, y), fill=SNOW if rnd.random() < 0.3 else SNOW_DIM)
    return img


def tree(img, cx, base):
    """The lit tree: stacked tiers with drooping ends and a dark outline, snow on the branch tips, strands of lights
    swinging across it, a glowing star, and presents either side of the trunk."""
    height = 132
    trunk_h = 10
    foot = base - trunk_h
    green, shade, outline = (24, 86, 60), (17, 64, 46), (8, 30, 24)
    # Its warm glow on the snow.
    glow = Image.new("L", img.size, 0)
    ImageDraw.Draw(glow).ellipse([cx - 74, base - 12, cx + 74, base + 10], fill=120)
    img.paste((72, 60, 38), mask=glow.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(img)
    d.rectangle([cx - 4, foot - 2, cx + 4, base], fill=(58, 36, 22))
    d.rectangle([cx + 1, foot - 2, cx + 4, base], fill=(44, 27, 17))
    tiers = 5
    shapes = []
    for i in range(tiers):
        top = foot - height + i * (height - 26) / tiers
        bottom = top + 34 + i * 4
        half = 14 + i * 11
        droop = 3 + i
        # Left edge down to a drooping tip, a scalloped hem back to the right tip, up the right edge.
        hem = [(cx - half + (2 * half) * k / 8, bottom + (droop if k % 2 else 0) - abs(k - 4)) for k in range(9)]
        shapes.append([(cx, top)] + [(cx - half - 2, bottom + droop)] + hem[1:-1] + [(cx + half + 2, bottom + droop)])
    # Back to front, so each tier's hem lies over the one below it.
    for points in reversed(shapes):
        d.polygon(points, fill=green, outline=outline)
        # The right side in shade.
        right = [(x, y) for x, y in points if x >= cx]
        d.polygon([(cx, points[0][1] + 2)] + right[1:] + [(cx, right[-1][1])], fill=shade)
    for points in shapes:
        # Snow on the two branch tips.
        for x, y in (points[1], points[-1]):
            step = 1 if x < cx else -1
            for k in range(5):
                d.point((round(x) + step * k, round(y) - 1 - (k // 2)), fill=SNOW if k < 3 else SNOW_DIM)
    # Strands of lights swinging across the tree, bulbs alternating colours.
    for j, frac in enumerate((0.28, 0.5, 0.72, 0.9)):
        y0 = foot - height + frac * height
        half = 4 + frac * 46
        points = [(cx - half + 2 * half * t / 12, y0 + 5 * math.sin(math.pi * t / 12) + 6 * t / 12) for t in range(13)]
        d.line(points, fill=(40, 52, 40))
        for k, (x, y) in enumerate(points[1:-1:2]):
            colour = LIGHTS[(k + j) % len(LIGHTS)]
            d.rectangle([round(x) - 1, round(y), round(x), round(y) + 1], fill=colour)
            d.point((round(x), round(y) + 2), fill=lerp(colour, green, 0.5))
    # The star, with a soft halo.
    sy = foot - height - 3
    halo = Image.new("L", img.size, 0)
    ImageDraw.Draw(halo).ellipse([cx - 14, sy - 14, cx + 14, sy + 14], fill=110)
    img.paste((150, 120, 60), mask=halo.filter(ImageFilter.GaussianBlur(6)))
    d = ImageDraw.Draw(img)
    d.polygon([(cx, sy - 8), (cx + 2, sy - 2), (cx + 8, sy - 2), (cx + 3, sy + 2), (cx + 5, sy + 8),
               (cx, sy + 4), (cx - 5, sy + 8), (cx - 3, sy + 2), (cx - 8, sy - 2), (cx - 2, sy - 2)], fill=(255, 214, 110))
    d.point((cx, sy), fill=(255, 244, 200))
    # Presents either side of the trunk.
    for x, w, h, colour, ribbon in [(-34, 16, 11, (178, 36, 52), (255, 202, 98)), (-17, 11, 15, (31, 122, 77), (232, 72, 82)),
                                    (17, 15, 10, (59, 120, 200), (255, 202, 98)), (34, 11, 13, (232, 180, 70), (178, 36, 52))]:
        left, right, top = cx + x - w // 2, cx + x + w // 2, base - h
        d.rectangle([left, top, right, base], fill=colour)
        d.rectangle([right - 2, top, right, base], fill=lerp(colour, (0, 0, 0), 0.25))
        d.line([(cx + x, top), (cx + x, base)], fill=ribbon)
        d.line([(left, top + h // 2), (right, top + h // 2)], fill=ribbon)
        d.point((cx + x - 1, top - 1), fill=ribbon)
        d.point((cx + x + 1, top - 1), fill=ribbon)


def window(src):
    crop = src.crop((WINDOW_X, WINDOW_Y, WINDOW_X + WINDOW_W, WINDOW_Y + WINDOW_H)).convert("RGB")
    d = ImageDraw.Draw(crop)
    d.rectangle([0, 0, WINDOW_W - 1, WINDOW_H - 1], outline=(4, 7, 13))
    d.rectangle([1, 1, WINDOW_W - 2, WINDOW_H - 2], outline=(36, 44, 58))
    return crop


def backdrop(src):
    wide = src.resize((BACKDROP_W, round(PLAIN_H * BACKDROP_W / PLAIN_W)), Image.LANCZOS)
    out = Image.new("RGB", (BACKDROP_W, BACKDROP_H), FLOOR)
    out.paste(wide, (0, 0))
    out = out.filter(ImageFilter.GaussianBlur(3))
    return Image.blend(out, Image.new("RGB", out.size, (2, 4, 9)), 0.45)


def tiles(name, img):
    """Cuts [img] row by row (y, then x) into tiles; returns their file names in that order."""
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
    # The same compact one-line form the prototype wrote, so the diff is only the new glyphs.
    FONT.write_text(json.dumps(font, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
    print(f"{len(cut)} tiles, glyphs U+{last + 1:04X}..U+{last + len(cut):04X}")


if __name__ == "__main__":
    main()
