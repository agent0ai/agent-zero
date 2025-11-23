"""
Stress tests for Unity memory data models using property-based testing.

These tests generate random data to validate that the data models handle
edge cases, large datasets, and various input combinations correctly.
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime, timedelta
import string

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
    Relationship,
    DependencyGraph,
)


# Custom strategies for generating Unity-specific data
@st.composite
def component_data_strategy(draw):
    """Generate random ComponentData."""
    component_types = ["Transform", "Rigidbody", "Collider", "Renderer", "AudioSource", "Camera"]
    return ComponentData(
        type=draw(st.sampled_from(component_types)),
        properties=draw(st.dictionaries(
            st.text(min_size=1, max_size=20, alphabet=string.ascii_letters),
            st.one_of(st.integers(), st.floats(allow_nan=False, allow_infinity=False), st.text(max_size=50), st.booleans())
        )),
        script_reference=draw(st.one_of(st.none(), st.text(min_size=1, max_size=100)))
    )


@st.composite
def gameobject_data_strategy(draw):
    """Generate random GameObjectData."""
    tags = ["Untagged", "Player", "Enemy", "UI", "Terrain", "Pickup"]
    return GameObjectData(
        name=draw(st.text(min_size=1, max_size=50, alphabet=string.ascii_letters + string.digits + "_")),
        tag=draw(st.sampled_from(tags)),
        layer=draw(st.integers(min_value=0, max_value=31)),
        components=draw(st.lists(component_data_strategy(), min_size=1, max_size=10)),
        children=draw(st.lists(st.text(min_size=1, max_size=50), max_size=20)),
        parent=draw(st.one_of(st.none(), st.text(min_size=1, max_size=50)))
    )


@st.composite
def scene_data_strategy(draw):
    """Generate random SceneData."""
    game_objects = draw(st.lists(gameobject_data_strategy(), min_size=1, max_size=100))
    return SceneData(
        scene_name=draw(st.text(min_size=1, max_size=50, alphabet=string.ascii_letters + string.digits)),
        scene_path=draw(st.text(min_size=10, max_size=200)),
        game_objects=game_objects,
        root_objects=draw(st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=len(game_objects)))
    )


@st.composite
def method_data_strategy(draw):
    """Generate random MethodData."""
    unity_callbacks = ["Start", "Update", "FixedUpdate", "LateUpdate", "OnEnable", "OnDisable", "Awake"]
    method_name = draw(st.one_of(
        st.sampled_from(unity_callbacks),
        st.text(min_size=1, max_size=50, alphabet=string.ascii_letters)
    ))
    return MethodData(
        name=method_name,
        parameters=draw(st.lists(
            st.tuples(
                st.text(min_size=1, max_size=20, alphabet=string.ascii_letters),
                st.text(min_size=1, max_size=30, alphabet=string.ascii_letters)
            ),
            max_size=10
        )),
        return_type=draw(st.sampled_from(["void", "int", "float", "bool", "string", "GameObject"])),
        is_unity_callback=method_name in unity_callbacks,
        is_public=draw(st.booleans())
    )


@st.composite
def field_data_strategy(draw):
    """Generate random FieldData."""
    return FieldData(
        name=draw(st.text(min_size=1, max_size=50, alphabet=string.ascii_letters + "_")),
        field_type=draw(st.sampled_from(["int", "float", "bool", "string", "Vector3", "GameObject"])),
        is_public=draw(st.booleans()),
        is_serialized=draw(st.booleans()),
        attributes=draw(st.lists(st.text(min_size=1, max_size=30), max_size=5))
    )


@st.composite
def class_data_strategy(draw):
    """Generate random ClassData."""
    return ClassData(
        name=draw(st.text(min_size=1, max_size=50, alphabet=string.ascii_letters)),
        base_classes=draw(st.lists(
            st.sampled_from(["MonoBehaviour", "ScriptableObject", "Object", "Component"]),
            min_size=1,
            max_size=3
        )),
        attributes=draw(st.lists(st.text(min_size=1, max_size=50), max_size=5)),
        methods=draw(st.lists(method_data_strategy(), min_size=1, max_size=20)),
        fields=draw(st.lists(field_data_strategy(), max_size=20))
    )


@st.composite
def script_data_strategy(draw):
    """Generate random ScriptData."""
    return ScriptData(
        file_path=draw(st.text(min_size=10, max_size=200)),
        namespace=draw(st.one_of(st.none(), st.text(min_size=1, max_size=100))),
        classes=draw(st.lists(class_data_strategy(), min_size=1, max_size=10)),
        imports=draw(st.lists(st.text(min_size=1, max_size=50), max_size=20))
    )


@st.composite
def asset_data_strategy(draw):
    """Generate random AssetData."""
    asset_types = ["Prefab", "Material", "Texture", "Audio", "Animation", "Shader", "Model"]
    return AssetData(
        asset_path=draw(st.text(min_size=10, max_size=200)),
        asset_type=draw(st.sampled_from(asset_types)),
        guid=draw(st.text(min_size=32, max_size=32, alphabet=string.hexdigits)),
        file_size=draw(st.integers(min_value=0, max_value=100_000_000)),
        dependencies=draw(st.lists(st.text(min_size=10, max_size=200), max_size=50)),
        used_in_scenes=draw(st.lists(st.text(min_size=10, max_size=200), max_size=20)),
        metadata=draw(st.dictionaries(
            st.text(min_size=1, max_size=20),
            st.one_of(st.integers(), st.text(max_size=100), st.booleans())
        ))
    )


@st.composite
def task_strategy(draw):
    """Generate random Task."""
    created = draw(st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2025, 12, 31)))
    updated = draw(st.datetimes(min_value=created, max_value=datetime(2025, 12, 31)))
    status = draw(st.sampled_from(["pending", "in_progress", "completed", "blocked"]))
    
    return Task(
        id=draw(st.text(min_size=1, max_size=50)),
        title=draw(st.text(min_size=1, max_size=200)),
        description=draw(st.text(min_size=0, max_size=1000)),
        status=status,
        priority=draw(st.integers(min_value=1, max_value=5)),
        created_at=created,
        updated_at=updated,
        completed_at=updated if status == "completed" else None,
        dependencies=draw(st.lists(st.text(min_size=1, max_size=50), max_size=20)),
        related_entities=draw(st.lists(st.text(min_size=1, max_size=50), max_size=30)),
        tags=draw(st.lists(st.text(min_size=1, max_size=30), max_size=10)),
        assignee=draw(st.one_of(st.none(), st.text(min_size=1, max_size=50)))
    )


# Property-based stress tests
@settings(max_examples=200)
@given(component_data_strategy())
def test_component_data_stress(component):
    """Stress test ComponentData with random inputs."""
    assert isinstance(component.type, str)
    assert len(component.type) > 0
    assert isinstance(component.properties, dict)
    if component.script_reference is not None:
        assert isinstance(component.script_reference, str)


@settings(max_examples=200)
@given(gameobject_data_strategy())
def test_gameobject_data_stress(gameobject):
    """Stress test GameObjectData with random inputs."""
    assert isinstance(gameobject.name, str)
    assert len(gameobject.name) > 0
    assert 0 <= gameobject.layer <= 31
    assert len(gameobject.components) > 0
    assert all(isinstance(c, ComponentData) for c in gameobject.components)


@settings(max_examples=100)
@given(scene_data_strategy())
def test_scene_data_stress(scene):
    """Stress test SceneData with random inputs and large GameObject counts."""
    assert isinstance(scene.scene_name, str)
    assert len(scene.scene_name) > 0
    assert len(scene.game_objects) > 0
    assert len(scene.root_objects) > 0
    assert all(isinstance(go, GameObjectData) for go in scene.game_objects)
    
    # Verify all root objects are valid
    assert len(scene.root_objects) <= len(scene.game_objects)


@settings(max_examples=100)
@given(script_data_strategy())
def test_script_data_stress(script):
    """Stress test ScriptData with random inputs."""
    assert isinstance(script.file_path, str)
    assert len(script.classes) > 0
    assert all(isinstance(c, ClassData) for c in script.classes)
    
    # Verify all classes have at least one method
    for cls in script.classes:
        assert len(cls.methods) > 0
        assert all(isinstance(m, MethodData) for m in cls.methods)


@settings(max_examples=200)
@given(asset_data_strategy())
def test_asset_data_stress(asset):
    """Stress test AssetData with random inputs."""
    assert isinstance(asset.asset_path, str)
    assert isinstance(asset.asset_type, str)
    assert len(asset.guid) == 32
    assert asset.file_size >= 0
    assert isinstance(asset.dependencies, list)
    assert isinstance(asset.used_in_scenes, list)


@settings(max_examples=200)
@given(task_strategy())
def test_task_stress(task):
    """Stress test Task with random inputs."""
    assert isinstance(task.id, str)
    assert len(task.id) > 0
    assert task.status in ["pending", "in_progress", "completed", "blocked"]
    assert 1 <= task.priority <= 5
    assert task.created_at <= task.updated_at
    
    # If completed, must have completion date
    if task.status == "completed":
        assert task.completed_at is not None
        assert task.completed_at >= task.created_at


@settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
@given(
    st.lists(gameobject_data_strategy(), min_size=10, max_size=1000)
)
def test_large_scene_stress(game_objects):
    """Stress test with very large scenes (up to 1000 GameObjects)."""
    scene = SceneData(
        scene_name="StressTestScene",
        scene_path="Assets/Scenes/StressTest.unity",
        game_objects=game_objects,
        root_objects=[go.name for go in game_objects[:min(10, len(game_objects))]]
    )
    
    assert len(scene.game_objects) >= 10
    assert len(scene.game_objects) <= 1000
    assert all(isinstance(go, GameObjectData) for go in scene.game_objects)


@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(
    st.lists(script_data_strategy(), min_size=10, max_size=500)
)
def test_large_project_scripts_stress(scripts):
    """Stress test with large number of scripts (up to 500)."""
    assert len(scripts) >= 10
    assert len(scripts) <= 500
    
    # Count total classes and methods
    total_classes = sum(len(s.classes) for s in scripts)
    total_methods = sum(len(c.methods) for s in scripts for c in s.classes)
    
    assert total_classes > 0
    assert total_methods > 0


@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(
    st.lists(asset_data_strategy(), min_size=10, max_size=1000)
)
def test_large_asset_database_stress(assets):
    """Stress test with large asset database (up to 1000 assets)."""
    assert len(assets) >= 10
    assert len(assets) <= 1000
    
    # Calculate total dependencies
    total_deps = sum(len(a.dependencies) for a in assets)
    total_scenes = sum(len(a.used_in_scenes) for a in assets)
    
    # Verify all assets have valid GUIDs
    guids = [a.guid for a in assets]
    assert all(len(g) == 32 for g in guids)


@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
@given(
    st.lists(task_strategy(), min_size=10, max_size=500)
)
def test_large_task_list_stress(tasks):
    """Stress test with large task lists (up to 500 tasks)."""
    assert len(tasks) >= 10
    assert len(tasks) <= 500
    
    # Count tasks by status
    status_counts = {}
    for task in tasks:
        status_counts[task.status] = status_counts.get(task.status, 0) + 1
    
    # Verify all statuses are valid
    assert all(status in ["pending", "in_progress", "completed", "blocked"] 
               for status in status_counts.keys())


@settings(max_examples=200)
@given(
    name_pattern=st.one_of(st.none(), st.text(max_size=50)),
    tags=st.one_of(st.none(), st.lists(st.text(min_size=1, max_size=20), max_size=10)),
    layers=st.one_of(st.none(), st.lists(st.integers(min_value=0, max_value=31), max_size=10)),
)
def test_gameobject_filters_stress(name_pattern, tags, layers):
    """Stress test GameObjectFilters with various combinations."""
    filters = GameObjectFilters(
        name_pattern=name_pattern,
        tags=tags,
        layers=layers
    )
    
    # Verify filters are properly constructed
    if filters.name_pattern is not None:
        assert isinstance(filters.name_pattern, str)
    if filters.tags is not None:
        assert isinstance(filters.tags, list)
    if filters.layers is not None:
        assert isinstance(filters.layers, list)
        assert all(0 <= layer <= 31 for layer in filters.layers)


@settings(max_examples=200)
@given(
    st.text(min_size=1, max_size=100),
    st.text(min_size=1, max_size=100),
    st.sampled_from([
        "script_references_gameobject",
        "gameobject_has_component",
        "prefab_instance",
        "asset_used_in_scene",
        "script_inherits_from",
        "method_calls_method"
    ]),
    st.dictionaries(st.text(min_size=1, max_size=20), st.text(max_size=100))
)
def test_relationship_stress(source_id, target_id, rel_type, metadata):
    """Stress test Relationship with various inputs."""
    rel = Relationship(
        source_id=source_id,
        target_id=target_id,
        relationship_type=rel_type,
        metadata=metadata
    )
    
    assert len(rel.source_id) > 0
    assert len(rel.target_id) > 0
    assert isinstance(rel.relationship_type, str)
    assert isinstance(rel.metadata, dict)


@settings(max_examples=100)
@given(
    st.text(min_size=1, max_size=100),
    st.lists(
        st.builds(
            Relationship,
            source_id=st.text(min_size=1, max_size=100),
            target_id=st.text(min_size=1, max_size=100),
            relationship_type=st.sampled_from(["script_references_gameobject", "gameobject_has_component"]),
            metadata=st.dictionaries(st.text(min_size=1, max_size=20), st.text(max_size=100))
        ),
        min_size=1,
        max_size=100
    ),
    st.integers(min_value=1, max_value=10)
)
def test_dependency_graph_stress(root_id, dependencies, depth):
    """Stress test DependencyGraph with complex dependency chains."""
    graph = DependencyGraph(
        root_entity_id=root_id,
        dependencies=dependencies,
        depth=depth
    )
    
    assert len(graph.root_entity_id) > 0
    assert len(graph.dependencies) > 0
    assert graph.depth >= 1
    assert all(isinstance(rel, Relationship) for rel in graph.dependencies)


def test_memory_entry_with_large_embedding():
    """Test UnityMemoryEntry with large embedding vectors."""
    now = datetime.now()
    
    # Test with various embedding sizes
    for size in [128, 256, 512, 768, 1024, 1536]:
        embedding = [0.1] * size
        entry = UnityMemoryEntry(
            id=f"entry-{size}",
            entity_type="script",
            entity_name="TestScript",
            content="Test content",
            metadata={},
            project_id="project-1",
            file_path="test.cs",
            last_updated=now,
            tags=["test"],
            embedding=embedding
        )
        
        assert len(entry.embedding) == size
        assert all(isinstance(v, float) for v in entry.embedding)


def test_concurrent_task_updates():
    """Test task updates with concurrent-like scenarios."""
    now = datetime.now()
    task = Task(
        id="task-1",
        title="Test Task",
        description="Testing concurrent updates",
        status="pending",
        priority=3,
        created_at=now,
        updated_at=now
    )
    
    # Simulate multiple updates
    for i in range(100):
        task.updated_at = now + timedelta(seconds=i)
        task.status = ["pending", "in_progress", "completed"][i % 3]
        
        assert task.updated_at >= task.created_at
        assert task.status in ["pending", "in_progress", "completed"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
