{{#if has_projects}}
## AVAILABLE PROJECTS

{{#each projects}}
• **{{name}}**: {{description}}{{#if instructions_preview}} | {{instructions_preview}}{{/if}}
{{/each}}

Use `project_manager` tool to list, activate, create, or edit projects.
{{else}}
## PROJECT SYSTEM

Use `project_manager` tool to create organized workspaces with specific contexts and instructions.

Example: `{"tool_name": "project_manager", "tool_args": {"action": "create", "name": "my_project", "description": "Brief description", "instructions": "Detailed instructions"}}`
{{/if}}