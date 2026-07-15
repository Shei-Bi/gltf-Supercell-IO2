import ctypes
from pathlib import Path

_current_path = Path(__file__).resolve().parent
_candidates = [
    _current_path / "TextureLoader.dll",
    _current_path / "TextureLoader.so",
]

_dll_path = None
for candidate in _candidates:
    if candidate.exists():
        _dll_path = candidate
        break

if _dll_path is None:
    raise FileNotFoundError("Could not find texture load shared library")

TextureLoaderLib = ctypes.CDLL(str(_dll_path))
