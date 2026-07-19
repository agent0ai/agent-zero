from __future__ import annotations

from agent import LoopData
from helpers.extension import Extension


class IncludeOfficeCanvasContext(Extension):
    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        loop_data.extras_temporary.pop("office_canvas", None)
