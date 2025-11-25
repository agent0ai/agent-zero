# Unity Development Tools

## Memory Tools for Unity

### unity_search
Search the Unity knowledge base for code, scenes, prefabs, and more.

```
Arguments:
- query: Search query (semantic search)
- entity_types: Filter by type (script, scene, prefab, gameobject, error, solution, task)
- scene_filter: Limit to specific scene
- include_relationships: Include related entities
- limit: Maximum results (default: 20)

Example:
unity_search(
    query="player movement controller",
    entity_types=["script"],
    include_relationships=True,
    limit=10
)
```

### unity_store
Store new knowledge about Unity entities.

```
Arguments:
- entity_type: Type of entity (script, scene, prefab, error, solution, task)
- name: Entity name
- content: Full content/description
- file_path: Optional file path
- metadata: Additional key-value data

Example:
unity_store(
    entity_type="solution",
    name="Camera Follow Fix",
    content="Use LateUpdate for camera follow to prevent jitter",
    metadata={
        "related_error": "camera_jitter",
        "effectiveness": 0.95
    }
)
```

### unity_relationships
Query entity relationships and dependencies.

```
Arguments:
- entity_id: Source entity ID
- relationship_type: Type of relationship (depends_on, uses, references)
- direction: "outgoing" or "incoming"
- depth: How deep to traverse (1-3)

Example:
unity_relationships(
    entity_id="PlayerController",
    relationship_type="uses",
    direction="outgoing",
    depth=2
)
```

### unity_extract_project
Extract and index a Unity project.

```
Arguments:
- project_path: Path to Unity project root
- incremental: Only process changed files (default: True)

Example:
unity_extract_project(
    project_path="/unity/MyGame",
    incremental=True
)
```

## Scene Tools

### unity_scene_info
Get comprehensive information about a Unity scene.

```
Arguments:
- scene_name: Name of the scene

Returns:
- Scene structure
- Root GameObjects
- Component summary
- Script usage
```

### unity_find_in_scene
Find GameObjects in a scene by criteria.

```
Arguments:
- scene_name: Scene to search
- tag: Filter by tag
- layer: Filter by layer
- component: Filter by component type
- name_pattern: Regex for name matching

Example:
unity_find_in_scene(
    scene_name="MainLevel",
    component="Rigidbody",
    tag="Player"
)
```

## Script Tools

### unity_analyze_script
Deep analysis of a C# script.

```
Arguments:
- script_path: Path to .cs file

Returns:
- Classes and their methods
- Unity callbacks used
- Dependencies
- Potential issues
```

### unity_find_method_usages
Find where a method is called.

```
Arguments:
- class_name: Class containing method
- method_name: Method to find
- include_overrides: Include override calls

Example:
unity_find_method_usages(
    class_name="PlayerController",
    method_name="TakeDamage"
)
```

### unity_class_hierarchy
Get inheritance hierarchy for a class.

```
Arguments:
- class_name: Starting class

Returns:
- Parent classes up to UnityEngine types
- Implemented interfaces
- Child classes
```

## Error Tools

### unity_find_error
Search for errors and their solutions.

```
Arguments:
- error_message: Full or partial error message
- error_type: Exception type
- include_solved: Include errors with solutions

Example:
unity_find_error(
    error_message="NullReferenceException",
    include_solved=True
)
```

### unity_store_solution
Store a solution for an error.

```
Arguments:
- error_type: Type of error
- error_pattern: Regex pattern to match
- solution: Description of fix
- code_example: Optional code example
- effectiveness: Score 0-1

Example:
unity_store_solution(
    error_type="NullReferenceException",
    error_pattern="Object reference not set.*GetComponent",
    solution="Cache GetComponent result in Awake or add null check",
    code_example="private Rigidbody _rb;\nvoid Awake() { _rb = GetComponent<Rigidbody>(); }",
    effectiveness=0.9
)
```

## Task Tools

### unity_task_create
Create a development task.

```
Arguments:
- title: Task title
- description: Detailed description
- priority: 1-5 (1 is highest)
- tags: List of tags
- related_entities: Scripts/scenes involved

Example:
unity_task_create(
    title="Implement Double Jump",
    description="Add double jump mechanic to PlayerController",
    priority=2,
    tags=["gameplay", "movement"],
    related_entities=["PlayerController.cs", "MainScene"]
)
```

### unity_task_update
Update task status.

```
Arguments:
- task_id: Task identifier
- status: New status (pending, in_progress, completed, blocked)
- notes: Optional update notes

Example:
unity_task_update(
    task_id="task_123",
    status="completed",
    notes="Double jump implemented with animation"
)
```

## Build Tools

### unity_analyze_build_log
Analyze Unity build output for issues.

```
Arguments:
- log_content: Build log text
- severity_filter: warning, error, all

Returns:
- Categorized issues
- Suggested fixes
- Performance warnings
```

### unity_check_references
Check for missing references in scenes/prefabs.

```
Arguments:
- target: Scene name or "all"

Returns:
- Missing script references
- Broken prefab connections
- Null serialized fields
```

## Performance Tools

### unity_profile_scene
Analyze scene for performance issues.

```
Arguments:
- scene_name: Scene to analyze

Returns:
- Draw call estimate
- Batching opportunities
- Heavy components
- Optimization suggestions
```

### unity_find_update_methods
Find all Update methods in project.

```
Arguments:
- include_fixed_update: Include FixedUpdate
- include_late_update: Include LateUpdate

Returns:
- List of Update methods
- Potential optimization candidates
- Empty Update warnings
```

## Integration Tools

### unity_mcp_execute
Execute a Unity Editor command via MCP.

```
Arguments:
- command: Command name
- parameters: Command parameters

Example:
unity_mcp_execute(
    command="CreatePrefab",
    parameters={
        "source": "Player",
        "path": "Assets/Prefabs/Player.prefab"
    }
)
```

### unity_hot_reload
Trigger Unity script hot reload.

```
Arguments:
- script_path: Specific script or "all"

Returns:
- Reload status
- Compilation errors if any
```
