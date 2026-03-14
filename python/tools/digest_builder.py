"""Digest builder tool for Agent Jumbo."""

from python.helpers import files
from python.helpers.tool import Response, Tool


class DigestBuilder(Tool):
    """Builds digests from ingested knowledge items."""

    def __init__(self, agent, name: str, method: str | None, args: dict, message: str, loop_data=None, **kwargs):
        super().__init__(agent, name, method, args, message, loop_data, **kwargs)
        from instruments.custom.digest_builder.digest_builder_manager import DigestBuilderManager

        db_path = files.get_abs_path("./instruments/custom/knowledge_ingest/data/knowledge_ingest.db")
        self.manager = DigestBuilderManager(db_path)

    async def execute(self, **kwargs):
        action = (self.args.get("action") or "").lower()

        if action == "build_digest":
            return self._build_digest()
        if action == "build_architecture_review":
            return self._build_architecture_review()
        if action == "list_digests":
            return self._list_digests()

        return Response(
            message="Unknown action. Use build_digest, build_architecture_review, or list_digests.",
            break_loop=False,
        )

    def _build_digest(self):
        window_hours = int(self.args.get("window_hours", 24))
        max_items = int(self.args.get("max_items_per_section", 3))
        channel = self.args.get("channel", "telegram")
        result = self.manager.build_digest(
            window_hours=window_hours,
            max_items_per_section=max_items,
            channel=channel,
        )

        # MOS hook: append Linear activity section to digest
        linear_section = self._get_linear_activity_section()
        summary = result.get("summary", str(result))
        if linear_section:
            summary += f"\n\n{linear_section}"

        return Response(message=summary, break_loop=False)

    def _get_linear_activity_section(self) -> str:
        """Pull recent Linear issues from cache for digest inclusion."""
        try:
            from instruments.custom.linear_integration.linear_db import LinearDatabase

            db_path = files.get_abs_path("./instruments/custom/linear_integration/data/linear_integration.db")
            db = LinearDatabase(db_path)
            issues = db.get_issues(limit=5)
            if not issues:
                return ""
            lines = ["## Linear Activity"]
            for issue in issues:
                lines.append(
                    f"- **{issue.get('identifier', '')}** {issue.get('title', '')} [{issue.get('state_name', '')}]"
                )
            return "\n".join(lines)
        except Exception:
            return ""

    def _list_digests(self):
        limit = int(self.args.get("limit", 10))
        result = self.manager.list_digests(limit=limit)
        return Response(message=str(result), break_loop=False)

    def _build_architecture_review(self):
        context = self.args.get("context", "")
        options = self.args.get("options") or []
        decision = self.args.get("decision", "")
        follow_ups = self.args.get("follow_ups") or []
        open_questions = self.args.get("open_questions") or []
        result = self.manager.build_architecture_review(
            context=context,
            options=options,
            decision=decision,
            follow_ups=follow_ups,
            open_questions=open_questions,
        )
        return Response(message=result.get("adr", str(result)), break_loop=False)
