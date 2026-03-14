# Mahoosuc OS Skills Adaptation Guide

**Imported**: 2026-01-24
**Source**: mahoosuc-operating-system
**Compatibility**: Claude Code Skills System

## Imported Skills

1. **brand-voice** - Brand voice consistency checking
2. **content-optimizer** - Content optimization for SEO and readability
3. **frontend-design** - Frontend design system and component generation
4. **stripe-revenue-analyzer** - Stripe revenue analytics and insights
5. **vercel-landing-page-builder** - Landing page generation for Vercel

## Claude Code Skills vs Agent Jumbo Tools

**Claude Code Skills**:

- Invoked via `Skill` tool
- Use `skill.md` format with frontmatter
- Designed for Claude Code CLI context

**Agent Jumbo Tools**:

- Python classes extending `Tool` base class
- Located in `python/tools/`
- Use `execute()` method returning `Response`

## Usage in Agent Jumbo

These skills are **Claude Code specific** and won't directly work in Agent Jumbo's tool system. Options:

### Option 1: Use via Claude Code MCP Integration

If Agent Jumbo has Claude Code MCP integration enabled, skills can be invoked through the MCP bridge.

### Option 2: Convert to Agent Jumbo Tools

Transform skill logic into Agent Jumbo tools:

**Example: brand-voice skill → brand_voice.py tool**

```python
from python.helpers.tool import Tool, Response


class BrandVoice(Tool):
    async def execute(self, **kwargs):
        """Check brand voice consistency"""
        text = self.args.get("text", "")

        # Port skill logic here
        # (analyze text, check brand guidelines, return feedback)

        return Response(
            message="Brand voice analysis results...",
            break_loop=False
        )
```

### Option 3: Reference Only

Keep skills as reference for design patterns and best practices when building Agent Jumbo equivalents.

## Recommended Approach

**Short-term**: Option 3 (Reference only)
**Medium-term**: Option 1 (MCP bridge if available)
**Long-term**: Option 2 (Convert high-value skills to native tools)
