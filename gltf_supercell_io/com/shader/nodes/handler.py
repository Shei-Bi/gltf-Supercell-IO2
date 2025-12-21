import bpy
import os
from bpy.app.handlers import persistent
from ..loader import LibraryLoader


@persistent
def node_tree_handler(dummy):
    need_relocate = False
    old_library = ""
    for group in bpy.data.node_groups:
        if (not group.is_missing):
            continue

        library = group.library
        filepath = library.filepath
        filename = os.path.basename(filepath)

        # making sure that source library is still there
        if (filename in ["supercell_io_shaders.blend"]):
            need_relocate = True
            old_library = filepath
            break

    # relocating if needed
    if (need_relocate):
        bpy.ops.wm.lib_relocate(
            library=old_library,
            filepath=LibraryLoader.LibraryPath
        )
