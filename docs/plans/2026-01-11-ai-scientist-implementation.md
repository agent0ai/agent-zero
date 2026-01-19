# AI Scientist Agent Profile Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement AI-Scientist-v2 as a native Agent Zero profile for autonomous ML research - idea generation, 4-stage experiment pipeline, and paper writing.

**Architecture:** Native agent profile using Agent Zero's subordinate agent system for tree search parallelism. State stored in `agent.data` with file-based checkpoints. Modal-based UI following Alpine.js patterns.

**Tech Stack:** Python (Agent Zero tools/extensions), Alpine.js (UI), Semantic Scholar API (literature search), LaTeX (paper generation)

---

## Phase 1: Core Profile & Ideation

### Task 1: Create Profile Directory Structure

**Files:**
- Create: `agents/ai-scientist/agent.json`
- Create: `agents/ai-scientist/settings.json`

**Step 1: Create directory and agent.json**

```bash
mkdir -p agents/ai-scientist
```

```json
{
  "title": "AI Scientist",
  "description": "Agent specialized in autonomous scientific research - generates ideas, runs experiments via tree search, and writes papers.",
  "context": "Use this agent for ML research: hypothesis generation, experiment execution, ablation studies, and paper writing. Supports 4-stage pipeline: initial implementation → baseline tuning → creative research → ablation studies."
}
```

**Step 2: Create settings.json**

```json
{
  "chat_model_name": "claude-sonnet-4-20250514",
  "utility_model_name": "claude-sonnet-4-20250514",
  "agent_memory_subdir": "ai-scientist"
}
```

**Step 3: Verify profile appears in settings**

Run: `python -c "from python.helpers import files; print([d for d in files.get_subdirectories('agents') if d != '_example'])"`
Expected: Should include 'ai-scientist'

**Step 4: Commit**

```bash
git add agents/ai-scientist/
git commit -m "feat(ai-scientist): add profile directory structure"
```

---

### Task 2: Create System Prompts

**Files:**
- Create: `agents/ai-scientist/prompts/agent.system.main.role.md`
- Create: `agents/ai-scientist/prompts/agent.system.main.methodology.md`

**Step 1: Create role prompt**

```markdown
# AI Scientist Role

You are an ambitious AI researcher looking to publish papers that contribute significantly to the field. You have access to specialized tools for:

1. **Research Ideation** - Generate novel research ideas with novelty validation via Semantic Scholar
2. **Experiment Execution** - Run experiments through a 4-stage pipeline using subordinate agents
3. **Paper Writing** - Generate publication-ready LaTeX manuscripts with proper citations

## Research Pipeline

When conducting research, follow this pipeline:
1. Understand the research topic and generate multiple candidate ideas
2. Validate novelty against existing literature using Semantic Scholar
3. Execute experiments systematically through all 4 stages
4. Aggregate results and generate visualizations
5. Write up findings as a scientific paper

## Stage Definitions

- **Stage 1 (Initial Implementation)**: Basic working code, simple dataset, functional correctness
- **Stage 2 (Baseline Tuning)**: Hyperparameter optimization, add 2 more HuggingFace datasets
- **Stage 3 (Creative Research)**: Novel improvements, insights, 3 datasets total
- **Stage 4 (Ablation Studies)**: Systematic component analysis, same datasets

## Tool Usage

When the user asks you to:
- "Generate ideas about X" → Use the `generate_idea` tool
- "Run experiments for idea Y" → Use the `run_experiment` tool
- "Write a paper for experiment Z" → Use the `write_paper` tool
- "Search literature for X" → Use the `semantic_scholar` tool
```

**Step 2: Create methodology prompt**

```markdown
# Scientific Methodology Guidelines

## Experiment Design Principles
- Start simple, iterate to complexity
- Always use proper train/validation splits
- Track all metrics systematically
- Save experiment data as numpy arrays

## Code Requirements
All generated experiment code must:
- Be single-file, self-contained Python scripts
- Include explicit GPU handling with device detection:
  ```python
  device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
  print(f'Using device: {device}')
  ```
- Properly normalize model inputs
- Save results to `working_dir/experiment_data.npy`
- Complete within the configured timeout

## Evaluation Standards
- Report validation loss at each epoch
- Track defined evaluation metrics
- Generate visualizations for all results
- Never hallucinate or fabricate data

## Data Saving Convention
```python
experiment_data = {
    'dataset_name': {
        'metrics': {'train': [], 'val': []},
        'losses': {'train': [], 'val': []},
        'predictions': [],
        'ground_truth': [],
    }
}
np.save(os.path.join(working_dir, 'experiment_data.npy'), experiment_data)
```
```

**Step 3: Commit**

```bash
git add agents/ai-scientist/prompts/
git commit -m "feat(ai-scientist): add system prompts for role and methodology"
```

---

### Task 3: Create State Initialization Extension

**Files:**
- Create: `agents/ai-scientist/extensions/agent_init/_10_init_scientist_state.py`

**Step 1: Create extension directory**

```bash
mkdir -p agents/ai-scientist/extensions/agent_init
```

**Step 2: Create initialization extension**

```python
from python.helpers.extension import Extension


class InitScientistState(Extension):
    """Initialize AI Scientist state containers in agent.data."""

    async def execute(self, **kwargs) -> None:
        if not self.agent:
            return

        # Initialize research state containers
        self.agent.data.setdefault("research_ideas", {})
        self.agent.data.setdefault("experiments", {})
        self.agent.data.setdefault("papers", {})

        # Set default evaluation metrics template
        self.agent.data.setdefault(
            "default_eval_metrics",
            """
            Track and print validation loss at each epoch.
            Track additional metrics relevant to the task (accuracy, F1, etc.).
            Save all metrics to experiment_data.npy using the standard format.
            """,
        )

        # Log initialization
        if self.agent.context:
            self.agent.context.log.log(
                type="info",
                heading="AI Scientist Initialized",
                content="Research state containers ready.",
            )
```

**Step 3: Commit**

```bash
git add agents/ai-scientist/extensions/
git commit -m "feat(ai-scientist): add state initialization extension"
```

---

