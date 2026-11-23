# Hall backgrounds and dialog layouts

The GUI-Design-v3 dialog engine (prototype jar `DialogStore-1.0.0.jar`, branch `gui-design-v3`, commit 49bfa2e)
drew some pack assets at server start-up (`HallArt.buildPack()`) and merged them into the pack it served itself.
They are checked in here as static files so the network pack is complete without that runtime step:

| Path | What |
|---|---|
| `assets/golbg/font/hall.json` | font `golbg:hall`: 290 bitmap glyphs U+E000..U+E121, `ascent` 0 (the shader positions them) |
| `assets/golbg/textures/hall/<hall>_<set>_<x>_<y>.png` | tiles (max 120 x 240 texels, 1 texel = 1 GUI px) of each hall: sets `backdrop`, `plain`, `window` |
| `assets/windsmp/layout/duels/layout.json` | duels menu / scene layout the plugin reads (`GolLayout`, `DuelsLayout`) |
| `assets/windsmp/layout/store/glyphs.json` | store menu glyph layout the plugin reads (`Glyphs`) |

Halls, in registration (= codepoint) order: `demo, settings, stats, leaderboard, welcome_welcome, welcome_rules,
welcome_media, rtp, welcome_store, crates`, then `advent` (U+E122..U+E13E, `tools/halls/advent/generate.py`) and `gold`
(U+E13F..U+E15B, `tools/halls/gold/generate.py`), drawn by those generators, not by the prototype; per hall 29 tiles: backdrop (6 x 2), plain (7 x 2), window (3 x 1).
Within a hall, tiles are cut row by row (y, then x), back to front. Codepoints are assigned sequentially
(backdrop, plain, window per hall), so the glyph for a tile is the `chars` entry of its provider in `hall.json`.

The layout JSONs are server data, not client assets; they live in the pack only so pack and layout ship together.
Clients ignore them.

## Regenerating

`tools/halls/dump-halls.sh /path/to/DialogStore-1.0.0.jar` runs the prototype's own `HallArt` code headlessly
(`DumpHalls.java` registers the scenes in the same order as `GoliathModule.enable` and calls `buildPack()`;
`stub/.../ItemStack.java` stands in for Bukkit items, which only scene icons use, never the hall pictures).
Verified on 2026-11-15: the output is byte-identical to what the jar serves from a real Paper 26.2 server (JDK 25).
Java2D rendering can differ between JDK versions; rerun on the same JDK if you want byte-identical output.

`tools/` is not part of the released `resource-pack.zip`.

The `advent` hall (Core's /advent dialog) is drawn by `python3 tools/halls/advent/generate.py` (Pillow), which also adds
its glyphs to `hall.json`. Copy `hall.json` to Core's `dialog/hall.json` afterwards.

The `gold` hall (Core's /chasinggold dialog) is drawn by `python3 tools/halls/gold/generate.py` the same way.
