## ACTIVE PROJECT: {{project_name}}

**Description**: {{project_description}}

{{#if project_instructions}}
**Instructions**: {{project_instructions}}
{{/if}}

**Working Directory**: {{project_directory}}

**Files**:
{{#if has_files}}
```
{{#each file_structure}}
{{this}}
{{/each}}
{{#if has_more_files}}... and {{additional_files_count}} more items{{/if}}
```
{{else}}
```
(Empty project directory)
```
{{/if}}