"""Knowledge ingest tool for Agent Jumbo."""

from python.helpers import files
from python.helpers.tool import Response, Tool


class KnowledgeIngest(Tool):
    """Ingests knowledge sources into local storage and the knowledge base."""

    def __init__(self, agent, name: str, method: str | None, args: dict, message: str, loop_data=None, **kwargs):
        super().__init__(agent, name, method, args, message, loop_data, **kwargs)
        from instruments.custom.knowledge_ingest.knowledge_ingest_manager import (
            KnowledgeIngestManager,
        )

        db_path = files.get_abs_path("./instruments/custom/knowledge_ingest/data/knowledge_ingest.db")
        self.manager = KnowledgeIngestManager(db_path)

    async def execute(self, **kwargs):
        action = (self.args.get("action") or "").lower()

        if action == "register_source":
            return self._register_source()
        if action == "list_sources":
            return self._list_sources()
        if action == "ingest_source":
            return await self._ingest_source()
        if action == "ingest_all":
            return await self._ingest_all()
        if action == "ingest_text":
            return self._ingest_text()
        if action == "ingest_mcp":
            return await self._ingest_mcp()

        return Response(
            message=(
                "Unknown action. Use one of: register_source, list_sources, "
                "ingest_source, ingest_all, ingest_text, ingest_mcp."
            ),
            break_loop=False,
        )

    def _register_source(self):
        name = self.args.get("name")
        source_type = self.args.get("source_type")
        uri = self.args.get("uri")
        tags = self.args.get("tags") or []
        cadence = self.args.get("cadence")
        config = self.args.get("config")

        result = self.manager.register_source(
            name,
            source_type,
            uri,
            tags=tags,
            cadence=cadence,
            config=config,
        )
        return Response(message=str(result), break_loop=False)

    def _list_sources(self):
        result = self.manager.list_sources()
        return Response(message=str(result), break_loop=False)

    async def _ingest_source(self):
        source_id = self.args.get("source_id")
        if source_id is None:
            return Response(message="Error: source_id is required", break_loop=False)
        max_items = int(self.args.get("max_items", 10))
        source = self.manager.db.get_source(int(source_id))
        if not source:
            return Response(message="Error: source not found", break_loop=False)
        if source.get("type") == "mcp":
            result = await self._ingest_mcp_source(source)
        else:
            result = self.manager.ingest_source(int(source_id), max_items=max_items)
        return Response(message=str(result), break_loop=False)

    async def _ingest_all(self):
        max_items = int(self.args.get("max_items", 10))
        results = []
        for source in self.manager.db.list_sources():
            if source.get("type") == "mcp":
                results.append(await self._ingest_mcp_source(source))
            else:
                results.append(self.manager.ingest_source(source["id"], max_items=max_items))
        result = {"status": "ok", "results": results}
        return Response(message=str(result), break_loop=False)

    def _ingest_text(self):
        title = self.args.get("title")
        content = self.args.get("content")
        tags = self.args.get("tags") or []
        confidence = float(self.args.get("confidence", 0.7))
        result = self.manager.ingest_text(title, content, tags=tags, confidence=confidence)
        return Response(message=str(result), break_loop=False)

    async def _ingest_mcp(self):
        tool_name = self.args.get("tool_name")
        tool_args = self.args.get("tool_args") or {}
        title = self.args.get("title") or f"MCP: {tool_name}"
        tags = self.args.get("tags") or []

        if not tool_name:
            return Response(message="Error: tool_name is required", break_loop=False)

        source = {
            "id": 0,
            "name": title,
            "type": "mcp",
            "uri": tool_name,
            "tags": tags,
        }

        try:
            payload = await self._call_mcp(tool_name, tool_args)
            result = self.manager.store_mcp_payload(source, payload)
            return Response(message=str(result), break_loop=False)
        except Exception as exc:
            return Response(message=f"MCP ingest failed: {exc}", break_loop=False)

    async def _ingest_mcp_source(self, source: dict):
        tool_name = source.get("uri")
        tool_args = source.get("config") or {}
        try:
            payload = await self._call_mcp(tool_name, tool_args)
            return self.manager.store_mcp_payload(source, payload)
        except Exception as exc:
            return {"error": f"MCP ingest failed: {exc}"}

    async def _call_mcp(self, tool_name: str, tool_args: dict):
        from python.helpers.mcp_handler import MCPConfig

        result = await MCPConfig.get_instance().call_tool(tool_name, tool_args)
        return result.model_dump()
