from bpy.types import NodeSocket
from .descriptor import ShaderPresetDescriptor
from typing import Optional

CONSTANT_MAP = {
    0: "AMBIENT",
    2: "DIFFUSE",
    4: "SPECULAR",
    7: "COLORIZE",
    9: "LIGHTMAP",
    12: "OPACITY",
    14: "EMISSION",
    16: "STENCIL",
    20: "CLIP_PLANE",
    22: "COLORTRANSFORM_ADD",  # Not sure about that, but it was smth like that
    24: "COLORTRANSFORM_MUL"
}

COLOR_MAP = {
    1: "ambient",
    3: "diffuse",
    6: "specular",
    8: "colorize",
    15: "emission",
    21: "clipPlane"
}

LIGHTMAP_MAP = {
    10: "lightmap",
    11: "lightmapSpecular",
}

OPACITY = 13
STENCIL_ENABLE = 17
STENCIL_TEXTURE = 18


class BrawlStarsLegacy(ShaderPresetDescriptor):
    shader_idname = "ScLegacyBrawlStarsShader"
    shader_label = "Brawl Stars Legacy Shader"

    @staticmethod
    def setup_props(shader, light_vector: Optional[NodeSocket] = None):
        for idx, key in CONSTANT_MAP.items():
            shader.set_constant_prop(key, idx)

        for idx, key in COLOR_MAP.items():
            shader.set_color_prop(key, idx)
            shader.set_texture_prop(f"{key}Tex2D", idx)

        for idx, key in LIGHTMAP_MAP.items():
            shader.set_color_prop(key, idx)
            node = shader.set_texture_prop(
                f"{key}Tex2D", idx
            )

            # Optional lightmap vector for import process
            if (light_vector is not None and node is not None):
                shader.material.node_tree.links.new(
                    node.inputs[0], light_vector
                )

        shader.set_float_prop("opacity", OPACITY)
        shader.set_texture_prop("opacityTex2D", OPACITY)
        shader.set_bool_prop("enableStencilTex", STENCIL_ENABLE)
        shader.set_texture_prop("stencilTex2D", STENCIL_TEXTURE)

    @staticmethod
    def import_shader(shader):
        lighting_node = shader.instantiate_utility("ScLightmapUV", "Lightmaps")
        lighting_vector = lighting_node.outputs[0]

        BrawlStarsLegacy.setup_props(shader, lighting_vector)

    @staticmethod
    def export_shader(shader):
        shader.set_blend_from_opacity_socket(OPACITY)
        BrawlStarsLegacy.setup_props(shader)
