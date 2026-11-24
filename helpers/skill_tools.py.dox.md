# Skill Tools DOX

## Ownership

- `registered` collects handler factories from the scoped `skill_tools` extension point.
- `SkillTool.definition` reads the callable declaration from the effective skill resolved by `helpers.skills`.

## Runtime Contracts

- An enabled plugin binds a callable and skill name to a trusted Python handler factory. Skill metadata supplies `tool.name` and the object-shaped `tool.parameters` schema. Metadata cannot select or import executable code.
- Use the chat's loaded skill names and normal scoped skill precedence and visibility. An override can supply a schema for the registered callable. An override without the declaration suppresses it.
- Tool Access catalog entries retain their plugin ID regardless of chat load. Current skill visibility and Tool Access apply to both native exposure and execution.
- Discovery gives same-name tool files precedence by path. The `Agent.get_tool/end` extension resolves registered skill handlers after ordinary file lookup and retains the selected handler's policy identity.
- Text-protocol instructions come from the loaded skill. Native Responses uses the same skill's structured schema.

## Verification

- Run `tests/test_tool_action_policy.py` and `tests/test_skills_runtime.py`. Verify a new chat can load the skill, call the handler, and honor saved denials.
