"""Shared context helper used by both ApiHandler and WsHandler."""

import threading
from typing import Union

ThreadLockType = Union[threading.Lock, threading.RLock]


def use_context(lock: ThreadLockType, ctxid: str, create_if_not_exists: bool = True):
    from agent import AgentContext
    from initialize import initialize_agent

    with lock:
        if not ctxid:
            first = AgentContext.first()
            if first:
                AgentContext.use(first.id)
                return first
            context = AgentContext(config=initialize_agent(), set_current=True)
            return context
        got = AgentContext.use(ctxid)
        if got:
            return got
        if create_if_not_exists:
            context = AgentContext(
                config=initialize_agent(), id=ctxid, set_current=True
            )
            return context
        else:
            raise Exception(f"Context {ctxid} not found")
