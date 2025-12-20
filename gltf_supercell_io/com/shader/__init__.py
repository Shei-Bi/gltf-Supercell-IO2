import bpy

class ShaderNodeScShader(bpy.types.ShaderNodeCustomGroup):
    bl_idname = "ShaderNodeScShader"
    bl_label = "Supercell Shader"
    bl_icon = 'SHADERFX'

    preset_tree: bpy.props.PointerProperty(
        type=bpy.types.NodeTree,
        update=lambda self, ctx: self.apply_preset(ctx)
    )
    
    preset_id: bpy.props.StringProperty(
        default=""
    )

    def init(self, context):
        self.color_tag = "SHADER"

    def apply_preset(self, context):
        if not self.preset_tree:
            return

        self.node_tree = self.preset_tree

    def copy(self, node):
        self.color_tag = node.color_tag
        self.preset_tree = node.preset_name
        self.preset_id = node.preset_id
        self.node_tree = node.node_tree
        self.width = node.width