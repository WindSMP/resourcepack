#!/usr/bin/env python3
"""Builds the shader overlays that run a shine across the Christmas kit, for every client from 1.21.6 on.

    tools/christmas/glow_shaders.py <1.21.6> <1.21.10> <26.1.2> <26.2> <26.3>

Each argument is the `assets/minecraft` folder of that unpacked client. Vanilla's shader for worn armor and its shader
for items are taken as they are, with one addition each: what carries the kit's mark is drawn as it is, and a shine
passes over it every six seconds, tilted 35 degrees, rising from the lower edge of the screen to the upper one: a
soft glow that fades from a near-white core through pink into the red, with texels glittering inside it, unlit so it
shows in the dark too. It is the kit's own glint, in place of vanilla's purple one, which the kit's items turn off
(`enchantment_glint_override=false`). The shine is placed on the screen, not on the texture, so it runs the same way
over every face, and sized in blocks at the fragment's distance, so it looks the same on an item held up close as
from behind or far away.

The game time and the screen size come from the Globals block. Every client from 1.21.6 on binds that block to any
shader that declares it, whether or not the pipeline lists it (GlProgram's built-in uniforms), so declaring it here
is enough.

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
# so the wrap does not show (the glitter's flicker fits it too). One band follows the next 7 blocks behind, measured
# at the fragment's own distance, so a player or an item has one band on it at a time.
BODY = """        // Across the band: 35 degrees off the vertical, so the band lies 35 degrees off the horizontal and rises.
        vec2 windsmpAcross = vec2(-0.5735764, 0.8191520);
        // Where the fragment is, in blocks off the middle of the view: its place on the screen times its distance
        // (1.4 is twice the tangent of half a 70 degree view). So the band is as wide on a sword in the hand, which
        // fills half the screen, as on the same sword seen from behind, and as on a player far away.
        vec2 windsmpPlace = (gl_FragCoord.xy - 0.5 * ScreenSize) / ScreenSize.y * 1.4 / gl_FragCoord.w;
        float windsmpWay = dot(windsmpPlace, windsmpAcross) / 7.0 - GameTime * 200.0;
        float windsmpOff = abs(fract(windsmpWay) - 0.5);
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
OLD_SHINE = """vec4 windsmpSample = texture(Sampler0, texCoord0);
    bool windsmpMarked = """ + (ALPHA_MARK % 'windsmpSample') + """;
    if (windsmpMarked) {
        windsmpSample.a = 1.0;
    }
    vec4 color = windsmpSample * vertexColor * ColorModulator;
    if (windsmpMarked && """ + IN_WORLD + """) {
""" + BODY + "    }"
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
    if name == OLD_ITEM:
        once(source, OLD_SAMPLE, name)
        return source.replace(OLD_SAMPLE, OLD_SHINE)
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
