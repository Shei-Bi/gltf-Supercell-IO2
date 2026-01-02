from .reader import OdinAnimationReader
from io_scene_gltf2.io.imp.gltf2_io_gltf import glTFImporter
from io_scene_gltf2.io.imp.gltf2_io_binary import BinaryData
import numpy as np


class OdinRawAnimationReader(OdinAnimationReader):
    def __init__(self, gltf: glTFImporter, animation: dict):
        super().__init__(animation)

        self.used_nodes = animation.get("nodes")  # type: ignore
        self.keyframe_mapping = animation.get("keyframeCounts")

        nodes_per_keyframe: list[int] = animation.get(
            "nodesNumberPerKeyframe"
        )  # type: ignore
        if (self.keyframe_mapping):
            self.keyframe_mapping = [num for i, num in enumerate(
                self.keyframe_mapping) for _ in range(nodes_per_keyframe[i])]

        self.buffer = BinaryData.decode_accessor(
            gltf, animation.get("accessor")
        )
        self.data: np.ndarray = None  # type: ignore

    def read(self):
        keyframes_total = sum(
            self.keyframe_mapping) if self.keyframe_mapping else self.keyframe_count

        # Position + Quaternion Rotation + Scale
        frame_transform_length = 3 + 4 + 3
        if (self.keyframe_mapping):
            remapped = np.reshape(
                self.buffer, (keyframes_total, frame_transform_length))
            self.data = np.split(remapped, np.cumsum(
                self.keyframe_mapping)[:-1])  # type: ignore
        else:
            self.data = np.reshape(self.buffer, (len(
                self.used_nodes), self.keyframe_count, frame_transform_length))
