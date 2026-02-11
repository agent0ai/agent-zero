### skills_tool

#### overview

skills are folders with instructions scripts files
give agent extra capabilities
agentskills.io standard

#### workflow
1. skill list titles descriptions in system prompt section available skills
2. use skills_tool:load to get full skill instructions and context
4. use code_execution_tool to run scripts or read files

#### examples

##### skills_tool:list

list all skills with metadata name version description tags author
only use when details needed

~~~json
{
    "thoughts": [
        "Need find skills of certain properties...",
    ],
    "headline": "Listing all available skills",
    "tool_name": "skills_tool:list",
}
~~~

##### skills_tool:load

loads complete SKILL.md content instructions procedures
returns metadata content file tree
use when potential skill identified and want usage instructions
use again when no longer in history

~~~json
{
    "thoughts": [
        "User needs PDF form extraction",
        "pdf_editing skill will provide procedures",
        "Loading full skill content"
    ],
    "headline": "Loading PDF editing skill",
    "tool_name": "skills_tool:load",
    "tool_args": {
        "skill_name": "pdf_editing"
    }
}
~~~

##### executing skill scripts

use skills_tool:load identify skill script files and instructions
use code_execution_tool runtime terminal to execute
write command and parameters as instructed
use full paths or cd to skill directory

~~~json
{
    "thoughts": [
        "Need to convert PDF to images",
        "Skill provides convert_pdf_to_images.py at scripts/convert_pdf_to_images.py",
        "Using code_execution_tool to run it directly"
    ],
    "headline": "Converting PDF to images",
    "tool_name": "code_execution_tool",
    "tool_args": {
        "runtime": "terminal",
        "code": "python /path/to/skill/scripts/convert_pdf_to_images.py /path/to/document.pdf /tmp/images"
    }
}
~~~

#### skills guide
use skills when relevant for task
load skill before use
read / execute files with code_execution_tool
follow instructions in skill
mind relative paths
conversation history discards old messages use skills_tool:load again when lost
