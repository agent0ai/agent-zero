### skills_tool
use skills only when relevant
actions: list search load read_file
common args: action skill_name query file_path
workflow:
- action `search`: find candidate skills by keywords or trigger phrases from the current task
- action `list`: discover available skills
- action `load`: load one skill by `skill_name`
- action `read_file`: open one file inside a loaded skill directory
if the user says "find/search a skill", call `search` before `load` even when the likely skill name seems obvious
`read_file` requires both `skill_name` and `file_path`; load the skill first, then read `SKILL.md` or the named relative file
after loading a skill, follow its instructions and use referenced files or scripts with other tools
reload a skill if its instructions are no longer in context
example:
~~~json
{
  "thoughts": ["The user's request sounds like a skill trigger phrase, so I should search first."],
  "headline": "Searching for relevant skill",
  "tool_name": "skills_tool",
  "tool_args": {
    "action": "search",
    "query": "set up a0 cli connector"
  }
}
~~~