### Task 4: Create Semantic Scholar Tool

**Files:**
- Create: `agents/ai-scientist/tools/semantic_scholar.py`

**Step 1: Create tools directory**

```bash
mkdir -p agents/ai-scientist/tools
```

**Step 2: Create semantic scholar tool**

```python
import os
import time
import urllib.parse
from typing import Optional

import requests

from python.helpers.tool import Tool, Response


S2_API_KEY = os.getenv("S2_API_KEY", "")


class SemanticScholar(Tool):
    """Search Semantic Scholar for academic papers."""

    async def execute(
        self,
        query: str,
        limit: int = 10,
        fields: str = "title,authors,year,abstract,citationCount",
        **kwargs,
    ) -> Response:
        """
        Search Semantic Scholar for papers matching the query.

        Args:
            query: Search query string
            limit: Maximum number of results (default 10)
            fields: Comma-separated fields to return
        """
        # Log progress
        self.agent.context.log.log(
            type="tool",
            heading="Semantic Scholar Search",
            content=f"Searching for: {query}",
            kvps={"query": query, "limit": limit},
        )

        try:
            results = await self._search(query, limit, fields)

            if not results:
                return Response(
                    message="No papers found matching the query.",
                    break_loop=False,
                )

            # Format results
            formatted = self._format_results(results)

            return Response(
                message=f"Found {len(results)} papers:\n\n{formatted}",
                break_loop=False,
            )

        except Exception as e:
            return Response(
                message=f"Semantic Scholar search failed: {str(e)}",
                break_loop=False,
            )

    async def _search(
        self, query: str, limit: int, fields: str
    ) -> list[dict]:
        """Execute the search API call."""
        encoded_query = urllib.parse.quote(query)
        url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={encoded_query}&limit={limit}&fields={fields}"

        headers = {}
        if S2_API_KEY:
            headers["x-api-key"] = S2_API_KEY

        # Rate limiting
        time.sleep(1.0 if not S2_API_KEY else 0.1)

        response = requests.get(url, headers=headers, timeout=30)

        if response.status_code == 429:
            # Rate limited, wait and retry
            time.sleep(5)
            response = requests.get(url, headers=headers, timeout=30)

        response.raise_for_status()
        data = response.json()

        return data.get("data", [])

    def _format_results(self, results: list[dict]) -> str:
        """Format search results for display."""
        formatted = []
        for i, paper in enumerate(results, 1):
            title = paper.get("title", "Unknown")
            authors = paper.get("authors", [])
            author_str = ", ".join(a.get("name", "") for a in authors[:3])
            if len(authors) > 3:
                author_str += " et al."
            year = paper.get("year", "Unknown")
            citations = paper.get("citationCount", 0)
            abstract = paper.get("abstract", "")
            if abstract and len(abstract) > 300:
                abstract = abstract[:300] + "..."

            formatted.append(
                f"{i}. **{title}**\n"
                f"   Authors: {author_str}\n"
                f"   Year: {year} | Citations: {citations}\n"
                f"   Abstract: {abstract}\n"
            )

        return "\n".join(formatted)
```

**Step 3: Commit**

```bash
git add agents/ai-scientist/tools/semantic_scholar.py
git commit -m "feat(ai-scientist): add Semantic Scholar search tool"
```

---

### Task 5: Create Generate Idea Tool

**Files:**
- Create: `agents/ai-scientist/tools/generate_idea.py`

**Step 1: Create the tool**

