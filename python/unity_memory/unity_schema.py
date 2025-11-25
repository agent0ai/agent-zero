"""
Advanced Unity Memory Schema with Relationships and Dependencies.

This module provides a comprehensive schema system for Unity project knowledge:
- Entity types with rich metadata
- Relationship graphs for dependencies
- Query builders for complex searches
- Schema validation and migration
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Set, Union
import json
import hashlib
import re


class EntityType(Enum):
    """Unity entity types for categorization."""
    SCENE = "scene"
    GAMEOBJECT = "gameobject"
    COMPONENT = "component"
    SCRIPT = "script"
    CLASS = "class"
    METHOD = "method"
    FIELD = "field"
    PREFAB = "prefab"
    MATERIAL = "material"
    TEXTURE = "texture"
    AUDIO = "audio"
    ANIMATION = "animation"
    ANIMATOR = "animator"
    SHADER = "shader"
    MESH = "mesh"
    ASSET = "asset"
    SCRIPTABLE_OBJECT = "scriptable_object"
    PROJECT_SETTINGS = "project_settings"
    TASK = "task"
    ERROR = "error"
    SOLUTION = "solution"
    BUILD_LOG = "build_log"
    DOCUMENTATION = "documentation"
    CONVERSATION = "conversation"


class RelationshipType(Enum):
    """Types of relationships between Unity entities."""
    # Hierarchy relationships
    PARENT_OF = "parent_of"
    CHILD_OF = "child_of"
    CONTAINS = "contains"
    CONTAINED_IN = "contained_in"

    # Component relationships
    ATTACHED_TO = "attached_to"
    HAS_COMPONENT = "has_component"

    # Script relationships
    INHERITS_FROM = "inherits_from"
    IMPLEMENTS = "implements"
    REFERENCES = "references"
    REFERENCED_BY = "referenced_by"
    USES_METHOD = "uses_method"
    CALLS = "calls"
    CALLED_BY = "called_by"

    # Asset relationships
    DEPENDS_ON = "depends_on"
    DEPENDENCY_OF = "dependency_of"
    USED_BY = "used_by"
    USES = "uses"
    INSTANTIATES = "instantiates"

    # Scene relationships
    IN_SCENE = "in_scene"
    SCENE_CONTAINS = "scene_contains"
    LOADS_SCENE = "loads_scene"

    # Development relationships
    SOLVES = "solves"
    CAUSED_BY = "caused_by"
    RELATED_TO = "related_to"
    BLOCKS = "blocks"
    BLOCKED_BY = "blocked_by"


class ComponentCategory(Enum):
    """Unity component categories."""
    TRANSFORM = "transform"
    RENDERER = "renderer"
    COLLIDER = "collider"
    RIGIDBODY = "rigidbody"
    AUDIO = "audio"
    CAMERA = "camera"
    LIGHT = "light"
    UI = "ui"
    ANIMATION = "animation"
    PHYSICS = "physics"
    NETWORKING = "networking"
    AI = "ai"
    CUSTOM = "custom"


@dataclass
class UnityEntitySchema:
    """Base schema for all Unity entities."""
    id: str
    entity_type: EntityType
    name: str
    project_id: str
    file_path: Optional[str] = None
    content: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_embedding_text(self) -> str:
        """Generate text for embedding."""
        parts = [
            f"Type: {self.entity_type.value}",
            f"Name: {self.name}",
        ]
        if self.file_path:
            parts.append(f"Path: {self.file_path}")
        if self.tags:
            parts.append(f"Tags: {', '.join(self.tags)}")
        parts.append(f"Content: {self.content}")
        return "\n".join(parts)

    def to_payload(self) -> Dict[str, Any]:
        """Convert to Qdrant payload format."""
        return {
            "id": self.id,
            "entity_type": self.entity_type.value,
            "entity_name": self.name,
            "project_id": self.project_id,
            "file_path": self.file_path,
            "text": self.to_embedding_text(),
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            **self.metadata,
        }


@dataclass
class SceneSchema(UnityEntitySchema):
    """Schema for Unity scenes."""
    scene_path: str = ""
    build_index: int = -1
    is_loaded: bool = False
    root_object_count: int = 0
    total_object_count: int = 0
    lighting_settings: Dict[str, Any] = field(default_factory=dict)
    navigation_settings: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.entity_type = EntityType.SCENE

    def to_embedding_text(self) -> str:
        text = super().to_embedding_text()
        text += f"\nBuild Index: {self.build_index}"
        text += f"\nRoot Objects: {self.root_object_count}"
        text += f"\nTotal Objects: {self.total_object_count}"
        return text


@dataclass
class GameObjectSchema(UnityEntitySchema):
    """Schema for Unity GameObjects."""
    scene_name: str = ""
    tag: str = "Untagged"
    layer: int = 0
    is_active: bool = True
    is_static: bool = False
    component_types: List[str] = field(default_factory=list)
    parent_name: Optional[str] = None
    children_names: List[str] = field(default_factory=list)
    prefab_source: Optional[str] = None
    transform_position: Tuple[float, float, float] = (0, 0, 0)
    transform_rotation: Tuple[float, float, float, float] = (0, 0, 0, 1)
    transform_scale: Tuple[float, float, float] = (1, 1, 1)

    def __post_init__(self):
        self.entity_type = EntityType.GAMEOBJECT

    def to_embedding_text(self) -> str:
        text = super().to_embedding_text()
        text += f"\nScene: {self.scene_name}"
        text += f"\nTag: {self.tag}"
        text += f"\nLayer: {self.layer}"
        if self.component_types:
            text += f"\nComponents: {', '.join(self.component_types)}"
        if self.parent_name:
            text += f"\nParent: {self.parent_name}"
        if self.children_names:
            text += f"\nChildren: {', '.join(self.children_names[:10])}"
        return text


@dataclass
class ComponentSchema(UnityEntitySchema):
    """Schema for Unity components."""
    component_type: str = ""
    category: ComponentCategory = ComponentCategory.CUSTOM
    gameobject_name: str = ""
    scene_name: str = ""
    is_enabled: bool = True
    properties: Dict[str, Any] = field(default_factory=dict)
    script_guid: Optional[str] = None

    def __post_init__(self):
        self.entity_type = EntityType.COMPONENT

    def to_embedding_text(self) -> str:
        text = super().to_embedding_text()
        text += f"\nComponent Type: {self.component_type}"
        text += f"\nCategory: {self.category.value}"
        text += f"\nAttached To: {self.gameobject_name}"
        text += f"\nIn Scene: {self.scene_name}"
        if self.properties:
            text += f"\nProperties: {json.dumps(self.properties, default=str)[:500]}"
        return text


@dataclass
class ScriptSchema(UnityEntitySchema):
    """Schema for C# scripts."""
    namespace: Optional[str] = None
    class_names: List[str] = field(default_factory=list)
    base_classes: List[str] = field(default_factory=list)
    interfaces: List[str] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    unity_callbacks: List[str] = field(default_factory=list)
    fields: List[str] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)
    line_count: int = 0
    is_monobehaviour: bool = False
    is_scriptable_object: bool = False
    is_editor_script: bool = False
    dependencies: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.entity_type = EntityType.SCRIPT

    def to_embedding_text(self) -> str:
        text = super().to_embedding_text()
        if self.namespace:
            text += f"\nNamespace: {self.namespace}"
        if self.class_names:
            text += f"\nClasses: {', '.join(self.class_names)}"
        if self.base_classes:
            text += f"\nInherits: {', '.join(self.base_classes)}"
        if self.interfaces:
            text += f"\nImplements: {', '.join(self.interfaces)}"
        if self.unity_callbacks:
            text += f"\nUnity Callbacks: {', '.join(self.unity_callbacks)}"
        if self.methods:
            text += f"\nMethods: {', '.join(self.methods[:20])}"
        return text


