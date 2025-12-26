from .importer import glTF2ImportUserExtension
from .importer.ui import draw_import
from .exporter import glTF2ExportUserExtension
from .exporter.ui import draw_export
from .com.editor import SHADER_OT_SC_create_shader, SHADER_PT_SC_create_shader
from .com.shader.nodes import ShaderNodeScShader, ShaderNodeScNode, node_tree_handler
from .importer.patch import patch_importer
from .importer.ui import glTFSupercellImporterProperties
from .exporter.ui import glTFSupercellExporterProperties
from .exporter.patch import patch_exporter
import bpy

bl_info = {
    "name": "glTF Supercell IO",
    "author": "DaniilSV",
    "description": "",
    "blender": (5, 0, 0),
    "version": (1, 0, 0),
    "location": "",
    "warning": "",
    "category": "Generic",
}


# Initialization functions for glTF importer extension

classes = [
    glTFSupercellImporterProperties,  # Importer properties
    glTFSupercellExporterProperties,  # Exporter properties
    ShaderNodeScNode,                 # Base class for custom nodes
    ShaderNodeScShader,               # Custom shader
    SHADER_PT_SC_create_shader,       # Custom shader graph panel
    SHADER_OT_SC_create_shader        # Create shader operator
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.glTFSupercellImporterProperties = bpy.props.PointerProperty(
        type=glTFSupercellImporterProperties
    )
    bpy.types.Scene.glTFSupercellExporterProperties = bpy.props.PointerProperty(
        type=glTFSupercellExporterProperties
    )

    patch_importer()
    patch_exporter()

    bpy.app.handlers.load_post.append(node_tree_handler)

    # Use the following 2 lines to register the UI for this hook
    from io_scene_gltf2 import exporter_extension_layout_draw
    # Make sure to use the same name in unregister()
    exporter_extension_layout_draw['Supercell'] = draw_export


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.glTFSupercellImporterProperties
    del bpy.types.Scene.glTFSupercellExporterProperties

    from io_scene_gltf2 import exporter_extension_layout_draw
    # Make sure to use the same name in register()
    del exporter_extension_layout_draw['Supercell']