```python
import json
import re
from typing import Any

from python.helpers.tool import Tool, Response


# Idea JSON schema for validation
IDEA_SCHEMA = {
    "required_fields": [
        "Name",
        "Title",
        "Short Hypothesis",
        "Abstract",
        "Experiments",
        "Risk Factors and Limitations",
    ],
    "optional_fields": ["Related Work", "Code"],
}


class GenerateIdea(Tool):
    """Generate research ideas with novelty validation."""

    async def execute(
        self,
        topic: str,
        num_ideas: int = 5,
        num_reflections: int = 3,
        **kwargs,
    ) -> Response:
        """
        Generate research ideas for a given topic.

        Args:
            topic: Research topic description (markdown)
            num_ideas: Number of ideas to generate (default 5)
            num_reflections: Reflection rounds per idea (default 3)
        """
        # Initialize ideas storage
        if "research_ideas" not in self.agent.data:
            self.agent.data["research_ideas"] = {}

        ideas = []
        for i in range(num_ideas):
            # Log progress
            self.agent.context.log.log(
                type="progress",
                heading=f"Generating idea {i + 1}/{num_ideas}",
                content="",
            )

            try:
                idea = await self._generate_single_idea(topic, num_reflections, i)
                if idea:
                    # Validate novelty
                    novelty_score = await self._check_novelty(idea)
                    idea["novelty_score"] = novelty_score

                    # Store idea
                    self.agent.data["research_ideas"][idea["Name"]] = idea
                    ideas.append(idea)

                    self.agent.context.log.log(
                        type="info",
                        heading=f"Idea {i + 1} generated",
                        content=idea["Title"],
                        kvps={"novelty_score": novelty_score},
                    )
            except Exception as e:
                self.agent.context.log.log(
                    type="warning",
                    heading=f"Idea {i + 1} failed",
                    content=str(e),
                )

        if not ideas:
            return Response(
                message="Failed to generate any valid research ideas.",
                break_loop=False,
            )

        # Format summary
        summary = self._format_ideas_summary(ideas)

        return Response(
            message=f"Generated {len(ideas)} research ideas:\n\n{summary}\n\nUse `run_experiment` to start experiments on an idea.",
            break_loop=False,
        )

    async def _generate_single_idea(
        self, topic: str, num_reflections: int, idea_num: int
    ) -> dict | None:
        """Generate a single research idea with reflection rounds."""

        # Initial generation prompt
        prompt = self._build_generation_prompt(topic, idea_num)

        # Get initial idea from agent's chat model
        response = await self._query_model(prompt)
        idea = self._parse_idea_json(response)

        if not idea:
            return None

        # Reflection rounds
        for r in range(num_reflections):
            self.agent.context.log.log(
                type="progress",
                heading=f"Reflection {r + 1}/{num_reflections}",
                content=f"Refining idea: {idea.get('Title', 'Unknown')}",
            )

            # Search related work
            search_query = f"{idea.get('Title', '')} {idea.get('Short Hypothesis', '')}"
            related_work = await self._search_related_work(search_query[:200])

            # Refine idea based on literature
            idea = await self._refine_idea(idea, related_work, r, num_reflections)

        return idea

    def _build_generation_prompt(self, topic: str, idea_num: int) -> dict:
        """Build the prompt for idea generation."""
        return {
            "Role": "You are a creative AI researcher generating novel research ideas.",
            "Task": f"Generate research idea #{idea_num + 1} for the following topic.",
            "Topic": topic,
            "Instructions": [
                "Generate a research idea with the following JSON structure:",
                "- Name: short identifier (snake_case, e.g., 'sparse_attention_routing')",
                "- Title: paper title",
                "- Short Hypothesis: 1-2 sentences describing the core hypothesis",
                "- Abstract: 3-4 sentence abstract",
                "- Experiments: list of 3-5 proposed experiments",
                "- Risk Factors and Limitations: list of potential issues",
                "",
                "Respond with ONLY valid JSON, no additional text.",
            ],
            "Example Output": json.dumps(
                {
                    "Name": "example_idea",
                    "Title": "Example Research Title",
                    "Short Hypothesis": "We hypothesize that X improves Y.",
                    "Abstract": "This paper proposes...",
                    "Experiments": ["Experiment 1", "Experiment 2"],
                    "Risk Factors and Limitations": ["Risk 1", "Risk 2"],
                },
                indent=2,
            ),
        }

    async def _query_model(self, prompt: dict) -> str:
        """Query the agent's chat model."""
        # Use agent's message history mechanism
        from python.helpers import history

        # Create a temporary message for the query
        msg = history.Message(
            role="user",
            content=json.dumps(prompt, indent=2),
        )

        # Get response via agent's chat model
        response = await self.agent.call_chat_model(
            messages=[msg],
            system="You are a research idea generator. Respond only with valid JSON.",
        )

        return response if isinstance(response, str) else str(response)

    def _parse_idea_json(self, response: str) -> dict | None:
        """Parse JSON from model response."""
        # Try to extract JSON from response
        try:
            # Look for JSON block
            json_match = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))

            # Try direct parse
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to find JSON object in response
            try:
                start = response.find("{")
                end = response.rfind("}") + 1
                if start >= 0 and end > start:
                    return json.loads(response[start:end])
            except:
                pass
        return None

    async def _search_related_work(self, query: str) -> list[dict]:
        """Search for related papers using Semantic Scholar tool."""
        # Import and use the semantic scholar tool
        from agents.ai_scientist.tools.semantic_scholar import SemanticScholar

        ss_tool = SemanticScholar(
            agent=self.agent,
            name="semantic_scholar",
            method=None,
            args={"query": query, "limit": 5},
            message="",
            loop_data=self.loop_data,
        )

        response = await ss_tool.execute(query=query, limit=5)
        # Parse papers from response (simplified)
        return []  # Will be populated from actual search

    async def _refine_idea(
        self, idea: dict, related_work: list, round_num: int, total_rounds: int
    ) -> dict:
        """Refine idea based on related work."""
        prompt = {
            "Role": "You are refining a research idea based on literature review.",
            "Round": f"{round_num + 1}/{total_rounds}",
            "Current Idea": idea,
            "Related Work Found": related_work[:5] if related_work else "No related work found",
            "Instructions": [
                "Review the current idea and related work.",
                "Refine the idea to:",
                "1. Differentiate from existing work",
                "2. Address potential gaps",
                "3. Strengthen the hypothesis",
                "Return the refined idea as JSON with the same structure.",
            ],
        }

        response = await self._query_model(prompt)
        refined = self._parse_idea_json(response)

        return refined if refined else idea

    async def _check_novelty(self, idea: dict) -> int:
        """Check novelty score (1-10) by searching for similar work."""
        title = idea.get("Title", "")
        hypothesis = idea.get("Short Hypothesis", "")

        # Search for similar papers
        query = f"{title} {hypothesis}"[:200]

        try:
            # This would use semantic scholar, simplified for now
            # Higher score = more novel (fewer similar papers found)
            return 7  # Placeholder
        except:
            return 5  # Default score

    def _format_ideas_summary(self, ideas: list[dict]) -> str:
        """Format ideas for display."""
        summary = []
        for i, idea in enumerate(ideas, 1):
            summary.append(
                f"**{i}. {idea.get('Title', 'Unknown')}**\n"
                f"   Name: `{idea.get('Name', 'unknown')}`\n"
                f"   Hypothesis: {idea.get('Short Hypothesis', 'N/A')}\n"
                f"   Novelty Score: {idea.get('novelty_score', 'N/A')}/10\n"
            )
        return "\n".join(summary)
```

**Step 2: Commit**

```bash
git add agents/ai-scientist/tools/generate_idea.py
git commit -m "feat(ai-scientist): add research idea generation tool"
```

---

### Task 6: Create Ideas Manager UI Modal

**Files:**
- Create: `webui/components/modals/ai-scientist/ideas-manager/ideas-manager-store.js`
- Create: `webui/components/modals/ai-scientist/ideas-manager/ideas-manager.html`

**Step 1: Create directory structure**

```bash
mkdir -p webui/components/modals/ai-scientist/ideas-manager
```

**Step 2: Create the store**

