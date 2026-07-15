from pathlib import Path

from ..bin.loader import TextureLoaderLib
from .free import free_buffer
from ctypes import c_char_p, POINTER, c_void_p, c_uint, c_int, byref, string_at

TextureLoaderLib.decompress_sctx.argtypes = [
    c_char_p,  # path
    POINTER(c_void_p),  # data_out
    POINTER(c_uint),  # data_out_len
    POINTER(c_uint),  # width_out
    POINTER(c_uint),  # height_out
    POINTER(c_char_p),  # error_out
]
TextureLoaderLib.decompress_sctx.restype = c_int


def decode_sctx(path: Path):
    print(f"Decoding sctx at {path} using image converter")

    data = c_void_p()
    data_len = c_uint()
    width = c_uint()
    height = c_uint()
    error = c_char_p()

    result = TextureLoaderLib.decompress_sctx(
        str(path).encode("utf-8"),
        byref(data),
        byref(data_len),
        byref(width),
        byref(height),
        byref(error),
    )

    if result != 0:
        if error.value:
            raise RuntimeError(error.value.decode("utf-8"))
        raise RuntimeError(f"Failed to decode sctx with code {result}")

    try:
        buffer = string_at(data, data_len.value)
        return buffer, width.value, height.value
    finally:
        if data:
            free_buffer(data)
