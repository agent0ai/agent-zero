# Training Data Extraction Pipeline

Extracts architecture decisions, code patterns, solution compositions, and quality standards from the Silver Surfer Platform codebase, then generates ChatML instruction-response seed pairs for fine-tuning an AI architect clone.

## Pipeline Overview

```text
Silver Surfer Codebase
        |
        v
  Extract & Classify     (4 extractors parse code + docs into structured chunks)
        |
        v
  Generate Seed Pairs    (Claude API converts chunks into instruction-response pairs)
        |
        v
  Validate                (format, length, dedup, diversity, balance checks)
        |
        v
  training_data.jsonl     (validated ChatML pairs ready for SFT)
```

## Quick Start

```bash
# Extract all chunks from Silver Surfer Platform
python -m scripts.training.cli extract --all

# Preview seed pair generation (no API calls)
python -m scripts.training.cli generate --dry-run

# Generate seed pairs for one category (requires ANTHROPIC_API_KEY)
export ANTHROPIC_API_KEY=sk-...
python -m scripts.training.cli generate --category skills.architecture_design

# Generate all seed pairs with resume support
python -m scripts.training.cli generate --resume

# Validate generated data
python -m scripts.training.cli validate

# Print pipeline statistics
python -m scripts.training.cli stats
```

## Commands

| Command | Description |
|---------|-------------|
| `extract --all` | Run all 4 extractors |
| `extract --architecture` | Extract architecture decision traces |
| `extract --code-patterns` | Extract code templates and framework patterns |
| `extract --solutions` | Extract solution composition blueprints |
| `extract --quality` | Extract quality gates and standards |
| `generate --dry-run` | Preview generation plan and cost estimate |
| `generate --category X` | Generate pairs for one taxonomy category |
| `generate --resume` | Continue an interrupted generation run |
| `generate --limit N` | Process at most N chunks per category |
| `validate` | Run quality checks on generated pairs |
| `stats` | Print pipeline statistics |

## Output Structure

```text
scripts/training/output/
  chunks/
    architecture_decisions.jsonl
    code_patterns.jsonl
    solution_compositions.jsonl
    quality_standards.jsonl
  seeds/
    {category}.jsonl          (one file per taxonomy category)
  validated/
    training_data.jsonl       (final validated pairs)
    report.md                 (validation report)
```

## Dependencies

- `tiktoken` — token counting
- `anthropic` — Claude API for seed pair generation (only needed for `generate`)
