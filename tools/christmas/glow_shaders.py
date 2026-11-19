#!/usr/bin/env python3
"""Builds the shader overlays that run a shine across the Christmas kit, for every client from 1.21.6 on.

    tools/christmas/glow_shaders.py <1.21.6> <1.21.10> <26.1.2> <26.2> <26.3>

Each argument is the `assets/minecraft` folder of that unpacked client. Vanilla's shader for worn armor and its shader
for items are taken as they are, with one addition each: what carries the kit's mark is drawn as it is, and a shine
passes over it every six seconds, tilted 35 degrees and rising: a soft glow that fades from a near-white core through
pink into the red, with texels glittering inside it, unlit so it shows in the dark too. It is the kit's own glint, in place of vanilla's purple one, which the kit's items turn off
(`enchantment_glint_override=false`). The shine is placed on what carries it, not on the screen or in the world, so
it passes over a player at the same moment for everyone who sees them, however they look at them, and stays on
them as they walk, jump or fall (a band placed on the screen moved as the viewer looked up or down or flew higher; one
placed in the world moved as the wearer did). Armor is always drawn on vanilla's humanoid model with its texture laid
out box by box, so the texel tells how high up the body the fragment is, and the band rises from the feet to the
head. An item's band lies on its texture in the item atlas and rises across it, 35 degrees off the vertical.

The game time comes from the Globals block. Every client from 1.21.6 on binds that block to any shader that declares
it, whether or not the pipeline lists it (GlProgram's built-in uniforms), so declaring it here is enough.

The mark is a tint (see generate.py): a vertex colour whose red is 254/255 of its green and blue. The armor's
equipment layers and the items' models carry it. Lighting scales all three alike, so the ratio survives it, and no
texture is involved: a skin or another pack's texture cannot carry the mark by accident, and no vanilla tint is that
colour.
- Worn armor, every version: read in `entity.fsh`, which gets its light apart from the vertex colour.
- Items from 26.2 on: read in `item.fsh` the same way.
- Items up to 26.1, in `rendertype_item_entity_translucent_cull.fsh` (1.21.x) and `item.fsh` (26.1): the light map
  is already in the vertex colour there and it is not grey, so the tint cannot be read back. These clients get item
  textures with alpha 252 instead (in their overlays only), and the mark is read from the texel. No vanilla item or
  block texture has that alpha.
"""
import json, os, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
# overlay directory -> (pack formats it is for, index of the client it is built from, its item shader)
# and whether its items are marked through the alpha of their textures)
OLD_ITEM, ITEM = 'rendertype_item_entity_translucent_cull', 'item'
OVERLAYS = {
    'glow_63': ((63, 64), 0, OLD_ITEM, True),   # 1.21.6 to 1.21.8
    'glow_69': ((69, 75), 1, OLD_ITEM, True),   # 1.21.9 to 1.21.11
    'glow_84': ((84, 87), 2, ITEM, True),       # 26.1
    'glow_88': ((88, 88), 3, ITEM, False),      # 26.2
    'glow_97': ((97, 97), 4, ITEM, False),      # 26.3
}
SAMPLER = 'uniform sampler2D Sampler0;\n'
STATE = SAMPLER + ('\n// WindSMP: how much of the Christmas kit\'s shine is on this fragment, 0 to 1 (see tools/christmas).\n'
                   'float windsmpShine = 0.0;\n')
