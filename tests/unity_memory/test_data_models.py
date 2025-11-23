"""
Unit tests for Unity memory data models.
"""

import pytest
from datetime import datetime
from python.unity_memory.data_models import (
    SceneData,
    GameObjectData,
    ComponentData,
    ScriptData,
    ClassData,
    MethodData,
    FieldData,
    AssetData,
    Task,
    TestScenario,
    UnityMemoryEntry,
    GameObjectFilters,
    ScriptFilters,
    AssetFilters,
)


def test_component_data_creation():
    """Test ComponentData can be created with required fields."""
    component = ComponentData(
        type="Transform",
        properties={"position": [0, 0, 0]},
    )
    assert component.type == "Transform"
    assert component.properties["position"] == [0, 0, 0]
    assert component.script_reference is None


def test_gameobject_data_creation(sample_gameobject):
    """Test GameObjectData can be created with components."""
    assert sample_gameobject.name == "Player"
    assert sample_gameobject.tag == "Player"
    assert len(sample_gameobject.components) == 2
    assert sample_gameobject.components[0].type == "Transform"


def test_scene_data_creation(sample_scene):
    """Test SceneData can be created with GameObjects."""
    assert sample_scene.scene_name == "TestScene"
    assert len(sample_scene.game_objects) == 1
    assert sample_scene.root_objects == ["Player"]


def test_script_data_creation(sample_script):
    """Test ScriptData can be created with classes."""
    assert sample_script.namespace == "Game.Player"
    assert len(sample_script.classes) == 1
    assert sample_script.classes[0].name == "PlayerController"
    assert len(sample_script.classes[0].methods) == 2


def test_asset_data_creation(sample_asset):
    """Test AssetData can be created with metadata."""
    assert sample_asset.asset_type == "Prefab"
    assert sample_asset.guid == "abc123def456"
    assert len(sample_asset.dependencies) == 1
    assert len(sample_asset.used_in_scenes) == 1


def test_task_creation():
    """Test Task can be created with all required fields."""
    now = datetime.now()
    task = Task(
        id="task-1",
        title="Implement player movement",
        description="Add WASD movement to player",
        status="pending",
        priority=3,
        created_at=now,
        updated_at=now,
    )
    assert task.id == "task-1"
    assert task.status == "pending"
    assert task.priority == 3
    assert task.completed_at is None


def test_test_scenario_creation():
    """Test TestScenario can be created with test data."""
    scenario = TestScenario(
        id="test-1",
        name="Player movement test",
        description="Test player moves correctly",
        test_type="unit",
        related_scripts=["PlayerController.cs"],
        related_scenes=[],
        inputs={"direction": "forward"},
        expected_outputs={"position": [0, 0, 1]},
    )
    assert scenario.id == "test-1"
    assert scenario.test_type == "unit"
    assert scenario.status == "not_run"


def test_unity_memory_entry_creation():
    """Test UnityMemoryEntry can be created."""
    now = datetime.now()
    entry = UnityMemoryEntry(
        id="entry-1",
        entity_type="script",
        entity_name="PlayerController",
        content="PlayerController script for player movement",
        metadata={"namespace": "Game.Player"},
        project_id="project-1",
        file_path="Assets/Scripts/PlayerController.cs",
        last_updated=now,
        tags=["script", "player", "controller"],
    )
    assert entry.id == "entry-1"
    assert entry.entity_type == "script"
    assert len(entry.tags) == 3


def test_gameobject_filters_creation():
    """Test GameObjectFilters can be created."""
    filters = GameObjectFilters(
        name_pattern="Player*",
        tags=["Player"],
        component_types=["Rigidbody"],
    )
    assert filters.name_pattern == "Player*"
    assert filters.tags == ["Player"]
    assert filters.layers is None


def test_script_filters_creation():
    """Test ScriptFilters can be created."""
    filters = ScriptFilters(
        class_name_pattern="*Controller",
        has_unity_callbacks=True,
    )
    assert filters.class_name_pattern == "*Controller"
    assert filters.has_unity_callbacks is True


def test_asset_filters_creation():
    """Test AssetFilters can be created."""
    filters = AssetFilters(
        asset_types=["Prefab", "Material"],
        size_range=(1024, 10240),
    )
    assert filters.asset_types == ["Prefab", "Material"]
    assert filters.size_range == (1024, 10240)
