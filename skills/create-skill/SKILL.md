---
name: "create-skill"
description: "Wizard for creating new Agent Zero skills. Guides users through creating well-structured SKILL.md files. Use when users want to create custom skills."
version: "1.0.0"
author: "Agent Zero Team"
tags: ["meta", "wizard", "creation", "tutorial", "skills"]
trigger_patterns:
  - "create skill"
  - "new skill"
  - "make skill"
  - "add skill"
  - "skill wizard"
---

# Create Skill Wizard

This skill helps you create new Agent Zero skills that follow the SKILL.md standard.

## Quick Start

To create a new skill, I'll guide you through these steps:

1. **Name & Purpose** - What should this skill do?
2. **Trigger Patterns** - When should this skill activate?
3. **Content Structure** - What instructions should the agent follow?
4. **Supporting Files** - Any scripts or templates needed?

## SKILL.md Format

Every skill needs a `SKILL.md` file with YAML frontmatter:

```yaml
---
name: "skill-name"
description: "Clear description of what this skill does and when to use it"
version: "1.0.0"
author: "Your Name"
tags: ["category1", "category2"]
trigger_patterns:
  - "keyword1"
  - "phrase that triggers this"
---

# Skill Title

Your skill instructions go here...
```

## Required Fields

| Field | Description | Example |
|-------|-------------|---------|
| `name` | Unique identifier (lowercase, hyphens) | `"code-review"` |
| `description` | When/why to use this skill | `"Review code for quality and security issues"` |

## Optional Fields

| Field | Description | Example |
|-------|-------------|---------|
| `version` | Semantic version | `"1.0.0"` |
| `author` | Creator name | `"Jane Developer"` |
| `tags` | Categorization keywords | `["review", "quality"]` |
| `trigger_patterns` | Words/phrases that activate skill | `["review", "check code"]` |
| `allowed_tools` | Tools this skill can use | `["code_execution", "web_search"]` |

## Skill Directory Structure

```
/a0/usr/skills/
└── my-skill/
   ├── SKILL.md           # Required: Main skill file
   ├── scripts/           # Optional: Helper scripts
   │   ├── helper.py
   │   └── process.sh
   ├── templates/         # Optional: Templates
   │   └── output.md
   └── docs/              # Optional: Additional docs
      └── examples.md
```

## Writing Good Skill Instructions

### Be Specific and Actionable

```markdown
# Good
When reviewing code:
1. Check for security vulnerabilities
2. Verify error handling
3. Assess test coverage

# Bad
Review the code and make it better.
```

### Include Examples

```markdown
## Example Usage

**User**: "Review my Python function for issues"

**Agent Response**:
> I'll review your function using the code review checklist:
>
> 1. **Security**: No user input validation detected
> 2. **Error Handling**: Missing try-catch for file operations
> 3. **Testing**: Function is testable but no tests found
```

### Provide Checklists

```markdown
## Review Checklist
- [ ] Input validation present
- [ ] Error handling complete
- [ ] Tests included
- [ ] Documentation updated
```

## Creating Your Skill: Step by Step

### Step 1: Define Purpose

Answer these questions:
- What problem does this skill solve?
- When should the agent use it?
- What's the expected output?

### Step 2: Choose a Name

- Use lowercase letters and hyphens
- Be descriptive but concise
- Examples: `code-review`, `data-analysis`, `deploy-helper`

### Step 3: Write Trigger Patterns

List words/phrases that should activate this skill:

```yaml
trigger_patterns:
  - "review"
  - "check code"
  - "code quality"
  - "pull request"
```

### Step 4: Structure Your Content

Organize with clear sections:

```markdown
# Skill Title

## When to Use
Describe the trigger conditions

## The Process
Step-by-step instructions

## Examples
Show sample interactions

## Tips
Additional guidance
```

### Step 5: Add Supporting Files (Optional)

If your skill needs scripts or templates:

```bash
# Create directory structure
mkdir -p /a0/usr/skills/my-skill/{scripts,templates,docs}
```

## Example: Complete Skill

```yaml
---
name: "python-optimizer"
description: "Optimize Python code for performance and readability. Use when asked to improve or optimize Python code."
version: "1.0.0"
author: "Agent Zero Team"
tags: ["python", "optimization", "performance"]
trigger_patterns:
  - "optimize python"
  - "improve performance"
  - "make faster"
  - "python optimization"
---

# Python Optimizer

## When to Use
Activate when user asks to optimize, improve, or speed up Python code.

## Optimization Process

### Step 1: Profile First
Before optimizing, understand where time is spent:
```python
import cProfile
cProfile.run('your_function()')
```

### Step 2: Common Optimizations

1. **Use List Comprehensions**
   ```python
   # Slow
   result = []
   for x in data:
       result.append(x * 2)

   # Fast
   result = [x * 2 for x in data]
   ```

2. **Use Sets for Lookups**
   ```python
   # Slow: O(n)
   if item in large_list:

   # Fast: O(1)
   if item in large_set:
   ```

3. **Use Generators for Large Data**
   ```python
   # Memory-heavy
   data = [process(x) for x in huge_list]

   # Memory-efficient
   data = (process(x) for x in huge_list)
   ```

### Step 3: Verify Improvement
Always measure before and after:
```python
import time
start = time.perf_counter()
# code to measure
elapsed = time.perf_counter() - start
print(f"Took {elapsed:.4f} seconds")
```

## Anti-Patterns to Avoid
- Premature optimization
- Optimizing without profiling
- Sacrificing readability for tiny gains
```

## Skill Installation

### Local Installation

1. Create skill directory:
   ```bash
   mkdir -p /a0/usr/skills/my-skill
   ```

2. Create SKILL.md:
   ```bash
   touch /a0/usr/skills/my-skill/SKILL.md
   ```

3. Add content and save

4. Skills are automatically loaded on next agent initialization

### Sharing Skills

To share skills with others:

1. Create a GitHub repository
2. Include the skill directory structure
3. Add a README with installation instructions
4. Users can copy to their `/a0/usr/skills/` directory

## Testing Your Skill

After creating a skill:

1. Start a new conversation
2. Use one of your trigger patterns
3. Verify the agent follows your instructions
4. Iterate and improve based on results