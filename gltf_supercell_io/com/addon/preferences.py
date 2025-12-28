import bpy
from bpy.types import AddonPreferences, Scene
from bpy.props import PointerProperty
from bpy.app.handlers import persistent
from ...importer.ui import glTFSupercellImporterProperties
from ...exporter.ui import glTFSupercellExporterProperties

class SupercellAddonPreferences(AddonPreferences):
    bl_idname = __package__
    
    import_settings: PointerProperty(type=glTFSupercellImporterProperties)
    export_settings: PointerProperty(type=glTFSupercellExporterProperties)
    
    @staticmethod
    def restore_defaults(scene: Scene):
        prefs = bpy.context.preferences.addons[__package__].preferences

        src_dst = [
            (prefs.import_settings, scene.importer_props),
            (prefs.export_settings, scene.exporter_props),
        ]

        for src, dst in src_dst:
            for prop_id in src.bl_rna.properties.keys():
                if prop_id == "rna_type":
                    continue
                if prop_id not in dst:
                    setattr(dst, prop_id, getattr(src, prop_id))
                    
    @staticmethod
    @persistent
    def handle_restore(dummy):
        for scene in bpy.data.scenes:
            SupercellAddonPreferences.restore_defaults(scene)