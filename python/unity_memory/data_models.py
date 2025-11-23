"""
Data models for Unity Game Development Memory System.

This module defines all data structures used throughout the Unity memory system,
including scene data, script data, asset data, tasks, and test scenarios.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple


@dataclass
class ComponentData:
    """Represents a Unity component attached to a GameObject."""
    type: str
    properties: Dict[str, Any]
    script_reference: Optional[str] = None


@dataclass
class GameObjectData:
    """Represents a Unity GameObject with its components and hierarchy."""
    name: str
    tag: str
    layer: int
    components: List[ComponentData]
    children: List[str]
    parent: Optional[str] = None


@dataclass
class SceneData:
    """Represents a Unity scene with its GameObject hierarchy."""
    scene_name: str
    scene_path: str
    game_objects: List[GameObjectData]
    root_objects: List[str]


@dataclass
class FieldData:
    """Represents a field in a C# class."""
    name: str
    field_type: str
    is_public: bool = False
    is_serialized: bool = False
    attributes: List[str] = field(default_factory=list)


@dataclass
class MethodData:
    """Represents a method in a C# class."""
    name: str
    parameters: List[Tuple[str, str]]  # (name, type)
    return_type: str
    is_unity_callback: bool = False
    is_public: bool = True


@dataclass
class ClassData:
    """Represents a C# class definition."""
    name: str
    base_classes: List[str]
    attributes: List[str]  # Unity attributes like [SerializeField]
    methods: List[MethodData]
    fields: List[FieldData]


@dataclass
class ScriptData:
    """Represents a C# script file."""
    file_path: str
    namespace: Optional[str]
    classes: List[ClassData]
    imports: List[str]


@dataclass
class AssetData:
    """Represents a Unity asset with metadata."""
    asset_path: str
    asset_type: str  # Prefab, Material, Texture, Audio, etc.
    guid: str
    file_size: int
    dependencies: List[str] = field(default_factory=list)
    used_in_scenes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProjectSettings:
    """Represents Unity project settings."""
    unity_version: str
    project_name: str
    settings: Dict[str, Any]


@dataclass
class Task:
    """Represents a development task."""
    id: str
    title: str
    description: str
    status: str  # pending, in_progress, completed, blocked
    priority: int  # 1-5
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    dependencies: List[str] = field(default_factory=list)  # Task IDs
    related_entities: List[str] = field(default_factory=list)  # Unity entity IDs
    tags: List[str] = field(default_factory=list)
    assignee: Optional[str] = None


@dataclass
class TestScenario:
    """Represents a test scenario and its results."""
    id: str
    name: str
    description: str
    test_type: str  # unit, integration, playmode
    related_scripts: List[str]
    related_scenes: List[str]
    inputs: Dict[str, Any]
    expected_outputs: Dict[str, Any]
    actual_outputs: Optional[Dict[str, Any]] = None
    status: str = "not_run"  # passed, failed, skipped, not_run
    execution_time: Optional[float] = None
    executed_at: Optional[datetime] = None
    failure_details: Optional[str] = None


@dataclass
class UnityMemoryEntry:
    """Represents an entry in the Unity memory system."""
    id: str  # Unique identifier
    entity_type: str  # scene, script, asset, gameobject, component, etc.
    entity_name: str
    content: str  # Text representation for embedding
    metadata: Dict[str, Any]
    project_id: str
    file_path: str
    last_updated: datetime
    tags: List[str]
    embedding: Optional[List[float]] = None


@dataclass
class GameObjectFilters:
    """Filters for GameObject search queries."""
    name_pattern: Optional[str] = None
    tags: Optional[List[str]] = None
    layers: Optional[List[int]] = None
    component_types: Optional[List[str]] = None
    scene_names: Optional[List[str]] = None


@dataclass
class ScriptFilters:
    """Filters for script search queries."""
    class_name_pattern: Optional[str] = None
    method_name_pattern: Optional[str] = None
    namespace_pattern: Optional[str] = None
    inherits_from: Optional[str] = None
    has_unity_callbacks: Optional[bool] = None


@dataclass
class AssetFilters:
    """Filters for asset search queries."""
    asset_types: Optional[List[str]] = None  # Prefab, Material, Texture, etc.
    name_pattern: Optional[str] = None
    used_in_scenes: Optional[List[str]] = None
    size_range: Optional[Tuple[int, int]] = None  # (min_bytes, max_bytes)


@dataclass
class Relationship:
    """Represents a relationship between two Unity entities."""
    source_id: str
    target_id: str
    relationship_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DependencyGraph:
    """Represents a dependency graph for an entity."""
    root_entity_id: str
    dependencies: List[Relationship]
    depth: int


@dataclass
class MemoryResult:
    """Represents a search result from the memory system."""
    entry: UnityMemoryEntry
    score: float
    rank: int


@dataclass
class QueryResult:
    """Represents a query result with additional context."""
    entry: UnityMemoryEntry
    score: float
    relationships: List[Relationship] = field(default_factory=list)


@dataclass
class DependencyResult:
    """Result of a dependency query."""
    entity_id: str
    dependency_graph: DependencyGraph
    total_dependencies: int


@dataclass
class UsageResult:
    """Result of a usage query."""
    entity_id: str
    usages: List[Relationship]
    total_usages: int
