---
description: Interactively update Serena memory files with new project knowledge
argument-hint: [memory-name] [--create] [--search <query>]
model: claude-sonnet-4-5-20250929
allowed-tools: [Read, Write, Edit, AskUserQuestion, Grep, mcp__plugin_serena_serena__read_memory, mcp__plugin_serena_serena__write_memory, mcp__plugin_serena_serena__list_memories, mcp__plugin_serena_serena__edit_memory]
---

# /knowledge:update-memory

Update Serena memory: **${ARGUMENTS:-interactive mode}**

---

## Step 1: Parse Arguments and Determine Mode

Understand what memory operation is requested:

<commentary>
Three modes:
1. Direct update: memory name provided
2. Create new: --create flag with name
3. Search and update: --search flag with query
4. Interactive: no args (guide user through process)
</commentary>

1. Check if memory name is provided as argument
2. Check for flags:
   - `--create`: Create new memory file
   - `--search <query>`: Find existing memory to update
3. If no args, enter interactive mode

---

## Step 2: List Existing Memories

Show available memory files to user:

Use the `list_memories` tool to get all available memories.

Display in organized format:

```
📚 Available Serena Memories:

Project Architecture:
- architecture-overview.md
- design-decisions.md
- technology-stack.md

Patterns & Conventions:
- coding-patterns.md
- api-design-patterns.md
- testing-conventions.md

Tools & Dependencies:
- development-tools.md
- deployment-process.md
- third-party-integrations.md

Project Context:
- business-logic.md
- domain-knowledge.md
- troubleshooting-guide.md

Total: ${memoryCount} memory files
```

---

## Step 3: Interactive Mode - Gather Knowledge

If in interactive mode, ask user what they want to document:

<commentary>
Use AskUserQuestion to understand what knowledge needs to be captured.
This helps users who may not know exactly what to document.
</commentary>

Ask:

```
What type of knowledge would you like to add to Serena's memory?

Options:
1. Architectural Decision
   - Why we chose a specific technology, pattern, or approach
   - Trade-offs considered
   - Alternatives evaluated

2. Pattern or Convention
   - Code patterns to follow
   - Naming conventions
   - File organization rules
   - Best practices

3. Tool or Dependency
   - How to use a specific tool
   - Configuration requirements
   - Common issues and solutions

4. Project-Specific Context
   - Business domain knowledge
   - Customer requirements
   - Project constraints
   - Stakeholder information

5. Troubleshooting Guide
   - Common errors and fixes
   - Debugging procedures
   - Performance optimization tips

6. Other (Specify)
```

---

## Step 4: Determine Target Memory File

Based on knowledge type, suggest appropriate memory file:

<commentary>
Map knowledge types to memory files:
- Architectural Decision → design-decisions.md or architecture-overview.md
- Pattern/Convention → coding-patterns.md or api-design-patterns.md
- Tool/Dependency → development-tools.md or third-party-integrations.md
- Project Context → business-logic.md or domain-knowledge.md
- Troubleshooting → troubleshooting-guide.md
</commentary>

If memory file exists:

```
📝 Suggested memory file: ${suggestedMemory}

This file currently contains:
- ${existingTopics.length} topics
- Last updated: ${lastUpdated}

Options:
1. Add to this file (recommended)
2. Create new file
3. Choose different existing file
```

If memory doesn't exist:

```
📝 Creating new memory file: ${memoryName}

This will be a new memory file for ${category}.
```

---

## Step 5: Read Current Memory Content

If updating existing memory, read current content:

Use `read_memory` tool to get current content.

Show user a summary:

```
📖 Current content of ${memoryName}:

Structure:
${toc}

Recent additions:
${recentSections}

Total sections: ${sectionCount}
```

---

## Step 6: Gather New Knowledge Content

Ask user to provide the knowledge to document:

<commentary>
Guide user to provide structured information.
For architectural decisions, use ADR format.
For patterns, provide examples.
For troubleshooting, include symptoms, causes, solutions.
</commentary>

Depending on knowledge type:

### For Architectural Decisions

