import asyncio
import time
import uuid
from agent import AgentContext, AgentContextType, UserMessage
from initialize import initialize_agent
from python.helpers.print_style import PrintStyle
from python.helpers.defer import DeferredTask


class NodeState:
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"
    SKIPPED = "skipped"


class FlowRun:
    """Tracks the state of a single flow execution."""

    def __init__(self, flow: dict, user_prompt: str = ""):
        self.id = str(uuid.uuid4())[:8]
        self.flow = flow
        self.user_prompt = user_prompt
        self.node_states: dict[str, str] = {}
        self.node_outputs: dict[str, str] = {}
        self.condition_results: dict[str, str] = {}  # nodeId -> "true"/"false"
        self.context_ids: list[str] = []
        self.node_context_ids: dict[str, str] = {}  # nodeId -> contextId
        self.node_start_times: dict[str, float] = {}  # nodeId -> epoch
        self.running = False
        self.cancelled = False
        self.error: str | None = None
        self.final_output: str | None = None

        for node in flow.get("nodes", []):
            self.node_states[node["id"]] = NodeState.PENDING

    def set_state(self, node_id: str, state: str, output: str = ""):
        self.node_states[node_id] = state
        if state == NodeState.RUNNING:
            self.node_start_times[node_id] = time.time()
        if output:
            self.node_outputs[node_id] = output

    def _get_node_progress(self) -> dict[str, dict]:
        """Query running nodes' agent contexts for live progress info."""
        progress = {}
        for node_id, ctx_id in self.node_context_ids.items():
            state = self.node_states.get(node_id, "")
            if state not in (NodeState.RUNNING, NodeState.COMPLETED):
                continue

            ctx = AgentContext.get(ctx_id)
            if not ctx or not ctx.log:
                continue

            info: dict = {}

            # Elapsed time since node started
            start = self.node_start_times.get(node_id)
            if start:
                info["elapsed_sec"] = round(time.time() - start, 1)

            # Latest log activity from the agent's context
            logs = ctx.log.logs
            if logs:
                last = logs[-1]
                info["log_type"] = getattr(last, "type", "")
                heading = getattr(last, "heading", "")
                # Strip icon prefixes (e.g., "icon://construction Agent 0: ...")
                if heading and "://" in heading[:20]:
                    heading = heading.split(" ", 1)[-1] if " " in heading else heading
                info["heading"] = heading[:120] if heading else ""
                # Extract tool name if it's a tool step
                kvps = getattr(last, "kvps", None)
                if kvps and "tool_name" in kvps:
                    info["tool"] = kvps["tool_name"]

            # Progress bar text from the log
            if ctx.log.progress:
                info["progress"] = ctx.log.progress[:120]

            if info:
                progress[node_id] = info

        return progress

    def to_status(self) -> dict:
        return {
            "run_id": self.id,
            "running": self.running,
            "cancelled": self.cancelled,
            "error": self.error,
            "node_states": self.node_states,
            "node_outputs": {k: v[:500] for k, v in self.node_outputs.items()},
            "node_progress": self._get_node_progress(),
            "context_ids": self.context_ids,
            "final_output": self.final_output,
        }


