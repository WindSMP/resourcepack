#version 330

#moj_import <minecraft:globals.glsl>
#moj_import <minecraft:fog.glsl>
#moj_import <minecraft:dynamictransforms.glsl>

uniform sampler2D Sampler0;

// WindSMP: how much of the Christmas kit's shine is on this fragment, 0 to 1 (see tools/christmas).
float windsmpShine = 0.0;

#ifdef DISSOLVE
uniform sampler2D DissolveMaskSampler;
#endif

in float sphericalVertexDistance;
in float cylindricalVertexDistance;
#ifdef PER_FACE_LIGHTING
in vec4 vertexPerFaceColorBack;
in vec4 vertexPerFaceColorFront;
#else
in vec4 vertexColor;
#endif

#ifndef EMISSIVE
in vec4 lightMapColor;
#endif

#ifndef NO_OVERLAY
in vec4 overlayColor;
#endif

in vec2 texCoord0;

out vec4 fragColor;

void main() {
    vec4 color = texture(Sampler0, texCoord0);
    // WindSMP: how the texture runs on the screen, for the Christmas kit's shine (see tools/christmas).
    vec2 windsmpAlongX = dFdx(texCoord0);
    vec2 windsmpAlongY = dFdy(texCoord0);
#ifdef ALPHA_CUTOUT
    if (color.a < ALPHA_CUTOUT) {
        discard;
    }
#endif

#ifdef PER_FACE_LIGHTING
    vec4 faceVertexColor = gl_FrontFacing ? vertexPerFaceColorFront : vertexPerFaceColorBack;
#else
    vec4 faceVertexColor = vertexColor;
#endif

#ifdef DISSOLVE
    if (faceVertexColor.a < texture(DissolveMaskSampler, texCoord0).a) {
        discard;
    }
    // The dissolve effect entirely replaces translucency
    faceVertexColor.a = 1.0;
#endif

    if (color.a > 0.5 && faceVertexColor.g > 0.0 && abs(faceVertexColor.r / faceVertexColor.g - 0.9960784) < 0.0015 && abs(faceVertexColor.b - faceVertexColor.g) < 0.0006 && abs(gl_FragCoord.w - 1.0) > 0.0001) {
        vec2 windsmpOnTexture = texCoord0 * vec2(64.0, 32.0);
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
            - windsmpX / 16.0 * 0.9375 * 0.0875262 - GameTime * 200.0;
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
    color *= faceVertexColor * ColorModulator;
#ifndef NO_OVERLAY
    color.rgb = mix(overlayColor.rgb, color.rgb, overlayColor.a);
#endif
#ifndef EMISSIVE
    color *= mix(lightMapColor, vec4(1.0), windsmpShine);
#endif

    fragColor = apply_fog(color, sphericalVertexDistance, cylindricalVertexDistance, FogEnvironmentalStart, FogEnvironmentalEnd, FogRenderDistanceStart, FogRenderDistanceEnd, FogColor);
}
