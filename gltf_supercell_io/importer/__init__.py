import bpy
from bpy.types import ShaderNodeTree

from ..com import glTF_extension_name, glTF_material_extension_name
from ..com.odin.constants import OdinAttributeFormat, OdinAttributeType
from ..com.odin.attribute import OdinAttribute
from ..com.materials import ScShaderMaterial
from ..com.animation.reader import OdinAnimationReader
from ..com.animation.packedReader import TranslationChannels, ScaleChannels, RotationChannels

from ..com.shader_presets import ShaderPresets
from ..com.shader.importer import ShaderImporter
from ..com.animation import OdinAnimation

from io_scene_gltf2.io.com.gltf2_io_extensions import Extension
from io_scene_gltf2.io.imp.gltf2_io_gltf import glTFImporter, ImportError
from io_scene_gltf2.io.com.gltf2_io import Accessor, Material, Node, Mesh, MeshPrimitive, Scene, Skin, Animation
from io_scene_gltf2.blender.imp.vnode import VNode
from io_scene_gltf2.io.imp.gltf2_io_binary import BinaryData
from io_scene_gltf2.blender.imp.animation_utils import get_or_create_action_and_slot, make_fcurve
from io_scene_gltf2.blender.imp.material import BlenderMaterial
from .ui import glTFSupercellImporterProperties

from typing import List, Dict, Any
from pathlib import Path
from mathutils import Vector


