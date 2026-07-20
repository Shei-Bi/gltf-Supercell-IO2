from .component import glTF2BaseImporterComponent, requires_extension
from ...com import glTF_material_extension_name
from ...com.materials import ScShaderMaterial
from ...com.shader_presets import ShaderPresets
from ...com.shader.importer import ShaderImporter


class SupercellShaderImporter(glTF2BaseImporterComponent):
    @requires_extension
    def gather_import_material_before_hook(
        self, gltf_material, vertex_color: str, gltf
    ):
        extensions = gltf_material.extensions = gltf_material.extensions or {}
        descriptor: dict = extensions.get(glTF_material_extension_name)  # type: ignore
        if descriptor is None:
            return

        material = descriptor
        if isinstance(descriptor, dict):
            material = ScShaderMaterial()
            material.from_dict(gltf, descriptor)
            extensions[glTF_material_extension_name] = material

        gltf_material.name = material.name

    @requires_extension
    def gather_import_material_after_hook(
        self,
        gltf_material,
        vertex_color,
        blender_mat,
        gltf,
    ):
        extensions = gltf_material.extensions or {}
        material = extensions.get(glTF_material_extension_name)
        if material is None:
            return

        # Cleanup material from glTF fallback and prepare for our own processing
        gltf_material.pbr_metallic_roughness.blender_nodetree = None
        gltf_material.pbr_metallic_roughness.blender_mat = None
        if not blender_mat.node_tree:
            blender_mat.use_nodes = True

        tree = blender_mat.node_tree
        if tree is None:
            return
        tree.nodes.clear()

        preset = ShaderPresets.get_preset_by_id(self.properties.shader_preset)
        importer = ShaderImporter(gltf, material, blender_mat, preset)
        importer.import_material()
