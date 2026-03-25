Perform an AutoDream pass for Agent Zero memory.

The durable index must stay under {{line_limit}} lines. The host will rebuild `MEMORY.md` from your file descriptions.

## Canonical Memory Scope
```json
{{memory_scope}}
```

## Current Durable Index
{{current_index}}

## Existing Durable Memory Files
```json
{{existing_memories}}
```

## Recent Sessions Since Last Dream
Each item includes the session id, first prompt, and a transcript excerpt.
```json
{{recent_sessions}}
```

## Recent Vector Memories Since Last Dream
These come from the existing memory system and may already capture fragments or solutions.
```json
{{recent_vector_memories}}
```

## Related Vector Memories
These are older or semantically related memory fragments retrieved from the vector DB to help with merging, refreshing, and pruning.
```json
{{related_vector_memories}}
```

## Rename / Orphan Hints
These are soft hints about nearby project memory folders that may be leftovers from a rename or split.
```json
{{orphan_candidates}}
```

Return JSON only.
