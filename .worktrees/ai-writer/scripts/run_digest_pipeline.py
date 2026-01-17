#!/usr/bin/env python3
"""Run ingestion and digest generation, optionally sending to Telegram."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from instruments.custom.digest_builder.digest_builder_manager import DigestBuilderManager
from instruments.custom.knowledge_ingest.knowledge_ingest_manager import KnowledgeIngestManager
from python.helpers import files
from python.helpers.mcp_handler import MCPConfig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run digest pipeline")
    parser.add_argument("--ingest", action="store_true", help="Ingest all sources before building digest")
    parser.add_argument("--window-hours", type=int, default=24)
    parser.add_argument("--max-items", type=int, default=3)
    parser.add_argument("--send-telegram", action="store_true", help="Send digest to Telegram")
    return parser.parse_args()


def send_telegram(text: str) -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        raise RuntimeError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set")

    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }
    endpoint = f"https://api.telegram.org/bot{token}/sendMessage"
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(endpoint, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=20) as response:
        response.read()


async def ingest_mcp_sources(manager: KnowledgeIngestManager) -> list[dict]:
    results = []
    for source in manager.db.list_sources():
        if source.get("type") != "mcp":
            continue
        tool_name = source.get("uri")
        tool_args = source.get("config") or {}
        try:
            payload = await MCPConfig.get_instance().call_tool(tool_name, tool_args)
            results.append(manager.store_mcp_payload(source, payload.model_dump()))
        except Exception as exc:
            results.append({"error": f"MCP ingest failed: {exc}", "source_id": source.get("id")})
    return results


def main() -> None:
    args = parse_args()
    db_path = files.get_abs_path("./instruments/custom/knowledge_ingest/data/knowledge_ingest.db")

    ingest_manager = KnowledgeIngestManager(db_path)
    digest_manager = DigestBuilderManager(db_path)

    if args.ingest:
        ingest_manager.ingest_all(max_items_per_source=args.max_items)
        asyncio.run(ingest_mcp_sources(ingest_manager))

    digest = digest_manager.build_digest(
        window_hours=args.window_hours,
        max_items_per_section=args.max_items,
    )

    if args.send_telegram:
        send_telegram(digest["summary"])
    else:
        print(digest["summary"])


if __name__ == "__main__":
    main()
