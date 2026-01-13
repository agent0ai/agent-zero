from agent import AgentContext
from python.helpers.api import ApiHandler, Input, Output, Request

# AI Scientist has 4 experiment stages
TOTAL_STAGES = 4


class GetExperimentProgress(ApiHandler):
    """API endpoint to get detailed progress for a specific experiment."""

    async def process(self, input: Input, request: Request) -> Output:
        idea_name = input.get("idea_name", "")
        if not idea_name:
            return {"status": "error", "message": "idea_name is required"}

        ctxid = input.get("context", "")

        # Get context if specified, otherwise use current
        if ctxid:
            try:
                context = self.use_context(ctxid, create_if_not_exists=False)
            except Exception:
                return {"status": "error", "message": "Context not found"}
        else:
            context = AgentContext.current()

        if not context:
            return {"status": "error", "message": "No active context"}

        # Retrieve experiment data
        experiments = context.get_data("experiments") or {}
        experiment = experiments.get(idea_name)

        if not experiment:
            return {"status": "error", "message": f"Experiment '{idea_name}' not found"}

        # Build stage progress
        stages = {}
        all_nodes = []

        journals = experiment.get("journals", {})
        for stage_num in range(1, TOTAL_STAGES + 1):
            stage_key = f"stage_{stage_num}"
            journal = journals.get(stage_key, {})

            # Handle both dataclass and dict representations
            if hasattr(journal, "nodes"):
                nodes = [n.to_dict() if hasattr(n, "to_dict") else n for n in journal.nodes]
                best_node_id = journal.best_node_id
            else:
                nodes = journal.get("nodes", [])
                best_node_id = journal.get("best_node_id")

            stages[stage_key] = {
                "nodes": nodes,
                "best_node_id": best_node_id,
                "node_count": len(nodes),
            }
            all_nodes.extend(nodes)

        # Build summary
        best_metric = None
        for node in all_nodes:
            metric = node.get("metric") if isinstance(node, dict) else getattr(node, "metric", None)
            if metric is not None:
                if best_metric is None or metric < best_metric:
                    best_metric = metric

        current_stage = experiment.get("current_stage", 1)

        return {
            "idea_name": idea_name,
            "current_stage": current_stage,
            "stages": stages,
            "tree_nodes": all_nodes,
            "summary": {
                "total_nodes": len(all_nodes),
                "best_metric": best_metric,
                "current_stage": current_stage,
            },
        }

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET", "POST"]