@dataclass
class ClassSchema(UnityEntitySchema):
    """Schema for individual C# classes."""
    script_path: str = ""
    namespace: Optional[str] = None
    base_class: Optional[str] = None
    interfaces: List[str] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)
    is_abstract: bool = False
    is_sealed: bool = False
    is_static: bool = False
    is_partial: bool = False
    generic_parameters: List[str] = field(default_factory=list)
    methods: List[Dict[str, Any]] = field(default_factory=list)
    fields: List[Dict[str, Any]] = field(default_factory=list)
    properties: List[Dict[str, Any]] = field(default_factory=list)
    events: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        self.entity_type = EntityType.CLASS

    def to_embedding_text(self) -> str:
        text = super().to_embedding_text()
        if self.namespace:
            text += f"\nNamespace: {self.namespace}"
        if self.base_class:
            text += f"\nBase Class: {self.base_class}"
        if self.interfaces:
            text += f"\nInterfaces: {', '.join(self.interfaces)}"
        if self.attributes:
            text += f"\nAttributes: {', '.join(self.attributes)}"

        modifiers = []
        if self.is_abstract:
            modifiers.append("abstract")
        if self.is_sealed:
            modifiers.append("sealed")
        if self.is_static:
            modifiers.append("static")
        if modifiers:
            text += f"\nModifiers: {', '.join(modifiers)}"

        if self.methods:
            method_names = [m.get("name", "") for m in self.methods]
            text += f"\nMethods: {', '.join(method_names[:15])}"

        return text


