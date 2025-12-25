from .importer import glTF2ImportUserExtension
from .importer.ui import draw_import
from .com.editor import SHADER_OT_SC_create_shader, SHADER_PT_SC_create_shader
from .com.shader.nodes import ShaderNodeScShader, ShaderNodeScNode, node_tree_handler
from .importer.importer_patch import patch_importer
from .importer.ui import glTFSupercellImporterProperties
import bpy

bl_info = {
    "name": "glTF Supercell IO",
    "author": "DaniilSV",
    "description": "",
    "blender": (2, 80, 0),
    "version": (0, 0, 1),
    "location": "",
    "warning": "",
    "category": "Generic",
}


# Initialization functions for glTF importer extension

classes = [
    glTFSupercellImporterProperties,  # Importer
    ShaderNodeScNode,                 # Base class for custom nodes
    ShaderNodeScShader,               # Custom shader
    SHADER_PT_SC_create_shader,       # Custom shader graph panel
    SHADER_OT_SC_create_shader        # Create shader operator
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.glTFSupercellImporterProperties = bpy.props.PointerProperty(
        type=glTFSupercellImporterProperties)
    patch_importer()

    bpy.app.handlers.load_post.append(node_tree_handler)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.glTFSupercellImporterProperties
