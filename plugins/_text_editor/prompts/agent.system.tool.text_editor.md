### text_editor
file read write patch with numbered lines
not code execution rejects binary
terminal (grep find sed) advance search/replace

#### text_editor:read
read file with numbered lines
args path line_from line_to (inclusive optional)
no range → first {{default_line_count}} lines
long lines cropped output may trim by token limit
read surrounding context before patching
usage:
~~~json
{
    ...
    "tool_name": "text_editor:read",
    "tool_args": {
        "path": "/path/file.py",
        "line_from": 1,
        "line_to": 50
    }
}
~~~

#### text_editor:write
create/overwrite file auto-creates dirs
args path content
usage:
~~~json
{
    ...
    "tool_name": "text_editor:write",
    "tool_args": {
        "path": "/path/file.py",
        "content": "import os\nprint('hello')\n"
    }
}
~~~

#### text_editor:patch
line edits on existing file
args path edits [{from to content}]
from to inclusive \n in content
{from:2 to:2 content:"x\n"} replace line
{from:1 to:3 content:"x\n"} replace range
{from:2 to:2} delete (no content)
{from:2 content:"x\n"} insert before (omit to)
use original line numbers from read 
dont adjust for shifts no overlapping edits
ensure valid syntax in content (all braces brackets tags closed)
only replace exact lines needed dont include surrounding unchanged lines
re-read when insert delete or N≠M replace else patch again ok
large changes write over multiple patches
usage:
~~~json
{
    ...
    "tool_name": "text_editor:patch",
    "tool_args": {
        "path": "/path/file.py",
        "edits": [
            {"from": 1, "content": "import sys\n"},
            {"from": 5, "to": 5, "content": "    if x == 2:\n"}
        ]
    }
}
~~~
