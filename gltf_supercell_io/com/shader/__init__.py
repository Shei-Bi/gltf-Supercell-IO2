from bpy.types import NodeSocket, NodeSocketColor, NodeSocketFloatFactor, NodeSocketFloat, NodeSocketBool
from typing import TypeGuard


class ShaderUtils:
    def __init__(self) -> None:
        pass

    def is_texture_socket(self, socket: NodeSocket, name: str) -> TypeGuard[NodeSocketColor]:
        if (not isinstance(socket, NodeSocketColor) and not isinstance(socket, NodeSocketFloatFactor)):
            print(
                f"Warning: Failed to get texture prop socket in SC IO shader for {name}")
            return False

        return True

    def is_color_socket(self, socket: NodeSocket, name: str) -> TypeGuard[NodeSocketColor]:
        if (not isinstance(socket, NodeSocketColor)):
            print(
                f"Warning: Failed to get color prop socket in SC IO shader for {name}")
            return False

        return True
    
    def is_float_socket(self, socket: NodeSocket, name: str) -> TypeGuard[NodeSocketFloat]:
        if (not isinstance(socket, NodeSocketFloatFactor) and not isinstance(socket, NodeSocketFloat)):
            print(
                f"Warning: Failed to get float prop socket in SC IO shader for {name}")
            return False

        return True
    
    def is_bool_socket(self, socket: NodeSocket, name: str) -> TypeGuard[NodeSocketBool]:
        if (not isinstance(socket, NodeSocketBool)):
            print(
                f"Warning: Failed to get boolean prop socket in SC IO shader for {name}")
            return False

        return True