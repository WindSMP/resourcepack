# Wind tools

Core's wind tools in 3D: each is vanilla's tool recoloured in the Breeze's colours and built pixel by pixel into cubes,
the head a little thicker than the handle. The sell axe keeps a gold head, so it never looks like the tree axe. The pack
shows them only on the custom model data Core gives the tools, so plain vanilla items are untouched.

| Tool | Vanilla item | Custom model data | Built from |
| --- | --- | --- | --- |
| Wind pickaxe | `netherite_pickaxe` | 9101 | diamond pickaxe |
| Tree axe | `netherite_axe` | 9102 | diamond axe |
| Wind shovel | `netherite_shovel` | 9103 | diamond shovel |
| Drain bucket | `bucket` | 9104 | bucket |
| Sell axe | `golden_axe` | 9110 | golden axe |

## Rebuilding

    python3 tools/models/wind_tools_tex.py <vanilla item textures> tools/models
    python3 tools/models/wind_bucket_tex.py tools/models
    python3 tools/models/wind_tools_build.py tools/models/<tool>_tex.png tools/models/<tool>_depth.json <ops.json>

`<vanilla item textures>` is `assets/minecraft/textures/item` of an unpacked 26.3 client jar (only read). The first
script writes each tool's texture and depth map, the second gives the bucket its rim, and the third turns a texture
into the cube list for the `.bbmodel` in this folder. Open the `.bbmodel` files in Blockbench to edit a tool, then
export it as a Java item model into `assets/windsmp/models/item/` (keep the `display` block that is there).

The mining sound is in `tools/sounds` (`wind_tool.sh`).
