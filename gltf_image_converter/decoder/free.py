from ctypes import c_void_p, c_int

from ..bin.loader import TextureLoaderLib

TextureLoaderLib.free_decompressed_data.argtypes = [
    c_void_p,
]
TextureLoaderLib.free_decompressed_data.restype = c_int


def free_buffer(ptr: c_void_p):
    TextureLoaderLib.free_decompressed_data(ptr)
