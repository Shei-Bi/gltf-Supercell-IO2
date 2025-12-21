from ..shader.builder import ShaderBuilder


class UnlitPreset(ShaderBuilder):
    shader_idname = "ScUnlitShader"
    shader_label = "Unlit Shader"

    def set_shader_props(self):
        self.setup_diffuse()
        self.setup_opacity()
        self.setup_clipping()

    def setup_diffuse(self):
        self.set_constant_prop("DIFFUSE", 0)
        self.set_texture_prop("diffuseTex2D", 1)
        self.set_color_prop("diffuse", 1)

    def setup_opacity(self):
        self.set_constant_prop("OPACITY", 2)
        self.set_float_prop("opacity", 3)

    def setup_clipping(self):
        self.set_constant_prop("CLIP_PLANE", 4)
        self.set_color_prop("clipPlane", 5)
