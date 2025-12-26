import bpy

from io_scene_gltf2.io.com.gltf2_io import Material as glMaterial
from bpy.types import Material
from ..com.shader.nodes.shader import ShaderNodeScShader
from io_scene_gltf2.blender.exp.material.search_node_tree import get_material_nodes


class glTF2ExportUserExtension:

    def __init__(self):
        # We need to wait until we create the gltf2UserExtension to import the gltf2 modules
        # Otherwise, it may fail because the gltf2 may not be loaded yet
        from io_scene_gltf2.io.com.gltf2_io_extensions import Extension
        self.Extension = Extension
        self.properties = bpy.context.scene.glTFSupercellExporterProperties

    def gather_material_hook(self, gltf2_material: glMaterial, blender_material: Material, export_settings: dict):
        nodes = get_material_nodes(blender_material.node_tree, [
            blender_material.node_tree], ShaderNodeScShader)
        pass
