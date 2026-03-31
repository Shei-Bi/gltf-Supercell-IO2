import bpy
import numpy as np
from bpy.types import Material

from ..com.shader.nodes import ShaderNodeScShader, ShaderNodeScUtility
from ..com import glTF_material_extension_name, glTF_extension_name
from ..com.shader.exporter import ShaderExporter
from ..com.utilities import ShaderUtils

from io_scene_gltf2.io.com.gltf2_io import Material as glMaterial
from io_scene_gltf2.blender.exp.material.search_node_tree import get_material_nodes
from io_scene_gltf2.io.com.gltf2_io import Gltf
from io_scene_gltf2.io.com.gltf2_io_extensions import Extension
from io_scene_gltf2.io.com.gltf2_io import Accessor, Mesh, MeshPrimitive
from io_scene_gltf2.io.com.constants import ComponentType, DataType
from io_scene_gltf2.blender.exp.accessors import array_to_accessor


def check_if_is_linked_to_active_output(shader_socket, group_path, modifiers: list[str]):

    # Here, group_path must be copied, because if there are muliple links that enter/exit a group node
    # This will modify it, and we don't want to modify the original group_path (from the parameter) inside the loop
    for link in shader_socket.links:
        is_modifier = isinstance(link.to_node, ShaderNodeScUtility)

        # If we are entering a node group
        if link.to_node.type == "GROUP" or is_modifier:
            socket_name = link.to_socket.name
            sockets = [
                n for n in link.to_node.node_tree.nodes if n.type == "GROUP_INPUT"][0].outputs
            socket = [s for s in sockets if s.name == socket_name][0]
            new_group_path = group_path.copy()
            new_group_path.append(link.to_node)

            # Add modifier name to modifiers list
            if (is_modifier):
                modifier: ShaderNodeScUtility = link.to_node
                modifiers.append(modifier.tree_id)

            # TODOSNode : Why checking outputs[0] ? What about alpha for texture node, that is outputs[1] ????
            # recursive until find an output material node
            ret = check_if_is_linked_to_active_output(
                socket, new_group_path, modifiers)
            if ret is True:
                return True
            continue

        # If we are exiting a node group

        if link.to_node.type == "GROUP_OUTPUT":
            socket_name = link.to_socket.name
            sockets = group_path[-1].outputs
            socket = [s for s in sockets if s.name == socket_name][0]
            new_group_path = group_path[:-1]
            # TODOSNode : Why checking outputs[0] ? What about alpha for texture node, that is outputs[1] ????
            # recursive until find an output material node
            ret = check_if_is_linked_to_active_output(
                socket, new_group_path, modifiers)
            if ret is True:
                return True
            continue

        if isinstance(link.to_node, bpy.types.ShaderNodeOutputMaterial) and link.to_node.is_active_output is True:
            return True

        if len(link.to_node.outputs) > 0:  # ignore non active output, not having output sockets
            # TODOSNode : Why checking outputs[0] ? What about alpha for texture node, that is outputs[1] ????
            ret = check_if_is_linked_to_active_output(
                link.to_node.outputs[0],
                group_path, modifiers)  # recursive until find an output material node
            if ret is True:
                return True

    return False


class glTF2ExportUserExtension:

    def __init__(self):
        # We need to wait until we create the gltf2UserExtension to import the gltf2 modules
        # Otherwise, it may fail because the gltf2 may not be loaded yet
        self.Extension = Extension
        self.properties = bpy.context.scene.glTFSupercellExporterProperties  # type: ignore

    def export_sc_material(self, material: Material, shader: ShaderNodeScShader, modifiers: list[str], export_settings: dict):
        exporter = ShaderExporter(shader, material, modifiers, export_settings)
        material_data = exporter.export_material()

        return Extension(glTF_material_extension_name, material_data, False)

    def pre_export_hook(self, export_settings: dict):
        if (not self.properties.legacy_materials):
            export_settings[glTF_material_extension_name] = []

    def convert_mesh_to_legacy(self, mesh: Mesh, export_settings):
        # In older versions, joints were always saved in shorts, and this seems to be critical.
        # glTF exporter can apply optimizations to such things, so we need to ensure it's saved in the correct format here.
        target_type = ComponentType.UnsignedShort
        target_dtype = ComponentType.to_numpy_dtype(target_type)

        primitives: list[MeshPrimitive] = mesh.primitives or []
        for primitive in primitives:
            accessors: dict[str, Accessor] = {
                name: value for name, value in primitive.attributes.items() if name.startswith("JOINTS_")
            }

            for name, accessor in accessors.items():
                if accessor.component_type != ComponentType.UnsignedByte or accessor.type != DataType.Vec4:
                    continue

                dtype = ComponentType.to_numpy_dtype(accessor.component_type)
                component_nb = DataType.num_elements(accessor.type)
                num_elems = accessor.count * component_nb
                array = np.frombuffer(
                    accessor.buffer_view.data,
                    dtype=np.dtype(dtype).newbyteorder('<'),
                    count=num_elems,
                ).reshape(accessor.count, 4)

                primitive.attributes[name] = array_to_accessor(
                    array.astype(target_dtype),
                    export_settings,
                    target_type,
                    data_type=accessor.type
                )

    def gather_mesh_hook(self, gltf2_mesh, blender_mesh, blender_object, vertex_groups, modifiers, materials, export_settings):
        if (self.properties.legacy_meshes):
            self.convert_mesh_to_legacy(gltf2_mesh, export_settings)

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

        gltf.asset.generator += " | Supercell-IO Exporter by DaniilSV"

    def gather_material_hook(self, gltf2_material: glMaterial, blender_material: Material, export_settings: dict):
        tree = ShaderUtils.get_node_tree(blender_material)

        nodes = get_material_nodes(
            tree,
            [tree],
            ShaderNodeScShader
        )

        material = None
        for node in nodes:
            modifiers = []
            if not check_if_is_linked_to_active_output(
                node[0].outputs[0], node[1], modifiers
            ):
                continue

            material = self.export_sc_material(
                blender_material, node[0], modifiers, export_settings
            )

            break

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