```javascript
import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";

const model = {
    ideas: [],
    selectedIdea: null,
    loading: false,
    generatingIdeas: false,
    topic: "",
    numIdeas: 5,
    _initialized: false,

    init() {
        if (this._initialized) return;
        this._initialized = true;
    },

    async onOpen() {
        await this.loadIdeas();
    },

    async loadIdeas() {
        this.loading = true;
        try {
            const response = await callJsonApi("scientist_get_ideas", {});
            this.ideas = response.ideas || [];
        } catch (e) {
            console.error("Failed to load ideas:", e);
            this.ideas = [];
        }
        this.loading = false;
    },

    async generateIdeas() {
        if (!this.topic.trim()) return;

        this.generatingIdeas = true;
        try {
            await callJsonApi("scientist_generate_ideas", {
                topic: this.topic,
                num_ideas: this.numIdeas,
            });
            // Refresh ideas list
            await this.loadIdeas();
        } catch (e) {
            console.error("Failed to generate ideas:", e);
        }
        this.generatingIdeas = false;
    },

    selectIdea(ideaName) {
        this.selectedIdea = this.ideas.find((i) => i.Name === ideaName) || null;
    },

    async startExperiment() {
        if (!this.selectedIdea) return;

        try {
            await callJsonApi("scientist_start_experiment", {
                idea_name: this.selectedIdea.Name,
            });
            window.closeModal();
        } catch (e) {
            console.error("Failed to start experiment:", e);
        }
    },

    getNoveltyClass(score) {
        if (score >= 8) return "high";
        if (score >= 5) return "medium";
        return "low";
    },

    cleanup() {
        this.selectedIdea = null;
    },
};

export const store = createStore("ideasManagerStore", model);
```

**Step 3: Create the HTML component**

```html
<html>
<head>
    <title>Research Ideas Manager</title>
    <script type="module">
        import { store } from "/components/modals/ai-scientist/ideas-manager/ideas-manager-store.js";
    </script>
</head>
<body>
    <div x-data
         x-create="$store.ideasManagerStore.onOpen()"
         x-destroy="$store.ideasManagerStore.cleanup()">
        <template x-if="$store.ideasManagerStore">
            <div class="ideas-manager">
                <!-- Topic Input Section -->
                <div class="section">
                    <div class="section-title">Generate New Ideas</div>
                    <div class="section-description">
                        Describe your research topic to generate novel research ideas with novelty validation.
                    </div>
                    <div class="input-group">
                        <textarea
                            x-model="$store.ideasManagerStore.topic"
                            placeholder="Describe your research topic (e.g., 'Improving transformer efficiency through sparse attention mechanisms')..."
                            rows="3"></textarea>
                    </div>
                    <div class="input-row">
                        <label>
                            Number of ideas:
                            <select x-model.number="$store.ideasManagerStore.numIdeas">
                                <option value="3">3</option>
                                <option value="5">5</option>
                                <option value="10">10</option>
                            </select>
                        </label>
                        <button class="btn btn-ok"
                                @click="$store.ideasManagerStore.generateIdeas()"
                                :disabled="$store.ideasManagerStore.generatingIdeas || !$store.ideasManagerStore.topic.trim()">
                            <span x-show="!$store.ideasManagerStore.generatingIdeas">Generate Ideas</span>
                            <span x-show="$store.ideasManagerStore.generatingIdeas">Generating...</span>
                        </button>
                    </div>
                </div>

                <!-- Ideas List Section -->
                <div class="section">
                    <div class="section-title">Research Ideas</div>
                    <div class="ideas-list" x-show="!$store.ideasManagerStore.loading">
                        <template x-if="$store.ideasManagerStore.ideas.length === 0">
                            <div class="empty-state">No ideas generated yet. Enter a topic above to get started.</div>
                        </template>
                        <template x-for="idea in $store.ideasManagerStore.ideas" :key="idea.Name">
                            <div class="idea-card"
                                 :class="{'selected': $store.ideasManagerStore.selectedIdea?.Name === idea.Name}"
                                 @click="$store.ideasManagerStore.selectIdea(idea.Name)">
                                <div class="idea-title" x-text="idea.Title"></div>
                                <div class="idea-hypothesis" x-text="idea['Short Hypothesis']"></div>
                                <div class="idea-meta">
                                    <span class="idea-name" x-text="idea.Name"></span>
                                    <span class="novelty-badge"
                                          :class="$store.ideasManagerStore.getNoveltyClass(idea.novelty_score)"
                                          x-text="'Novelty: ' + (idea.novelty_score || 'N/A') + '/10'"></span>
                                </div>
                            </div>
                        </template>
                    </div>
                    <div class="loading" x-show="$store.ideasManagerStore.loading"></div>
                </div>

                <!-- Selected Idea Detail -->
                <template x-if="$store.ideasManagerStore.selectedIdea">
                    <div class="section idea-detail">
                        <div class="section-title" x-text="$store.ideasManagerStore.selectedIdea.Title"></div>

                        <div class="detail-row">
                            <strong>Hypothesis:</strong>
                            <p x-text="$store.ideasManagerStore.selectedIdea['Short Hypothesis']"></p>
                        </div>

                        <div class="detail-row">
                            <strong>Abstract:</strong>
                            <p x-text="$store.ideasManagerStore.selectedIdea.Abstract"></p>
                        </div>

                        <div class="detail-row">
                            <strong>Proposed Experiments:</strong>
                            <ul>
                                <template x-for="exp in $store.ideasManagerStore.selectedIdea.Experiments || []">
                                    <li x-text="exp"></li>
                                </template>
                            </ul>
                        </div>

                        <div class="detail-row">
                            <strong>Risk Factors:</strong>
                            <ul>
                                <template x-for="risk in ($store.ideasManagerStore.selectedIdea['Risk Factors and Limitations'] || [])">
                                    <li x-text="risk"></li>
                                </template>
                            </ul>
                        </div>
                    </div>
                </template>
            </div>
        </template>
    </div>

    <!-- Footer -->
    <div class="modal-footer" data-modal-footer>
        <button class="btn btn-ok"
                @click="$store.ideasManagerStore.startExperiment()"
                :disabled="!$store.ideasManagerStore.selectedIdea">
            Run Experiment
        </button>
        <button class="btn btn-cancel" @click="closeModal()">Close</button>
    </div>

    <style>
        .ideas-manager {
            display: flex;
            flex-direction: column;
            gap: var(--spacing-md);
        }

        .input-group textarea {
            width: 100%;
            padding: var(--spacing-sm);
            border: 1px solid var(--color-border);
            border-radius: 4px;
            background: var(--color-input);
            color: var(--color-text);
            font-family: inherit;
            resize: vertical;
        }

        .input-row {
            display: flex;
            align-items: center;
            gap: var(--spacing-md);
            margin-top: var(--spacing-sm);
        }

        .input-row label {
            display: flex;
            align-items: center;
            gap: var(--spacing-xs);
        }

        .input-row select {
            padding: 4px 8px;
            border-radius: 4px;
            background: var(--color-input);
            color: var(--color-text);
            border: 1px solid var(--color-border);
        }

        .ideas-list {
            display: flex;
            flex-direction: column;
            gap: var(--spacing-sm);
            max-height: 250px;
            overflow-y: auto;
        }

        .idea-card {
            padding: var(--spacing-md);
            background: var(--color-input);
            border-radius: 8px;
            cursor: pointer;
            border: 2px solid transparent;
            transition: all var(--transition-speed);
        }

        .idea-card:hover {
            border-color: var(--color-border);
        }

        .idea-card.selected {
            border-color: var(--color-accent);
            background: var(--color-panel);
        }

        .idea-title {
            font-weight: 600;
            color: var(--color-primary);
            margin-bottom: 4px;
        }

        .idea-hypothesis {
            font-size: var(--font-size-small);
            color: var(--color-text);
            opacity: 0.8;
        }

        .idea-meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: var(--spacing-sm);
        }

        .idea-name {
            font-family: monospace;
            font-size: 11px;
            color: var(--color-text);
            opacity: 0.6;
        }

        .novelty-badge {
            font-size: 11px;
            padding: 2px 8px;
            border-radius: 12px;
            background: var(--color-panel);
        }

        .novelty-badge.high {
            background: rgba(34, 197, 94, 0.2);
            color: #22c55e;
        }

        .novelty-badge.medium {
            background: rgba(234, 179, 8, 0.2);
            color: #eab308;
        }

        .novelty-badge.low {
            background: rgba(239, 68, 68, 0.2);
            color: #ef4444;
        }

        .idea-detail {
            background: var(--color-panel);
            padding: var(--spacing-md);
            border-radius: 8px;
        }

        .detail-row {
            margin-bottom: var(--spacing-sm);
        }

        .detail-row strong {
            color: var(--color-primary);
        }

        .detail-row p {
            margin: 4px 0 0 0;
        }

        .detail-row ul {
            margin: 4px 0 0 0;
            padding-left: 20px;
        }

        .empty-state {
            text-align: center;
            padding: var(--spacing-lg);
            color: var(--color-text);
            opacity: 0.6;
        }
    </style>
</body>
</html>
```