# The game time runs from 0 to 1 over a day-night cycle of 1200 seconds: 200 passes of six seconds, a whole number,
# so the wrap does not show (the glitter's flicker fits it too). One band follows the next 8 blocks behind, so a
# player or an item has one band on it at a time.
#
# On the wearer: armor is drawn on vanilla's humanoid model, its texture 64 by 32 texels laid out box by box
# (HumanoidModel.createMesh, whose layout the armor mesh keeps; ModelPart.Cube): a row of top and bottom faces, below
# it a row of sides. The box is told by where the texel lies, and the texel's place in it tells how high up the body
# and how far across it the fragment is, in model units: 16 to a block, y downwards from the neck with the feet at 24,
# x towards the wearer's left; the player is drawn at 15/16. Arms and legs swing with their boxes, so the band stays
# on the body as the wearer moves. The left arm and leg use the right one's texels, mirrored: a texture that runs the
# other way round on the screen (ALONG, taken before any branch, where derivatives are
# defined). Seen on a face that is not mirrored, u runs to the right on the screen and v downwards, so u x v is negative there.
ON_THE_BODY = """vec2 windsmpOnTexture = texCoord0 * vec2(64.0, 32.0);
        // The box: its corner on the texture, its width, height and depth, the model height of its top and the model x
        // of its right side (for an arm or a leg: the right one's).
        vec2 windsmpCorner; vec3 windsmpSize; float windsmpTop; float windsmpRight;
        if (windsmpOnTexture.y < 16.0) {
            // the head, and the hat over it
            windsmpCorner = vec2(windsmpOnTexture.x < 32.0 ? 0.0 : 32.0, 0.0); windsmpSize = vec3(8.0); windsmpTop = -8.0; windsmpRight = -4.0;
        } else if (windsmpOnTexture.x < 16.0) {
            // a leg (boots are drawn on it too)
            windsmpCorner = vec2(0.0, 16.0); windsmpSize = vec3(4.0, 12.0, 4.0); windsmpTop = 12.0; windsmpRight = -3.9;
        } else if (windsmpOnTexture.x < 40.0) {
            // the body
            windsmpCorner = vec2(16.0, 16.0); windsmpSize = vec3(8.0, 12.0, 4.0); windsmpTop = 0.0; windsmpRight = -4.0;
        } else {
            // an arm
            windsmpCorner = vec2(40.0, 16.0); windsmpSize = vec3(4.0, 12.0, 4.0); windsmpTop = 0.0; windsmpRight = -8.0;
        }
        vec2 windsmpInBox = windsmpOnTexture - windsmpCorner;
        float windsmpDown;
        float windsmpAcross;
        if (windsmpInBox.y >= windsmpSize.z) {
            // The row of sides, from the right side round the front, the left side and the back: down the box.
            windsmpDown = clamp(windsmpInBox.y - windsmpSize.z, 0.0, windsmpSize.y);
            float windsmpRound = windsmpInBox.x - windsmpSize.z;
            windsmpAcross = windsmpRound < 0.0 ? 0.0
                : windsmpRound < windsmpSize.x ? windsmpRound
                : windsmpRound < windsmpSize.x + windsmpSize.z ? windsmpSize.x
                : windsmpSize.x + windsmpSize.z + windsmpSize.x - windsmpRound;
        } else {
            // The row above it: the top face, then the bottom face.
            bool windsmpBottom = windsmpInBox.x >= windsmpSize.z + windsmpSize.x;
            windsmpDown = windsmpBottom ? windsmpSize.y : 0.0;
            windsmpAcross = windsmpInBox.x - windsmpSize.z - (windsmpBottom ? windsmpSize.x : 0.0);
        }
        float windsmpX = windsmpRight + clamp(windsmpAcross, 0.0, windsmpSize.x);
        // The left arm or leg: the right one's texels, mirrored.
        if (windsmpAlongX.x * windsmpAlongY.y - windsmpAlongY.x * windsmpAlongX.y > 0.0) {
            windsmpX = -windsmpX;
        }
        // In blocks above the feet and towards the wearer's left; across the band: 35 degrees off the vertical, an
        // eighth of a band per block upwards, so seen from the front the band lies 35 degrees off the horizontal and
        // rises to the right.
        float windsmpWay = (24.0 - windsmpTop - windsmpDown) / 16.0 * 0.9375 * 0.125
            - windsmpX / 16.0 * 0.9375 * 0.0875262 - GameTime * 200.0;"""
# How the texture runs on the screen, for ON_THE_BODY: taken right after the texture is read.
ALONG = """
    // WindSMP: how the texture runs on the screen, for the Christmas kit's shine (see tools/christmas).
    vec2 windsmpAlongX = dFdx(texCoord0);
    vec2 windsmpAlongY = dFdy(texCoord0);"""
# On the item: its place on the item atlas, 16 texels to a block. The atlas is the same for everyone with the same
# client and packs, and the item's texture goes with the item: in the hand, on the ground, in someone else's hand.
ON_THE_SPRITE = """vec2 windsmpOnAtlas = texCoord0 * vec2(textureSize(Sampler0, 0)) / 16.0;
        // Across the band: 35 degrees off the vertical towards the texture's right (its rows run downwards), so the
        // band lies 35 degrees off the horizontal and falls to the right. Vanilla draws a sword, an axe, a pickaxe and
        // a mace rising to the right, the handle at the lower left: the band crosses them and runs from the handle to
        // the tip. An eighth of a band per block.
        float windsmpWay = dot(vec2(windsmpOnAtlas.x, -windsmpOnAtlas.y), vec2(0.5735764, 0.8191520)) * 0.125 - GameTime * 200.0;"""


