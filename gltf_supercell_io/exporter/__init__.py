import bpy
from bpy.types import Material

from ..com.shader.nodes.shader import ShaderNodeScShader
from ..com import glTF_material_extension_name, glTF_extension_name
from ..com.shader.exporter import ShaderExporter

from io_scene_gltf2.io.com.gltf2_io import Material as glMaterial
from io_scene_gltf2.blender.exp.material.search_node_tree import get_material_nodes, check_if_is_linked_to_active_output
from io_scene_gltf2.io.com.gltf2_io import Gltf
from io_scene_gltf2.io.com.gltf2_io_extensions import Extension


class glTF2ExportUserExtension:

    def __init__(self):
        # We need to wait until we create the gltf2UserExtension to import the gltf2 modules
        # Otherwise, it may fail because the gltf2 may not be loaded yet
        self.Extension = Extension
        self.properties = bpy.context.scene.glTFSupercellExporterProperties

    def export_sc_material(self, material: Material, shader: ShaderNodeScShader, export_settings: dict):
        exporter = ShaderExporter(shader, material, export_settings)
        material_data = exporter.export_material()

        return Extension(glTF_material_extension_name, material_data, False)

    def pre_export_hook(self, export_settings: dict):
        if (not self.properties.legacy_materials):
            export_settings[glTF_material_extension_name] = []

    def gather_gltf_extensions_hook(self, gltf: Gltf, export_settings: dict):
        extension = {}
        if (not self.properties.legacy_materials):
            materials = export_settings[glTF_material_extension_name]
            if (len(materials)):
                extension["materials"] = materials
                gltf.materials = []
        
        if (extension):
            gltf.extensions[glTF_extension_name] = Extension(
                glTF_extension_name, extension, True
            )

    def gather_material_hook(self, gltf2_material: glMaterial, blender_material: Material, export_settings: dict):
        gltf2_material.alpha_mode
        nodes = get_material_nodes(
            blender_material.node_tree, [blender_material.node_tree],
            ShaderNodeScShader
        )

        nodes = [
            node for node in nodes if check_if_is_linked_to_active_output(
                node[0].outputs[0], node[1])
        ]

        material = None
        if (len(nodes) != 0):
            shader, tree = nodes[0]
            material = self.export_sc_material(
                blender_material, shader, export_settings
            )

        if (self.properties.legacy_materials):
            # Append as material extension in legacy format
            if (material is None):
                return

            gltf2_material.extensions[glTF_material_extension_name] = material
        else:
            # Append to export settings for future use in separate extension
            # Also, in new format all materials should use sc materials
            # so create fallback one if material doesn't use sc material
            if (material is None):
                pass  # TODO: fallback material

            export_settings[glTF_material_extension_name].append(material)
