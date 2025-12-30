from .exporter.patch import patch_exporter
from .importer.patch import patch_importer
from .importer import glTF2ImportUserExtension
from .importer.ui import draw_import
from .exporter import glTF2ExportUserExtension
from .exporter.ui import draw_export
from .com.editor import SHADER_OT_SC_create_shader, SHADER_PT_SC_create_shader
from .com.shader.nodes import ShaderNodeScShader, ShaderNodeScUtility, ShaderNodeScNode
from .com.shader.handler import shader_linkage_handler
from .importer.ui import glTFSupercellImporterProperties
from .exporter.ui import glTFSupercellExporterProperties
import bpy

classes = [
    glTFSupercellImporterProperties,  # Importer properties
    glTFSupercellExporterProperties,  # Exporter properties
    ShaderNodeScNode,                 # Base class for custom nodes
    ShaderNodeScUtility,              # Custom utility nodes holder
    ShaderNodeScShader,               # Custom shader node holder
    SHADER_PT_SC_create_shader,       # Custom shader graph panel
    SHADER_OT_SC_create_shader,       # Create shader operator
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

    bpy.app.handlers.load_post.append(shader_linkage_handler)

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
    if ('Supercell' in exporter_extension_layout_draw):
        del exporter_extension_layout_draw['Supercell']

    bpy.app.handlers.load_post.remove(shader_linkage_handler)
