"""A chat's DevTools browser session and its attached targets on the private pipe."""
from __future__ import annotations

import asyncio
from collections import deque


class RawCDPClient:
    MAX_EVENTS = 512
    MAX_BYTES = 8 * 1024 * 1024

    def __init__(self, context):
        self.context = context
        self.lock = asyncio.Lock()
        self.closed = False
        self.root = None
        self.parents = {}
        self.tabs = {}
        self.events = deque()
        self.size = self.dropped = 0

    async def send(self, method, params, target_id, session_id):
        # Chromium can attach before cancellation reaches the caller. Keep the handle for cleanup.
        attach = asyncio.create_task(self._session(target_id, session_id))
        try:
            session_id = await asyncio.shield(attach)
        except asyncio.CancelledError:
            await asyncio.gather(attach, return_exceptions=True)
            raise
        result = await self.context.command(method, params, session_id=session_id)
        return {"session_id": session_id, "result": result}

    async def _session(self, target_id, session_id):
        async with self.lock:
            if self.closed:
                raise ValueError("CDP client closed")
            if session_id is not None:
                if not isinstance(session_id, str) or session_id not in self.parents:
                    raise ValueError("Unknown CDP session_id for this chat")
                return session_id
            if self.root is None:
                attached = await self.context.command("Target.attachToBrowserTarget")
                self.root = attached["sessionId"]
                self.register(self.root, None)
            if target_id is None:
                return self.root
            if target_id not in self.tabs:
                attached = await self.context.command("Target.attachToTarget", {
                    "targetId": target_id, "flatten": True,
                }, session_id=self.root)
                self.tabs[target_id] = attached["sessionId"]
            return self.tabs[target_id]

    def register(self, session_id, parent):
        self.context.raw_sessions[session_id] = self
        self.parents[session_id] = parent

    def detached(self, session_id):
        for child, parent in tuple(self.parents.items()):
            if parent == session_id:
                self.detached(child)
        self.parents.pop(session_id, None)
        self.context.raw_sessions.pop(session_id, None)
        self.context._fail_requests(session_id)
        self.tabs = {tab: sid for tab, sid in self.tabs.items() if sid != session_id}
        if self.root == session_id:
            self.root = None

    def receive(self, message, size):
        method, params = message["method"], message.get("params", {})
        if method == "Target.attachedToTarget":
            self.register(params["sessionId"], message["sessionId"])
        elif method == "Target.detachedFromTarget":
            self.detached(params["sessionId"])
        if size > self.MAX_BYTES:
            self.dropped += 1
            return
        while len(self.events) >= self.MAX_EVENTS or self.size + size > self.MAX_BYTES:
            self.size -= self.events.popleft()[1]
            self.dropped += 1
        self.events.append((message, size))
        self.size += size

    def drain(self):
        events = []
        while self.events and len(events) < 64:
            message, size = self.events.popleft()
            self.size -= size
            events.append(message)
        dropped, self.dropped = self.dropped, 0
        return {"events": events, "remaining": len(self.events), "dropped": dropped}

    async def close(self):
        self.closed = True
        async with self.lock:
            if self.root and not self.context.closed:
                await self.context.command("Target.detachFromTarget", {"sessionId": self.root})
