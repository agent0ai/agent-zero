---
name: "prompt-engineering"
description: "Best practices for crafting effective prompts for LLMs. Use when designing prompts, creating system messages, or optimizing AI interactions."
version: "1.0.0"
author: "Agent Zero Team"
tags: ["prompts", "llm", "ai", "gpt", "claude", "optimization"]
trigger_patterns:
  - "prompt"
  - "system message"
  - "llm"
  - "ai instruction"
  - "chatgpt"
  - "claude"
---

# Prompt Engineering Skill

Best practices for designing effective prompts for Large Language Models.

## Core Principles

### 1. Be Specific and Clear

```markdown
# Bad
"Write something about dogs"

# Good
"Write a 200-word article about the top 3 benefits of adopting
a rescue dog. Include a brief introduction and conclusion.
Use a friendly, conversational tone suitable for pet owners."
```

### 2. Provide Context

```markdown
# Bad
"Fix this code"

# Good
"I have a Python function that should validate email addresses.
Currently it accepts invalid emails like 'test@'.

Current code:
```python
def validate_email(email):
    return '@' in email
```

Please fix this to properly validate email format."
```

### 3. Specify Output Format

```markdown
# Bad
"List some programming languages"

# Good
"List 5 programming languages for web development.
Format as a markdown table with columns:
- Language name
- Primary use case
- Learning difficulty (Easy/Medium/Hard)"
```

## Prompt Patterns

### Role Pattern

Assign a specific persona to guide responses:

```markdown
You are a senior Python developer with 10 years of experience.
You specialize in clean code, testing, and code reviews.
When reviewing code, you:
- Focus on readability and maintainability
- Suggest improvements with explanations
- Point out potential bugs or security issues

Please review the following code:
[code here]
```

### Chain of Thought

Guide step-by-step reasoning:

```markdown
Solve this problem step by step:

Problem: A store has 150 apples. They sell 30% on Monday,
then receive a shipment of 50 apples on Tuesday.
How many apples do they have now?

Please show your work:
1. Calculate apples sold on Monday
2. Calculate remaining apples after Monday
3. Add Tuesday's shipment
4. State the final answer
```

### Few-Shot Learning

Provide examples to establish patterns:

```markdown
Convert these sentences to formal English:

Example 1:
Casual: "gonna grab some coffee"
Formal: "I am going to get some coffee."

Example 2:
Casual: "wanna come with?"
Formal: "Would you like to accompany me?"

Now convert:
Casual: "lemme know if you're free"
Formal:
```

### Template Pattern

Create reusable structures:

```markdown
# Bug Report Template

Please analyze this bug and provide:

## Summary
[One sentence description]

## Root Cause
[Technical explanation of why this bug occurs]

## Impact
[Who is affected and how]

## Solution
[Recommended fix with code example]

## Prevention
[How to prevent similar bugs in the future]

---
Bug to analyze:
[user's bug description]
```

## System Prompts

### Structure

```markdown
# [Role/Identity]
You are [description of the assistant's role and expertise]

# [Core Behaviors]
You should always:
- [Behavior 1]
- [Behavior 2]

You should never:
- [Anti-pattern 1]
- [Anti-pattern 2]

# [Response Format]
When responding:
- [Format guideline 1]
- [Format guideline 2]

# [Examples] (optional)
Here's an example of how to respond:
[example interaction]
```

### Example System Prompt

```markdown
# Role
You are a helpful coding assistant specializing in Python.
You have expertise in data science, web development, and automation.

# Core Behaviors
Always:
- Write clean, well-documented code
- Explain your reasoning
- Suggest tests for code you write
- Consider edge cases

Never:
- Write code without explanation
- Use deprecated libraries
- Ignore security best practices
- Make assumptions about requirements without clarifying

# Response Format
When writing code:
1. Start with a brief explanation of the approach
2. Write the code with comments
3. Explain any complex parts
4. Suggest how to test it

When debugging:
1. Identify the likely cause
2. Explain why it happens
3. Provide the fix
4. Suggest how to prevent similar issues
```

