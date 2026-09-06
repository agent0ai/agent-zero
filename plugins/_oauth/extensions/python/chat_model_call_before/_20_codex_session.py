from helpers.extension import Extension


class CodexSession(Extension):
    def execute(self, call_data: dict, **kwargs):
        model = call_data.get("model")
        config = getattr(model, "a0_model_conf", None)
        if not self.agent or getattr(config, "provider", "") != "codex_oauth":
            return

        extra_body = dict(model.kwargs.get("extra_body") or {})
        metadata = dict(extra_body.get("client_metadata") or {})
        session_id = f"agent-zero-{self.agent.context.id}-{self.agent.number}"
        metadata.setdefault("session_id", session_id)
        metadata.setdefault("thread_id", session_id)
        extra_body["client_metadata"] = metadata
        model.kwargs["extra_body"] = extra_body
