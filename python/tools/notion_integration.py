"""
Notion Integration Tool for Agent Jumbo / MOS.

5 actions: create_page, update_page, query_database, sync_specs, sync_crm.
"""

import json
import os

from python.helpers import files
from python.helpers.tool import Response, Tool


class NotionIntegration(Tool):
    """Agent tool for managing Notion pages and cross-system sync."""

    def __init__(self, agent, name: str, method: str | None, args: dict, message: str, loop_data=None, **kwargs):
        super().__init__(agent, name, method, args, message, loop_data, **kwargs)

        from instruments.custom.notion_integration.notion_manager import NotionManager

        db_path = files.get_abs_path("./instruments/custom/notion_integration/data/notion_integration.db")

        api_key = None
        try:
            from python.helpers.settings import get_settings

            api_key = get_settings().get("notion_api_key", "")
        except Exception:
            pass
        if not api_key:
            api_key = os.getenv("NOTION_API_KEY", "")

        self.manager = NotionManager(db_path, api_key=api_key or None)

    async def execute(self, **kwargs):
        action = (self.args.get("action") or "").lower()

        handlers = {
            "create_page": self._create_page,
            "update_page": self._update_page,
            "query_database": self._query_database,
            "sync_specs": self._sync_specs,
            "sync_crm": self._sync_crm,
        }

        handler = handlers.get(action)
        if not handler:
            return Response(
                message=f"Unknown action: {action}. Available: {', '.join(handlers.keys())}",
                break_loop=False,
            )
        return await handler()

    async def _create_page(self):
        database_id = self.args.get("database_id") or self._get_default_database_id()
        if not database_id:
            return Response(
                message="database_id is required. Set notion_default_database_id in settings or pass it.",
                break_loop=False,
            )
        result = await self.manager.create_page(
            database_id=database_id,
            title=self.args.get("title", ""),
            properties=self.args.get("properties"),
            content_blocks=self.args.get("content_blocks"),
        )
        return Response(message=self._fmt(result, "Notion Page Created"), break_loop=False)

    async def _update_page(self):
        page_id = self.args.get("page_id")
        if not page_id:
            return Response(message="page_id is required.", break_loop=False)
        result = await self.manager.update_page(
            page_id=page_id,
            properties=self.args.get("properties"),
            archived=self.args.get("archived"),
        )
        return Response(message=self._fmt(result, "Notion Page Updated"), break_loop=False)

    async def _query_database(self):
        database_id = self.args.get("database_id") or self._get_default_database_id()
        if not database_id:
            return Response(message="database_id is required.", break_loop=False)
        pages = await self.manager.query_database(
            database_id=database_id,
            filter_obj=self.args.get("filter"),
            sorts=self.args.get("sorts"),
            page_size=int(self.args.get("page_size", 100)),
        )
        return Response(
            message=self._fmt({"pages": pages, "count": len(pages)}, "Database Query"),
            break_loop=False,
        )

    async def _sync_specs(self):
        database_id = self.args.get("database_id") or self._get_default_database_id()
        if not database_id:
            return Response(message="database_id is required for spec sync.", break_loop=False)

        linear_api_key = None
        linear_team_id = None
        try:
            from python.helpers.settings import get_settings

            settings = get_settings()
            linear_api_key = settings.get("linear_api_key", "")
            linear_team_id = self.args.get("linear_team_id") or settings.get("linear_default_team_id", "")
        except Exception:
            pass
        if not linear_api_key:
            linear_api_key = os.getenv("LINEAR_API_KEY", "")

        result = await self.manager.sync_specs(
            notion_database_id=database_id,
            linear_api_key=linear_api_key or None,
            linear_team_id=linear_team_id or None,
            spec_label_name=self.args.get("spec_label", "Spec"),
        )
        return Response(message=self._fmt(result, "Spec Sync (Linear → Notion)"), break_loop=False)

    async def _sync_crm(self):
        database_id = self.args.get("database_id") or self._get_default_database_id()
        if not database_id:
            return Response(message="database_id is required for CRM sync.", break_loop=False)
        result = await self.manager.sync_crm(notion_database_id=database_id)
        return Response(message=self._fmt(result, "CRM Sync → Notion"), break_loop=False)

    # ── Helpers ──────────────────────────────────────────────────────

    def _get_default_database_id(self) -> str:
        try:
            from python.helpers.settings import get_settings

            return get_settings().get("notion_default_database_id", "")
        except Exception:
            return os.getenv("NOTION_DEFAULT_DATABASE_ID", "")

    def _fmt(self, result: dict, title: str) -> str:
        if not result:
            return f"**{title}**: No data"
        if "error" in result:
            return f"**{title} - Error**: {result['error']}"
        return f"**{title}**:\n```json\n{json.dumps(result, indent=2, default=str)}\n```"
