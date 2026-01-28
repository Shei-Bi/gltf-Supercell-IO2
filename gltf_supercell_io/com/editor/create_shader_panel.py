import bpy
from bpy.types import Panel, Operator
from ..shader.loader import LibraryLoader
from ..shader_presets import ShaderPresets, ShaderPresetType
from ..utilities import ShaderUtils


class SHADER_OT_SC_create_shader(Operator):
    bl_idname = "supercell.create_tree"
    bl_label = "Create shader"

    item_type: bpy.props.StringProperty()
    item_id: bpy.props.StringProperty()
    item_label: bpy.props.StringProperty()

    def execute(self, context):  # type: ignore
        obj = context.active_object
        if (obj is None):
            self.report({'WARNING'}, "No active object")
            return {'CANCELLED'}

        mat = obj.active_material
        if (mat is None):
            self.report({'WARNING'}, "No active material")
            return {'CANCELLED'}

        if (self.item_type == "utility"):
            node = LibraryLoader.instantiate_utility(
                ShaderUtils.get_node_tree(mat),
                self.item_id
            )
        else:
            node = LibraryLoader.instantiate_shader(
                ShaderUtils.get_node_tree(mat),
                self.item_id
            )

            if (not self.item_label):
                preset = ShaderPresets.get_preset_by_id(self.item_id)
                node.label = preset.shader_label

        if (node):
            if (self.item_label):
                node.label = self.item_label

        return {'FINISHED'}


class SHADER_PT_SC_create_shader(Panel):
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_label = "Shaders"
    bl_category = "Supercell"

    def draw(self, context):
        if (self.layout is not None):
            self.layout.operator("supercell.create_tree", text="Create unlit shader")\
                .item_id = ShaderPresetType.UNLIT
            self.layout.operator("supercell.create_tree", text="Create Brawl Stars Legacy shader")\
                .item_id = ShaderPresetType.BRAWL_STARS_LEGACY


class SHADER_PT_SC_create_utilities(Panel):
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_label = "Utilities"
    bl_category = "Supercell"

    def draw(self, context):
        if (self.layout is not None):
            lightmap = self.layout.operator(
                "supercell.create_tree", text="Create Lightmap UV"
            )
            lightmap.item_id = "ScLightmapUV"
            lightmap.item_type = "utility"
            lightmap.item_label = "Lightmaps"