@dataclass
class MethodSchema(UnityEntitySchema):
    """Schema for individual methods."""
    class_name: str = ""
    script_path: str = ""
    return_type: str = "void"
    parameters: List[Tuple[str, str]] = field(default_factory=list)
    is_public: bool = True
    is_static: bool = False
    is_virtual: bool = False
    is_override: bool = False
    is_abstract: bool = False
    is_async: bool = False
    is_unity_callback: bool = False
    attributes: List[str] = field(default_factory=list)
    line_number: int = 0

    def __post_init__(self):
        self.entity_type = EntityType.METHOD

    def to_embedding_text(self) -> str:
        text = super().to_embedding_text()
        text += f"\nClass: {self.class_name}"
        text += f"\nReturn Type: {self.return_type}"
        if self.parameters:
            param_str = ", ".join(f"{t} {n}" for n, t in self.parameters)
            text += f"\nParameters: {param_str}"
        if self.is_unity_callback:
            text += "\nUnity Callback: Yes"
        return text


@dataclass
class AssetSchema(UnityEntitySchema):
    """Schema for Unity assets."""
    asset_type: str = ""
    guid: str = ""
    file_size: int = 0
    import_settings: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    used_in_scenes: List[str] = field(default_factory=list)
    used_by_prefabs: List[str] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.entity_type = EntityType.ASSET

    def to_embedding_text(self) -> str:
        text = super().to_embedding_text()
        text += f"\nAsset Type: {self.asset_type}"
        text += f"\nGUID: {self.guid}"
        text += f"\nSize: {self.file_size} bytes"
        if self.dependencies:
            text += f"\nDependencies: {len(self.dependencies)}"
        if self.used_in_scenes:
            text += f"\nUsed in Scenes: {', '.join(self.used_in_scenes[:5])}"
        return text


@dataclass
class PrefabSchema(AssetSchema):
    """Schema for Unity prefabs."""
    root_gameobject: str = ""
    component_types: List[str] = field(default_factory=list)
    nested_prefabs: List[str] = field(default_factory=list)
    gameobject_count: int = 0
    is_variant: bool = False
    base_prefab: Optional[str] = None

    def __post_init__(self):
        self.entity_type = EntityType.PREFAB
        self.asset_type = "Prefab"

    def to_embedding_text(self) -> str:
        text = super().to_embedding_text()
        text += f"\nRoot GameObject: {self.root_gameobject}"
        if self.component_types:
            text += f"\nComponents: {', '.join(self.component_types)}"
        text += f"\nGameObject Count: {self.gameobject_count}"
        if self.is_variant:
            text += f"\nVariant of: {self.base_prefab}"
        return text


@dataclass
class TaskSchema(UnityEntitySchema):
    """Schema for development tasks."""
    title: str = ""
    description: str = ""
    status: str = "pending"  # pending, in_progress, completed, blocked
    priority: int = 3  # 1-5, 1 highest
    assignee: Optional[str] = None
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    dependencies: List[str] = field(default_factory=list)
    related_entities: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.entity_type = EntityType.TASK

    def to_embedding_text(self) -> str:
        text = f"Task: {self.title}\n"
        text += f"Status: {self.status}\n"
        text += f"Priority: {self.priority}\n"
        text += f"Description: {self.description}\n"
        if self.tags:
            text += f"Tags: {', '.join(self.tags)}\n"
        return text


@dataclass
class ErrorSchema(UnityEntitySchema):
    """Schema for Unity errors and exceptions."""
    error_type: str = ""
    error_message: str = ""
    stack_trace: str = ""
    severity: str = "error"  # warning, error, exception
    related_script: Optional[str] = None
    related_line: Optional[int] = None
    context: str = ""
    frequency: int = 1
    first_occurrence: datetime = field(default_factory=datetime.now)
    last_occurrence: datetime = field(default_factory=datetime.now)
    solution: Optional[str] = None
    is_resolved: bool = False

    def __post_init__(self):
        self.entity_type = EntityType.ERROR

    def to_embedding_text(self) -> str:
        text = f"Error Type: {self.error_type}\n"
        text += f"Message: {self.error_message}\n"
        text += f"Severity: {self.severity}\n"
        if self.related_script:
            text += f"Script: {self.related_script}\n"
        if self.related_line:
            text += f"Line: {self.related_line}\n"
        text += f"Stack Trace:\n{self.stack_trace[:1000]}\n"
        if self.solution:
            text += f"\nSolution: {self.solution}"
        return text


