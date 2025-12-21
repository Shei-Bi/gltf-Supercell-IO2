import bpy
from ..loader import LibraryLoader


class ShaderNodeScNode(bpy.types.ShaderNodeCustomGroup):
    bl_idname = "ShaderNodeScNode"
    bl_label = "Supercell IO Node"
    bl_icon = "NODE"

    tree_id: bpy.props.StringProperty(
        default="",
        update=lambda self, ctx: self.init_tree(ctx)
    )

    def init_tree(self, context):
        if not self.tree_id or self.tree_id == "":
            return

        tree = LibraryLoader.load_shader_tree(self.tree_id)
        self.node_tree = tree
        self.width = tree.default_group_node_width

    def copy(self, node):
        self.tree_id = node.tree_id
        self.node_tree = node.node_tree
        self.width = node.width