```
Please provide the following information:

1. Decision Title
   (e.g., "Use PostgreSQL instead of MongoDB")

2. Context
   (What situation led to this decision?)

3. Decision
   (What did we decide to do?)

4. Rationale
   (Why did we make this decision?)

5. Consequences
   (What are the trade-offs and implications?)

6. Alternatives Considered
   (What other options did we evaluate?)
```

### For Patterns/Conventions

```
Please provide:

1. Pattern Name
   (e.g., "Repository Pattern for Data Access")

2. When to Use
   (What situations call for this pattern?)

3. Implementation
   (Code example or description)

4. Examples in Codebase
   (File paths where this is used)

5. Anti-patterns to Avoid
   (What NOT to do)
```

### For Troubleshooting

```
Please provide:

1. Problem/Error
   (What is the issue?)

2. Symptoms
   (How does it manifest?)

3. Root Cause
   (Why does it happen?)

4. Solution
   (How to fix it)

5. Prevention
   (How to avoid it in the future)
```

### For Tools/Dependencies

```
Please provide:

1. Tool/Library Name

2. Purpose
   (What does it do?)

3. Setup/Configuration
   (How to install and configure)

4. Usage
   (How to use it, with examples)

5. Common Issues
   (Known problems and solutions)
```

### For Project Context

```
Please provide:

1. Topic/Area

2. Background
   (Context and history)

3. Current State
   (How things are now)

4. Important Details
   (Key information to remember)

5. Related Areas
   (Connections to other topics)
```

---

## Step 7: Format Content for Memory

Structure the content in markdown format:

<commentary>
Use clear headings, bullet points, code blocks.
Include date for traceability.
Add links to related memories.
</commentary>

Generate structured markdown:

```markdown
## ${Title}

**Added**: ${date}
**Category**: ${category}
**Related**: ${relatedMemories}

### Context
${context}

### ${Section1Title}
${section1Content}

### ${Section2Title}
${section2Content}

### Examples
\`\`\`${language}
${codeExample}
\`\`\`

### See Also
- [${relatedTopic1}](#${link1})
- [${relatedTopic2}](#${link2})

---
```

---

## Step 8: Show Preview and Confirm

Display preview of changes to user:

<commentary>
Show before/after diff or just new content if creating.
Use clear formatting so user can review.
</commentary>

If updating existing memory:

```
📋 Preview of changes to ${memoryName}:

=== NEW CONTENT TO BE ADDED ===

${newContent}

=== END NEW CONTENT ===

This will be added to section: ${sectionName}

Confirm? (y/n)
```

If creating new memory:

```
📋 Preview of new memory file ${memoryName}:

${fullContent}

Create this memory file? (y/n)
```

---

## Step 9: Apply Changes to Memory

Update or create the memory file:

<commentary>
Use write_memory for new files or small updates.
Use edit_memory for targeted updates to existing files.
</commentary>

If creating new memory:

```typescript
mcp__plugin_serena_serena__write_memory({
  memory_file_name: memoryName,
  content: formattedContent
});
```

If updating existing memory (append):

```typescript
mcp__plugin_serena_serena__write_memory({
  memory_file_name: memoryName,
  content: existingContent + '\n\n' + newContent
});
```

If updating existing memory (targeted edit):

```typescript
mcp__plugin_serena_serena__edit_memory({
  memory_file_name: memoryName,
  needle: sectionMarker,  // regex pattern
  repl: updatedSection,
  mode: 'regex'
});
```

---

## Step 10: Verify Update

Read back the memory to confirm changes:

Use `read_memory` to verify the update was applied correctly.

Show confirmation:

```
✅ Memory updated successfully!

Memory file: ${memoryName}
Content added: ${addedLines} lines
Total size: ${totalLines} lines

Latest addition:
${latestSection}
```

---

## Step 11: Link Related Memories (Optional)

Ask if user wants to link to related memories:

<commentary>
Help build a knowledge graph by linking related topics.
This makes knowledge discovery easier later.
</commentary>

```
Would you like to link this to related memories?

Related topics detected:
1. ${relatedMemory1} (${relevanceScore1}% relevant)
2. ${relatedMemory2} (${relevanceScore2}% relevant)
3. ${relatedMemory3} (${relevanceScore3}% relevant)

Add cross-references? (y/n)
```

If yes:

