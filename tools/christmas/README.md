# Christmas kit

The kit's red armor and shield. Nothing here changes a vanilla item: the kit's items opt in through components.

| Item | Components |
| --- | --- |
| Helmet | `equippable={slot:"head",asset_id:"windsmp:christmas",equip_sound:"minecraft:item.armor.equip_netherite"}`, `item_model="windsmp:christmas_helmet"`, `enchantment_glint_override=false` |
| Chestplate | the same with `slot:"chest"` and `windsmp:christmas_chestplate` |
| Leggings | the same with `slot:"legs"` and `windsmp:christmas_leggings` |
| Boots | the same with `slot:"feet"` and `windsmp:christmas_boots` |
| Shield | `item_model="windsmp:christmas_shield"`, `enchantment_glint_override=false` |
| Sword, axe, pickaxe, spear, mace | `item_model="windsmp:christmas_sword"` (`_axe`, `_pickaxe`, `_spear`, `_mace`), `enchantment_glint_override=false` |

`enchantment_glint_override=false` turns vanilla's purple glint off for the item: the kit has a glint of its own, and
the two would lie on top of each other. The armor pieces must not carry a `trim` component either: vanilla would draw
that trim over the red.

## What is in the pack

- `assets/windsmp/equipment/christmas.json` and its two textures: netherite armor, all of it red (netherite's shading
  kept, its colour replaced).
- `assets/windsmp/items|models|textures/item/christmas_*`: the armor's inventory icons; the shield as a model of its
  own (vanilla's shield shape and hand positions), all of it red; and the sword, axe, pickaxe, spear and mace,
  which are vanilla's item definitions and models with the metal of their textures turned red (wooden handles stay
  wood; the mace is red all over).
- `glow_63`, `glow_69`, `glow_84`, `glow_88`, `glow_97`: for each client version from 1.21.6 to 26.3, vanilla's
  shader for worn armor (`entity.fsh`) and its shader for items (`item.fsh`, or
  `rendertype_item_entity_translucent_cull.fsh` before 26.1), each with an addition that is the kit's glint. A shine
  passes over what carries the kit's mark every six seconds: tilted 35 degrees, rising from the lower edge of the
  screen to the upper one, a soft glow that fades from a near-white core through pink into the red, with texels
  glittering inside it, unlit so it shows in the dark. Not on inventory icons: the game draws an icon once and
  keeps the picture, so a shine would freeze on it.
- The mark is a tint: red 254 of 255, which no eye sees. The armor's equipment layers carry it (`dyeable`, the way
  leather armor carries its dye) and so do the items' models (in their item definitions). No texture is involved, so
  a skin or another texture cannot carry the mark by accident.
- Clients up to 26.1 cannot read that tint on an item (their light is already in the colour there), so `glow_63`,
  `glow_69` and `glow_84` also hold the item textures once more with alpha 252, which their item shader reads
  instead. No vanilla item or block texture has that alpha.
- `glow_spear_old`: a plain spear for clients before 1.21.11, which have no spear and do not know what vanilla's
  spear definition asks for.

Pack formats between releases (snapshots) get no overlay: there the kit is simply red, with no glint.

## Rebuilding

Both scripts read an unpacked vanilla client (`assets/minecraft`), which is not kept in this repository.

```sh
tools/christmas/glow_shaders.py <1.21.6> <1.21.10> <26.1.2> <26.2> <26.3>   # each: .../assets/minecraft
tools/christmas/generate.py <26.3>/assets/minecraft
```

`glow_shaders.py` stops if vanilla's shader no longer has
the lines it adds to; a new client version needs a look.
