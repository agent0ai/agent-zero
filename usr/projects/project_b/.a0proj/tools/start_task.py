import importlib.util
import inspect
import os
import json
import shutil
from datetime import datetime
from typing import Any
from python.helpers.tool import Tool, Response
from python.helpers import files, projects
import models


def _safe_score(value: Any) -> float:
    """Coerce a value to a float score, defaulting to 0.0."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _kwarg_or(kwargs: dict[str, Any], key: str, default: Any) -> Any:
    """Return kwargs[key] if present and not None, else default."""
    value = kwargs.get(key)
    return value if value is not None else default


class StartTask(Tool):
    """Tool for Agent 0 to start benchmark tasks or task sets."""

    async def execute(self, **kwargs) -> Response:
        if self.agent.number != 0:
            return Response(
                message="This tool is only available to Agent 0.",
                break_loop=False
            )

        task_names = kwargs.get("task_names", [])
        task_name = kwargs.get("task_name", "")
        task_set_file = kwargs.get("task_set", "")
        agent_profile = kwargs.get("agent_profile", "")

        if task_name and not task_names:
            task_names = [task_name]

        score_multipliers: dict[str, float] = {}
        if task_set_file:
            task_names, score_multipliers = await self._load_task_set(task_set_file)

        if not task_names:
            return Response(
                message="No task(s) specified. Provide task_name, task_names array, or task_set file.",
                break_loop=False
            )

        model_config = self._build_model_config(kwargs)

        if len(task_names) == 1:
            result = await self._run_single_task(
                task_name=task_names[0],
                model_config=model_config,
                score_multiplier=score_multipliers.get(task_names[0], 1.0),
                agent_profile=agent_profile,
            )
            return Response(message=self._format_single_result(result), break_loop=False)

        results = await self._run_task_set(
            task_names=task_names,
            model_config=model_config,
            score_multipliers=score_multipliers,
            agent_profile=agent_profile,
        )
        return Response(message=self._format_set_results(results), break_loop=False)

    async def _load_task_set(self, set_file: str) -> tuple[list[str], dict[str, float]]:
        """Load task set from JSON file."""
        project_dir = self._get_project_dir()
        set_path = os.path.join(project_dir, "task_sets", set_file)

        if not os.path.exists(set_path):
            set_path = set_file

        with open(set_path, 'r') as f:
            data = json.load(f)

        task_names: list[str] = []
        multipliers: dict[str, float] = {}

        for item in data:
            if isinstance(item, str):
                task_names.append(item)
                multipliers[item] = 1.0
            elif isinstance(item, dict):
                name = str(item.get("task_name", item.get("name", ""))).strip()
                if not name:
                    continue
                task_names.append(name)
                multipliers[name] = _safe_score(item.get("score_multiplier", 1.0)) or 1.0

        return task_names, multipliers

    def _build_model_config(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        """Build model configuration from kwargs or use current settings."""
        cfg = self.agent.config.chat_model
        return {
            "provider": _kwarg_or(kwargs, "chat_model_provider", cfg.provider),
            "name": _kwarg_or(kwargs, "chat_model_name", cfg.name),
            "api_endpoint": (
                kwargs.get("chat_model_api_endpoint")
                or kwargs.get("chat_model_api_base")
                or cfg.api_base
            ),
            "ctx_length": _kwarg_or(kwargs, "chat_model_context_size", cfg.ctx_length),
            "vision": _kwarg_or(kwargs, "chat_model_vision_enabled", cfg.vision),
            "kwargs": _kwarg_or(kwargs, "chat_model_kwargs", cfg.kwargs),
        }

    def _get_project_name(self) -> str:
        project_name = projects.get_context_project_name(self.agent.context)
        if not project_name:
            raise RuntimeError("No active project in context.")
        return project_name

    def _get_project_dir(self) -> str:
        return projects.get_project_folder(self._get_project_name())

    def _next_number_in_dir(self, directory: str, extract_number) -> int:
        """Scan directory entries, extract numbers via callback, return max+1 (or 1)."""
        os.makedirs(directory, exist_ok=True)
        nums = [n for name in os.listdir(directory) if (n := extract_number(name)) is not None]
        return (max(nums) + 1) if nums else 1

    def _get_next_exec_number(self, kind: str) -> int:
        project_dir = self._get_project_dir()

        if kind == "run":
            return self._next_number_in_dir(
                os.path.join(project_dir, "run"),
                lambda name: int(name) if name.isdigit() else None,
            )

        if kind in ("task", "set"):
            prefix = f"{kind}-"
            def extract(name: str) -> int | None:
                if name.startswith(prefix) and name.endswith(".json"):
                    raw = name[len(prefix):-5]
                    return int(raw) if raw.isdigit() else None
                return None
            return self._next_number_in_dir(
                os.path.join(project_dir, "results"),
                extract,
            )

        raise ValueError(f"Unknown execution kind: {kind}")

    def _make_parameters(self, model_config: dict[str, Any], agent_profile: str, **extra: Any) -> dict[str, Any]:
        """Build the parameters sub-dict shared by single tasks and task sets."""
        params = {
            "agent_profile": agent_profile or self.agent.config.profile,
            "chat_model_provider": model_config["provider"],
            "chat_model_name": model_config["name"],
            "chat_model_api_endpoint": model_config["api_endpoint"],
            "chat_model_context_size": model_config["ctx_length"],
            "chat_model_vision_enabled": model_config["vision"],
            "chat_model_kwargs": model_config["kwargs"],
        }
        params.update(extra)
        return params

    def _save_json(self, path: str, data: dict[str, Any]) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=True, default=str)

    async def _run_single_task(
        self,
        task_name: str,
        model_config: dict[str, Any],
        score_multiplier: float = 1.0,
        agent_profile: str = "",
    ) -> dict[str, Any]:
        project_dir = self._get_project_dir()
        task_dir = os.path.join(project_dir, "tasks", task_name)

        if not os.path.exists(task_dir):
            return {"task_name": task_name, "error": f"Task '{task_name}' not found"}

        run_no = self._get_next_exec_number("run")
        run_dir = os.path.join(project_dir, "run", str(run_no))
        os.makedirs(run_dir, exist_ok=True)

        assets_dir = os.path.join(task_dir, "assets")
        if os.path.isdir(assets_dir):
            shutil.copytree(assets_dir, run_dir, dirs_exist_ok=True)

        state: dict[str, Any] = {
            "task_name": task_name,
            "run_number": run_no,
            "run_dir": run_dir,
            "started_at": datetime.now().isoformat(),
            "parameters": self._make_parameters(
                model_config, agent_profile, score_multiplier=score_multiplier,
            ),
            "instructions": "",
            "initialize_output": None,
            "subordinate_response": None,
            "evaluation": None,
            "stats": {
                "llm_calls": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "reasoning_tokens": 0,
                "timestamps": [],
            },
        }

        self.agent.context.set_data("benchmark_project_state", state)

        try:
            instructions_path = os.path.join(task_dir, "instructions.md")
            if os.path.exists(instructions_path):
                state["instructions"] = files.read_prompt_file(instructions_path)
            else:
                state["instructions"] = f"Complete the task in directory: {run_dir}"

            state["initialize_output"] = await self._execute_task_script(
                script_path=os.path.join(task_dir, "initialize.py"),
                runtime_path=run_dir,
                state=state,
                optional=True,
            )

            state["subordinate_response"] = await self._call_subordinate(
                instructions=state["instructions"],
                model_config=model_config,
                run_dir=run_dir,
                agent_profile=agent_profile,
            )

            evaluation = await self._execute_task_script(
                script_path=os.path.join(task_dir, "evaluate.py"),
                runtime_path=run_dir,
                state=state,
                optional=False,
            )
            if not isinstance(evaluation, dict):
                evaluation = {"score": 0, "error": "evaluate.py returned non-dict output"}

            score = max(0.0, min(100.0, _safe_score(evaluation.get("score", 0))))
            evaluation["score"] = score
            evaluation["weighted_score"] = score * score_multiplier
            state["evaluation"] = evaluation
            state["completed_at"] = datetime.now().isoformat()

            task_no = self._get_next_exec_number("task")
            result_path = os.path.join(project_dir, "results", f"task-{task_no}.json")
            self._save_json(result_path, state)
            state["result_file"] = result_path

            return state

        finally:
            self.agent.context.set_data("benchmark_project_state", None)

    async def _run_task_set(
        self,
        task_names: list[str],
        model_config: dict[str, Any],
        score_multipliers: dict[str, float],
        agent_profile: str = "",
    ) -> dict[str, Any]:
        project_dir = self._get_project_dir()
        set_no = self._get_next_exec_number("set")
        result_path = os.path.join(project_dir, "results", f"set-{set_no}.json")

        results: dict[str, Any] = {
            "set_number": set_no,
            "started_at": datetime.now().isoformat(),
            "parameters": self._make_parameters(model_config, agent_profile),
            "tasks": [],
            "task_states": [],
            "total_weighted_score": 0.0,
            "max_possible_weighted_score": 0.0,
            "weighted_average": 0.0,
        }

        for task_name in task_names:
            multiplier = float(score_multipliers.get(task_name, 1.0))
            task_state = await self._run_single_task(
                task_name=task_name,
                model_config=model_config,
                score_multiplier=multiplier,
                agent_profile=agent_profile,
            )
            results["task_states"].append(task_state)

            eval_data = task_state.get("evaluation") or {}
            score = _safe_score(eval_data.get("score", 0))
            weighted = _safe_score(eval_data.get("weighted_score", score * multiplier))

            results["tasks"].append({
                "task_name": task_name,
                "score_multiplier": multiplier,
                "score": score,
                "weighted_score": weighted,
                "error": task_state.get("error") or eval_data.get("error"),
                "comment": eval_data.get("comment"),
                "result_file": task_state.get("result_file"),
                "stats": task_state.get("stats", {}),
            })

            results["total_weighted_score"] += weighted
            results["max_possible_weighted_score"] += 100.0 * multiplier
            results["weighted_average"] = (
                results["total_weighted_score"] / results["max_possible_weighted_score"]
            ) * 100.0

            self._save_json(result_path, results)

        results["completed_at"] = datetime.now().isoformat()
        results["result_file"] = result_path
        self._save_json(result_path, results)

        return results

    async def _execute_task_script(
        self,
        script_path: str,
        runtime_path: str,
        state: dict[str, Any],
        optional: bool = False,
    ) -> Any:
        """Load and run a task script's execute() function.

        Each task script (initialize.py, evaluate.py) exposes:
            def execute(runtime_path: str, agent, state: dict) -> dict
        The function may also be async.
        """
        if not os.path.isfile(script_path):
            if optional:
                return None
            raise FileNotFoundError(f"Required task script not found: {script_path}")

        spec = importlib.util.spec_from_file_location("task_script", script_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load script: {script_path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        execute_fn = getattr(module, "execute", None)
        if execute_fn is None:
            raise AttributeError(f"Script missing execute() function: {script_path}")

        if inspect.iscoroutinefunction(execute_fn):
            return await execute_fn(runtime_path, self.agent, state)
        return execute_fn(runtime_path, self.agent, state)

    async def _call_subordinate(
        self,
        instructions: str,
        model_config: dict[str, Any],
        run_dir: str,
        agent_profile: str = "",
    ) -> str:
        from agent import Agent, AgentConfig, UserMessage

        sub_chat_model = models.ModelConfig(
            type=models.ModelType.CHAT,
            provider=model_config["provider"],
            name=model_config["name"],
            api_base=model_config.get("api_endpoint", ""),
            ctx_length=model_config.get("ctx_length", 8192),
            vision=model_config.get("vision", False),
            kwargs=model_config.get("kwargs", {}),
        )

        sub_config = AgentConfig(
            chat_model=sub_chat_model,
            utility_model=self.agent.config.utility_model,
            embeddings_model=self.agent.config.embeddings_model,
            browser_model=self.agent.config.browser_model,
            mcp_servers=self.agent.config.mcp_servers,
            profile=agent_profile or self.agent.config.profile,
        )

        subordinate = Agent(
            number=self.agent.number + 1,
            config=sub_config,
            context=self.agent.context,
        )

        subordinate.set_data(Agent.DATA_NAME_SUPERIOR, self.agent)
        self.agent.set_data(Agent.DATA_NAME_SUBORDINATE, subordinate)

        message = f"Working directory: {run_dir}\n\n{instructions}"
        subordinate.hist_add_user_message(UserMessage(message=message, attachments=[]))

        try:
            response = await subordinate.monologue()
            subordinate.history.new_topic()
            return response
        finally:
            self.agent.set_data(Agent.DATA_NAME_SUBORDINATE, None)

    def _format_single_result(self, result: dict) -> str:
        """Format single task result for Agent 0."""
        if result.get("error") and not result.get("evaluation"):
            return f"Task failed: {result['error']}"

        eval_data = result.get("evaluation") or {}
        score = _safe_score(eval_data.get("score", 0))
        stats = result.get("stats") or {}

        lines = [
            f"## Task Complete: {result.get('task_name', 'Unknown')}",
            "",
            f"**Score: {score:.1f}/100**",
            "",
            "### Stats",
            f"- LLM Calls: {stats.get('llm_calls', 0)}",
            f"- Input Tokens: {stats.get('input_tokens', 0)}",
            f"- Output Tokens: {stats.get('output_tokens', 0)}",
            f"- Reasoning Tokens: {stats.get('reasoning_tokens', 0)}",
            "",
            "### Evaluation Details",
        ]

        for key, value in eval_data.items():
            if key not in ("score", "weighted_score"):
                lines.append(f"- {key}: {value}")

        lines.append("")
        lines.append(f"Full results: {result.get('result_file', 'N/A')}")
        return "\n".join(lines)

    def _format_set_results(self, results: dict[str, Any]) -> str:
        avg = _safe_score(results.get("weighted_average", 0))
        total = _safe_score(results.get("total_weighted_score", 0))
        maximum = _safe_score(results.get("max_possible_weighted_score", 0))

        lines = [
            "## Task Set Complete",
            "",
            f"**Overall Score: {avg:.1f}/100**",
            f"**Total Weighted: {total:.1f}/{maximum:.1f}**",
            "",
            "### Individual Results",
        ]

        for task in results.get("tasks", []):
            status = "✗" if task.get("error") else "✓"
            s = _safe_score(task.get("score", 0))
            m = _safe_score(task.get("score_multiplier", 1.0))
            w = _safe_score(task.get("weighted_score", 0))
            lines.append(f"- {status} **{task['task_name']}**: {s:.1f} (x{m:.2f} = {w:.1f})")
            if task.get("error"):
                lines.append(f"  error: {task['error']}")

        lines.append("")
        lines.append(f"Full results: {results.get('result_file', 'N/A')}")
        return "\n".join(lines)