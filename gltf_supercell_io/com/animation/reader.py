from typing import Tuple, List
from .flags import OdinAnimationFlags


class OdinAnimationReader:
    def __init__(self, animation: dict):
        self.frame_rate = animation.get("frameRate") or 30
        self.frame_spf = 1.0 / self.frame_rate
        self.keyframe_count = (animation.get(
            "keyframesCount") or animation.get("keyframeCount")) or 1
        self.nodes_per_keyframe = animation.get("nodesNumberPerKeyframe")
        self.keyframe_mapping: List[int] | None = None
        self.used_nodes: List[int] = []

    def get_node_flags(self, node_idx: int):
        return OdinAnimationFlags(0xFF)

    def read(self):
        """Reads buffer data"""
        raise NotImplementedError()

    def get_scale(self, node_idx: int):
        return None

    def get_translation(self, node_idx: int):
        return None

    def get_rotation(self, node_idx: int):
        return None

    def get_frame_data(self, node_index: int, frame_index: int) -> Tuple[list, list, list]:
        """Returns frame data for specific node in format (Translation, Rotation, Scale)"""
        raise NotImplementedError()
