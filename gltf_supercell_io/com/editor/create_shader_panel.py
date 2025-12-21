import bpy
from bpy.types import Panel, Operator
from ..shader.loader import LibraryLoader
from ..shader_presets import ShaderPresets, ShaderPresetType

class SHADER_OT_SC_create_shader(Operator):
    bl_idname = "supercell.create_shader"
    bl_label = "Create shader"
    
    shader_id: bpy.props.StringProperty()
    
    def execute(self, context):
        preset = ShaderPresets.get_preset_by_id(self.shader_id)
        obj = bpy.context.active_object
        mat = obj.active_material
        if (not mat.node_tree):
            mat.use_nodes = True
        
        node = LibraryLoader.instantiate_shader(mat.node_tree, self.shader_id)
        node.label = preset.shader_label
        
        return {'FINISHED'}

class SHADER_PT_SC_create_shader(Panel):
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_label = "Shaders"
    bl_category = "Supercell"
    
    def draw(self, context):
        self.layout.operator("supercell.create_shader", text="Create unlit shader")\
            .shader_id = ShaderPresetType.UNLIT
        self.layout.operator("supercell.create_shader", text="Create Brawl Stars Legacy shader")\
            .shader_id = ShaderPresetType.BRAWL_STARS_LEGACY