from agent import AgentContext, UserMessage
from helpers.api import ApiHandler, Input, Output, Request, Response
from helpers import guids, message_queue as mq
from helpers.persist_chat import remove_chat
from plugins._plugin_scan.helpers.prompt import build_prompt


class PluginScanRun(ApiHandler):
    """
    POST /api/plugins/_plugin_scan/plugin_scan_run
    Body:    { "git_url": "https://github.com/...", "checks": [...] }  # checks optional, defaults to all
    Returns: { "ok": true, "verdict": "safe|caution|dangerous|unknown", "report": "<markdown>" }

    Combines plugin_scan_queue + plugin_scan_start into one synchronous call and awaits the result.
    No server-side timeout - set an appropriate client-side timeout (repos can take 5+ min to scan).
    """

    async def process(self, input: Input, request: Request) -> Output:
        git_url: str = input.get("git_url", "").strip()
        if not git_url:
            return Response("Missing 'git_url'.", 400)

        ctxid = guids.generate_id()
        report = ""
        try:
            context = self.use_context(ctxid)
            prompt = build_prompt(git_url, input.get("checks"))
            mq.log_user_message(context, prompt, [])
            task = context.communicate(UserMessage(prompt, []))
            report: str = await task.result()
        except Exception as e:
            return Response(f"Scan failed: {e}", 500)
        finally:
            try:
                AgentContext.remove(ctxid)
                remove_chat(ctxid)
            except Exception:
                pass

        return {
            "ok": True,
            "git_url": git_url,
            "report": report or "",
        }
