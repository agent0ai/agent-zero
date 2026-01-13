import json
import os
import pickle
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from python.helpers.tool import Tool, Response
from agent import Agent, UserMessage


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

        # Register superior/subordinate relationship
        subordinate.set_data(Agent.DATA_NAME_SUPERIOR, self.agent)
        self.agent.set_data(Agent.DATA_NAME_SUBORDINATE, subordinate)

        # Pass context to subordinate via proper user message
        subordinate.set_data("parent_node", parent_node.to_dict() if parent_node else None)
        subordinate.set_data("stage_num", stage_num)
        subordinate.hist_add_user_message(UserMessage(message=task_desc, attachments=[]))

        try:
            # Run subordinate to generate and execute code
            result = await subordinate.monologue()

            # Parse result into node
            node = self._parse_result_to_node(node_id, result, parent_node, stage_num)

            # Execute the generated code
            if node.code:
                await self._execute_code(node.code, node)

            return node

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

    async def _execute_code(self, code: str, node: ExperimentNode) -> None:
        """Execute experiment code and update node with results."""
        import re

        try:
            # Use agent's code execution capability
            code_tool = self.agent.get_tool(
                name="code_execution_tool",
                method=None,
                args={"runtime": "python", "code": code},
                message="",
                loop_data=None,
            )

            if code_tool:
                response = await code_tool.execute(runtime="python", code=code)
                output = response.message if hasattr(response, "message") else str(response)

                node.term_out = output

                # Check for errors in output
                if "error" in output.lower() or "traceback" in output.lower():
                    node.is_buggy = True
                else:
                    node.is_buggy = False
                    # Try to extract metric (validation loss) from output
                    loss_match = re.search(
                        r"(?:val[_\s]?loss|validation[_\s]?loss)[:\s]+([0-9.]+)",
                        output.lower(),
                    )
                    if loss_match:
                        node.metric = float(loss_match.group(1))
        except Exception as e:
            node.is_buggy = True
            node.term_out = str(e)

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
