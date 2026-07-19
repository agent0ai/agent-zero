### text_editor
file read write patch with numbered lines
not code execution rejects binary
terminal (grep find sed) advance search/replace
actions: read write patch
common args: action path

#### read
read file with numbered lines
args path line_from line_to (inclusive optional)
no range -> first {{default_line_count}} lines
long lines cropped output may trim by token limit
read surrounding context before patching
usage:
~~~json
{
    "thoughts": ["I need file context before editing."],
    "headline": "Reading file",
    "tool_name": "text_editor",
    "tool_args": {
        "action": "read",
        "path": "/path/file.py",
        "line_from": 1,
        "line_to": 50
    }
}
~~~

#### write
create/overwrite file auto-creates dirs
args path content
usage:
~~~json
{
    "thoughts": ["I need to create or replace the file content."],
    "headline": "Writing file",
    "tool_name": "text_editor",
    "tool_args": {
        "action": "write",
        "path": "/path/file.py",
        "content": "import os\nprint('hello')\n"
    }
}
~~~

#### patch
edit existing file. prefer exact replace for simple "change X to Y"; use patch_text for context changes; use edits only right after read for tiny line edits
if the user says patch, change without rewriting, or don't rewrite, use action patch instead of write
args path plus exactly one of: old_text+new_text OR patch_text string OR edits [{from to content}]
exact replace: `old_text` must be the exact current text span and must match once; `new_text` is the replacement
patch_text uses current file content, no prior read required
patch_text update-only forms:
- insert after anchor: @@ exact existing line then +new lines
- replace: use @@ line before target then -old +new, or @@ old target line then -same old target line +new
- do not repeat the same old line as both a space-context line and a -removed line
- context lines start with space, removals with -, additions with +
- use enough unique context; add @@ anchor when repeated text exists
edits legacy line mode: from/to inclusive, original line numbers from read, no overlaps
edits examples: {from:2 to:2 content:"x\n"} replace; {from:2 to:2} delete; {from:2 content:"x\n"} insert before
for edits, re-read after insert/delete or line-count-changing replace
ensure valid syntax in content (all braces brackets tags closed)
usage:
~~~json
{
    "thoughts": ["I can replace one exact current string without rewriting the whole file."],
    "headline": "Patching file",
    "tool_name": "text_editor",
    "tool_args": {
        "action": "patch",
        "path": "/path/file.py",
        "old_text": "status = 'draft'",
        "new_text": "status = 'ready'"
    }
}
~~~
