# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
import bpy

bl_info = {
    "name": "glTF Supercell IO",
    "author": "DaniilSV",
    "description": "",
    "blender": (2, 80, 0),
    "version": (0, 0, 1),
    "location": "",
    "warning": "",
    "category": "Generic",
}

from .importer.ui import glTFSupercellImporterProperties
from .importer.importer_patch import patch_importer
from .com.shader.nodes import ShaderNodeScShader, ShaderNodeScNode, node_tree_handler
from .com.editor import SHADER_OT_SC_create_shader, SHADER_PT_SC_create_shader

# Initialization functions for glTF importer extension
from .importer.ui import draw_import
from .importer import glTF2ImportUserExtension

classes = [
    glTFSupercellImporterProperties, # Importer
    ShaderNodeScNode,                # Base class for custom nodes
    ShaderNodeScShader,              # Custom shader
    SHADER_PT_SC_create_shader,      # Custom shader graph panel
    SHADER_OT_SC_create_shader       # Create shader operator
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.glTFSupercellImporterProperties = bpy.props.PointerProperty(type=glTFSupercellImporterProperties)
    patch_importer()
    
    bpy.app.handlers.load_post.append(node_tree_handler)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.glTFSupercellImporterProperties