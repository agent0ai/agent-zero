---
description: Track and analyze command usage statistics
argument-hint: [--period 7d|30d|90d|all] [--category <name>] [--export csv|json]
model: claude-haiku-4-20250528
allowed-tools: [Bash, Read, Write, Grep]
---

# /analytics:command-usage

Analyze command usage: **${ARGUMENTS:-last 30 days}**

## Step 1: Collect Command History

```bash
# Shell history
if [ -f ~/.bash_history ]; then
  grep "^/" ~/.bash_history | grep -v "^//  " > /tmp/commands.txt
elif [ -f ~/.zsh_history ]; then
  grep "^/" ~/.zsh_history > /tmp/commands.txt
fi

# Extract slash commands
grep -oP '/[a-z-]+:[a-z-]+ ' /tmp/commands.txt | sort | uniq -c | sort -rn > /tmp/command-counts.txt
```

## Step 2: Parse and Categorize

```javascript
const commands = parseCommandLog('/tmp/commands.txt');

const categories = groupBy(commands, c => c.split(':')[0]);

const stats = {
  total: commands.length,
  unique: new Set(commands).size,
  perDay: commands.length / daysInPeriod,
  byCategory: Object.keys(categories).map(cat => ({
    name: cat,
    count: categories[cat].length,
    percentage: (categories[cat].length / commands.length) * 100
  }))
};
```

## Step 3: Generate Report

```markdown
# 📊 Command Usage Report (${period})

## Summary
- **Total Commands**: ${totalCommands}
- **Unique Commands**: ${uniqueCommands}
- **Commands/Day**: ${commandsPerDay}
- **Categories Used**: ${categoryCount}

## Top 10 Commands
| Rank | Command | Count | % of Total |
|------|---------|-------|------------|
${topCommands.map((c, i) => `| ${i+1} | ${c.name} | ${c.count} | ${c.percentage}% |`).join('\n')}

## Usage by Category
${categories.map(c => `- **${c.name}**: ${c.count} commands (${c.percentage}%)`).join('\n')}

## Time-of-Day Patterns
${timePatterns}

## Recommendations
- Underutilized: ${underutilized.join(', ')}
- Create aliases for: ${frequentCommands.join(', ')}
- Explore: ${suggestedCommands.join(', ')}
```

**Command Complete** 📊