1. Add "See Also" links to current memory
2. Add backlinks to related memories

---

## Step 12: Suggest Regular Reviews

Remind user about memory maintenance:

```
💡 Memory Maintenance Tips:

1. Review and update memories when context changes
2. Add new examples as they emerge in the codebase
3. Remove outdated information
4. Link related concepts
5. Run /knowledge:search to verify memories are discoverable

Next review suggested: ${suggestDate}

Set reminder? (y/n)
```

---

## Step 13: Summary

Display operation summary:

```markdown
# ✅ Memory Update Complete

## Updated Memory
📄 File: ${memoryName}
📊 Size: ${totalLines} lines (${changeType})
📅 Last updated: ${timestamp}

## Changes Made
${changeType === 'created' ? '🆕 New memory file created' : '➕ Content added to existing memory'}

### New Content Summary
- **Title**: ${title}
- **Category**: ${category}
- **Lines added**: ${addedLines}
- **Code examples**: ${exampleCount}
- **Cross-references**: ${linkCount}

## Related Memories
${relatedMemories.map(m => `- ${m.name} (${m.relation})`).join('\n')}

## Next Steps

1. **Verify Knowledge**
   Run: \`/knowledge:search "${keyTerm}"\`

2. **Share with Team**
   Memory files are in: \`.claude/memories/\`
   Commit changes: \`git add .claude/memories/ && git commit -m "docs: update ${memoryName}"\`

3. **Build on Knowledge**
   Add more examples as you encounter them
   Update when requirements change

## Quick Access
- View this memory: \`/knowledge:search ${memoryName}\`
- Update again: \`/knowledge:update-memory ${memoryName}\`
- All memories: \`/knowledge:search\`

---

🧠 Serena's knowledge has been expanded!
```

---

## Advanced Features

### Bulk Import from Documentation

If user has existing documentation:

```
Would you like to import content from existing docs?

Options:
1. Import from README.md
2. Import from docs/ directory
3. Import from specific file
4. Extract from code comments
```

Process:

1. Read source documentation
2. Parse and structure content
3. Categorize into appropriate memories
4. Show preview
5. Apply with user approval

---

### Memory Templates

Provide templates for common memory types:

```
Choose a template:

1. ADR (Architectural Decision Record)
2. API Design Pattern
3. Troubleshooting Guide
4. Tool Configuration
5. Business Logic
6. Custom (blank template)
```

Pre-fill template structure, user fills in details.

---

### Search Mode

If `--search` flag is used:

```bash
/knowledge:update-memory --search "authentication"
```

1. Search across all memories for keyword
2. Show matching memories:

   ```
   Found 3 memories matching "authentication":

   1. security-patterns.md (5 matches)
      - OAuth2 Implementation
      - JWT Token Handling
      - Session Management

   2. api-design-patterns.md (2 matches)
      - Authentication Middleware
      - Protected Routes

   3. troubleshooting-guide.md (1 match)
      - Common Auth Errors

   Which would you like to update?
   ```

3. User selects memory to update
4. Continue with normal update flow

---

## Error Handling

### Memory File Not Found

```
❌ Error: Memory file "${memoryName}" not found

Available memories:
${availableMemories}

Options:
1. Create new memory: /knowledge:update-memory ${memoryName} --create
2. Search memories: /knowledge:search ${term}
3. List all: /knowledge:update-memory
```

### Invalid Content Format

```
⚠️  Warning: Content format may need adjustment

Suggestions:
- Use markdown headings (##, ###)
- Include code examples in fenced blocks
- Add cross-references to related topics
- Structure with clear sections

Continue anyway? (y/n)
```

### Write Permission Error

```
❌ Error: Cannot write to memory file

Check:
- File permissions on .claude/memories/
- Disk space availability
- File not locked by another process

Fix permissions: chmod -R u+w .claude/memories/
```

---

## Example Usage

### Interactive mode

```bash
/knowledge:update-memory
```

### Update specific memory

```bash
/knowledge:update-memory architecture-overview
```

### Create new memory

```bash
/knowledge:update-memory api-versioning --create
```

### Search and update

```bash
/knowledge:update-memory --search "database migrations"
```

---

**Command Complete** 🧠
