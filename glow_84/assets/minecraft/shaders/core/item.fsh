#version 330

#moj_import <minecraft:globals.glsl>
#moj_import <minecraft:fog.glsl>
#moj_import <minecraft:dynamictransforms.glsl>

uniform sampler2D Sampler0;

// WindSMP: how much of the Christmas kit's shine is on this fragment, 0 to 1 (see tools/christmas).
float windsmpShine = 0.0;

in float sphericalVertexDistance;
in float cylindricalVertexDistance;
in vec4 vertexColor;
in vec2 texCoord0;

out vec4 fragColor;

void main() {
    vec4 color = texture(Sampler0, texCoord0);
    bool windsmpMarked = abs(color.a * 255.0 - 252.0) < 0.5;
    if (windsmpMarked) {
        color.a = 1.0;
    }
#ifdef ALPHA_CUTOUT
    if (color.a < ALPHA_CUTOUT) {
        discard;
    }
#endif

    color *= vertexColor * ColorModulator;
    if (windsmpMarked && abs(gl_FragCoord.w - 1.0) > 0.0001) {
        vec2 windsmpOnAtlas = texCoord0 * vec2(textureSize(Sampler0, 0)) / 16.0;
        // Across the band: 35 degrees off the vertical towards the texture's right (its rows run downwards), so the
        // band lies 35 degrees off the horizontal and falls to the right. Vanilla draws a sword, an axe, a pickaxe and
        // a mace rising to the right, the handle at the lower left: the band crosses them and runs from the handle to
        // the tip. An eighth of a band per block.
        float windsmpWay = dot(vec2(windsmpOnAtlas.x, -windsmpOnAtlas.y), vec2(0.5735764, 0.8191520)) * 0.125 - GameTime * 200.0;
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
    }
    fragColor = apply_fog(color, sphericalVertexDistance, cylindricalVertexDistance, FogEnvironmentalStart, FogEnvironmentalEnd, FogRenderDistanceStart, FogRenderDistanceEnd, FogColor);
}
