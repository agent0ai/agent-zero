from __future__ import annotations

from typing import Any

from agent import LoopData
from helpers import tool_policy
from helpers.extension import Extension
from plugins._browser.helpers.runtime import get_runtime


class BrowserContextPrompt(Extension):
    async def execute(
        self,
        system_prompt: list[str] = [],
        loop_data: LoopData = LoopData(),
        **kwargs: Any,
    ):
        if not self.agent:
            return

        runtime = await get_runtime(self.agent.context.id, create=False)
        if not runtime:
            return
        if not tool_policy.resolve_tool(self.agent, "browser").allowed:
            return

        try:
            listing = await runtime.call("list")
        except Exception:
            return

        browsers = listing.get("browsers") or []
        if not browsers:
            return

        rows = ["browser id|url|title"]
        for browser in browsers:
            rows.append(
                f"{browser.get('id')}|{browser.get('currentUrl', '')}|{browser.get('title', '')}"
            )

        section = ["currently open web browsers", "\n".join(rows)]
        last_id = listing.get("last_interacted_browser_id")
        if last_id:
            try:
                state = await runtime.call("state", last_id)
                content = await runtime.call("content", last_id, None)
                document = content.get("document") if isinstance(content, dict) else ""
                if document:
                    section.extend(
                        [
                            "",
                            "last interacted web browser",
                            f"browser id|url|title\n{state.get('id')}|{state.get('currentUrl', '')}|{state.get('title', '')}",
                            "page content↓",
                            str(document),
                        ]
                    )
            except Exception:
                pass

        system_prompt.append("\n".join(section))
