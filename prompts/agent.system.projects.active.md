## active project
path: {{project_path}}
{{if project_name}}title: {{project_name}}{{endif}}
{{if project_description}}description: {{project_description}}{{endif}}
{{if project_git_url}}git: {{project_git_url}}{{endif}}
rules:
- work inside {{project_path}}
- do not rename project dir or change `.a0proj` unless asked

{{project_instructions}}
