import bpy
import os

from bpy.types import ShaderNodeTree
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .nodes import ShaderNodeScNode, ShaderNodeScUtility, ShaderNodeScShader


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
    def instantiate_node(type_id: str, node_tree: ShaderNodeTree, tree_id: str):
        shader: ShaderNodeScNode = node_tree.nodes.new(type_id)  # type: ignore # noqa
        shader.tree_id = tree_id

        return shader  # type: ignore

    @staticmethod
    def instantiate_utility(node_tree: ShaderNodeTree, tree_id: str) -> 'ShaderNodeScUtility':
        return LibraryLoader.instantiate_node("ShaderNodeScUtility", node_tree, tree_id)  # type: ignore # noqa

    @staticmethod
    def instantiate_shader(node_tree: ShaderNodeTree, tree_id: str) -> 'ShaderNodeScShader':
        shader: ShaderNodeScShader = LibraryLoader.instantiate_node(
            "ShaderNodeScShader", node_tree, tree_id)  # type: ignore # noqa

        props = bpy.context.scene.glTFSupercellImporterProperties
        shader.preset_id = props.shader_preset

        return shader
