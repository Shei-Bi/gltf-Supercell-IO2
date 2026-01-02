import bpy
import sys
import types
import traceback
from io_scene_gltf2.blender.exp.export import __postprocess_with_gltfpack

TARGET_MODULE = "io_scene_gltf2.blender.exp.export"
TARGET_METHOD = "__write_file"

def write_gltf(json: dict, buffer: bytes):
    pass


def patched_write_file(fallback):
    """Patch the exporter to use the custom write_gltf function"""
    def __write_file(json, buffer, export_settings):
        props = bpy.context.scene.glTFSupercellExporterProperties # type: ignore
        if (not props.optimize_json):
            return fallback(json, buffer, export_settings)

        try:
            write_gltf(json, buffer)
            if (export_settings['gltf_use_gltfpack']):
                __postprocess_with_gltfpack(export_settings)

        except AssertionError as e:
            _, _, tb = sys.exc_info()
            traceback.print_tb(tb)  # Fixed format
            tb_info = traceback.extract_tb(tb)
            for tbi in tb_info:
                filename, line, func, text = tbi
                export_settings['log'].error('An error occurred on line {} in statement {}'.format(line, text))
            export_settings['log'].error(str(e))
            raise e

    return __write_file


if TARGET_MODULE not in sys.modules:
    fake_module = types.ModuleType(TARGET_MODULE)
    sys.modules[TARGET_MODULE] = fake_module


def patch_exporter():
    return
    try:
        mod = __import__(TARGET_MODULE, fromlist=[TARGET_METHOD])
        default = getattr(mod, TARGET_METHOD)

        #if getattr(default, "__sc_patched__", False):
        #    return

        wrapper = patched_write_file(default)
        wrapper.__sc_patched__ = True

        setattr(mod, TARGET_METHOD, wrapper)
    except Exception as e:
        print(f"[SC IO] Failed to patch exporter: {e}")
