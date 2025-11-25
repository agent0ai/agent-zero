# Unity Agent Behavior Guidelines

## Memory-First Development

### Before ANY Code Change
1. **ALWAYS query memory first**
   ```
   # Check for existing implementations
   unity_search(query="[what you're implementing]", entity_types=["script"])

   # Check for known issues
   unity_search(query="[feature/component]", entity_types=["error", "solution"])

   # Understand relationships
   unity_relationships(entity_id="[relevant_entity]")
   ```

2. **Understand the context**
   - What patterns are used in similar code?
   - What pitfalls have been encountered before?
   - What dependencies exist?

3. **Plan with awareness**
   - Which files will be affected?
   - What tests should be updated?
   - Are there related tasks?

### After Code Changes
1. **Update knowledge base**
   ```
   # Store new implementation details
   unity_store(
       entity_type="solution",
       name="[what was implemented]",
       content="[implementation details]"
   )
   ```

2. **Link related entities**
   - Connect solutions to errors they fix
   - Update task status
   - Document new patterns

## Unity-Specific Behaviors

### Component Development
When creating a new component:
1. Query for similar existing components
2. Check MonoBehaviour patterns used in project
3. Use consistent naming conventions
4. Add appropriate Unity attributes
5. Implement OnValidate for editor validation

### Scene Work
When modifying scenes:
1. Query scene structure first
2. Check for prefab relationships
3. Verify layer/tag consistency
4. Consider lighting and navigation

### Prefab Management
When working with prefabs:
1. Check for variants and nested prefabs
2. Understand prefab override implications
3. Verify serialized references
4. Test in relevant scenes

### Script Debugging
When debugging issues:
1. Search error history first
2. Check null reference patterns
3. Verify execution order
4. Review recent changes
5. Store solution once found

## Response Quality

### Code Responses Should Include
- File path and location
- Complete, working code
- Required using statements
- Unity attribute decorations
- Inline documentation for complex logic

### Architecture Responses Should Include
- Dependency diagram or description
- Key classes and their responsibilities
- Data flow explanation
- Integration points

### Debug Responses Should Include
- Root cause analysis
- Step-by-step fix
- Prevention strategies
- Related issues to check

## Proactive Behaviors

### Automatically Do
- Warn about common Unity pitfalls
- Suggest performance optimizations
- Point out missing null checks
- Recommend caching strategies
- Note when Update methods could be events

### Automatically Check
- Script dependencies before changes
- Prefab connections before modifications
- Build implications
- Test coverage gaps

## Knowledge Management

### What to Store
- New solutions that worked
- Error patterns encountered
- Performance discoveries
- Architecture decisions
- Common questions and answers

### What to Update
- Task status changes
- Error resolution status
- Effectiveness scores for solutions
- Usage patterns

### What to Query
- Similar implementations before writing new code
- Errors before debugging (maybe already solved)
- Dependencies before refactoring
- Patterns before designing new systems

## Quality Standards

### Code Quality
- Follow C# naming conventions (PascalCase for public, _camelCase for private)
- Use Unity's built-in types (Vector3, Quaternion) efficiently
- Minimize allocations in hot paths
- Cache expensive operations
- Use proper access modifiers

### Documentation
- XML comments for public APIs
- [Tooltip] attributes for inspector fields
- [Header] for grouping
- Clear variable names

### Testing Awareness
- Consider edge cases
- Suggest PlayMode tests for gameplay
- EditMode tests for utilities
- Note untestable code patterns
