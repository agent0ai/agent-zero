### skills_tool

manage and use agent skills for specialized capabilities
skills are composable bundles of instructions context and executable code
use progressive disclosure: metadata → full content → referenced files
use "method" arg to specify operation: "list" "load" "read_file" "execute_script" "search"

## Overview

Skills system provides three-level progressive disclosure:
- Level 1: Metadata (name + description) loaded in system prompt at startup
- Level 2: Full SKILL.md content loaded when relevant to task
- Level 3+: Referenced files and scripts loaded on-demand

When to use skills:
- Task matches skill description from available skills list
- Need specialized procedures or domain knowledge
- Task requires bundled scripts or automation
- Need step-by-step guidance for complex operations

Progressive workflow:
1. Check available skills metadata already in your context
2. Use "search" if looking for specific capability
3. Use "load" to get full skill instructions and context
4. Use "read_file" to load additional reference documents
5. Use "execute_script" to run deterministic operations

## Operations

### 1. list available skills

Lists all available skills with metadata
Shows name, version, description, tags, and author
Use when: exploring available capabilities or confirming skill exists

~~~json
{
    "thoughts": [
        "Need to see what skills are available",
        "User asked about available capabilities"
    ],
    "headline": "Listing all available skills",
    "tool_name": "skills_tool",
    "tool_args": {
        "method": "list"
    }
}
~~~

Response format:
- Skill name and version
- Brief description
- Tags for categorization
- Author attribution

### 2. load full skill content

Loads complete SKILL.md content with instructions and procedures
Returns metadata, full content, and list of referenced files
Use when: identified relevant skill and need detailed instructions

~~~json
{
    "thoughts": [
        "User needs PDF form extraction",
        "pdf_editing skill will provide procedures",
        "Loading full skill content"
    ],
    "headline": "Loading PDF editing skill",
    "tool_name": "skills_tool",
    "tool_args": {
        "method": "load",
        "skill_name": "pdf_editing"
    }
}
~~~

Required args:
- skill_name: exact name from metadata or list

Response includes:
- Skill metadata (name, version, description, tags)
- Full markdown content with instructions
- List of referenced files available to load
- Code examples and procedures

### 3. read skill reference file

Reads additional reference files from skill directory
Files referenced in SKILL.md can be loaded progressively
Use when: need detailed documentation or examples from skill references

~~~json
{
    "thoughts": [
        "Skill mentioned forms.md for form filling details",
        "Need specific form field handling instructions",
        "Loading reference file"
    ],
    "headline": "Reading PDF forms reference documentation",
    "tool_name": "skills_tool",
    "tool_args": {
        "method": "read_file",
        "skill_name": "pdf_editing",
        "file_path": "forms.md"
    }
}
~~~

Required args:
- skill_name: name of skill containing file
- file_path: relative path within skill directory (e.g. "reference.md" or "examples/example1.md")

Security:
- Path validation prevents directory traversal
- Only files within skill directory accessible
- Supports markdown, text, code files

### 4. execute skill script

Executes bundled scripts from skill with arguments
Scripts receive arguments via standard CLI conventions (sys.argv, process.argv)
Use when: skill provides script for deterministic operation or automation

~~~json
{
    "thoughts": [
        "Need to convert PDF to images",
        "Skill provides convert_pdf_to_images.py script",
        "Script expects positional args: input_pdf output_dir"
    ],
    "headline": "Converting PDF to images",
    "tool_name": "skills_tool",
    "tool_args": {
        "method": "execute_script",
        "skill_name": "pdf_editing",
        "script_path": "scripts/convert_pdf_to_images.py",
        "script_args": {
            "input_pdf": "/path/to/document.pdf",
            "output_dir": "/tmp/images"
        }
    }
}
~~~

Required args:
- skill_name: name of skill containing script
- script_path: relative path to script file
- script_args: dictionary of arguments passed to script

Optional args:
- arg_style: how to pass arguments to script (default: "positional")
  - "positional": values as positional args → sys.argv = ['script.py', 'value1', 'value2']
  - "named": as --key value pairs → sys.argv = ['script.py', '--key1', 'value1', '--key2', 'value2']
  - "env": only environment variables, no CLI args

How scripts receive arguments:
- .py (Python): sys.argv[1], sys.argv[2], etc. (standard argparse/CLI compatible)
- .js (Node.js): process.argv[2], process.argv[3], etc. (standard CLI compatible)
- .sh (Shell): $1, $2, etc. as positional parameters

Environment variables (always available as fallback):
- SKILL_ARG_KEY1=value1, SKILL_ARG_KEY2=value2, etc.
- Scripts can use os.environ.get('SKILL_ARG_INPUT_PDF') if needed

Script execution:
- Runs in Docker container sandbox
- Has access to installed packages
- Returns stdout/stderr output
- Secure and isolated execution

Example with argparse script (use arg_style="named"):
~~~json
{
    "thoughts": [
        "Script uses argparse with --input and --output flags",
        "Need to use named arg_style"
    ],
    "headline": "Running argparse-based script",
    "tool_name": "skills_tool",
    "tool_args": {
        "method": "execute_script",
        "skill_name": "data_processor",
        "script_path": "scripts/process.py",
        "script_args": {
            "input": "/path/to/data.csv",
            "output": "/tmp/result.json"
        },
        "arg_style": "named"
    }
}
~~~

### 5. search skills by query

Searches skills by text matching in name, description, and tags
Returns ranked results by relevance score
Use when: looking for skills without knowing exact name

