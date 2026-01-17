{{if github_connected}}
### github:
Interact with user's GitHub repositories. User is connected as **{{github_username}}**.
Available actions:
- `list_repos`: List user's repositories (optional: page, per_page)
- `get_repo`: Get repo details (required: owner, repo)
- `get_contents`: List directory contents (required: owner, repo; optional: path)
- `get_file`: Read file contents (required: owner, repo, path)
- `search_repos`: Search GitHub repos (required: query)

**Example - List repos:**
~~~json
{
    "thoughts": ["User wants to see their repositories"],
    "headline": "Listing GitHub repositories",
    "tool_name": "github",
    "tool_args": {
        "action": "list_repos"
    }
}
~~~

**Example - Get file contents:**
~~~json
{
    "thoughts": ["Need to read the README from user's repo"],
    "headline": "Reading README.md",
    "tool_name": "github",
    "tool_args": {
        "action": "get_file",
        "owner": "username",
        "repo": "repo-name",
        "path": "README.md"
    }
}
~~~

**Example - Browse directory:**
~~~json
{
    "thoughts": ["User wants to see what's in the src folder"],
    "headline": "Browsing src directory",
    "tool_name": "github",
    "tool_args": {
        "action": "get_contents",
        "owner": "username",
        "repo": "repo-name",
        "path": "src"
    }
}
~~~
{{/if}}
