import json

from helpers.tool import Tool, Response
from plugins._memory.helpers.memory import Memory

from plugins._memory.tools.memory_load import DEFAULT_THRESHOLD

PREVIEW_CHARS = 80


def _coerce_bool(value, default: bool) -> bool:
    """Normalize tool args that may arrive stringified (e.g. "true"/"false").

    Guards against DirtyJson stringification where any non-empty string is
    truthy — a literal "false" must not silently enable cascade deletion.
    """
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("true", "1", "yes")
    return bool(value)


class MemoryForget(Tool):

    async def execute(
        self,
        query="",
        threshold=DEFAULT_THRESHOLD,
        filter="",
        dry_run=False,
        cascade=True,
        **kwargs,
    ):
        """Find and remove memories matching ``query``.

        Args:
            query: semantic query text.
            threshold: similarity threshold from 0 to 1 (default 0.7).
            filter: metadata expression (e.g. ``area=='main'``).
            dry_run: preview mode — performs the identical search, exact-match
                pass, and cascade expansion but deletes NOTHING; returns the
                full candidate list with IDs, reasons, and content previews.
            cascade: default true — besides semantic and exact-text matches,
                also deletes documents whose metadata references a matched
                memory ID (consolidation relatives such as ``replaced_memories``
                / ``consolidated_from``), in a single expansion pass with no
                recursive expansion. ``cascade: false`` limits deletion to
                exact semantic and exact-text matches only.

        Returns a JSON payload listing every deleted (or candidate) memory ID
        with a short content preview — not just a count.
        """
        dry = _coerce_bool(dry_run, False)
        casc = _coerce_bool(cascade, True)

        db = await Memory.get(self.agent)
        dels = await db.delete_documents_by_query(
            query=query,
            threshold=threshold,
            filter=filter,
            include_exact=True,
            cascade=casc,
            dry_run=dry,
        )

        details = []
        for doc in dels:
            preview = " ".join(str(doc.page_content or "").split())
            details.append(
                {
                    "id": str(doc.metadata.get("id", "")),
                    "reason": getattr(doc, "_forget_reason", "semantic"),
                    "preview": preview[:PREVIEW_CHARS],
                }
            )

        ids = [str(doc.metadata.get("id", "")) for doc in dels]
        if dry:
            payload = {
                "dry_run": True,
                "deleted": False,
                "would_delete_count": len(dels),
                "candidate_ids": ids,
                "candidates": details,
            }
        else:
            payload = {
                "dry_run": False,
                "deleted": True,
                "memories_deleted": len(dels),
                "deleted_ids": ids,
                "details": details,
            }

        result = "~~~json\n" + json.dumps(payload, indent=2) + "\n~~~"
        return Response(message=result, break_loop=False)
