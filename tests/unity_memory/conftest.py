"""
Pytest configuration and fixtures for Unity memory tests.
"""

import pytest
from datetime import datetime
from typing import List
from python.unity_memory.data_models import (
    SceneData,
    GameObjectData,
    ComponentData,
    ScriptData,
    ClassData,
    MethodData,
    FieldData,
    AssetData,
)


@pytest.fixture
def sample_gameobject():
    """Create a sample GameObject for testing."""
    return GameObjectData(
        name="Player",
        tag="Player",
        layer=0,
        components=[
            ComponentData(
                type="Transform",
                properties={"position": [0, 0, 0], "rotation": [0, 0, 0, 1]},
            ),
            ComponentData(
                type="Rigidbody",
                properties={"mass": 1.0, "useGravity": True},
            ),
        ],
        children=[],
        parent=None,
    )


@pytest.fixture
def sample_scene(sample_gameobject):
    """Create a sample scene for testing."""
    return SceneData(
        scene_name="TestScene",
        scene_path="Assets/Scenes/TestScene.unity",
        game_objects=[sample_gameobject],
        root_objects=["Player"],
    )


@pytest.fixture
def sample_script():
    """Create a sample script for testing."""
    return ScriptData(
        file_path="Assets/Scripts/PlayerController.cs",
        namespace="Game.Player",
        classes=[
            ClassData(
                name="PlayerController",
                base_classes=["MonoBehaviour"],
                attributes=["RequireComponent(typeof(Rigidbody))"],
                methods=[
                    MethodData(
                        name="Start",
                        parameters=[],
                        return_type="void",
                        is_unity_callback=True,
                    ),
                    MethodData(
                        name="Update",
                        parameters=[],
                        return_type="void",
                        is_unity_callback=True,
                    ),
                ],
                fields=[
                    FieldData(
                        name="moveSpeed",
                        field_type="float",
                        is_public=True,
                        is_serialized=True,
                        attributes=["SerializeField"],
                    ),
                ],
            )
        ],
        imports=["UnityEngine"],
    )


@pytest.fixture
def sample_asset():
    """Create a sample asset for testing."""
    return AssetData(
        asset_path="Assets/Prefabs/Player.prefab",
        asset_type="Prefab",
        guid="abc123def456",
        file_size=4096,
        dependencies=["Assets/Materials/PlayerMat.mat"],
        used_in_scenes=["Assets/Scenes/MainScene.unity"],
        metadata={"version": 1},
    )