def body(held):
    """The shine: on the wearer, or for [held] (the item shader) on the item."""
    return '        ' + (ON_THE_SPRITE if held else ON_THE_BODY) + '\n' + REST


REST = """        float windsmpOff = abs(fract(windsmpWay) - 0.5);
        // A wide soft glow that fades into the red, and a narrow bright core.
        float windsmpGlow = exp(-(windsmpOff * windsmpOff) / (0.045 * 0.045));
        float windsmpCore = exp(-(windsmpOff * windsmpOff) / (0.012 * 0.012));
        // Glitter: about a quarter of the texels catch the light as the band passes, each flickering at its own beat.
        vec2 windsmpTexel = floor(texCoord0 * vec2(textureSize(Sampler0, 0)));
        float windsmpGrain = fract(sin(dot(windsmpTexel, vec2(12.9898, 78.233))) * 43758.5453);
        float windsmpGlint = windsmpGrain > 0.74 ? abs(sin(3.14159265 * (GameTime * 2400.0 + windsmpGrain * 8.0))) : 0.0;
        // The edge of the glow is a brighter red, the middle pink, the core and the glitter near white.
        color.rgb += windsmpGlow * vec3(0.42, 0.07, 0.09);
        color.rgb = mix(color.rgb, vec3(1.0, 0.80, 0.82), 0.45 * windsmpGlow * windsmpGlow);
        color.rgb = mix(color.rgb, vec3(1.0, 0.96, 0.96), 0.70 * windsmpCore);
        color.rgb = mix(color.rgb, vec3(1.0), 0.85 * windsmpGlow * windsmpGlint);
        color.rgb = min(color.rgb, vec3(1.0));
        windsmpShine = min(1.0, windsmpGlow + windsmpGlow * windsmpGlint);
"""
ALPHA_MARK = 'abs(%s.a * 255.0 - 252.0) < 0.5'
# The tint, on the vertex colour named {0}. The texture's clear texels carry it as well and are left out.
TINT_MARK = ('color.a > 0.5 && {0}.g > 0.0 && abs({0}.r / {0}.g - 0.9960784) < 0.0015'
             ' && abs({0}.b - {0}.g) < 0.0006')
# Not in the inventory. The game draws an item's icon once and keeps the picture: drawn while the shine was on it,
# the icon stayed pale. Icons are drawn without perspective, where gl_FragCoord.w is exactly 1; in the world it is
# one over the distance.
IN_WORLD = 'abs(gl_FragCoord.w - 1.0) > 0.0001'
SAMPLE = 'vec4 color = texture(Sampler0, texCoord0);'
LIGHT = 'color *= lightMapColor;'
UNLIT = 'color *= mix(lightMapColor, vec4(1.0), windsmpShine);'
# The old item shader samples, tints and lights in one line; the shine goes on after it, so it is unlit by itself.
OLD_SAMPLE = 'vec4 color = texture(Sampler0, texCoord0) * vertexColor * ColorModulator;'
OLD_SHINE = lambda shine: """vec4 windsmpSample = texture(Sampler0, texCoord0);
    bool windsmpMarked = """ + (ALPHA_MARK % 'windsmpSample') + """;
    if (windsmpMarked) {
        windsmpSample.a = 1.0;
    }
    vec4 color = windsmpSample * vertexColor * ColorModulator;
    if (windsmpMarked && """ + IN_WORLD + """) {
""" + shine + "    }"
TINTED = 'color *= vertexColor * ColorModulator;'
FACE_TINTED = 'color *= faceVertexColor * ColorModulator;'
PER_FACE = ('#ifdef PER_FACE_LIGHTING\n'
            '    color *= (gl_FrontFacing ? vertexPerFaceColorFront : vertexPerFaceColorBack) * ColorModulator;\n'
            '#else\n    color *= vertexColor * ColorModulator;\n#endif\n')
GLINT_GLOBALS = '#ifdef GLINT\n#include <minecraft:globals.glsl>\n#endif\n'
FOG_IMPORT = '#moj_import <minecraft:fog.glsl>\n'


def once(source, needle, name):
    if source.count(needle) != 1:
        raise SystemExit('%s.fsh changed: %r occurs %d times' % (name, needle, source.count(needle)))