class glTF2ImportUserExtension:
    def __init__(self):
        self.properties: glTFSupercellImporterProperties = bpy.context.scene.glTFSupercellImporterProperties  # type: ignore
        self.extensions = [
            # Odin extension with custom meshes and animations store method
            Extension(name=glTF_extension_name, extension={}, required=True),

            # Custom materials
            Extension(name=glTF_material_extension_name,
                      extension={}, required=False)
        ]

    def valid_gltf(self, gltf: glTFImporter):
        """Returns True if gltf is valid Supercell glTF and is subject to further processing"""
        required = gltf.data.extensions_required or []
        used = gltf.data.extensions_used or []
        has_extension = glTF_extension_name in required
        has_shader = glTF_material_extension_name in used

        return has_extension or has_shader

    def process_accessors(self, gltf: glTFImporter):
        """Supercell uses special component types for some accessors to optimize gpu memory usage, 
            which is not standard and needs to be converted to normal here"""
        # Exclusive Accessor Component Types
        # 1 - Float Vector 3
        # 2 - Float Vector 4
        # 3 - Matrix4x4

        accessors: List[Accessor] = gltf.data.accessors
        for accessor in accessors:
            accessor.component_type = accessor.component_type & 0x0000FFFF

    def get_extension_descriptor(self, gltf: glTFImporter) -> dict | None:
        """Returns SC_odin_format extension descriptor, if exists, otherwise returns None"""
        extensions: dict = gltf.data.extensions
        if (extensions is None):
            return None

        return extensions.get(glTF_extension_name, None)

    def move_materials(self, gltf: glTFImporter):
        """Supercell stores their materials in extensions, 
            so we need to move them to the main materials list if there is a need"""
        descriptor = self.get_extension_descriptor(gltf)
        if (descriptor is None):
            return

        materials = descriptor.get("materials")
        if (materials is None):
            return

        gltf.data.materials = [
            Material.from_dict({"extensions": {glTF_material_extension_name: material}}) for material in materials
        ]

    def process_nodes_extension(self, gltf: glTFImporter):
        """Repairs gltf children relation indexing based on classic parent indexing stored in node extensions"""
        nodes: List[Node] = gltf.data.nodes or []

        childrens: dict[int, list[int]] = {}

        def add_child(idx: int, parent_idx: int):
            if (parent_idx not in childrens):
                childrens[parent_idx] = []
            childrens[parent_idx].append(idx)

        for i, node in enumerate(nodes):
            extensions = node.extensions
            if (extensions is None):
                continue

            descriptor = extensions.get(glTF_extension_name)
            if (descriptor is None):
                continue

            parent = descriptor.get("parent")
            add_child(i, parent)

        for idx, children in childrens.items():
            nodes[idx].children = children

    def do_final_fixups(self, gltf: glTFImporter):
        """Very often Supercell glTF files have missing fields that are required by the importer, this function adds them back"""

        root_nodes = []
        nodes: List[Node] = gltf.data.nodes or []
        skins = gltf.data.skins = gltf.data.skins or []

        # Fix for scene nodes
        if (gltf.data.scenes is None):
            childrens = set()
            for node in nodes:
                if node.children is None:
                    continue

                childrens.update(node.children)

            root_nodes = [i for i in range(len(nodes)) if i not in childrens]
            gltf.data.scenes = [Scene(None, None, None, root_nodes)]
        else:
            for scene in gltf.data.scenes:
                if (scene.nodes is None):
                    root_nodes = scene.nodes
                    break
                    
        is_skinned = len(gltf.data.skins or []) != 0 #or len(gltf.data.animations or []) != 0
        if (self.properties.single_skeleton and len(root_nodes) and is_skinned):
            # Most of animations doesn't have actual skin
            # We should create placeholder one, so blender could process it properly
            if (len(skins) == 0):
                joints = [i for i, node in enumerate(
                    gltf.data.nodes) if node.mesh is None and node.camera is None and node.skin is None]
                skins.append(Skin.from_dict({"joints": joints}))

            if (len(root_nodes) == 1):
                for skin in skins:
                    skin.skeleton = root_nodes[0]
            else:
                children_mapping = {key: [] for key in root_nodes}

                def visit(key: int, node_index: int):
                    childrens = gltf.data.nodes[node_index].children or []

                    for idx in childrens:
                        children_mapping[key].append(idx)
                        visit(key, idx)

                for key in root_nodes:
                    visit(key, key)

                for skin in skins:
                    for key, childrens in children_mapping.items():
                        if (any(i in childrens for i in skin.joints or [])):
                            skin.skeleton = key
                            break

        gltf.data.meshes = gltf.data.meshes or []

    def setup_settings(self, gltf: glTFImporter):
        # Why tf this exists at all
        gltf.import_settings['disable_bone_shape'] = True

        # May have other values in some older versions
        gltf.import_settings['bone_heuristic'] = 'BLENDER'

        # Also very useful thing for mesh
        gltf.import_settings['merge_vertices'] = True

    def move_animation(self, gltf: glTFImporter):
        """Supercell also stores animations in the extension, 
            so they also need to be moved to the animations for proper processing. 
            Only one animation per file is possible."""
        descriptor = self.get_extension_descriptor(gltf)
        if (descriptor is None):
            return

        animation = descriptor.get("animation")
        if (animation is None):
            return

        name = Path(gltf.filename).stem
        animations = gltf.data.animations = gltf.data.animations or []
        animations.append(
            Animation([], {glTF_extension_name: animation}, None, name, [])
        )

    def gather_import_gltf_before_hook(self, gltf: glTFImporter):
        if (not self.valid_gltf(gltf)):
            return

        self.process_accessors(gltf)
        self.move_materials(gltf)
        self.move_animation(gltf)

        self.process_nodes_extension(gltf)
        self.do_final_fixups(gltf)

        if (self.properties.better_settings):
            self.setup_settings(gltf)

        # Shared cache for all meshes import operations
        gltf.supercell_vertex_cache = {}  # type: ignore
        gltf.supercell_vertex_accessor_offset = 0  # type: ignore

    def gather_import_node_before_hook(self, vnode: VNode, node: Node | None, gltf: glTFImporter):
        """Some nodes (especially in animation files) may have invalid indices, we need to clean them up to avoid errors"""
        if (not self.valid_gltf(gltf)):
            return

        if (node is None):
            return

        meshes_count = len(gltf.data.meshes or [])
        if (node.mesh is not None):
            if (node.mesh >= meshes_count):
                node.mesh = None
                vnode.type = VNode.DummyRoot
                vnode.mesh_node_idx = None

    def decode_mesh_attribute(self, gltf: glTFImporter, buffer_idx: int, attribute: dict, offset: int, stride: int):
        attribute_type = OdinAttributeType(attribute.get("index"))
        attribute_format = OdinAttributeFormat(attribute.get("format"))
        element_offset = attribute.get("offset", 0)
        buffer_data = BinaryData.get_buffer_view(gltf, buffer_idx)

        name = OdinAttributeType.to_attribute_name(attribute_type)
        data = OdinAttribute(
            buffer_data, attribute_format, attribute_type, offset, element_offset, stride
        )

        return (name, data)

    def decode_mesh_info(self, gltf: glTFImporter, idx: int):
        descriptor = self.get_extension_descriptor(gltf) or {}
        mesh_infos: list[dict] = descriptor.get(
            "meshDataInfos")  # type: ignore
        buffer_idx = descriptor.get("bufferView")
        if (mesh_infos is None or buffer_idx is None):
            raise ImportError("Missing Supercell glTF mesh data")

        # Prepare cache
        attributes = {}

        mesh_info = mesh_infos[idx]
        vertex_descriptors: List[dict] = mesh_info.get(
            "vertexDescriptors"
        )  # type: ignore
        for descriptors in vertex_descriptors:
            offset = descriptors.get("offset", 0)
            stride = descriptors.get("stride", 0)

            for attribute in descriptors.get("attributes", []):
                name, data = self.decode_mesh_attribute(
                    gltf, buffer_idx, attribute, offset, stride)
                attributes[name] = data

        gltf.supercell_vertex_cache[idx] = attributes  # type: ignore

    def decode_primitive(self, gltf: glTFImporter, primitive: MeshPrimitive):
        extensions = primitive.extensions
        if (extensions is None):
            return

        descriptor = extensions.get(glTF_extension_name)
        if (descriptor is None):
            return

        mesh_info_idx = descriptor.get("meshDataInfoIndex")
        if (mesh_info_idx is None):
            return

        if (mesh_info_idx not in gltf.supercell_vertex_cache):  # type: ignore
            self.decode_mesh_info(gltf, mesh_info_idx)

        # MEGA HACK: instead of writing writing back to buffer and then to accessors and blah blah blah...
        # We do next magic:
        # 1. Create custom class that will "emulate" np.array for attributes (basically just a wrapper with __getitem__ method)
        # that will have streaming-like behavior to avoid multiple indices reading in order to creating usual fixed-size numpy arrays
        # We will pass this streaming attribute to glTF importer directly
        # 2. To actually pass our custom attribute data, we will use existing cache system
        # We can just create our own accessor indices to which importer will ask data from,
        # so we can set it in advance in caching pool it will return our custom streaming attribute
        # Profit 500%

        primitive.attributes = {}

        for name, data in gltf.supercell_vertex_cache[mesh_info_idx].items():  # type: ignore # noqa
            fake_accessor_idx = gltf.supercell_vertex_accessor_offset  # type: ignore
            primitive.attributes[name] = fake_accessor_idx
            gltf.decode_accessor_cache[fake_accessor_idx] = data
            gltf.accessor_cache[fake_accessor_idx] = data

            gltf.supercell_vertex_accessor_offset += 1  # type: ignore

        # TRICK: gltf importer proceeds vertex color kinda... strangely.
        # It creates separate material specifically if there is COLOR_0 attribute.
        # Should i say that this thing breaks EVERYTHING?
        # So... We need to trick gltf importer and somehow avoid creating
        # this stupid materials and also import this color attributes, so user can decide yourself what to do with that
        # or in the future i will custom processing anyway
        # So I came up with the idea that we need to get ahead of
        # gltf importer and import materials manually, filling in all variations as needed

        # Checking if primitive has color and material at all
        if ("COLOR_0" in primitive.attributes and primitive.material is not None):
            pymaterial = gltf.data.materials[primitive.material]
            mat = pymaterial.blender_material

            # Check if material already created and we just need to apply it to color
            if (None in mat):
                mat["COLOR_0"] = mat[None]
            else:
                # Else create material ahead of time and apply
                mat["COLOR_0"] = mat[None] = BlenderMaterial.create(
                    gltf, primitive.material, None)

    def gather_import_mesh_options(self, mesh_options, pymesh: Mesh, skin_idx, gltf: glTFImporter):
        """Please khronos i need this. My glTF importer is kinda homeless"""
        if (not self.valid_gltf(gltf)):
            return

        # sooo... since exporter settings up some settings at top-level of mesh conversion
        # we need to decode all mesh infos here to have them ready for primitives decoding
        # not a good place but... there will be no peaceful solution

        gltf.supercell_vertex_accessor_offset = len(  # type: ignore #noqa
            gltf.data.accessors or [])
        primitives: List[MeshPrimitive] = pymesh.primitives or []
        for primitive in primitives:
            self.decode_primitive(gltf, primitive)

    def gather_import_material_before_hook(self, gltf_material: Material, vertex_color: str, gltf: glTFImporter):
        if (not self.valid_gltf(gltf)):
            return

        extensions = gltf_material.extensions = gltf_material.extensions or {}
        descriptor: dict = extensions.get(
            glTF_material_extension_name)  # type: ignore
        if (descriptor is None):
            return

        material = ScShaderMaterial()
        material.from_dict(gltf, descriptor)
        extensions[glTF_material_extension_name] = material
        gltf_material.name = material.name

    def gather_import_material_after_hook(self, gltf_material: Material, vertex_color, blender_mat: bpy.types.Material, gltf: glTFImporter):
        if (not self.valid_gltf(gltf)):
            return

        extensions = gltf_material.extensions or {}
        material: ScShaderMaterial = extensions.get(
            glTF_material_extension_name)  # type: ignore
        if (material is None):
            return

        # Cleanup material from glTF fallback and prepare for our own processing
        gltf_material.pbr_metallic_roughness.blender_nodetree = None
        gltf_material.pbr_metallic_roughness.blender_mat = None
        if not blender_mat.node_tree:
            blender_mat.use_nodes = True

        tree: ShaderNodeTree = blender_mat.node_tree # type: ignore
        tree.nodes.clear()

        preset = ShaderPresets.get_preset_by_id(self.properties.shader_preset)
        importer = ShaderImporter(gltf, material, blender_mat, preset)
        importer.import_material()

    def gather_import_scene_after_nodes_hook(self, gltf_scene, blender_scene: bpy.types.Scene, gltf):
        if (not self.valid_gltf(gltf)):
            return

        if (self.properties.adjust_colorspace):
            blender_scene.view_settings.view_transform = "Raw" # type: ignore

    def do_animation_channel(self, animation: OdinAnimationReader, duration: int, fps: float, path: str, values: list, anim_idx: int, node_idx: int, gltf: glTFImporter):
        vnodes: Dict[Any, VNode] = gltf.vnodes  # type: ignore
        vnode: VNode = vnodes[node_idx]  # type: ignore

        action, slot = get_or_create_action_and_slot(
            gltf, node_idx, anim_idx, path)

        num_components = 0
        blender_path = ""
        group_name = ""
        if path == "translation":
            blender_path = "location"
            group_name = "Object Transforms"
            num_components = 3
            values = [gltf.loc_gltf_to_blender(  # type: ignore #noqa
                vals) for vals in values]
            values = vnode.base_locs_to_final_locs(values)

        elif path == "rotation":
            blender_path = "rotation_quaternion"
            group_name = "Object Transforms"
            num_components = 4
            values = [gltf.quaternion_gltf_to_blender(  # type: ignore #noqa
                vals) for vals in values]
            values = vnode.base_rots_to_final_rots(values)

        elif path == "scale":
            blender_path = "scale"
            group_name = "Object Transforms"
            num_components = 3
            values = [gltf.scale_gltf_to_blender(  # type: ignore #noqa
                vals) for vals in values]
            values = vnode.base_scales_to_final_scales(values)

        # Objects parented to a bone are translated to the bone tip by default.
        # Correct for this by translating backwards from the tip to the root.
        if vnode.type == VNode.Object and path == "translation":
            if vnode.parent is not None and vnodes[vnode.parent].type == VNode.Bone:
                bone_length = vnodes[vnode.parent].bone_length  # type: ignore
                off = Vector((0, -bone_length, 0))
                values = [vals + off for vals in values]

        if vnode.type == VNode.Bone:
            # Need to animate the pose bone when the node is a bone.
            group_name = vnode.blender_bone_name  # type: ignore
            blender_path = 'pose.bones["%s"].%s' % (
                bpy.utils.escape_identifier(
                    vnode.blender_bone_name),  # type: ignore
                blender_path
            )

            # We have the final TRS of the bone in values. We need to give
            # the TRS of the pose bone though, which is relative to the edit
            # bone.
            #
            #     Final = EditBone * PoseBone
            #   where
            #     Final =    Trans[ft] Rot[fr] Scale[fs]
            #     EditBone = Trans[et] Rot[er]
            #     PoseBone = Trans[pt] Rot[pr] Scale[ps]
            #
            # Solving for PoseBone gives
            #
            #     pt = Rot[er^{-1}] (ft - et)
            #     pr = er^{-1} fr
            #     ps = fs

            if path == 'translation':
                edit_trans, edit_rot = vnode.editbone_trans, vnode.editbone_rot  # type: ignore
                edit_rot_inv = edit_rot.conjugated()
                values = [
                    edit_rot_inv @ (trans - edit_trans)
                    for trans in values
                ]

            elif path == 'rotation':
                edit_rot = vnode.editbone_rot  # type: ignore
                edit_rot_inv = edit_rot.conjugated()
                values = [
                    edit_rot_inv @ rot
                    for rot in values
                ]

            elif path == 'scale':
                pass  # no change needed

        # To ensure rotations always take the shortest path, we flip
        # adjacent antipodal quaternions.
        if path == 'rotation':
            for i in range(1, len(values)):
                if values[i].dot(values[i - 1]) < 0:
                    values[i] = -values[i]

        fps = (fps * bpy.context.scene.render.fps_base) # type: ignore

        coords = [0] * (2 * duration)
        coords[::2] = ((animation.frame_spf * i) *  # type: ignore
                       fps for i in range(duration))

        for i in range(0, num_components):
            coords[1::2] = (vals[i] for vals in values)
            make_fcurve(
                action,
                slot,
                coords,
                data_path=blender_path,
                index=i,
                group_name=group_name,
            )

    def gather_import_animation_before_hook(self, anim_idx: int, gltf: glTFImporter):
        extensions = gltf.data.animations[anim_idx].extensions or {}
        descriptor = extensions.get(glTF_extension_name)
        if (descriptor is None):
            return
        animation = OdinAnimation.Create(gltf, descriptor)

        fps = bpy.context.scene.render.fps # type: ignore
        if (self.properties.fps_source == 'SEQUENCE'):
            bpy.context.scene.render.fps = int(animation.frame_rate) # type: ignore
            fps = animation.frame_rate
        elif (self.properties.fps_source == 'CUSTOM'):
            fps = self.properties.fps_custom

        for i, node_idx in enumerate(animation.used_nodes):
            duration = animation.keyframe_count
            if (animation.keyframe_mapping is not None):
                duration = animation.keyframe_mapping[i]
            translation = animation.get_translation(i)
            rotation = animation.get_rotation(i)
            scale = animation.get_scale(i)

            if (translation is not None):
                translation = [list(translation[c][f] for c in range(
                    TranslationChannels)) for f in range(duration)]
                self.do_animation_channel(
                    animation, duration, fps, "translation", translation, anim_idx, node_idx, gltf)

            if (rotation is not None):
                rotation = [list(rotation[c][f] for c in range(
                    RotationChannels)) for f in range(duration)]
                self.do_animation_channel(
                    animation, duration, fps, "rotation", rotation, anim_idx, node_idx, gltf)

            if (scale is not None):
                scale = [list(scale[c][f] for c in range(ScaleChannels))
                         for f in range(duration)]
                self.do_animation_channel(
                    animation, duration, fps, "scale", scale, anim_idx, node_idx, gltf)
