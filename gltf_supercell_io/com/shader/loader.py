import bpy
import os

from bpy.types import ShaderNodeGroup, ShaderNodeTree


class LibraryLoader:
    LibraryName = "SupercellIO"
    BaseDirectory = os.path.dirname(os.path.abspath(__file__))
    LibraryPath = os.path.join(
        BaseDirectory, "library", "supercell_io_shaders.blend")

    @staticmethod
    def load_shader_tree(id: str) -> bpy.types.NodeTree:
        asset = bpy.data.node_groups.get(id)
        if (asset is None):
            with bpy.data.libraries.load(LibraryLoader.LibraryPath, link=True, assets_only=True) as (data_from, data_to):
                data_to.node_groups = [id]

            asset = bpy.data.node_groups.get(id)
            if asset is None:
                raise ImportError("Failed to instantiate Supercell IO shader")

        return asset

    @staticmethod
    def instantiate_shader(node_tree: ShaderNodeTree, tree_id: str) -> ShaderNodeGroup:
        shader: ShaderNodeGroup = node_tree.nodes.new(
            "ShaderNodeScShader"
        )

        props = bpy.context.scene.glTFSupercellImporterProperties
        preset_id = props.shader_preset

        shader.tree_id = tree_id
        shader.preset_id = preset_id

        return shader
