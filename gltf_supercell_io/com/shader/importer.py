from __future__ import annotations

import bpy
from pathlib import Path
from os.path import join, exists
from bpy.types import ShaderNodeTexImage, ShaderNodeOutputMaterial, Image, Material, ShaderNodeTree
from io_scene_gltf2.io.imp.gltf2_io_gltf import glTFImporter
from io_scene_gltf2.io.com.gltf2_io import Image as glImage
from typing import Tuple, Dict
from ..materials import ScShaderMaterial, ScBlendMode
from ..materials.variables import ShaderFloatVectorProperty, ShaderFloatProperty, ShaderTextureProperty, ShaderBooleanProperty, ShaderProperty
from ..utilities import ShaderUtils
from .loader import LibraryLoader

from typing import TYPE_CHECKING, Type
if TYPE_CHECKING:
    from ..shader_presets import ShaderPresetDescriptor

NATIVE_IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".tif",
                           ".tiff", ".tga", ".bmp", ".exr",
                           ".dpx", ".cin", ".hdr"]

COMPRESSED_IMAGE_EXTENSIONS = [".ktx", ".sctx", ".pvr"]

IMAGE_EXTENSIONS = NATIVE_IMAGE_EXTENSIONS + COMPRESSED_IMAGE_EXTENSIONS


