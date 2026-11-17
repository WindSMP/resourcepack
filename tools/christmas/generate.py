#!/usr/bin/env python3
"""Builds the Christmas kit's textures and models from vanilla's.

    tools/christmas/generate.py <vanilla assets dir>

<vanilla assets dir> is the `assets/minecraft` folder of an unpacked client jar (26.3). It is only read: the armor
and shield are Mojang's, so they are not kept in this repository, only what is built from them.

The armor is netherite recoloured red, and so are the shield and the metal of the sword, axe, pickaxe, spear and mace.
The shader overlays run a shine across all of it, and know the kit by a tint: red 254 of 255, which no eye sees.
The armor's equipment layers carry it (the way leather armor carries its dye), and so do the items' models. The
textures themselves are plain and opaque. Clients up to 26.1 cannot read the tint on an item (their light is already
in the colour there), so their overlays get the item textures once more with alpha 252. See glow_shaders.py.
"""
import json, os, sys
from PIL import Image

V = sys.argv[1]
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
OUT = os.path.join(ROOT, 'assets', 'windsmp')
# Netherite's shading kept, its colour replaced by red, darkest to brightest.
RED_RAMP = [(58, 4, 8), (118, 8, 12), (176, 14, 18), (222, 28, 30), (255, 92, 86)]
# The alpha that marks an item's texels for the clients up to 26.1. No vanilla texture their item shader draws
# (items and blocks) has it, counted over the clients from 1.21.8 to 26.1.
SHINE = 252
# The same tint as a packed ARGB, for an equipment layer.
SHINE_DYE = {'color_when_undyed': -65537}
# The tint that marks an item's model: white but for a red of 254, as the packed ARGB that item definitions take.
SHINE_TINT = [{'type': 'minecraft:constant', 'value': -65537}]


def vanilla(path):
    return Image.open(os.path.join(V, 'textures', path)).convert('RGBA')