def with_globals(source, name):
    if GLINT_GLOBALS in source:
        return source.replace(GLINT_GLOBALS, '#include <minecraft:globals.glsl>\n')
    once(source, FOG_IMPORT, name)
    return source.replace(FOG_IMPORT, '#moj_import <minecraft:globals.glsl>\n' + FOG_IMPORT)


def patched(source, name, alpha_items):
    once(source, SAMPLER, name)
    # The state is declared with the sampler, outside any #ifdef, so every variant of the shader has it.
    source = with_globals(source, name).replace(SAMPLER, STATE)
    BODY = body(name != 'entity')
    if name == 'entity':
        once(source, SAMPLE, name)
        source = source.replace(SAMPLE, SAMPLE + ALONG)
    if name == OLD_ITEM:
        once(source, OLD_SAMPLE, name)
        return source.replace(OLD_SAMPLE, OLD_SHINE(BODY))
    if name == ITEM and alpha_items:
        # 26.1: the mark is the texel's alpha, read before the vertex colour (with the light in it) goes on; the
        # shine goes on after, so it is unlit by itself.
        for needle in (SAMPLE, TINTED):
            once(source, needle, name)
        mark = (SAMPLE + '\n    bool windsmpMarked = ' + (ALPHA_MARK % 'color')
                + ';\n    if (windsmpMarked) {\n        color.a = 1.0;\n    }')
        return source.replace(SAMPLE, mark).replace(
            TINTED, TINTED + '\n    if (windsmpMarked && ' + IN_WORLD + ') {\n' + BODY + '    }')
    once(source, LIGHT, name)
    if PER_FACE in source:
        # 1.21.9 to 1.21.11: the vertex colour has one of two names, by a define. Armor is drawn with the per-face
        # one. Both go into one variable first, so the shine is in either variant.
        once(source, PER_FACE, name)
        shine = ('#ifdef PER_FACE_LIGHTING\n    vec4 windsmpTint = gl_FrontFacing ? vertexPerFaceColorFront : vertexPerFaceColorBack;\n'
                 '#else\n    vec4 windsmpTint = vertexColor;\n#endif\n'
                 '    if (' + TINT_MARK.format('windsmpTint') + ' && ' + IN_WORLD + ') {\n' + BODY + '    }\n'
                 '    color *= windsmpTint * ColorModulator;\n')
        return source.replace(PER_FACE, shine).replace(LIGHT, UNLIT)
    # The shine goes on right before the vertex colour does, whatever this shader calls it by then.
    tinted = [line for line in (TINTED, FACE_TINTED) if line in source]
    if len(tinted) != 1:
        raise SystemExit('%s.fsh changed: its vertex colour is applied %d times' % (name, len(tinted)))
    once(source, tinted[0], name)
    colour = 'faceVertexColor' if tinted[0] == FACE_TINTED else 'vertexColor'
    shine = 'if (' + TINT_MARK.format(colour) + ' && ' + IN_WORLD + ') {\n' + BODY + '    }\n    ' + tinted[0]
    return source.replace(tinted[0], shine).replace(LIGHT, UNLIT)


def main():
    clients = sys.argv[1:]
    if len(clients) != len(OVERLAYS):
        raise SystemExit(__doc__)
    meta_path = os.path.join(ROOT, 'pack.mcmeta')
    with open(meta_path) as handle:
        meta = json.load(handle)
    entries = [e for e in meta['overlays']['entries'] if not e['directory'].startswith('glow_')]
    for directory, ((low, high), client, item, alpha_items) in OVERLAYS.items():
        target = os.path.join(ROOT, directory, 'assets', 'minecraft', 'shaders', 'core')
        os.makedirs(target, exist_ok=True)
        for name in ('entity', item):
            with open(os.path.join(clients[client], 'shaders', 'core', name + '.fsh')) as handle:
                source = handle.read()
            with open(os.path.join(target, name + '.fsh'), 'w') as handle:
                handle.write(patched(source, name, alpha_items))
        entries.append({'formats': [low, high], 'min_format': low, 'max_format': high, 'directory': directory})
    # generate.py's plain spear for the clients before 1.21.11 (pack format 75), which have no spear.
    entries.append({'formats': [63, 74], 'min_format': 63, 'max_format': 74, 'directory': 'glow_spear_old'})
    meta['overlays']['entries'] = entries
    with open(meta_path, 'w') as handle:
        json.dump(meta, handle, indent=1)
        handle.write('\n')


main()