## Optimization Techniques

### Iterative Refinement

```markdown
# First attempt
"Write a story"

# After iteration 1: Add specifics
"Write a 500-word short story about a robot"

# After iteration 2: Add constraints
"Write a 500-word short story about a robot
learning to paint. Include dialogue."

# After iteration 3: Add style
"Write a 500-word short story about a robot
learning to paint. Include dialogue. Write in
a warm, hopeful tone similar to Studio Ghibli films."
```

### Decomposition

Break complex tasks into steps:

```markdown
Instead of:
"Create a complete e-commerce website"

Use:
"Let's build an e-commerce website step by step:

Step 1: Define the data models we need for products,
users, and orders. Show me the schema.

[Wait for response]

Step 2: Based on those models, create the API endpoints.

[Wait for response]

Step 3: Now let's build the product listing page..."
```

### Constraint Setting

```markdown
# Add boundaries for better results
"Write a product description for a coffee maker.

Constraints:
- Maximum 100 words
- Include 3 key features
- End with a call to action
- Don't use superlatives like 'best' or 'amazing'
- Write at a 6th-grade reading level"
```

## Common Pitfalls

### 1. Vague Instructions

```markdown
# Bad
"Make it better"

# Good
"Improve the readability by:
- Using shorter sentences (max 20 words)
- Adding subheadings every 100-150 words
- Replacing jargon with plain language"
```

### 2. Missing Context

```markdown
# Bad
"Why isn't my code working?"

# Good
"My Python code throws a TypeError.
Environment: Python 3.11, macOS
Error message: TypeError: 'NoneType' object is not iterable
Code:
```python
def process(items):
    for item in items:
        print(item)

process(get_items())  # Error occurs here
```
The get_items() function should return a list."
```

### 3. Overloading

```markdown
# Bad (too many things at once)
"Write a blog post about AI, make it SEO optimized,
include code examples, add images, make it funny but professional,
target beginners but also appeal to experts..."

# Good (focused request)
"Write a 500-word introduction to machine learning
for complete beginners. Use simple analogies and
avoid technical jargon. Include 3 real-world examples."
```

## Evaluation Checklist

```markdown
Before submitting a prompt, verify:

## Clarity
- [ ] Is the task clearly defined?
- [ ] Are ambiguous terms explained?
- [ ] Is the expected output format specified?

## Context
- [ ] Is relevant background provided?
- [ ] Are constraints clearly stated?
- [ ] Are examples included if needed?

## Structure
- [ ] Is the prompt well-organized?
- [ ] Are complex tasks broken into steps?
- [ ] Is there a clear order of operations?

## Completeness
- [ ] Does it include all necessary information?
- [ ] Are edge cases considered?
- [ ] Is the success criteria clear?
```

## Examples by Use Case

### Code Generation

```markdown
Write a Python function that:
- Takes a list of dictionaries representing users
- Filters users older than 18
- Sorts by last name alphabetically
- Returns their email addresses

Input example:
[{"name": "John Doe", "age": 25, "email": "john@example.com"}]

Requirements:
- Include type hints
- Add docstring
- Handle empty list case
- Include unit test
```

### Data Analysis

```markdown
Analyze this sales data and provide:

1. Summary statistics (mean, median, std dev)
2. Top 3 performing products
3. Month-over-month growth rate
4. Any anomalies or patterns

Present findings in a markdown table.
Include a brief executive summary (3-4 sentences).

Data:
[paste data here]
```

### Writing Assistance

```markdown
Help me improve this email to a client:

Context: We need to delay the project by 2 weeks
due to unexpected technical issues.

Current draft:
"Hi, the project will be late. Sorry about that."

Goals:
- Maintain professional relationship
- Clearly explain the delay
- Provide new timeline
- Offer mitigation options

Tone: Professional but warm
Length: 150-200 words
```