def save(image, path):
    full = os.path.join(OUT, 'textures', path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    image.save(full)


def write(path, data):
    full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w') as handle:
        json.dump(data, handle, indent=2)
        handle.write('\n')


def wooden(r, g, b):
    """Whether a texel is a tool's wooden handle rather than its netherite: clearly brown."""
    return r > b and max(r, g, b) > 0 and (max(r, g, b) - min(r, g, b)) / max(r, g, b) > 0.4


def red(image, keep=lambda r, g, b: False):
    """image with every opaque texel recoloured along the red ramp by how bright it was, but for those keep picks."""
    out = image.copy()
    px = out.load()
    lumas = [0.299 * px[x, y][0] + 0.587 * px[x, y][1] + 0.114 * px[x, y][2]
             for y in range(out.height) for x in range(out.width) if px[x, y][3] and not keep(*px[x, y][:3])]
    low, high = min(lumas), max(lumas)
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = px[x, y]
            if a == 0 or keep(r, g, b):
                continue
            t = (0.299 * r + 0.587 * g + 0.114 * b - low) / max(1.0, high - low) * (len(RED_RAMP) - 1)
            i = min(len(RED_RAMP) - 2, int(t))
            c0, c1 = RED_RAMP[i], RED_RAMP[i + 1]
            px[x, y] = tuple(int(c0[k] + (c1[k] - c0[k]) * (t - i)) for k in range(3)) + (a,)
    return out


def marked(image):
    """image with every opaque texel given the alpha the shader overlays look for."""
    px = image.load()
    for y in range(image.height):
        for x in range(image.width):
            if px[x, y][3] == 255:
                px[x, y] = px[x, y][:3] + (SHINE,)
    return image


def armor():
    save(red(vanilla('entity/equipment/humanoid/netherite.png')), 'entity/equipment/humanoid/christmas.png')
    save(red(vanilla('entity/equipment/humanoid_leggings/netherite.png')),
         'entity/equipment/humanoid_leggings/christmas.png')
    # "dyeable" tints the layer, as leather armor is dyed: the kit's armor has no dye, so it always gets this colour.
    write('equipment/christmas.json', {'layers': {
        'humanoid': [{'texture': 'windsmp:christmas', 'dyeable': SHINE_DYE}],
        'humanoid_leggings': [{'texture': 'windsmp:christmas', 'dyeable': SHINE_DYE}],
    }})


def icons():
    for piece in ('helmet', 'chestplate', 'leggings', 'boots'):
        save(red(vanilla('item/netherite_%s.png' % piece)), 'item/christmas_%s.png' % piece)
        write('models/item/christmas_%s.json' % piece, {
            'parent': 'minecraft:item/generated', 'textures': {'layer0': 'windsmp:item/christmas_%s' % piece}})
        write('items/christmas_%s.json' % piece, {
            'model': {'type': 'minecraft:model', 'model': 'windsmp:item/christmas_%s' % piece, 'tints': SHINE_TINT}})


def tools():
    """The sword, axe, pickaxe, spear and mace: vanilla's item definitions and models, with the metal of their
    textures turned red (wooden handles stay wood) and their models tinted for the shine."""
    def ours(name):
        return 'christmas_' + (name[len('netherite_'):] if name.startswith('netherite_') else name)

    def model(reference):
        name = reference.split('item/')[1]
        with open(os.path.join(V, 'models', 'item', name + '.json')) as handle:
            data = json.load(handle)
        for layer, texture in data['textures'].items():
            source = texture.split('item/')[1]
            save(red(vanilla('item/%s.png' % source), wooden), 'item/%s.png' % ours(source))
            data['textures'][layer] = 'windsmp:item/' + ours(source)
        write('models/item/%s.json' % ours(name), data)
        return 'windsmp:item/' + ours(name)

    def rewritten(node):
        if isinstance(node, dict):
            if node.get('type') == 'minecraft:model':
                return dict(node, model=model(node['model']), tints=SHINE_TINT)
            return {key: rewritten(value) for key, value in node.items()}
        if isinstance(node, list):
            return [rewritten(value) for value in node]
        return node

    for item in ('netherite_sword', 'netherite_axe', 'netherite_pickaxe', 'netherite_spear', 'mace'):
        with open(os.path.join(V, 'items', item + '.json')) as handle:
            write('items/%s.json' % ours(item), rewritten(json.load(handle)))


def shield():
    # The plain shield (planks in an iron rim, with its handle), all of it red.
    save(red(vanilla('entity/shield/shield_base_nopattern.png')), 'item/christmas_shield.png')

    def uv(x0, y0, x1, y1):
        return [x0 / 4.0, y0 / 4.0, x1 / 4.0, y1 / 4.0]

    def box(x, y, z, w, h, d, u, v):
        """A box as vanilla's shield model has it, turned the way the shield renderer turns it (y and z flipped)."""
        faces = {
            'south': uv(u + d, v + d, u + d + w, v + d + h),            # the model's front, away from the holder
            'north': uv(u + d + w + d, v + d, u + d + w + d + w, v + d + h),
            'west': uv(u, v + d, u + d, v + d + h),
            'east': uv(u + d + w, v + d, u + d + w + d, v + d + h),
            'up': uv(u + d, v, u + d + w, v + d),
            'down': uv(u + d + w, v, u + d + w + w, v + d),
        }
        return {
            'from': [x, -(y + h), -(z + d)], 'to': [x + w, -y, -z],
            # tintindex 0: the item definition's tint reaches these faces.
            'faces': {name: {'uv': coords, 'texture': '#shield', 'tintindex': 0} for name, coords in faces.items()},
        }

    with open(os.path.join(V, 'models', 'item', 'shield.json')) as handle:
        held = json.load(handle)
    with open(os.path.join(V, 'models', 'item', 'shield_blocking.json')) as handle:
        blocking = json.load(handle)
    write('models/item/christmas_shield.json', {
        'gui_light': 'front',
        'texture_size': [64, 64],
        'textures': {'shield': 'windsmp:item/christmas_shield', 'particle': 'windsmp:item/christmas_shield'},
        'elements': [box(-6, -11, -2, 12, 22, 1, 0, 0), box(-1, -3, -1, 2, 6, 6, 26, 0)],
        'display': held['display'],
    })
    write('models/item/christmas_shield_blocking.json', {
        'parent': 'windsmp:item/christmas_shield', 'display': blocking['display']})
    write('items/christmas_shield.json', {'model': {
        'type': 'minecraft:condition', 'property': 'minecraft:using_item',
        'on_false': {'type': 'minecraft:model', 'model': 'windsmp:item/christmas_shield', 'tints': SHINE_TINT},
        'on_true': {'type': 'minecraft:model', 'model': 'windsmp:item/christmas_shield_blocking', 'tints': SHINE_TINT},
    }})


def old_clients():
    """The item textures again for the clients up to 26.1, in their overlays: the same, with every opaque texel
    given the alpha the shader overlays look for. Those clients cannot read the models' tint (see glow_shaders.py)."""
    items = os.path.join(OUT, 'textures', 'item')
    for overlay in ('glow_63', 'glow_69', 'glow_84'):
        target = os.path.join(ROOT, overlay, 'assets', 'windsmp', 'textures', 'item')
        os.makedirs(target, exist_ok=True)
        for name in sorted(os.listdir(items)):
            if name.startswith('christmas_') and name.endswith('.png'):
                marked(Image.open(os.path.join(items, name)).convert('RGBA')).save(os.path.join(target, name))


def old_spear():
    """The spear for clients before 1.21.11, which have no spear: the server shows them another item in its place,
    with this item model still on it. Vanilla's spear definition asks for things those clients do not know (a model
    for the hand, a display context), and they would show a missing model: they get the plain icon, held like any
    tool."""
    base = os.path.join(ROOT, 'glow_spear_old', 'assets', 'windsmp')
    for path, data in (
        ('models/item/christmas_spear_plain.json',
         {'parent': 'minecraft:item/handheld', 'textures': {'layer0': 'windsmp:item/christmas_spear'}}),
        ('items/christmas_spear.json',
         {'model': {'type': 'minecraft:model', 'model': 'windsmp:item/christmas_spear_plain', 'tints': SHINE_TINT}}),
    ):
        full = os.path.join(base, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, 'w') as handle:
            json.dump(data, handle, indent=2)
            handle.write('\n')


armor()
icons()
tools()
shield()
old_clients()
old_spear()
print('built into', os.path.normpath(OUT))