class FlowEngine:
    """Walks a flow graph and executes agent nodes with parallel + condition support."""

    _runs: dict[str, FlowRun] = {}

    @classmethod
    def get_run(cls, run_id: str) -> FlowRun | None:
        return cls._runs.get(run_id)

    @classmethod
    def cancel_run(cls, run_id: str) -> bool:
        run = cls._runs.get(run_id)
        if run and run.running:
            run.cancelled = True
            return True
        return False

    @classmethod
    def start_background(cls, flow: dict, user_prompt: str = "") -> FlowRun:
        """Start flow execution on a background thread. Returns immediately."""
        run = FlowRun(flow, user_prompt)
        cls._runs[run.id] = run
        run.running = True

        async def _run_wrapper():
            try:
                await cls._walk_graph(run)
            except Exception as e:
                run.error = str(e)
                PrintStyle.error(f"Flow execution error: {e}")
            finally:
                run.running = False
                cls._update_flow_contexts_running(run)

        DeferredTask(thread_name="FlowEngine").start_task(_run_wrapper)
        return run

    @classmethod
    async def execute(cls, flow: dict, user_prompt: str = "") -> FlowRun:
        """Execute flow synchronously (awaitable). Mostly for testing."""
        run = FlowRun(flow, user_prompt)
        cls._runs[run.id] = run
        run.running = True

        try:
            await cls._walk_graph(run)
        except Exception as e:
            run.error = str(e)
            PrintStyle.error(f"Flow execution error: {e}")
        finally:
            run.running = False
            cls._update_flow_contexts_running(run)

        return run

    @classmethod
    def _update_flow_contexts_running(cls, run: FlowRun):
        """Mark all flow-created contexts as no longer running."""
        for ctx_id in run.context_ids:
            ctx = AgentContext.get(ctx_id)
            if ctx:
                ctx.set_output_data("flow_running", False)

    # ─── Graph Walker ───

    @classmethod
    async def _walk_graph(cls, run: FlowRun):
        """Topological sort then execute with parallel/condition awareness."""
        nodes = {n["id"]: n for n in run.flow.get("nodes", [])}
        edges = run.flow.get("edges", [])

        # Build adjacency list and in-degree counts
        adj: dict[str, list[str]] = {nid: [] for nid in nodes}
        in_degree: dict[str, int] = {nid: 0 for nid in nodes}

        for edge in edges:
            src, tgt = edge["source"], edge["target"]
            if src in adj and tgt in in_degree:
                adj[src].append(tgt)
                in_degree[tgt] += 1

        # Kahn's algorithm for topological sort
        order: list[str] = []
        queue = [nid for nid, deg in in_degree.items() if deg == 0]

        while queue:
            nid = queue.pop(0)
            order.append(nid)
            for neighbor in adj.get(nid, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(order) != len(nodes):
            run.error = "Flow contains a cycle"
            return

        # Track nodes already executed by parallel groups
        already_executed: set[str] = set()

        for node_id in order:
            if node_id in already_executed:
                continue

            if run.cancelled:
                run.set_state(node_id, NodeState.SKIPPED)
                continue

            node = nodes[node_id]
            node_type = node.get("type", "")
            node_data = node.get("data", {})

            predecessor_outputs = cls._gather_inputs(node_id, nodes, edges, run)
            run.set_state(node_id, NodeState.RUNNING)

            try:
                if node_type == "parallelGroupNode":
                    output = await cls._execute_parallel(
                        node_data, predecessor_outputs, adj.get(node_id, []),
                        nodes, edges, run, already_executed
                    )
                elif node_type == "conditionNode":
                    output = cls._execute_condition(node_id, node_data, predecessor_outputs, run)
                else:
                    output = await cls._execute_node(
                        node_type, node_data, predecessor_outputs, run,
                        node_id=node_id,
                    )

                run.set_state(node_id, NodeState.COMPLETED, output)
            except Exception as e:
                run.set_state(node_id, NodeState.ERROR, str(e))
                run.error = f"Node {node_id} failed: {e}"
                break

    # ─── Input Gathering (handle-aware for conditions) ───

    @classmethod
    def _gather_inputs(
        cls, node_id: str, nodes: dict, edges: list, run: FlowRun
    ) -> list[str]:
        """Collect output strings from predecessors, respecting condition routing."""
        outputs = []
        for edge in edges:
            if edge["target"] != node_id:
                continue
            src = edge["source"]
            if src not in run.node_outputs:
                continue

            # For edges from condition nodes, only include if the edge's
            # sourceHandle matches the condition's evaluation result
            src_node = nodes.get(src, {})
            if src_node.get("type") == "conditionNode":
                handle = edge.get("sourceHandle", "")
                condition_result = run.condition_results.get(src, "")
                if handle and condition_result and handle != condition_result:
                    continue

            outputs.append(run.node_outputs[src])
        return outputs

    # ─── Node Executors ───

    @classmethod
    async def _execute_node(
        cls, node_type: str, data: dict, inputs: list[str], run: FlowRun,
        node_id: str = "",
    ) -> str:
        if node_type == "inputNode":
            return cls._execute_input(data, run)
        elif node_type == "agentNode":
            return await cls._execute_agent(data, inputs, run=run, node_id=node_id)
        elif node_type == "outputNode":
            return cls._execute_output(data, inputs, run)
        else:
            return "\n\n".join(inputs) if inputs else ""

    @classmethod
    def _execute_input(cls, data: dict, run: FlowRun) -> str:
        mode = data.get("promptMode", "runtime")
        if mode == "fixed":
            return data.get("fixedPrompt", "") or ""
        return run.user_prompt

    @classmethod
    async def _execute_agent(
        cls, data: dict, inputs: list[str],
        run: "FlowRun | None" = None, node_id: str = "",
    ) -> str:
        combined = "\n\n".join(inputs) if inputs else ""
        if not combined:
            return ""

        prompt_override = (data.get("promptOverride") or data.get("systemPromptOverride") or "").strip()
        if prompt_override:
            prompt = f"{prompt_override}\n\n{combined}"
        else:
            prompt = combined

        config = initialize_agent()
        profile = data.get("agentProfile") or ""
        if profile:
            config.profile = profile

        context = AgentContext(config=config, type=AgentContextType.TASK)

        # Tag context with flow metadata and a readable name
        flow_name = run.flow.get("name", "Flow") if run else ""
        label = (data.get("label") or "").strip() or "Flow Agent"
        if run:
            context.name = label
            run.context_ids.append(context.id)
            if node_id:
                run.node_context_ids[node_id] = context.id

        try:
            agent = context.agent0
            agent.hist_add_user_message(UserMessage(message=prompt))
            result = await agent.monologue()
            return result
        finally:
            if run:
                # Keep context alive — tag with flow metadata for frontend grouping
                context.set_output_data("flow_run_id", run.id)
                context.set_output_data("flow_name", flow_name)
                context.set_output_data("flow_node_id", node_id)
                context.set_output_data("flow_node_label", label)
                context.set_output_data("flow_running", run.running)
            else:
                # No flow run (e.g. summarize branch) — clean up immediately
                AgentContext.remove(context.id)

    @classmethod
    def _execute_output(
        cls, data: dict, inputs: list[str], run: FlowRun
    ) -> str:
        output = "\n\n".join(inputs) if inputs else ""
        run.final_output = output
        return output

    # ─── Parallel Group Execution ───

    @classmethod
    async def _execute_parallel(
        cls,
        data: dict,
        inputs: list[str],
        successor_ids: list[str],
        nodes: dict,
        edges: list,
        run: FlowRun,
        already_executed: set[str],
    ) -> str:
        """Execute parallel branches concurrently, merge their outputs.

        Uses explicit `branches` list from node data when available.
        Successors not listed as branches are left for the main graph
        walker so they correctly receive the merged output.
        """
        explicit_branches = data.get("branches", [])
        if explicit_branches:
            # Use only explicitly declared branches
            branch_ids = [
                sid for sid in successor_ids
                if sid in explicit_branches
            ]
        else:
            # Fallback: all agent-type successors are branches
            branch_ids = [
                sid for sid in successor_ids
                if nodes.get(sid, {}).get("type") == "agentNode"
            ]

        if not branch_ids:
            return "\n\n".join(inputs) if inputs else ""

        # Resolve branch labels for output formatting
        branch_labels = {}
        for sid in branch_ids:
            s_node = nodes.get(sid, {})
            branch_labels[sid] = (s_node.get("data", {}).get("label") or sid).strip()

        async def _run_branch(sid: str) -> tuple[str, str]:
            """Returns (branch_label, output)."""
            if run.cancelled:
                run.set_state(sid, NodeState.SKIPPED)
                return (branch_labels.get(sid, sid), "")

            s_node = nodes.get(sid)
            if not s_node:
                return (branch_labels.get(sid, sid), "")

            s_type = s_node.get("type", "")
            s_data = s_node.get("data", {})

            # Branch gets the parallel group's input
            run.set_state(sid, NodeState.RUNNING)
            try:
                result = await cls._execute_node(
                    s_type, s_data, inputs, run, node_id=sid,
                )
                run.set_state(sid, NodeState.COMPLETED, result)
                return (branch_labels.get(sid, sid), result)
            except Exception as e:
                run.set_state(sid, NodeState.ERROR, str(e))
                return (branch_labels.get(sid, sid), "")

        # Run branches concurrently
        results = await asyncio.gather(
            *[_run_branch(sid) for sid in branch_ids],
            return_exceptions=True,
        )

        # Mark only branch nodes as already executed
        for sid in branch_ids:
            already_executed.add(sid)

        # Collect results — each is (label, output), filter out exceptions and empties
        labeled_outputs = []
        for r in results:
            if isinstance(r, tuple) and len(r) == 2:
                label, output = r
                if output:
                    labeled_outputs.append((label, output))

        # Merge based on strategy
        strategy = data.get("mergeStrategy", "concatenate")
        if strategy == "first":
            return labeled_outputs[0][1] if labeled_outputs else ""
        elif strategy == "summarize":
            # Summarize by asking an agent to combine the outputs
            if len(labeled_outputs) <= 1:
                return labeled_outputs[0][1] if labeled_outputs else ""
            combined = "\n\n---\n\n".join(
                f"## {label}\n\n{output}" for label, output in labeled_outputs
            )
            summary_prompt = (
                "Synthesize the following parallel agent outputs into a "
                "single coherent response:\n\n" + combined
            )
            return await cls._execute_agent({}, [summary_prompt])
        else:
            # concatenate (default) — with section headers for clarity
            if len(labeled_outputs) == 1:
                return labeled_outputs[0][1]
            return "\n\n---\n\n".join(
                f"## {label}\n\n{output}" for label, output in labeled_outputs
            )

    # ─── Condition Evaluation ───

    @classmethod
    def _execute_condition(
        cls,
        node_id: str,
        data: dict,
        inputs: list[str],
        run: FlowRun,
    ) -> str:
        """Evaluate expression and store routing decision."""
        combined = "\n\n".join(inputs) if inputs else ""
        expression = (data.get("expression") or "").strip()

        if not expression:
            # No expression → default to true
            run.condition_results[node_id] = "true"
            return combined

        try:
            # Evaluate with 'input' as the combined text from predecessors
            result = bool(eval(expression, {"__builtins__": {}}, {
                "input": combined,
                "len": len,
                "int": int,
                "float": float,
                "str": str,
                "bool": bool,
            }))
        except Exception as e:
            PrintStyle.warning(f"Condition expression error: {e}, defaulting to true")
            result = True

        run.condition_results[node_id] = "true" if result else "false"
        return combined
