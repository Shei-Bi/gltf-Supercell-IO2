
from enum import StrEnum
from .brawlStarsLegacy import BrawlStarsLegacy
from .unlit import UnlitPreset


class ShaderPresetType(StrEnum):
    UNLIT = UnlitPreset.shader_idname
    BRAWL_STARS_LEGACY = BrawlStarsLegacy.shader_idname


class ShaderPresets:
    @staticmethod
    def get_preset_by_id(id: str):
        preset = None
        match(id):
            case ShaderPresetType.UNLIT:
                preset = UnlitPreset

            case ShaderPresetType.BRAWL_STARS_LEGACY:
                preset = BrawlStarsLegacy
            case _:
                raise NotImplementedError()

        return preset
