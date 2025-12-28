from .descriptor import ShaderPresetDescriptor
from ..shader.importer import ShaderImporter

# Unlit shader socket map
# Its really simple, so i think we can hold it as simple module constants
DIFFUSE_ENABLED = 0
DIFFUSE_TEX = 1
OPACITY_ENABLED = 2
OPACITY = 3
CLIP_PLANE_ENABLED = 4
CLIP_PLANE = 5


class UnlitPreset(ShaderPresetDescriptor):
    shader_idname = "ScUnlitShader"
    shader_label = "Unlit Shader"

    @staticmethod
    def setup_props(shader):
        UnlitPreset.setup_diffuse(shader)
        UnlitPreset.setup_opacity(shader)
        UnlitPreset.setup_clipping(shader)

    @staticmethod  # Need this for IDE to work correctly
    def import_shader(shader):
        UnlitPreset.setup_props(shader)

    @staticmethod
    def export_shader(shader):
        shader.set_blend_from_opacity_socket(OPACITY)
        UnlitPreset.setup_props(shader)

    @staticmethod
    def setup_diffuse(shader: ShaderImporter):
        shader.set_constant_prop("DIFFUSE", DIFFUSE_ENABLED)
        shader.set_texture_prop("diffuseTex2D", DIFFUSE_TEX)
        shader.set_color_prop("diffuse", DIFFUSE_TEX)

    @staticmethod
    def setup_opacity(shader: ShaderImporter):
        shader.set_constant_prop("OPACITY", OPACITY_ENABLED)
        shader.set_float_prop("opacity", OPACITY)

    @staticmethod
    def setup_clipping(shader: ShaderImporter):
        shader.set_constant_prop("CLIP_PLANE", CLIP_PLANE_ENABLED)
        shader.set_color_prop("clipPlane", CLIP_PLANE)
