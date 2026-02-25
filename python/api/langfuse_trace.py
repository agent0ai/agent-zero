from python.helpers.api import ApiHandler, Request, Response
from python.helpers.langfuse_helper import get_langfuse_client


class LangfuseTrace(ApiHandler):

    async def process(self, input: dict, request: Request) -> dict | Response:
        trace_id = input.get("trace_id", "")
        if not trace_id:
            return {"success": False, "error": "trace_id is required"}

        client = get_langfuse_client()
        if not client:
            return {"success": False, "error": "Langfuse is not configured"}

        try:
            trace = client.api.trace.get(trace_id)
        except Exception as e:
            return {"success": False, "error": f"Failed to fetch trace: {e}"}

        # Build observation tree from flat list
        observations = []
        for obs in trace.observations:
            usage_details = {}
            if obs.usage_details:
                usage_details = dict(obs.usage_details)
            elif obs.usage:
                u = obs.usage
                usage_details = {
                    "input": getattr(u, "input", 0) or 0,
                    "output": getattr(u, "output", 0) or 0,
                    "total": getattr(u, "total", 0) or 0,
                }

            observations.append({
                "id": obs.id,
                "type": obs.type,
                "name": obs.name or "unnamed",
                "parent_observation_id": obs.parent_observation_id,
                "start_time": obs.start_time.isoformat() if obs.start_time else None,
                "end_time": obs.end_time.isoformat() if obs.end_time else None,
                "model": obs.model,
                "latency": obs.latency,
                "input": _truncate(obs.input),
                "output": _truncate(obs.output),
                "usage_details": usage_details,
                "calculated_total_cost": obs.calculated_total_cost,
                "calculated_input_cost": obs.calculated_input_cost,
                "calculated_output_cost": obs.calculated_output_cost,
                "level": obs.level.value if obs.level else "DEFAULT",
                "metadata": obs.metadata if isinstance(obs.metadata, dict) else {},
            })

        trace_url = ""
        try:
            trace_url = client.get_trace_url(trace_id=trace_id) or ""
        except Exception:
            pass

        return {
            "success": True,
            "trace": {
                "id": trace.id,
                "name": trace.name or "unnamed",
                "input": _truncate(trace.input),
                "output": _truncate(trace.output),
                "session_id": trace.session_id,
                "latency": trace.latency,
                "total_cost": trace.total_cost,
                "tags": trace.tags or [],
                "metadata": trace.metadata if isinstance(trace.metadata, dict) else {},
            },
            "observations": observations,
            "trace_url": trace_url,
        }


def _truncate(value, max_len=10000):
    if value is None:
        return None
    s = str(value)
    return s[:max_len] + "..." if len(s) > max_len else s