@dataclass
class SolutionSchema(UnityEntitySchema):
    """Schema for documented solutions."""
    problem_description: str = ""
    solution_description: str = ""
    code_example: str = ""
    related_errors: List[str] = field(default_factory=list)
    affected_versions: List[str] = field(default_factory=list)
    effectiveness_score: float = 0.0
    usage_count: int = 0
    last_used: Optional[datetime] = None
    source: str = ""  # internal, stackoverflow, documentation, etc.

    def __post_init__(self):
        self.entity_type = EntityType.SOLUTION

    def to_embedding_text(self) -> str:
        text = f"Problem: {self.problem_description}\n"
        text += f"Solution: {self.solution_description}\n"
        if self.code_example:
            text += f"Code Example:\n{self.code_example[:1000]}\n"
        if self.tags:
            text += f"Tags: {', '.join(self.tags)}"
        return text


@dataclass
class RelationshipSchema:
    """Schema for entity relationships."""
    id: str
    source_id: str
    source_type: EntityType
    target_id: str
    target_type: EntityType
    relationship_type: RelationshipType
    project_id: str
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def to_payload(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source_entity": self.source_id,
            "source_type": self.source_type.value,
            "target_entity": self.target_id,
            "target_type": self.target_type.value,
            "relationship_type": self.relationship_type.value,
            "project_id": self.project_id,
            "weight": self.weight,
            "created_at": self.created_at.isoformat(),
            **self.metadata,
        }

    @classmethod
    def create(
        cls,
        source_id: str,
        source_type: EntityType,
        target_id: str,
        target_type: EntityType,
        relationship_type: RelationshipType,
        project_id: str,
        **kwargs
    ) -> "RelationshipSchema":
        rel_id = hashlib.md5(
            f"{source_id}:{target_id}:{relationship_type.value}".encode()
        ).hexdigest()

        return cls(
            id=rel_id,
            source_id=source_id,
            source_type=source_type,
            target_id=target_id,
            target_type=target_type,
            relationship_type=relationship_type,
            project_id=project_id,
            **kwargs
        )


class UnityQueryBuilder:
    """Build complex queries for Unity entity searches."""

    def __init__(self, project_id: str):
        self.project_id = project_id
        self._filters: Dict[str, Any] = {"project_id": project_id}
        self._entity_types: List[EntityType] = []
        self._sort_by: Optional[str] = None
        self._sort_desc: bool = True
        self._limit: int = 20

    def entity_type(self, *types: EntityType) -> "UnityQueryBuilder":
        """Filter by entity types."""
        self._entity_types = list(types)
        return self

    def in_scene(self, scene_name: str) -> "UnityQueryBuilder":
        """Filter to entities in a specific scene."""
        self._filters["scene_name"] = scene_name
        return self

    def with_tag(self, tag: str) -> "UnityQueryBuilder":
        """Filter GameObjects by tag."""
        self._filters["tag"] = tag
        return self

    def with_layer(self, layer: int) -> "UnityQueryBuilder":
        """Filter GameObjects by layer."""
        self._filters["layer"] = layer
        return self

    def with_component(self, component_type: str) -> "UnityQueryBuilder":
        """Filter by component type."""
        self._filters["component_types"] = component_type
        return self

    def in_namespace(self, namespace: str) -> "UnityQueryBuilder":
        """Filter scripts by namespace."""
        self._filters["namespace"] = namespace
        return self

    def inherits_from(self, base_class: str) -> "UnityQueryBuilder":
        """Filter classes by inheritance."""
        self._filters["base_classes"] = base_class
        return self

    def has_method(self, method_name: str) -> "UnityQueryBuilder":
        """Filter by method presence."""
        self._filters["methods"] = method_name
        return self

    def has_unity_callback(self, callback: str) -> "UnityQueryBuilder":
        """Filter by Unity callback."""
        self._filters["unity_callbacks"] = callback
        return self

    def with_status(self, status: str) -> "UnityQueryBuilder":
        """Filter tasks by status."""
        self._filters["status"] = status
        return self

    def with_priority(self, priority: int) -> "UnityQueryBuilder":
        """Filter tasks by priority."""
        self._filters["priority"] = priority
        return self

    def asset_type(self, asset_type: str) -> "UnityQueryBuilder":
        """Filter by asset type."""
        self._filters["asset_type"] = asset_type
        return self

    def with_guid(self, guid: str) -> "UnityQueryBuilder":
        """Filter by asset GUID."""
        self._filters["guid"] = guid
        return self

    def sort_by(self, field: str, descending: bool = True) -> "UnityQueryBuilder":
        """Set sort order."""
        self._sort_by = field
        self._sort_desc = descending
        return self

    def limit(self, count: int) -> "UnityQueryBuilder":
        """Set result limit."""
        self._limit = count
        return self

    def add_filter(self, key: str, value: Any) -> "UnityQueryBuilder":
        """Add custom filter."""
        self._filters[key] = value
        return self

    def build(self) -> Dict[str, Any]:
        """Build query parameters."""
        return {
            "filters": self._filters,
            "entity_types": [t.value for t in self._entity_types],
            "sort_by": self._sort_by,
            "sort_desc": self._sort_desc,
            "limit": self._limit,
        }


