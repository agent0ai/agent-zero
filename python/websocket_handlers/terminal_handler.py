from __future__ import annotations
import asyncio
import os
import time
from python.helpers.print_style import PrintStyle
from python.helpers.websocket import WebSocketHandler, WebSocketResult
from python.helpers.tty_session import TTYSession

_SESSIONS: dict[str, object] = {}
_SESSION_TTL = 86400


class _Entry:
    def __init__(self, session_id, tty):
        self.session_id = session_id
        self.tty = tty
        self.last_active = time.time()
        self.current_sid = None
        self.current_handler = None
        self.pump_task = None
        self.mouse_enabled = False

    def touch(self):
        self.last_active = time.time()

    def is_alive(self):
        proc = getattr(self.tty, '_proc', None)
        if proc is None:
            return False
        return getattr(proc, 'returncode', None) is None


def _cull():
    now = time.time()
    dead = [k for k, e in _SESSIONS.items()
            if not e.is_alive() or (now - e.last_active) > _SESSION_TTL]
    for k in dead:
        try:
            asyncio.ensure_future(_SESSIONS[k].tty.close())
        except Exception:
            pass
        del _SESSIONS[k]


class TerminalHandler(WebSocketHandler):

    @classmethod
    def get_event_types(cls):
        return ["terminal_start", "terminal_input", "terminal_resize", "terminal_stop", "terminal_redraw"]

    async def on_disconnect(self, sid):
        for e in _SESSIONS.values():
            if e.current_sid == sid:
                e.current_sid = None
                e.current_handler = None

    async def process_event(self, event_type, data, sid):
        if event_type == "terminal_start":
            return await self._start(sid, data)
        if event_type == "terminal_input":
            return await self._input(sid, data)
        if event_type == "terminal_resize":
            return await self._resize(sid, data)
        if event_type == "terminal_stop":
            return await self._stop(sid, data)
        if event_type == "terminal_redraw":
            return await self._redraw(sid, data)

    async def _start(self, sid, data):
        session_id = data.get("session_id") or "default"
        shell = data.get("shell", "/bin/bash")
        cols = int(data.get("cols", 80))
        rows = int(data.get("rows", 24))

        _cull()
        entry = _SESSIONS.get(session_id)

        if entry and entry.is_alive():
            entry.touch()
            entry.current_sid = sid
            entry.current_handler = self
            if entry.pump_task and not entry.pump_task.done():
                entry.pump_task.cancel()
                try:
                    await asyncio.wait_for(asyncio.shield(entry.pump_task), 0.5)
                except Exception:
                    pass
            entry.pump_task = asyncio.ensure_future(self._pump(entry))
            # Do NOT resize here - terminal_redraw will fire from client once
            # the pump is running and xterm is ready to receive the full repaint
            PrintStyle.info(f"[Terminal] reattached session={session_id} mouse={entry.mouse_enabled}")
            return self.result_ok({"status": "reattached", "session_id": session_id, "mouse_enabled": entry.mouse_enabled})

        if entry:
            try:
                await entry.tty.close()
            except Exception:
                pass
            del _SESSIONS[session_id]

        env = {**os.environ.copy(),
               "TERM": "xterm-256color", "COLORTERM": "truecolor", "LANG": "en_US.UTF-8"}
        tty = TTYSession(shell, env=env, echo=True)
        await tty.start()
        try:
            tty.resize(cols, rows)
        except Exception:
            pass

        entry = _Entry(session_id, tty)
        entry.current_sid = sid
        entry.current_handler = self
        _SESSIONS[session_id] = entry
        entry.pump_task = asyncio.ensure_future(self._pump(entry))
        PrintStyle.info(f"[Terminal] started session={session_id}")
        return self.result_ok({"status": "started", "session_id": session_id})

    async def _input(self, sid, data):
        entry = _SESSIONS.get(data.get("session_id", "default"))
        if entry and entry.is_alive():
            entry.touch()
            await entry.tty.send(data.get("input", ""))

    async def _resize(self, sid, data):
        entry = _SESSIONS.get(data.get("session_id", "default"))
        if entry and entry.is_alive():
            entry.touch()
            try:
                entry.tty.resize(int(data.get("cols", 80)), int(data.get("rows", 24)))
            except Exception:
                pass

    async def _stop(self, sid, data):
        entry = _SESSIONS.pop(data.get("session_id", "default"), None)
        if entry:
            if entry.pump_task and not entry.pump_task.done():
                entry.pump_task.cancel()
            try:
                await entry.tty.close()
            except Exception:
                pass
        return self.result_ok({})

    async def _redraw(self, sid, data):
        """Resize PTY to post-layout dimensions. TIOCSWINSZ automatically
        delivers SIGWINCH to the foreground process, causing htop/nano/vim
        to fully redraw at the correct size."""
        entry = _SESSIONS.get(data.get("session_id", "default"))
        if not entry or not entry.is_alive():
            return
        entry.touch()
        cols, rows = data.get("cols"), data.get("rows")
        if cols and rows:
            try:
                entry.tty.resize(int(cols), int(rows))
            except Exception:
                pass

    async def _pump(self, entry):
        try:
            while entry.is_alive():
                chunk = await entry.tty.read(timeout=0.05)
                if chunk:
                    entry.touch()
                    sid, handler = entry.current_sid, entry.current_handler
                    # Track mouse mode state from PTY output
                    if '1000h' in chunk:
                        entry.mouse_enabled = True
                    if '1000l' in chunk:
                        entry.mouse_enabled = False
                    if sid and handler:
                        try:
                            await handler.emit_to(sid, "terminal_output", {
                                "output": chunk,
                                "session_id": entry.session_id,
                            })
                        except Exception:
                            pass
        except asyncio.CancelledError:
            pass
        finally:
            sid, handler = entry.current_sid, entry.current_handler
            if sid and handler:
                try:
                    await handler.emit_to(sid, "terminal_exit",
                                          {"session_id": entry.session_id})
                except Exception:
                    pass
