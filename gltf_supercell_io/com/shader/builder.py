import bpy
from pathlib import Path
from os.path import join, exists
from bpy.types import ShaderNodeGroup, ShaderNodeTexImage, ShaderNodeOutputMaterial, NodeOutputs, Image
from io_scene_gltf2.io.imp.gltf2_io_gltf import glTFImporter
from io_scene_gltf2.io.com.gltf2_io import Image as glImage
from typing import Tuple
from ..materials import ScShaderMaterial, ScBlendMode
from ..materials.variables import ShaderFloatVectorProperty, ShaderFloatProperty, ShaderTextureProperty, ShaderBooleanProperty, ShaderProperty
from .loader import LibraryLoader

NATIVE_IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".tif",
                           ".tiff", ".tga", ".bmp", ".exr",
                           ".dpx", ".cin", ".hdr"]

COMPRESSED_IMAGE_EXTENSIONS = [".ktx", ".sctx", ".pvr"]

IMAGE_EXTENSIONS = NATIVE_IMAGE_EXTENSIONS + COMPRESSED_IMAGE_EXTENSIONS


class ShaderBuilder:
    shader_idname = ""
    shader_label = ""

    def __init__(self, gltf: glTFImporter, sc_material: ScShaderMaterial, material: bpy.types.Material):
        self.gltf = gltf
        self.sc_material = sc_material
        self.material = material
        self.shader: ShaderNodeGroup = None
        self.node_counter = 0
        self.util_node_pos_offset = -125
        self.image_cache = {}
        self.basepath = Path(gltf.import_settings["filepath"]).parent

    def create_material(self):
        tree = self.material.node_tree
        self.setup_blending()

        output: ShaderNodeOutputMaterial = tree.nodes.new(
            'ShaderNodeOutputMaterial'
        )
        output.location = 200, 100

        self.shader = self.setup_shader()
        self.set_shader_props()
        tree.links.new(output.inputs[0], self.shader.outputs[0])

        if (len(self.sc_material.unused_constants)):
            self.shader["$constants"] = self.sc_material.unused_constants

        for variable in self.sc_material.unused_variables:
            self.set_raw_shader_prop(variable)

    def setup_blending(self):
        if self.sc_material.blend_mode == ScBlendMode.Opaque:
            self.material.surface_render_method = 'DITHERED'
        else:
            self.material.surface_render_method = 'BLENDED'

    def set_raw_shader_prop(self, raw_property: Tuple[str, ShaderProperty]):
        key, prop = raw_property
        if (isinstance(raw_property, ShaderNodeTexImage)):
            # TODO: Add image conversion ?
            self.shader[key] = prop.texture_path
        else:
            self.shader[key] = prop.value

    def set_constant_prop(self, name: str, index: int):
        socket = self.shader.inputs[index]
        socket.default_value = self.sc_material.has_constant(name)

    def load_compressed_texture_image(self, path: str) -> Image | None:
        return None

    def try_load_texture_image(self, path: Path) -> Image | None:
        for extension in IMAGE_EXTENSIONS:
            # Trying to load with usual path
            paths = [
                # Tweak for brawl stars, trying to use highres textures preferably
                join(self.basepath, "highres", path.with_suffix(
                    extension)),            # Default
                join(self.basepath, "highres", Path(
                    path.stem).with_suffix(extension)),  # Stem

                # Default path
                join(self.basepath, path.with_suffix(
                    extension)), path.with_suffix(extension),

                # Using path stem
                join(self.basepath, Path(path.stem).with_suffix(
                    extension)), Path(path.stem).with_suffix(extension),
            ]

            for maybe_path in paths:
                if (exists(maybe_path)):
                    if (extension not in NATIVE_IMAGE_EXTENSIONS):
                        return self.load_compressed_texture_image(maybe_path)

                    return bpy.data.images.load(maybe_path)

    def load_texture_image(self, node: ShaderNodeTexImage, prop: ShaderTextureProperty):
        # Using gltf images as our cache
        # Should be more reliable for some edge cases
        self.gltf.data.images = self.gltf.data.images or []
        gltf_images = [image for image in self.gltf.data.images if image.uri ==
                       prop.texture_path and image.blender_image_name is not None]
        if (len(gltf_images) > 0):
            name = gltf_images[0].blender_image_name
            image = bpy.data.images[name]
            node.image = image
            return

        path = Path(prop.texture_path)
        name = path.name
        extension = path.suffix

        def cache_image(image: Image):
            gltf_image = glImage(None, None, None, None,
                                 prop.texture_path, prop.texture_path)
            gltf_image.blender_image_name = image.name
            self.gltf.data.images.append(gltf_image)

        def fallback():
            image = bpy.data.images.new(name, 1, 1)
            node.image = image
            cache_image(image)

        if extension not in IMAGE_EXTENSIONS:
            print(
                f"Caught unknown image extension while processing SC IO materials: {prop.texture_path}. Creating empty image...")
            return fallback()

        # Firstly, trying to load texture as it is, and if blender supports that extension
        absolute_path = join(self.basepath, prop.texture_path)
        if (exists(absolute_path) and extension in NATIVE_IMAGE_EXTENSIONS):
            image = bpy.data.images.load(absolute_path)
            node.image = image
            cache_image(image)
            return

        # Finally, trying to load image with different extension and basepaths
        image = self.try_load_texture_image(path)
        if image is None:
            print(
                f"Failed to load texture while generating SC IO materials: {prop.texture_path}. Creating empty image...")
            return fallback()

        # Success
        image.name = prop.texture_path
        image.colorspace_settings.name = "scene_linear"
        node.image = image
        cache_image(image)

    def set_texture_prop(self, name: str, index: int, vector: NodeOutputs = None):
        prop: ShaderTextureProperty = self.sc_material.get_property(
            name, ShaderTextureProperty
        )

        if (prop is None):
            # Often textures leave a color, it needs to be marked as read
            self.sc_material.get_property(
                name, ShaderFloatVectorProperty
            )
            return

        node: ShaderNodeTexImage = self.image_cache.get(prop.texture_path)
        if (node is None):
            node: ShaderNodeTexImage = self.material.node_tree.nodes.new(
                "ShaderNodeTexImage"
            )
            self.load_texture_image(node, prop)

            x, y = self.shader.location

            # Base horizontal offset
            x -= 465

            # Vertical offset based on current node count and number
            if (self.node_counter and self.node_counter % 3 == 0):
                x -= 300
                y -= (self.node_counter / 2) * 100
            else:
                y -= self.node_counter * 280

            node.location = x, y
            node.extension = "REPEAT" if "repeat" in prop.keywords else "CLIP"
            self.node_counter += 1
            self.image_cache[prop.texture_path] = node

            if (vector is not None):
                self.material.node_tree.links.new(node.inputs[0], vector)

        self.material.node_tree.links.new(
            self.shader.inputs[index], node.outputs[0]
        )

        return node

    def set_color_prop(self, name: str, index: int):
        prop: ShaderFloatVectorProperty = self.sc_material.get_property(
            name, ShaderFloatVectorProperty
        )

        if (prop is None):
            return

        socket = self.shader.inputs[index]
        socket.default_value = prop.vector

    def set_float_prop(self, name: str, index: int):
        prop: ShaderFloatProperty = self.sc_material.get_property(
            name, ShaderFloatProperty
        )

        if (prop is None):
            return

        socket = self.shader.inputs[index]
        socket.default_value = prop.number

    def set_bool_prop(self, name: str, index: int):
        prop: ShaderBooleanProperty = self.sc_material.get_property(
            name, ShaderBooleanProperty
        )

        if (prop is None):
            return

        socket = self.shader.inputs[index]
        socket.default_value = prop.status

    def setup_shader(self):
        node = LibraryLoader.instantiate_shader(
            self.material.node_tree, self.shader_idname)

        node.label = self.shader_label
        node.location = 40 - node.width, 100

        return node

    def instantiate_utility(self, id: str, label: str) -> ShaderNodeGroup:
        node = LibraryLoader.instantiate_shader(self.material.node_tree, id)

        node.label = label
        x, y = self.shader.location

        # Base horizontal offset
        x -= 1040
        y = self.util_node_pos_offset
        self.util_node_pos_offset -= node.height + 50

        node.location = x, y

        return node

    def set_shader_props(self) -> ShaderNodeGroup:
        raise NotImplementedError()
