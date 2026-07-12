from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..shader.importer import ShaderImporter
    from ..shader.exporter import ShaderExporter


class ShaderPresetDescriptor(ABC):
    shader_idname = ""
    shader_label = ""

    @staticmethod
    @abstractmethod
    def import_shader(shader: ShaderImporter) -> None:
        pass

    @staticmethod
    @abstractmethod
    def export_shader(shader: ShaderExporter) -> None:
        pass
