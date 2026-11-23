#!/usr/bin/env python3
"""The golden elytra's shine on worn wings: adds a gold band and glitter to each glow overlay's entity.fsh, next to
the Christmas kit's (tools/christmas). Run it again after tools/christmas/glow_shaders.py rewrites those shaders.

    python3 tools/goldevent/wings_shine.py

Two marks together, so nothing else can switch it on: the golden elytra's equipment tint
(assets/windsmp/equipment/golden_elytra.json, `dyeable`): green 254 of 255 with red and blue full, and its wing
texture's alpha of 254 (set by this script). Dyed leather or wolf armour can reach the tint, but its textures are
vanilla and fully opaque; a skin can carry the alpha, but players are drawn untinted. The wings
glow a little always and pulse, a wide band runs down them every 2.5 s, and texels sparkle all over.
Rerunning replaces an earlier version of the block, so it never ends up there twice.
"""
import glob
import os
import re

from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
ANCHOR = "        windsmpShine = min(1.0, windsmpGlow + windsmpGlow * windsmpGlint);\n    }\n"
MARKER = "// WindSMP: the golden elytra's shine"

BLOCK = """    {marker} (tools/goldevent/wings_shine.py).
    if (abs(color.a - 0.9960784) < 0.002 && {tint}.r > 0.0 && abs({tint}.g / {tint}.r - 0.9960784) < 0.0015 && abs({tint}.b - {tint}.r) < 0.0006 && abs(gl_FragCoord.w - 1.0) > 0.0001) {{
        float windsmpTicks = GameTime * 24000.0;
        vec2 windsmpWing = texCoord0 * vec2(64.0, 32.0) - vec2(34.0, 2.0);
        // A wide bright band down the wing, tilted, once every 2.5 s, and a second, fainter one behind it.
        float windsmpWay = windsmpWing.y / 20.0 * 0.9 + windsmpWing.x / 12.0 * 0.35 - windsmpTicks / 50.0;
        float windsmpOff = abs(fract(windsmpWay) - 0.5);
        float windsmpTrail = abs(fract(windsmpWay + 0.22) - 0.5);
        float windsmpGlow = exp(-(windsmpOff * windsmpOff) / (0.09 * 0.09)) + 0.45 * exp(-(windsmpTrail * windsmpTrail) / (0.05 * 0.05));
        float windsmpCore = exp(-(windsmpOff * windsmpOff) / (0.025 * 0.025));
        // Sparkles all over, all the time: each texel flashes at its own beat.
        vec2 windsmpTexel = floor(texCoord0 * vec2(textureSize(Sampler0, 0)));
        float windsmpGrain = fract(sin(dot(windsmpTexel, vec2(12.9898, 78.233))) * 43758.5453);
        float windsmpSparkle = windsmpGrain > 0.78 ? pow(abs(sin(3.14159265 * (windsmpTicks * 0.06 + windsmpGrain * 20.0))), 12.0) : 0.0;
        // A slow pulse of the whole wing.
        float windsmpPulse = 0.5 + 0.5 * sin(windsmpTicks * 0.1);
        color.rgb *= 1.05 + 0.12 * windsmpPulse;
        color.rgb += windsmpGlow * vec3(0.42, 0.30, 0.06);
        color.rgb = mix(color.rgb, vec3(1.0, 0.94, 0.66), 0.55 * min(1.0, windsmpGlow * windsmpGlow));
        color.rgb = mix(color.rgb, vec3(1.0, 0.99, 0.92), 0.85 * windsmpCore);
        color.rgb = mix(color.rgb, vec3(1.0), 0.95 * windsmpSparkle);
        color.rgb = min(color.rgb, vec3(1.0));
        // Unlit: the wings glow, a little always and fully where the light passes.
        windsmpShine = min(1.0, 0.6 + windsmpGlow + windsmpSparkle);
    }}
"""


def main() -> None:
    for path in sorted(glob.glob(os.path.join(ROOT, "glow_*/assets/minecraft/shaders/core/entity.fsh"))):
        source = open(path, encoding="utf-8").read()
        # An older version of the block goes, so a rerun brings it up to date.
        source = re.sub(r"    // WindSMP: the golden elytra's shine.*?\n    }\n", "", source, flags=re.S)
        if source.count(ANCHOR) != 1:
            raise SystemExit(f"{path}: the Christmas shine's end isn't where it was; it needs a look")
        tint = re.search(r"&& (\w+)\.g > 0\.0 && abs\(\1\.r / \1\.g - 0\.9960784\)", source)
        if not tint:
            raise SystemExit(f"{path}: the Christmas kit's mark isn't where it was; it needs a look")
        source = source.replace(ANCHOR, ANCHOR + BLOCK.format(marker=MARKER, tint=tint.group(1)))
        open(path, "w", encoding="utf-8").write(source)
        print("patched", os.path.relpath(path, ROOT))


def mark_texture():
    """Gives every visible texel of the wings alpha 254 (still opaque in the game's cutout armour rendering)."""
    path = os.path.join(ROOT, "assets", "windsmp", "textures", "entity", "equipment", "wings", "golden_elytra.png")
    image = Image.open(path).convert("RGBA")
    image.putdata([(r, g, b, 254 if a > 0 else 0) for r, g, b, a in image.getdata()])
    image.save(path)


if __name__ == "__main__":
    main()
    mark_texture()
