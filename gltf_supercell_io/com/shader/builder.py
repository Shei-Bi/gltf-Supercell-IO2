import bpy
from bpy.types import ShaderNodeGroup, ShaderNodeTexImage, ShaderNodeOutputMaterial, NodeOutputs
from typing import Tuple
from ..materials import ScShaderMaterial, ScBlendMode
from ..materials.variables import ShaderFloatVectorProperty, ShaderFloatProperty, ShaderTextureProperty, ShaderBooleanProperty, ShaderProperty
from .loader import LibraryLoader


class ShaderBuilder:
    shader_idname = ""
    shader_label = ""

    def __init__(self, sc_material: ScShaderMaterial, material: bpy.types.Material):
        self.sc_material = sc_material
        self.material = material
        self.shader: ShaderNodeGroup = None
        self.node_counter = 0
        self.utility_node_offset = -125
        self.image_cache = {}

    def create_material(self):
        tree = self.material.node_tree
        self.setup_blending()

        output: ShaderNodeOutputMaterial = tree.nodes.new(
            'ShaderNodeOutputMaterial'
        )
        output.location = 200, 100

        self.shader = self.setup_shader()
        self.set_shader_props()
        tree.links.new(output.inputs[0], self.shader.outputs[0])

        if (len(self.sc_material.unused_constants)):
            self.shader["$constants"] = self.sc_material.unused_constants

        for variable in self.sc_material.unused_variables:
            self.set_raw_shader_prop(variable)

    def setup_blending(self):
        if self.sc_material.blend_mode == ScBlendMode.Opaque:
            self.material.surface_render_method = 'DITHERED'
        else:
            self.material.surface_render_method = 'BLENDED'

    def set_raw_shader_prop(self, raw_property: Tuple[str, ShaderProperty]):
        key, prop = raw_property
        if (isinstance(raw_property, ShaderNodeTexImage)):
            # TODO: Add image conversion ?
            self.shader[key] = prop.texture_path
        else:
            self.shader[key] = prop.value

    def set_constant_prop(self, name: str, index: int):
        socket = self.shader.inputs[index]
        socket.default_value = self.sc_material.has_constant(name)

    def set_texture_prop(self, name: str, index: int, vector: NodeOutputs = None):
        prop: ShaderTextureProperty = self.sc_material.get_property(
            name, ShaderTextureProperty
        )

        if (prop is None):
            # Often textures leave a color, it needs to be marked as read
            self.sc_material.get_property(
                name, ShaderFloatVectorProperty
            )
            return

        node: ShaderNodeTexImage = self.image_cache.get(prop.texture_path)
        if (node is None):
            node: ShaderNodeTexImage = self.material.node_tree.nodes.new(
                "ShaderNodeTexImage"
            )

            x, y = self.shader.location

            # Base horizontal offset
            x -= 465

            # Vertical offset based on current node count and number
            if (self.node_counter and self.node_counter % 3 == 0):
                x -= 300
                y -= (self.node_counter / 2) * 100
            else:
                y -= self.node_counter * 210

            node.location = x, y
            node.extension = "REPEAT" if "repeat" in prop.keywords else "CLIP"
            self.node_counter += 1
            self.image_cache[prop.texture_path] = node
            
            if (vector is not None):
                self.material.node_tree.links.new(node.inputs[0], vector)

        self.material.node_tree.links.new(
            self.shader.inputs[index], node.outputs[0]
        )
        
        return node

    def set_color_prop(self, name: str, index: int):
        prop: ShaderFloatVectorProperty = self.sc_material.get_property(
            name, ShaderFloatVectorProperty
        )

        if (prop is None):
            return

        socket = self.shader.inputs[index]
        socket.default_value = prop.vector

    def set_float_prop(self, name: str, index: int):
        prop: ShaderFloatProperty = self.sc_material.get_property(
            name, ShaderFloatProperty
        )

        if (prop is None):
            return

        socket = self.shader.inputs[index]
        socket.default_value = prop.number

    def set_bool_prop(self, name: str, index: int):
        prop: ShaderBooleanProperty = self.sc_material.get_property(
            name, ShaderBooleanProperty
        )

        if (prop is None):
            return

        socket = self.shader.inputs[index]
        socket.default_value = prop.status

    def setup_shader(self):
        node = LibraryLoader.instantiate_shader(
            self.material.node_tree, self.shader_idname)

        node.label = self.shader_label
        node.location = 40 - node.width, 100

        return node

    def instantiate_utility(self, id: str, label: str) -> ShaderNodeGroup:
        node = LibraryLoader.instantiate_shader(self.material.node_tree, id)

        node.label = label
        x, y = self.shader.location

        # Base horizontal offset
        x -= 1040
        y = self.utility_node_offset
        self.utility_node_offset -= node.height + 50

        node.location = x, y

        return node

    def set_shader_props(self) -> ShaderNodeGroup:
        raise NotImplementedError()
