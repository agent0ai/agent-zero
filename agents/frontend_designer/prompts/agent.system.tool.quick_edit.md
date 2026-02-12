### quick_edit

Make targeted modifications to existing code files.
Supports replace, insert_after, and insert_before operations.
Maintains file formatting and syntax.

Args:
- file_path (required): Path to file to edit
- edits (required): Array of edit objects with operation, find, replace, marker, insert fields

Operations:
- replace: Find and replace text
- insert_after: Insert text after a marker
- insert_before: Insert text before a marker

Usage example:

~~~json
{
    "thoughts": [
        "Need to update the component prop types",
        "Will replace the interface definition"
    ],
    "headline": "Updating component interface",
    "tool_name": "quick_edit",
    "tool_args": {
        "file_path": "components/button.tsx",
        "edits": [
            {
                "operation": "replace",
                "find": "variant?: string",
                "replace": "variant?: 'default' | 'outline' | 'ghost'"
            }
        ]
    }
}
~~~
