from agent import AgentContext, UserMessage
from helpers.api import ApiHandler, Input, Output, Request, Response
from helpers import guids, message_queue as mq
from helpers.persist_chat import remove_chat
from plugins._plugin_validator.helpers.prompt import build_prompt


class PluginValidatorRun(ApiHandler):
    """
    POST /api/plugins/_plugin_validator/plugin_validator_run
    Body:    { "source": "local|git", "target": "<plugin name or git url>", "checks": [...] }
    Returns: { "ok": true, "source": "local|git", "target": "...", "report": "<markdown>" }

    Combines plugin_validator_queue + plugin_validator_start into one synchronous call and awaits the result.
    No server-side timeout - set an appropriate client-side timeout for large repositories.
    """

    async def process(self, input: Input, request: Request) -> Output:
        source: str = input.get("source", "local").strip().lower()
        target: str = input.get("target", "").strip()

        if source not in {"local", "git"}:
            return Response("Unsupported 'source'. Use 'local' or 'git'.", 400)
        if not target:
            return Response("Missing 'target'.", 400)

        ctxid = guids.generate_id()
        report = ""
        try:
            context = self.use_context(ctxid)
            prompt = build_prompt(source, target, input.get("checks"))
            mq.log_user_message(context, prompt, [])
            task = context.communicate(UserMessage(prompt, []))
            report: str = await task.result()
        except Exception as e:
            return Response(f"Validation failed: {e}", 500)
        finally:
            try:
                AgentContext.remove(ctxid)
                remove_chat(ctxid)
            except Exception:
                pass

        return {
            "ok": True,
            "source": source,
            "target": target,
            "report": report or "",
        }
