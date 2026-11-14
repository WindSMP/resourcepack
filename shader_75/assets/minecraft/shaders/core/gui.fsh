#version 330

// Copy of the game's gui.fsh (it cannot moj_import). Added: pure white quads are not drawn.
// That is the outline the game puts around dialog text once it was clicked; it would cover the store art.
layout(std140) uniform DynamicTransforms {
    mat4 ModelViewMat;
    vec4 ColorModulator;
    vec3 ModelOffset;
    mat4 TextureMat;
};

in vec4 vertexColor;

out vec4 fragColor;

void main() {
    vec4 color = vertexColor;
    if (color.a == 0.0) {
        discard;
    }
    if (all(greaterThanEqual(color, vec4(0.999)))) {
        discard;
    }
    fragColor = color * ColorModulator;
}