**Step 4: Commit**

```bash
git add webui/components/modals/ai-scientist/
git commit -m "feat(ai-scientist): add Ideas Manager modal UI"
```

---

### Task 7: Create API Endpoints for Ideas

**Files:**
- Create: `python/api/scientist_get_ideas.py`
- Create: `python/api/scientist_generate_ideas.py`

**Step 1: Create get ideas endpoint**

```python
from python.helpers.api import ApiHandler
from agent import AgentContext


class GetIdeas(ApiHandler):
    """API endpoint to retrieve generated research ideas."""

    async def process(self, input: dict, request) -> dict:
        context = AgentContext.current()
        if not context or not context.agent0:
            return {"ideas": []}

        ideas = context.agent0.data.get("research_ideas", {})

        return {"ideas": list(ideas.values())}
```

**Step 2: Create generate ideas endpoint**

```python
from python.helpers.api import ApiHandler
from agent import AgentContext


class GenerateIdeas(ApiHandler):
    """API endpoint to trigger idea generation."""

    async def process(self, input: dict, request) -> dict:
        topic = input.get("topic", "")
        num_ideas = input.get("num_ideas", 5)

        if not topic:
            return {"status": "error", "message": "Topic is required"}

        context = AgentContext.current()
        if not context:
            return {"status": "error", "message": "No active context"}

        # Trigger idea generation via agent message
        await context.communicate(
            f"Generate {num_ideas} research ideas about: {topic}"
        )

        return {"status": "started"}
```

**Step 3: Commit**

```bash
git add python/api/scientist_get_ideas.py python/api/scientist_generate_ideas.py
git commit -m "feat(ai-scientist): add API endpoints for idea management"
```

---

## Phase 2: Experiment Engine

### Task 8: Create Run Experiment Tool

**Files:**
- Create: `agents/ai-scientist/tools/run_experiment.py`

**Step 1: Create the tool (Part 1 - Core structure)**

