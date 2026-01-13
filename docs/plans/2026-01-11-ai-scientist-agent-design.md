# AI Scientist Agent Profile - Design Document

**Date:** 2026-01-11
**Status:** Ready for Implementation
**Integration Type:** Deep Integration (Native Agent Zero Profile)

## Overview

This document describes the design for integrating AI-Scientist-v2 as a native Agent Zero profile. The AI Scientist is a research automation system that generates research ideas, runs experiments via agentic tree search, analyzes data, and writes scientific manuscripts.

## Architecture Decision

**Chosen Approach:** Deep Integration
- Rewrite AI Scientist core logic to use Agent Zero's agent system, tools, and messaging
- AI Scientist becomes a native Agent Zero profile with full UI integration
- All LLM calls go through Agent Zero's chat model
- Experiments use subordinate agents for tree search parallelism

## Profile Structure

```
agents/ai-scientist/
├── agent.json                    # Profile metadata
├── settings.json                 # Default model configs
├── prompts/
│   ├── agent.system.main.role.md           # Scientific research persona
│   ├── agent.system.main.methodology.md    # Research methodology
│   └── agent.system.tools.scientist.md     # Tool documentation
├── tools/
│   ├── generate_idea.py          # Ideation with Semantic Scholar
│   ├── semantic_scholar.py       # Literature search
│   ├── run_experiment.py         # Spawns subordinate agents for BFTS
│   ├── write_paper.py            # LaTeX generation + citation
│   └── plot_aggregator.py        # Result visualization
└── extensions/
    └── agent_init/
        └── _10_init_scientist_state.py   # Initialize research state
```

## Profile Metadata

**agent.json:**
```json
{
  "title": "AI Scientist",
  "description": "Agent specialized in autonomous scientific research - generates ideas, runs experiments via tree search, and writes papers.",
  "context": "Use this agent for ML research: hypothesis generation, experiment execution, ablation studies, and paper writing. Supports 4-stage pipeline: initial implementation → baseline tuning → creative research → ablation studies."
}
```

## Core Components

### 1. Research Ideation System

**Tool:** `generate_idea.py`

Generates research ideas with novelty validation using Semantic Scholar.

**Idea JSON Structure (from AI-Scientist-v2):**
```json
{
  "Name": "attention_sparse_routing",
  "Title": "Sparse Attention Routing for Efficient Transformers",
  "Short Hypothesis": "Dynamic routing reduces compute while maintaining accuracy",
  "Related Work": "Builds on Mixture of Experts but applies to attention...",
  "Abstract": "We propose a novel sparse attention mechanism...",
  "Experiments": ["Baseline comparison on GLUE", "Ablation on routing strategies"],
  "Risk Factors and Limitations": ["May not scale to very long sequences"]
}
```

**Process:**
1. Parse topic description
2. Generate candidate ideas via LLM
3. Run reflection rounds with Semantic Scholar lookups
4. Validate novelty against existing literature
5. Store ideas in `agent.data["research_ideas"]`

### 2. Experiment Management via Tree Search

**Tool:** `run_experiment.py`

Implements 4-stage Best-First Tree Search (BFTS) using subordinate agents.

**Stage Definitions:**

| Stage | Name | Goals |
|-------|------|-------|
| 1 | Initial Implementation | Basic working code, simple dataset, functional correctness |
| 2 | Baseline Tuning | Hyperparameter optimization, add 2 more HuggingFace datasets |
| 3 | Creative Research | Novel improvements, insights, 3 datasets total |
| 4 | Ablation Studies | Systematic component analysis, same datasets |

**Subordinate Agent Architecture:**
```
Main AI Scientist Agent (A0)
    ├── Experiment Worker A1 (Stage 1)
    │   ├── Debug Worker A2 (if code fails)
    │   └── ...
    ├── Experiment Worker A1 (Stage 2)
    ├── Experiment Worker A1 (Stage 3)
    └── Experiment Worker A1 (Stage 4)
```

### 3. Paper Generation System

**Tool:** `write_paper.py`

Generates publication-ready LaTeX manuscripts.

**Process:**
1. Load experiment summaries (baseline, research, ablation)
2. Gather citations via Semantic Scholar
3. Run plot aggregation
4. Generate LaTeX with reflection rounds
5. Compile PDF

**Supported Formats:**
- Normal (NeurIPS-style): 8 pages
- ICBINB (workshop): 4 pages

## Prompt Templates

### Draft Prompt (Stage 1)

```python
prompt = {
    "Introduction": (
        "You are an AI researcher who is looking to publish a paper that will contribute significantly to the field."
        "Your first task is to write a python code to implement a solid baseline based on your research idea provided below, "
        "from data preparation to model training, as well as evaluation and visualization. "
        "Focus on getting a simple but working implementation first, before any sophisticated improvements. "
        "We will explore more advanced variations in later stages."
    ),
    "Research idea": task_desc,
    "Memory": memory_summary,
    "Instructions": {
        "Response format": (
            "Your response should be a brief outline/sketch of your proposed solution in natural language (7-10 sentences), "
            "followed by a single markdown code block (using ```python ... ```) which implements this solution..."
        ),
        "Experiment design sketch guideline": [...],
        "Evaluation Metric(s)": evaluation_metrics,
        "Implementation guideline": [
            "CRITICAL GPU REQUIREMENTS - Your code MUST include ALL of these:",
            "  - device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')",
            "  - ALWAYS move models to device using .to(device)",
            ...
        ],
        "Installed Packages": "numpy, pandas, scikit-learn, torch, torchvision, timm, ..."
    }
}
```