~~~json
{
    "thoughts": [
        "User needs web scraping capability",
        "Not sure of exact skill name",
        "Searching for web-related skills"
    ],
    "headline": "Searching for web scraping skills",
    "tool_name": "skills_tool",
    "tool_args": {
        "method": "search",
        "query": "web scraping html parsing"
    }
}
~~~

Required args:
- query: search text (searches name, description, tags)

Scoring:
- Name match: +3 points
- Description match: +2 points
- Tag match: +1 point per tag
- Results sorted by descending score

## Best Practices

### When to use skills vs other tools

Use skills when:
- Task requires specialized domain knowledge
- Need structured procedures or step-by-step guidance
- Deterministic scripts available for automation
- Complex multi-step operations with best practices

Use other tools when:
- Simple file operations (use code_execution_tool)
- Web search (use search_engine)
- General computation (use code_execution_tool)
- Memory operations (use memory tools)

### Progressive disclosure workflow

1. Start with metadata (already in context)
   - Check available skills list in system prompt
   - Match task to skill description

2. Load full content when relevant
   - Use "load" to get complete instructions
   - Review procedures and examples

3. Load references as needed
   - Use "read_file" for detailed documentation
   - Load only files relevant to current subtask

4. Execute scripts for automation
   - Use "execute_script" for deterministic operations
   - Provide appropriate arguments from context

### Common patterns

Pattern: Using a skill for first time
1. Identify skill from metadata
2. Load full skill content
3. Follow instructions in content
4. Load reference files if mentioned
5. Execute scripts if provided

Pattern: Quick script execution
1. Know skill name from previous use
2. Execute script directly with args
3. Process output

Pattern: Exploring capabilities
1. Search with query terms
2. Review matches
3. Load most relevant skill

## Error Handling

Common errors:
- "Skill not found": Check spelling, use list or search to find correct name
- "File not found": Verify file_path matches referenced files from load output
- "Script failed": Check script_args match expected parameters, review skill docs
- "Unsupported script type": Only .py, .js, .sh supported

When skill loading fails:
- Verify skill exists using list method
- Check for typos in skill_name
- Ensure skill system is enabled in settings

When script execution fails:
- Review skill documentation for required arguments
- Check script_args dictionary format
- Verify required packages installed in container
- Check script output for specific error messages

## Examples

Example 1: Simple script with positional args (default)
Script expects: python script.py /path/to/file.pdf
~~~json
{
    "thoughts": [
        "User has PDF to convert to images",
        "Script uses sys.argv[1] for input, sys.argv[2] for output",
        "Using default positional arg_style"
    ],
    "headline": "Converting PDF to images",
    "tool_name": "skills_tool",
    "tool_args": {
        "method": "execute_script",
        "skill_name": "pdf_editing",
        "script_path": "scripts/convert_pdf_to_images.py",
        "script_args": {
            "input_pdf": "/workspace/document.pdf",
            "output_dir": "/tmp/images"
        }
    }
}
~~~
Result: sys.argv = ['script.py', '/workspace/document.pdf', '/tmp/images']

Example 2: Argparse script with named args
Script expects: python script.py --url https://... --selector .price
~~~json
{
    "thoughts": [
        "Need to scrape product prices from website",
        "Script uses argparse with --url and --selector flags",
        "Using arg_style='named' for argparse compatibility"
    ],
    "headline": "Scraping product prices from webpage",
    "tool_name": "skills_tool",
    "tool_args": {
        "method": "execute_script",
        "skill_name": "web_scraping",
        "script_path": "scripts/fetch_page.py",
        "script_args": {
            "url": "https://example.com/products",
            "selector": ".price"
        },
        "arg_style": "named"
    }
}
~~~
Result: sys.argv = ['script.py', '--url', 'https://...', '--selector', '.price']

Example 3: Environment-only script
Script reads from os.environ only
~~~json
{
    "thoughts": [
        "Script reads configuration from environment variables",
        "Using arg_style='env' to only set env vars"
    ],
    "headline": "Running config-based processor",
    "tool_name": "skills_tool",
    "tool_args": {
        "method": "execute_script",
        "skill_name": "data_processor",
        "script_path": "scripts/process.py",
        "script_args": {
            "input_file": "/data/input.csv",
            "mode": "production"
        },
        "arg_style": "env"
    }
}
~~~
Result: SKILL_ARG_INPUT_FILE=/data/input.csv, SKILL_ARG_MODE=production

Example 4: Data analysis workflow
~~~json
{
    "thoughts": [
        "User needs CSV analysis",
        "data_analysis skill has analysis procedures",
        "Loading skill for detailed instructions"
    ],
    "headline": "Loading data analysis skill",
    "tool_name": "skills_tool",
    "tool_args": {
        "method": "load",
        "skill_name": "data_analysis"
    }
}
~~~

Then follow up with script (positional args):
~~~json
{
    "thoughts": [
        "Skill loaded, now analyzing CSV",
        "Script takes csv_path as first arg, group_by as second"
    ],
    "headline": "Analyzing sales data grouped by category",
    "tool_name": "skills_tool",
    "tool_args": {
        "method": "execute_script",
        "skill_name": "data_analysis",
        "script_path": "scripts/analyze_csv.py",
        "script_args": {
            "csv_path": "/workspace/sales_data.csv",
            "group_by": "category"
        }
    }
}
~~~

## Notes

- Skills metadata already loaded in your system prompt
- Skills cache after first load for efficiency
- Referenced files listed in load response
- Scripts receive arguments via sys.argv (positional by default) + SKILL_ARG_* env vars
- Use arg_style parameter to control argument passing: "positional", "named", or "env"
- All operations return formatted text responses
- Skills follow the open SKILL.md standard (cross-platform compatible)
- Use skills for structured procedures and contextual expertise