class DependencyGraph:
    """Build and analyze entity dependency graphs."""

    def __init__(self):
        self._nodes: Dict[str, Dict[str, Any]] = {}
        self._edges: List[RelationshipSchema] = []

    def add_node(self, entity_id: str, entity_type: EntityType, name: str, **metadata):
        """Add a node to the graph."""
        self._nodes[entity_id] = {
            "id": entity_id,
            "type": entity_type.value,
            "name": name,
            **metadata
        }

    def add_edge(self, relationship: RelationshipSchema):
        """Add an edge to the graph."""
        self._edges.append(relationship)

    def get_dependencies(self, entity_id: str, depth: int = 1) -> List[str]:
        """Get direct dependencies of an entity."""
        deps = []
        for edge in self._edges:
            if edge.source_id == entity_id and edge.relationship_type == RelationshipType.DEPENDS_ON:
                deps.append(edge.target_id)
        return deps

    def get_dependents(self, entity_id: str) -> List[str]:
        """Get entities that depend on this entity."""
        dependents = []
        for edge in self._edges:
            if edge.target_id == entity_id and edge.relationship_type == RelationshipType.DEPENDS_ON:
                dependents.append(edge.source_id)
        return dependents

    def get_connected(self, entity_id: str, max_depth: int = 3) -> Set[str]:
        """Get all connected entities within depth."""
        connected = set()
        to_visit = [(entity_id, 0)]
        visited = set()

        while to_visit:
            current, depth = to_visit.pop(0)
            if current in visited or depth > max_depth:
                continue

            visited.add(current)
            connected.add(current)

            for edge in self._edges:
                if edge.source_id == current and edge.target_id not in visited:
                    to_visit.append((edge.target_id, depth + 1))
                if edge.target_id == current and edge.source_id not in visited:
                    to_visit.append((edge.source_id, depth + 1))

        return connected

    def find_cycles(self) -> List[List[str]]:
        """Find circular dependencies."""
        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(node: str, path: List[str]) -> Optional[List[str]]:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for edge in self._edges:
                if edge.source_id == node:
                    neighbor = edge.target_id
                    if neighbor not in visited:
                        result = dfs(neighbor, path.copy())
                        if result:
                            return result
                    elif neighbor in rec_stack:
                        # Found cycle
                        cycle_start = path.index(neighbor)
                        return path[cycle_start:]

            rec_stack.discard(node)
            return None

        for node in self._nodes:
            if node not in visited:
                cycle = dfs(node, [])
                if cycle:
                    cycles.append(cycle)

        return cycles

    def to_dict(self) -> Dict[str, Any]:
        """Convert graph to dictionary format."""
        return {
            "nodes": list(self._nodes.values()),
            "edges": [e.to_payload() for e in self._edges],
        }


# Schema registry for easy access
SCHEMA_REGISTRY = {
    EntityType.SCENE: SceneSchema,
    EntityType.GAMEOBJECT: GameObjectSchema,
    EntityType.COMPONENT: ComponentSchema,
    EntityType.SCRIPT: ScriptSchema,
    EntityType.CLASS: ClassSchema,
    EntityType.METHOD: MethodSchema,
    EntityType.ASSET: AssetSchema,
    EntityType.PREFAB: PrefabSchema,
    EntityType.TASK: TaskSchema,
    EntityType.ERROR: ErrorSchema,
    EntityType.SOLUTION: SolutionSchema,
}


def create_entity(entity_type: EntityType, **kwargs) -> UnityEntitySchema:
    """Factory function to create entities."""
    schema_class = SCHEMA_REGISTRY.get(entity_type, UnityEntitySchema)
    return schema_class(**kwargs)