### Debug Prompt

```python
prompt = {
    "Introduction": (
        "You are an experienced AI researcher. Your previous code for research experiment had a bug, "
        "so based on the information below, you should revise it in order to fix this bug."
    ),
    "Research idea": task_desc,
    "Previous (buggy) implementation": parent_node.code,
    "Execution output": parent_node.term_out,
    "Feedback based on generated plots": parent_node.vlm_feedback_summary,
    "Feedback about execution time": parent_node.exec_time_feedback,
    "Instructions": {...}
}
```

### Writeup Prompt

```python
writeup_prompt = """Your goal is to write up the following idea:

```markdown
{idea_text}
```

We have the following experiment summaries (JSON):
```json
{summaries}
```

Available plots for the writeup (use these filenames):
```
{plot_list}
```

Produce the final version of the LaTeX manuscript now, ensuring the paper is coherent,
concise, and reports results accurately.
"""
```

## UI Components

### Modal-Based Architecture

```
webui/components/modals/ai-scientist/
├── ideas-manager/
│   ├── ideas-manager.html
│   └── ideas-manager-store.js
├── experiment-dashboard/
│   ├── experiment-dashboard.html
│   └── experiment-dashboard-store.js
└── paper-generator/
    ├── paper-generator.html
    └── paper-generator-store.js
```

### Ideas Manager Modal
- Topic input for idea generation
- List of generated ideas with novelty scores
- Detailed view of selected idea
- Button to start experiment

### Experiment Dashboard Modal
- 4-stage progress bar with status indicators
- Tree visualization of explored nodes
- Live metrics (validation loss, accuracy)
- Node inspector (code, output, plots)

### Paper Generator Modal
- Select completed experiment
- Choose format (8-page / 4-page)
- Citation progress indicator
- LaTeX preview
- PDF download

## API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `scientist_get_ideas` | List all generated ideas |
| `scientist_generate_ideas` | Trigger idea generation |
| `scientist_get_experiments` | List all experiments |
| `scientist_get_experiment_progress` | Get detailed experiment status |
| `scientist_start_experiment` | Start experiment for an idea |
| `scientist_generate_paper` | Trigger paper generation |

## Data Flow

```
User → UI Modals → API Layer → AgentContext.communicate()
                                        ↓
                              AI Scientist Agent (A0)
                                        ↓
                    ┌───────────────────┼───────────────────┐
                    ↓                   ↓                   ↓
             generate_idea        run_experiment       write_paper
                    ↓                   ↓                   ↓
             Semantic Scholar    Subordinate Agents    LaTeX + PDF
                                        ↓
                               code_execution_tool
                                        ↓
                               Results & Plots
```

## State Persistence

```
work_dir/ai-scientist/{idea_name}/
├── idea.json                    # Original idea
├── checkpoint.pkl               # Resumable state
├── logs/0-run/
│   ├── stage_1_initial_implementation/
│   │   ├── journal.json
│   │   └── experiment_results/node_*/
│   ├── stage_2_baseline_tuning/
│   ├── stage_3_creative_research/
│   ├── stage_4_ablation_studies/
│   └── *_summary.json
├── figures/                     # Aggregated plots
├── latex/                       # Generated LaTeX
└── paper.pdf                    # Final output
```

## Message System Integration

**New Log Types:**
- `scientist_idea` - Idea generation progress
- `scientist_stage` - Stage transition
- `scientist_node` - Tree node exploration
- `scientist_paper` - Paper generation progress

**Status Badges:**
- `IDEA` - generate_idea tool
- `LIT` - semantic_scholar tool
- `EXP` - run_experiment tool
- `PAPER` - write_paper tool

## Implementation Phases

### Phase 1: Core Profile & Ideation
1. Create `agents/ai-scientist/` directory structure
2. Implement `agent.json`, system prompts
3. Port `generate_idea.py` tool with Semantic Scholar integration
4. Create Ideas Manager modal

### Phase 2: Experiment Engine
1. Implement `run_experiment.py` with subordinate agent spawning
2. Port MinimalAgent prompts (draft, debug, improve, ablation)
3. Implement journal and checkpoint persistence
4. Create Experiment Dashboard modal

### Phase 3: Paper Generation
1. Implement `write_paper.py` with citation gathering
2. Port writeup and reflection prompts
3. Integrate LaTeX compilation
4. Create Paper Generator modal

### Phase 4: Polish & Testing
1. End-to-end testing of full pipeline
2. UI refinements
3. Documentation
4. Performance optimization

## Dependencies

**External:**
- Semantic Scholar API (S2_API_KEY)
- LLM provider APIs (already in Agent Zero)
- LaTeX distribution (pdflatex)
- matplotlib, numpy, torch (for experiments)

**Agent Zero:**
- Alpine.js component system
- Store management (AlpineStore.js)
- Modal framework (modals.js)
- Message rendering system
- code_execution_tool
- call_subordinate tool

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Complex integration | Phased implementation with clear milestones |
| Long-running experiments | Checkpoint system for resumption |
| LLM API reliability | Retry logic, fallback models |
| Code execution safety | Use existing sandboxed code_execution_tool |
| Resource management | GPU manager, timeout enforcement |

## Success Criteria

- [ ] Generate research ideas from topic descriptions
- [ ] Validate novelty via Semantic Scholar
- [ ] Execute 4-stage experiment pipeline
- [ ] Spawn subordinate agents for parallel exploration
- [ ] Generate publication-ready papers with citations
- [ ] UI integration following Agent Zero patterns
- [ ] Full state persistence and resumption
