#version 330

// Copy of the game's gui.fsh. Added: pure white quads are not drawn, except in the middle of the screen.
// That is the outline the game puts around dialog text once it was clicked; it would cover the store art.
// Crosshair mods draw their crosshair as white quads in the middle too, and need them.
#moj_import <minecraft:globals.glsl>

layout(std140) uniform DynamicTransforms {
    mat4 ModelViewMat;
    vec4 ColorModulator;
    vec3 ModelOffset;
    mat4 TextureMat;
    float LineWidth;
};

in vec4 vertexColor;

out vec4 fragColor;

void main() {
    vec4 color = vertexColor;
    if (color.a == 0.0) {
        discard;
    }
    vec2 fromMiddle = abs(gl_FragCoord.xy - 0.5 * ScreenSize) / ScreenSize.y;
    if (all(greaterThanEqual(color, vec4(0.999))) && max(fromMiddle.x, fromMiddle.y) > 0.1) {
        discard;
    }
    fragColor = color * ColorModulator;
}