class ShaderImporter(ShaderUtils):
    def __init__(self, gltf: glTFImporter, sc_material: ScShaderMaterial, material: Material, preset: Type[ShaderPresetDescriptor]):
        self.gltf = gltf
        self.sc_material = sc_material
        self.material = material
        self.tree: ShaderNodeTree = ShaderUtils.get_node_tree(material)
        self.preset = preset

        self.node_counter = 0
        self.util_node_pos_offset = -125
        self.image_cache: Dict[str, ShaderNodeTexImage] = {}
        self.basepath = Path(gltf.import_settings["filepath"]).parent

    def import_material(self):
        self.setup_blending()

        output: ShaderNodeOutputMaterial = self.tree.nodes.new(  # type: ignore
            'ShaderNodeOutputMaterial'
        )
        output.location = 200, 100

        self.shader = self.setup_shader()
        self.preset.import_shader(self)
        self.tree.links.new(output.inputs[0], self.shader.outputs[0])

        # Preserve unsupported shader constants
        if (len(self.sc_material.unused_constants)):
            self.shader["$constants"] = self.sc_material.unused_constants

        # Preserve shader name, uber by default
        if (self.sc_material.shader_name != "uber"):
            self.shader["$shader"] = self.sc_material.shader_name

        for variable in self.sc_material.unused_variables:
            self.set_raw_shader_prop(variable)

    def setup_blending(self):
        if self.sc_material.blend_mode == ScBlendMode.Opaque:
            self.material.surface_render_method = 'DITHERED'
        else:
            self.material.surface_render_method = 'BLENDED'

    def set_raw_shader_prop(self, raw_property: Tuple[str, ShaderProperty]):
        key, prop = raw_property
        if (isinstance(prop, ShaderTextureProperty)):
            if (not prop.path):
                return

            image = self.load_texture_image(prop, True)
            self.shader[key] = image
            return

        self.shader[key] = prop.value

    def set_constant_prop(self, name: str, index: int):
        socket = self.shader.inputs[index]

        if (self.is_bool_socket(socket, name)):
            socket.default_value = self.sc_material.has_constant(name)

    def load_compressed_texture_image(self, path: str) -> Image | None:
        return None

    def try_load_texture_image(self, path: Path) -> Image | None:
        for extension in IMAGE_EXTENSIONS:
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

    def load_texture_image(self, prop: ShaderTextureProperty, preserve_path: bool = False) -> Image:
        # Using gltf images as our cache
        # Should be more reliable for some edge cases
        self.gltf.data.images = self.gltf.data.images or []
        gltf_images = [image for image in self.gltf.data.images if image.uri ==
                       prop.path and image.blender_image_name is not None]
        if (len(gltf_images) > 0):
            name = gltf_images[0].blender_image_name
            image = bpy.data.images[name]
            return image

        path = Path(prop.path)
        extension = path.suffix

        if (extension == ".sc"):
            print(
                f"Supercell Flash as textures not supported now. Creating empty texture for '{path}'")
            preserve_path = True

        # Special handle for textures in custom properties
        # Since they dont have nodes in shader graph, it would be good if we preserve keywords at least in image name
        name = Path(prop.value) if preserve_path else Path(path.name)

        def cache_image(image: Image):
            gltf_image = glImage(None, None, None, None,
                                 prop.path, prop.path)
            gltf_image.blender_image_name = image.name  # type: ignore
            self.gltf.data.images.append(gltf_image)
            image.colorspace_settings.name = "scene_linear"  # type: ignore
            image.use_view_as_render = True

        def fallback():
            image = bpy.data.images.new(str(name), 1, 1)
            cache_image(image)
            return image

        if extension not in IMAGE_EXTENSIONS:
            print(
                f"Caught unknown image extension while processing SC IO materials: {prop.path}. Creating empty image...")
            return fallback()

        # Firstly, trying to load texture as it is, and if blender supports that extension
        absolute_path = join(self.basepath, prop.path)
        if (exists(absolute_path) and extension in NATIVE_IMAGE_EXTENSIONS):
            image = bpy.data.images.load(absolute_path)
            cache_image(image)
            return image

        # Finally, trying to load image with different extension and basepaths
        image = self.try_load_texture_image(path)
        if image is None:
            print(
                f"Failed to load texture while generating SC IO materials: {prop.path}. Creating empty image...")
            return fallback()

        # Success
        image.name = prop.path
        cache_image(image)
        return image

    def set_texture_prop(self, name: str, index: int):
        prop = self.sc_material.get_property(
            name, ShaderTextureProperty
        )

        if (prop is None):
            # Often textures leave a color, it needs to be marked as read
            self.sc_material.get_property(
                name, ShaderFloatVectorProperty
            )
            return

        if (not prop.path):
            return

        node = self.image_cache.get(
            prop.path
        )  # type: ignore
        if (node is None):
            texture: ShaderNodeTexImage = self.tree.nodes.new(
                "ShaderNodeTexImage"
            )  # type: ignore
            texture.image = self.load_texture_image(prop)

            x, y = self.shader.location

            # Base horizontal offset
            x -= 465

            # Vertical offset based on current node count and number
            if (self.node_counter and self.node_counter % 3 == 0):
                x -= 300
                y -= (self.node_counter / 2) * 100
            else:
                y -= self.node_counter * 280

            texture.location = x, y
            texture.extension = "REPEAT" if "repeat" in prop.keywords else "CLIP"
            self.node_counter += 1
            node = self.image_cache[prop.path] = texture

        self.tree.links.new(  # type: ignore
            self.shader.inputs[index], node.outputs[0]
        )

        return node

    def set_color_prop(self, name: str, index: int):
        prop = self.sc_material.get_property(
            name, ShaderFloatVectorProperty
        )

        if (prop is None):
            return

        socket = self.shader.inputs[index]
        if (self.is_color_socket(socket, name)):
            socket.default_value = prop.vector

    def set_float_prop(self, name: str, index: int):
        socket = self.shader.inputs[index]
        if (not self.is_float_socket(socket, name)):
            return

        float_prop = self.sc_material.get_property(
            name, ShaderFloatProperty
        )

        if (float_prop):
            socket.default_value = float_prop.number
            return

        # Sometimes floats are saved as color, as if after conversion or something
        # Bruh, based supercell devs
        # so trying to get it as color
        vector_prop = self.sc_material.get_property(
            name, ShaderFloatVectorProperty
        )
        if (vector_prop and len(vector_prop.value)):
            socket.default_value = vector_prop.value[0]

    def set_bool_prop(self, name: str, index: int):
        prop = self.sc_material.get_property(
            name, ShaderBooleanProperty
        )

        if (prop is None):
            return

        socket = self.shader.inputs[index]
        if (self.is_bool_socket(socket, name)):
            socket.default_value = prop.status

    def setup_shader(self):
        node = LibraryLoader.instantiate_shader(
            self.tree, self.preset.shader_idname
        )

        node.label = self.preset.shader_label
        node.location = 40 - node.width, 100

        return node

    def instantiate_utility(self, id: str, label: str):
        node = LibraryLoader.instantiate_utility(
            self.tree, id
        )

        node.label = label
        x, y = self.shader.location

        # Base horizontal offset
        x -= 1040
        y = self.util_node_pos_offset
        self.util_node_pos_offset -= node.height + 50

        node.location = x, y

        return node
