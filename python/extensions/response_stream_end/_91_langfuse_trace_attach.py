from python.helpers.extension import Extension
from python.helpers.langfuse_helper import get_langfuse_client
from agent import LoopData


class LangfuseTraceAttach(Extension):

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        if not loop_data.params_persistent.get("lf_sampled"):
            return

        trace_id = loop_data.params_persistent.get("lf_trace_id")
        if not trace_id:
            return

        log_item = loop_data.params_temporary.get("log_item_response")
        if not log_item:
            return

        # Build Langfuse trace URL
        trace_url = ""
        client = get_langfuse_client()
        if client:
            try:
                trace_url = client.get_trace_url(trace_id=trace_id) or ""
            except Exception:
                pass

        log_item.update(kvps={"trace_id": trace_id, "trace_url": trace_url})
