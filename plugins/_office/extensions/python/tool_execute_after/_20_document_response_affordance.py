from __future__ import annotations

from typing import Any

from helpers.extension import Extension


class DocumentResponseAffordance(Extension):
    """Compatibility shim for the retired response artifact affordance."""

    async def execute(self, **kwargs: Any):
        return None