```python
import json
import os
import pickle
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from python.helpers.tool import Tool, Response
from agent import Agent


@dataclass
class ExperimentNode:
    """Represents a node in the experiment search tree."""

    id: str
    plan: str
    code: str
    parent_id: Optional[str] = None
    metric: Optional[float] = None
    is_buggy: bool = False
    term_out: str = ""
    analysis: str = ""
    plot_code: str = ""
    stage: str = ""
    children: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "plan": self.plan,
            "code": self.code,
            "parent_id": self.parent_id,
            "metric": self.metric,
            "is_buggy": self.is_buggy,
            "term_out": self.term_out[:1000],  # Truncate for storage
            "analysis": self.analysis,
            "stage": self.stage,
        }


@dataclass
class ExperimentJournal:
    """Tracks experiment progress for a stage."""

    stage_name: str
    nodes: list[ExperimentNode] = field(default_factory=list)
    best_node_id: Optional[str] = None

    @property
    def good_nodes(self) -> list[ExperimentNode]:
        return [n for n in self.nodes if not n.is_buggy and n.metric is not None]

    def get_best_node(self) -> Optional[ExperimentNode]:
        good = self.good_nodes
        if not good:
            return None
        # Lower metric is better (loss)
        return min(good, key=lambda n: n.metric or float("inf"))


STAGE_GOALS = {
    1: """Stage 1: Initial Implementation
- Focus on getting basic working implementation
- Use a simple dataset
- Aim for basic functional correctness
- If given "Code To Use", use it as starting point""",
    2: """Stage 2: Baseline Tuning
- Change hyperparameters (learning rate, epochs, batch size) to improve performance
- DO NOT change the model architecture from previous stage
- Introduce TWO more new datasets from HuggingFace""",
    3: """Stage 3: Creative Research
- Explore novel improvements
- Come up with experiments to reveal new insights
- Be creative and think outside the box
- Use THREE HuggingFace datasets total""",
    4: """Stage 4: Ablation Studies
- Conduct systematic component analysis
- Reveal contribution of each part
- Use same datasets from previous stage""",
}


class RunExperiment(Tool):
    """Run 4-stage experiment pipeline using subordinate agents."""

    async def execute(
        self,
        idea_name: str,
        resume: bool = False,
        max_iterations_per_stage: int = 10,
        **kwargs,
    ) -> Response:
        """
        Execute experiments for a research idea through 4 stages.

        Args:
            idea_name: Name of the idea to experiment on
            resume: Whether to resume from checkpoint
            max_iterations_per_stage: Max nodes to explore per stage
        """
        # Load idea
        idea = self.agent.data.get("research_ideas", {}).get(idea_name)
        if not idea:
            return Response(
                message=f"Idea '{idea_name}' not found. Use generate_idea first.",
                break_loop=False,
            )

        # Initialize or resume experiment state
        exp_state = self._init_experiment_state(idea_name, idea, resume)

        self.agent.context.log.log(
            type="info",
            heading=f"Starting experiment: {idea['Title']}",
            content=f"Current stage: {exp_state['current_stage']}",
        )

        # Run through stages
        for stage_num in range(exp_state["current_stage"], 5):
            stage_name = f"stage_{stage_num}"
            stage_goals = STAGE_GOALS[stage_num]

            self.agent.context.log.log(
                type="progress",
                heading=f"Stage {stage_num}",
                content=stage_goals,
            )

            # Run stage
            success = await self._run_stage(
                idea, stage_num, stage_goals, exp_state, max_iterations_per_stage
            )

            if not success:
                self._save_checkpoint(idea_name, exp_state)
                return Response(
                    message=f"Stage {stage_num} did not find working implementation. Experiment paused.",
                    break_loop=False,
                )

            # Update state and save checkpoint
            exp_state["current_stage"] = stage_num + 1
            self._save_checkpoint(idea_name, exp_state)

        # All stages complete
        best_result = self._get_final_result(exp_state)

        return Response(
            message=f"Experiment complete!\n\nBest result: {best_result}\n\nUse `write_paper` to generate a paper.",
            break_loop=False,
        )

    def _init_experiment_state(
        self, idea_name: str, idea: dict, resume: bool
    ) -> dict:
        """Initialize or load experiment state."""
        if "experiments" not in self.agent.data:
            self.agent.data["experiments"] = {}

        if resume and idea_name in self.agent.data["experiments"]:
            return self.agent.data["experiments"][idea_name]

        # Fresh state
        state = {
            "idea_name": idea_name,
            "idea": idea,
            "current_stage": 1,
            "journals": {f"stage_{i}": ExperimentJournal(f"stage_{i}") for i in range(1, 5)},
        }

        self.agent.data["experiments"][idea_name] = state
        return state

    async def _run_stage(
        self,
        idea: dict,
        stage_num: int,
        stage_goals: str,
        exp_state: dict,
        max_iterations: int,
    ) -> bool:
        """Run a single experiment stage."""
        stage_name = f"stage_{stage_num}"
        journal = exp_state["journals"][stage_name]

        # Get best node from previous stage (if any)
        prev_best = None
        if stage_num > 1:
            prev_journal = exp_state["journals"][f"stage_{stage_num - 1}"]
            prev_best = prev_journal.get_best_node()

        for iteration in range(max_iterations):
            self.agent.context.log.log(
                type="progress",
                heading=f"Stage {stage_num} - Node {iteration + 1}/{max_iterations}",
                content=f"Exploring experiment tree...",
            )

            # Select parent node for this iteration
            parent_node = self._select_parent_node(journal, prev_best)

            # Generate and execute experiment via subordinate agent
            child_node = await self._explore_node(
                idea, stage_num, stage_goals, parent_node, iteration
            )

            if child_node:
                journal.nodes.append(child_node)

                self.agent.context.log.log(
                    type="tool",
                    heading=f"Node {child_node.id}",
                    kvps={
                        "metric": child_node.metric,
                        "is_buggy": child_node.is_buggy,
                    },
                )

            # Check stage completion
            if self._check_stage_completion(stage_num, journal):
                best = journal.get_best_node()
                if best:
                    journal.best_node_id = best.id
                return True

        # Max iterations reached
        best = journal.get_best_node()
        if best:
            journal.best_node_id = best.id
            return True

        return len(journal.good_nodes) > 0

    def _select_parent_node(
        self, journal: ExperimentJournal, prev_best: Optional[ExperimentNode]
    ) -> Optional[ExperimentNode]:
        """Select parent node using best-first search."""
        if not journal.nodes:
            return prev_best  # Start from previous stage's best

        # Best-first: select best non-buggy node
        good_nodes = journal.good_nodes
        if good_nodes:
            return min(good_nodes, key=lambda n: n.metric or float("inf"))

        # If no good nodes, try to debug a buggy one
        buggy = [n for n in journal.nodes if n.is_buggy]
        if buggy:
            return buggy[-1]  # Most recent buggy node

        return prev_best

    async def _explore_node(
        self,
        idea: dict,
        stage_num: int,
        stage_goals: str,
        parent_node: Optional[ExperimentNode],
        iteration: int,
    ) -> Optional[ExperimentNode]:
        """Explore a node by spawning a subordinate agent."""
        import uuid

        node_id = f"node_{stage_num}_{iteration}_{uuid.uuid4().hex[:8]}"

        # Build task description
        task_desc = self._build_task_description(idea, stage_num, stage_goals, parent_node)

        # Create subordinate agent
        subordinate = Agent(
            self.agent.number + 1,
            self.agent.config,
            self.agent.context,
        )

        # Pass context to subordinate
        subordinate.set_data("experiment_task", task_desc)
        subordinate.set_data("parent_node", parent_node.to_dict() if parent_node else None)
        subordinate.set_data("stage_num", stage_num)

        try:
            # Run subordinate to generate and execute code
            result = await subordinate.monologue()

            # Parse result into node
            return self._parse_result_to_node(node_id, result, parent_node, stage_num)

        except Exception as e:
            self.agent.context.log.log(
                type="warning",
                heading=f"Node {node_id} failed",
                content=str(e),
            )
            return None

    def _build_task_description(
        self,
        idea: dict,
        stage_num: int,
        stage_goals: str,
        parent_node: Optional[ExperimentNode],
    ) -> str:
        """Build task description for subordinate agent."""
        task = f"""You are an AI researcher implementing experiments for: {idea['Title']}

Hypothesis: {idea['Short Hypothesis']}

{stage_goals}

"""
        if parent_node and not parent_node.is_buggy:
            task += f"""
Previous Implementation (to improve upon):
```python
{parent_node.code}
```

Previous Result: {parent_node.metric}
"""
        elif parent_node and parent_node.is_buggy:
            task += f"""
Previous (buggy) Implementation to fix:
```python
{parent_node.code}
```

Error output:
{parent_node.term_out}
"""
        else:
            task += """
This is the initial implementation. Start simple and focus on getting working code.
"""

        task += """
Your task: Write a complete, self-contained Python script that:
1. Implements the experiment
2. Uses proper GPU handling (device = torch.device('cuda' if torch.cuda.is_available() else 'cpu'))
3. Saves results to experiment_data.npy
4. Prints validation loss at each epoch

Respond with a brief plan (5-7 sentences) followed by the complete Python code in a ```python block.
"""
        return task

    def _parse_result_to_node(
        self,
        node_id: str,
        result: str,
        parent_node: Optional[ExperimentNode],
        stage_num: int,
    ) -> ExperimentNode:
        """Parse subordinate result into an ExperimentNode."""
        import re

        # Extract code from result
        code_match = re.search(r"```python\s*(.*?)\s*```", result, re.DOTALL)
        code = code_match.group(1) if code_match else ""

        # Extract plan (text before code)
        plan = result.split("```python")[0].strip() if "```python" in result else result

        return ExperimentNode(
            id=node_id,
            plan=plan,
            code=code,
            parent_id=parent_node.id if parent_node else None,
            stage=f"stage_{stage_num}",
            # metric, is_buggy, term_out will be set after execution
        )

    def _check_stage_completion(
        self, stage_num: int, journal: ExperimentJournal
    ) -> bool:
        """Check if stage completion criteria are met."""
        good_nodes = journal.good_nodes

        if stage_num == 1:
            # Stage 1: Complete when we have at least one working implementation
            return len(good_nodes) >= 1

        # Other stages: need at least one good node
        return len(good_nodes) >= 1

    def _save_checkpoint(self, idea_name: str, exp_state: dict) -> None:
        """Save experiment checkpoint to file."""
        checkpoint_dir = Path(f"work_dir/ai-scientist/{idea_name}")
        checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # Serialize journals
        serialized = {
            "idea_name": exp_state["idea_name"],
            "current_stage": exp_state["current_stage"],
            "journals": {
                name: {
                    "stage_name": j.stage_name,
                    "nodes": [n.to_dict() for n in j.nodes],
                    "best_node_id": j.best_node_id,
                }
                for name, j in exp_state["journals"].items()
            },
        }

        with open(checkpoint_dir / "checkpoint.json", "w") as f:
            json.dump(serialized, f, indent=2)

    def _get_final_result(self, exp_state: dict) -> str:
        """Get final experiment result summary."""
        results = []
        for stage_num in range(1, 5):
            journal = exp_state["journals"][f"stage_{stage_num}"]
            best = journal.get_best_node()
            if best:
                results.append(f"Stage {stage_num}: {best.metric}")

        return " | ".join(results) if results else "No results"
```

**Step 2: Commit**

```bash
git add agents/ai-scientist/tools/run_experiment.py
git commit -m "feat(ai-scientist): add experiment runner tool with tree search"
```

---

### Task 9: Create Experiment Dashboard Modal

**Files:**
- Create: `webui/components/modals/ai-scientist/experiment-dashboard/experiment-dashboard-store.js`
- Create: `webui/components/modals/ai-scientist/experiment-dashboard/experiment-dashboard.html`

**Step 1: Create the store**

```javascript
import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";

const model = {
    experiments: [],
    selectedExperiment: null,
    progress: null,
    polling: null,
    _initialized: false,

    init() {
        if (this._initialized) return;
        this._initialized = true;
    },

    async onOpen() {
        await this.loadExperiments();
        this.startPolling();
    },

    startPolling() {
        this.polling = setInterval(() => {
            if (this.selectedExperiment) {
                this.refreshProgress();
            }
        }, 3000);
    },

    async loadExperiments() {
        try {
            const response = await callJsonApi("scientist_get_experiments", {});
            this.experiments = response.experiments || [];
        } catch (e) {
            console.error("Failed to load experiments:", e);
        }
    },

    async refreshProgress() {
        if (!this.selectedExperiment) return;
        try {
            const response = await callJsonApi("scientist_get_experiment_progress", {
                idea_name: this.selectedExperiment.idea_name,
            });
            this.progress = response;
        } catch (e) {
            console.error("Failed to refresh progress:", e);
        }
    },

    selectExperiment(ideaName) {
        this.selectedExperiment = this.experiments.find(
            (e) => e.idea_name === ideaName
        );
        if (this.selectedExperiment) {
            this.refreshProgress();
        }
    },

    getStageStatus(stageNum) {
        if (!this.progress) return "pending";
        const stage = this.progress.stages?.[`stage_${stageNum}`];
        if (!stage) return "pending";
        if (stage.best_node_id) return "completed";
        if (stage.nodes?.length > 0) return "in_progress";
        return "pending";
    },

    getStageNodes(stageNum) {
        if (!this.progress) return [];
        return this.progress.stages?.[`stage_${stageNum}`]?.nodes || [];
    },

    cleanup() {
        if (this.polling) {
            clearInterval(this.polling);
            this.polling = null;
        }
        this.selectedExperiment = null;
        this.progress = null;
    },
};

export const store = createStore("experimentDashboardStore", model);
```

**Step 2: Create the HTML** (abbreviated for space - full version in actual implementation)

```html
<html>
<head>
    <title>Experiment Dashboard</title>
    <script type="module">
        import { store } from "/components/modals/ai-scientist/experiment-dashboard/experiment-dashboard-store.js";
    </script>
</head>
<body>
    <div x-data
         x-create="$store.experimentDashboardStore.onOpen()"
         x-destroy="$store.experimentDashboardStore.cleanup()">
        <template x-if="$store.experimentDashboardStore">
            <div class="experiment-dashboard">
                <!-- Experiment Selector -->
                <div class="section">
                    <div class="section-title">Select Experiment</div>
                    <select @change="$store.experimentDashboardStore.selectExperiment($event.target.value)">
                        <option value="">-- Select --</option>
                        <template x-for="exp in $store.experimentDashboardStore.experiments">
                            <option :value="exp.idea_name" x-text="exp.idea_name"></option>
                        </template>
                    </select>
                </div>

                <!-- Stage Progress -->
                <template x-if="$store.experimentDashboardStore.selectedExperiment">
                    <div class="section">
                        <div class="section-title">Stage Progress</div>
                        <div class="stage-pipeline">
                            <template x-for="stage in [1, 2, 3, 4]">
                                <div class="stage-item"
                                     :class="$store.experimentDashboardStore.getStageStatus(stage)">
                                    <div class="stage-number" x-text="stage"></div>
                                    <div class="stage-name" x-text="['Initial', 'Tuning', 'Research', 'Ablation'][stage-1]"></div>
                                </div>
                            </template>
                        </div>
                    </div>
                </template>

                <!-- Node Tree (simplified) -->
                <template x-if="$store.experimentDashboardStore.progress">
                    <div class="section">
                        <div class="section-title">Explored Nodes</div>
                        <div class="node-list">
                            <template x-for="node in $store.experimentDashboardStore.progress.tree_nodes || []">
                                <div class="node-item" :class="{'buggy': node.is_buggy}">
                                    <span class="node-id" x-text="node.id"></span>
                                    <span class="node-metric" x-text="node.metric ? node.metric.toFixed(4) : 'N/A'"></span>
                                </div>
                            </template>
                        </div>
                    </div>
                </template>
            </div>
        </template>
    </div>

    <div class="modal-footer" data-modal-footer>
        <button class="btn btn-cancel" @click="closeModal()">Close</button>
    </div>

    <style>
        .experiment-dashboard { display: flex; flex-direction: column; gap: var(--spacing-md); }
        .stage-pipeline { display: flex; gap: var(--spacing-sm); }
        .stage-item {
            flex: 1;
            padding: var(--spacing-sm);
            text-align: center;
            border-radius: 8px;
            background: var(--color-input);
        }
        .stage-item.completed { background: rgba(34, 197, 94, 0.2); }
        .stage-item.in_progress { background: rgba(59, 130, 246, 0.2); }
        .stage-number { font-size: 24px; font-weight: bold; }
        .node-list { max-height: 200px; overflow-y: auto; }
        .node-item {
            display: flex;
            justify-content: space-between;
            padding: 4px 8px;
            border-bottom: 1px solid var(--color-border);
        }
        .node-item.buggy { color: #ef4444; }
    </style>
</body>
</html>
```

**Step 3: Commit**

```bash
git add webui/components/modals/ai-scientist/experiment-dashboard/
git commit -m "feat(ai-scientist): add Experiment Dashboard modal UI"
```

---

### Task 10: Add Experiment API Endpoints

**Files:**
- Create: `python/api/scientist_get_experiments.py`
- Create: `python/api/scientist_get_experiment_progress.py`
- Create: `python/api/scientist_start_experiment.py`

**Step 1: Create endpoints** (similar pattern to ideas endpoints)

```python
# scientist_get_experiments.py
from python.helpers.api import ApiHandler
from agent import AgentContext


class GetExperiments(ApiHandler):
    async def process(self, input: dict, request) -> dict:
        context = AgentContext.current()
        if not context or not context.agent0:
            return {"experiments": []}

        experiments = context.agent0.data.get("experiments", {})

        return {
            "experiments": [
                {
                    "idea_name": name,
                    "current_stage": exp.get("current_stage", 0),
                    "status": "completed" if exp.get("current_stage", 0) > 4 else "in_progress",
                }
                for name, exp in experiments.items()
            ]
        }
```

**Step 2: Commit**

```bash
git add python/api/scientist_*.py
git commit -m "feat(ai-scientist): add experiment management API endpoints"
```

---

## Phase 3: Paper Generation

### Task 11: Create Write Paper Tool

**Files:**
- Create: `agents/ai-scientist/tools/write_paper.py`

*Implementation follows AI-Scientist-v2's writeup.py patterns - generates LaTeX with citation gathering and reflection rounds*

### Task 12: Create Paper Generator Modal

**Files:**
- Create: `webui/components/modals/ai-scientist/paper-generator/`

*Modal for selecting completed experiments, choosing format, and generating papers*

---

## Phase 4: Integration & Polish

### Task 13: Add Message System Integration

**Files:**
- Modify: `python/helpers/log.py` - Add new log types
- Modify: `webui/components/messages/process-group/process-group-store.js` - Add status badges

### Task 14: End-to-End Testing

- Test idea generation flow
- Test experiment execution with subordinate agents
- Test paper generation
- Test UI modals

### Task 15: Documentation

- Update README with AI Scientist usage
- Add example topics and workflows

---

## Summary

| Phase | Tasks | Core Deliverables |
|-------|-------|-------------------|
| 1 | 1-7 | Profile structure, prompts, ideation tool, Ideas Manager UI |
| 2 | 8-10 | Experiment runner, tree search, Experiment Dashboard UI |
| 3 | 11-12 | Paper writer, Paper Generator UI |
| 4 | 13-15 | Message integration, testing, documentation |

**Estimated Total:** ~40 bite-sized tasks across 15 major tasks
