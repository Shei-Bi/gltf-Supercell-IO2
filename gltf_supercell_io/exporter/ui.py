import bpy
from bpy.types import PropertyGroup
from bpy.props import StringProperty, BoolProperty
from ..com import glTF_extension_name


class glTFSupercellExporterProperties(PropertyGroup):
    enabled: BoolProperty(
        name="Supercell",
        description='Include this extension in the exported glTF file.',
        default=True
    )
    
    path_prefix: StringProperty(
        name="Texture prefix",
        description="Exports textures with this prefix if needed",
        default="sc3d/"
    )
    
    legacy_materials: BoolProperty(
        name="Legacy materials",
        description="Exports materials in legacy format",
        default=False
    )


def draw_export(context, layout):
    header, body = layout.panel(glTF_extension_name, default_closed=False)
    header.use_property_split = False

    props = bpy.context.scene.glTFSupercellExporterProperties

    header.prop(props, "enabled")
    if body != None:
        body.prop(props, "path_prefix")
        body.prop(props, "legacy_materials")
