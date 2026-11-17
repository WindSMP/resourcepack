#version 330
#extension GL_ARB_separate_shader_objects : require

#include <minecraft:globals.glsl>
#include <minecraft:fog.glsl>
#include <minecraft:dynamictransforms.glsl>
#include <minecraft:oit.glsl>

uniform sampler2D Sampler0;

// WindSMP: how much of the Christmas kit's shine is on this fragment, 0 to 1 (see tools/christmas).
float windsmpShine = 0.0;

#ifdef GLINT
uniform sampler2D GlintSampler;
#endif

#ifndef OIT_ALPHA_ONLY
layout(location = 0) in float sphericalVertexDistance;
layout(location = 1) in float cylindricalVertexDistance;
#endif
layout(location = 2) in vec4 vertexColor;
#ifndef OIT_ALPHA_ONLY
layout(location = 3) in vec4 lightMapColor;
layout(location = 4) in vec4 overlayColor;
#endif
layout(location = 5) in vec2 texCoord0;
#ifdef GLINT
layout(location = 6) in vec2 texCoordGlint;
#endif

#ifndef OIT_ALPHA_ONLY
layout(location = 0) out vec4 fragColor;
#endif

#ifndef OIT_ALPHA_ONLY
vec4 calculateFinalColor(vec4 color) {
    color.rgb = mix(overlayColor.rgb, color.rgb, overlayColor.a);
    color *= mix(lightMapColor, vec4(1.0), windsmpShine);

    #ifdef GLINT
    vec4 glintColor = GlintAlpha * texture(GlintSampler, texCoordGlint);// Glint color modulator?
    // Matches BlendFuntion.GLINT
    color.rgb += glintColor.rgb * glintColor.rgb;
    #endif

    #ifdef OIT_ACCUMULATE
    color = sampleColorForAccumulation(color);
    vec4 fogColor = vec4(FogColor.rgb * color.a, FogColor.a);
    #else
    vec4 fogColor = FogColor;
    #endif

    return apply_fog(color, sphericalVertexDistance, cylindricalVertexDistance, FogEnvironmentalStart, FogEnvironmentalEnd, FogRenderDistanceStart, FogRenderDistanceEnd, fogColor);
}
#endif

void main() {
    vec4 color = texture(Sampler0, texCoord0);
    #ifdef ALPHA_CUTOUT
    if (color.a < ALPHA_CUTOUT) {
        discard;
    }
    #endif

    if (color.a > 0.5 && vertexColor.g > 0.0 && abs(vertexColor.r / vertexColor.g - 0.9960784) < 0.0015 && abs(vertexColor.b - vertexColor.g) < 0.0006 && abs(gl_FragCoord.w - 1.0) > 0.0001) {
        // Across the band: 35 degrees off the vertical, so the band lies 35 degrees off the horizontal and rises.
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
    }
    color *= vertexColor * ColorModulator;

    #ifdef GLINT
    color.a = max(color.a, GlintAlpha);
    #endif

    #ifdef OIT_ALPHA_ONLY
    executeAlphaOnlyPhase(gl_FragCoord.z, color.a);
    #else
    fragColor = calculateFinalColor(color);
    #endif
}
