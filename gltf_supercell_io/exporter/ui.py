import bpy
from bpy.types import PropertyGroup
from ..com import glTF_extension_name


class glTFSupercellExporterProperties(PropertyGroup):
    enabled: bpy.props.BoolProperty(
        name="Supercell",
        description='Include this extension in the exported glTF file.',
        default=True
    )
    
    #optimize_json: bpy.props.BoolProperty(
    #    name="Optimize JSON",
    #    description='Encode json data using FlatBuffers.',
    #    default=True
    #)


def draw_export(context, layout):
    header, body = layout.panel(glTF_extension_name, default_closed=False)
    header.use_property_split = False

    props = bpy.context.scene.glTFSupercellExporterProperties

    header.prop(props, "enabled")
    if body != None:
        #body.prop(props, "optimize_json")
        pass
