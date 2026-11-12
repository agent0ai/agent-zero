"""Recoverable, exact-owner legacy context/history quarantine. No v1 authority."""
from __future__ import annotations

import hashlib
import json
import os
import stat
import threading

from plugins._a0_connector.helpers.browser_bridge_legacy_retirement import (
    LegacyRetirementDenied, get_legacy_retirement,
)

LOCK = threading.RLock()
CONTEXT_KEYS = ("source", "chrome_browser_session_id", "chrome_extension_capabilities")
MAX_BYTES = 32 * 1024 * 1024
MAX_RECORDS = 10000
MAX_REMOVALS = 1024


def enabled():
    owner = get_legacy_retirement()
    try:
        with owner.lock:
            return owner._journal() is not None
    except Exception:
        return False  # Corrupt state is not permission to mutate unrelated chats.


def _encode(value):
    raw = json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")
    if len(raw) > MAX_BYTES:
        raise LegacyRetirementDenied("legacy_quarantine_limit")
    return raw


def _unique(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise LegacyRetirementDenied("legacy_quarantine_ambiguous")
        value[key] = item
    return value


def _tool_result(content):
    return (type(content) is dict and content.get("tool_name") == "chrome_bridge"
            and type(content.get("tool_result")) is str
            and type(content.get("browser_session_id")) is str
            and type(content.get("command_id")) is str
            and content.get("command_status") in {"completed", "failed"})


def _summary_tree(summary):
    if type(summary) is not str or '"image_data_url"' not in summary:
        return None
    if len(summary.encode("utf-8")) > MAX_BYTES:
        raise LegacyRetirementDenied("legacy_quarantine_limit")
    try:
        tree = json.loads(summary, object_pairs_hook=_unique)
    except (ValueError, TypeError):
        return None  # Never substring-redact prose or malformed historical text.
    return tree if _tool_result(tree) and "image_data_url" in tree else None


def _walk(node, path, budget, summaries):
    if type(node) is not dict:
        return
    budget[0] += 1
    if budget[0] > MAX_RECORDS or len(path) > 64:
        raise LegacyRetirementDenied("legacy_quarantine_limit")
    kind = node.get("_cls")
    if kind == "Message":
        content = node.get("content")
        if node.get("ai") is False and _tool_result(content):
            if "image_data_url" in content:
                yield content, "image_data_url", path + ["content", "image_data_url"]
            summary = _summary_tree(node.get("summary"))
            if summary is not None:
                summaries.append((node, summary))
                yield summary, "image_data_url", path + ["summary", "image_data_url"]
        return
    lists = {"History": ("bulks", "topics"), "Bulk": ("records",), "Topic": ("messages",)}.get(kind, ())
    for key in lists:
        children = node.get(key, [])
        if type(children) is not list:
            raise LegacyRetirementDenied("legacy_quarantine_ambiguous")
        for index, child in enumerate(children):
            yield from _walk(child, path + [key, index], budget, summaries)
    if kind == "History":
        yield from _walk(node.get("current"), path + ["current"], budget, summaries)


def _context_slots(data):
    if type(data) is dict and data.get("source") == "chrome_extension":
        for key in CONTEXT_KEYS:
            if key in data:
                yield data, key, ["data", key]


def _commit(context_id, slots, store):
    if not slots:
        return {"context_keys": 0, "screenshots": 0}
    if len(slots) > MAX_REMOVALS:
        raise LegacyRetirementDenied("legacy_quarantine_limit")
    # Shared Message/content objects can appear more than once in a live
    # history. Reject ambiguous recovery locations before backup or deletion;
    # never delete one alias and then fail with KeyError on another.
    identities = {(id(mapping), key) for mapping, key, _path in slots}
    if len(identities) != len(slots):
        raise LegacyRetirementDenied("legacy_quarantine_ambiguous")
    entries = [{"location": path, "value": mapping[key]} for mapping, key, path in slots]
    # Preserve precisely the removed values, not entire chats or user artifacts.
    raw = _encode({"contract": "a0.legacy-quarantine.v1", "context_id": context_id, "entries": entries})
    originals = [mapping[key] for mapping, key, _path in slots]
    store(raw)  # Durable private recovery copy must precede the first removal.
    if any(mapping.get(key) is not old for (mapping, key, _path), old in zip(slots, originals)):
        raise LegacyRetirementDenied("legacy_quarantine_changed")
    counts = {"context_keys": 0, "screenshots": 0}
    for mapping, key, _path in slots:
        del mapping[key]
        counts["screenshots" if key == "image_data_url" else "context_keys"] += 1
    return counts


def quarantine_document(document, *, store=None):
    """Sanitize a serialized context before deserialization; preserve other data."""
    if type(document) is not dict:
        raise LegacyRetirementDenied("legacy_quarantine_ambiguous")
    with LOCK:
        slots = list(_context_slots(document.get("data")))
        rewrites, summaries = [], []
        agents = document.get("agents", [])
        if type(agents) is not list or len(agents) > 64:
            raise LegacyRetirementDenied("legacy_quarantine_limit")
        budget = [0]
        for index, agent in enumerate(agents):
            if type(agent) is not dict:
                continue
            raw = agent.get("history")
            if type(raw) is not str or '"image_data_url"' not in raw or '"chrome_bridge"' not in raw:
                continue
            if len(raw.encode("utf-8")) > MAX_BYTES:
                raise LegacyRetirementDenied("legacy_quarantine_limit")
            tree = json.loads(raw, object_pairs_hook=_unique)
            history_slots = list(_walk(tree, ["agents", index, "history"], budget, summaries))
            if history_slots:
                slots.extend(history_slots)
                rewrites.append((agent, tree))
        counts = _commit(document.get("id"), slots, store or retain_private)
        for node, summary in summaries:
            node["summary"] = json.dumps(summary, ensure_ascii=False, separators=(",", ":"))
        for agent, tree in rewrites:
            agent["history"] = json.dumps(tree, ensure_ascii=False, separators=(",", ":"))
        return counts


def quarantine_context(context, *, store=None):
    """Remove exact live slots, including subordinate histories, after backup."""
    from helpers.history import History, Bulk, Topic, Message
    from agent import Agent
    with LOCK:
        slots = list(_context_slots(context.data))
        agent, seen, budget, changed_messages, summaries = context.agent0, set(), [0], [], []
        while agent is not None:
            if id(agent) in seen or len(seen) >= 64:
                raise LegacyRetirementDenied("legacy_quarantine_limit")
            index = len(seen)
            seen.add(id(agent))
            history = agent.history
            if type(history) is not History:
                raise LegacyRetirementDenied("legacy_quarantine_ambiguous")
            stack = [(history, ["agents", index, "history"])]
            while stack:
                record, path = stack.pop()
                budget[0] += 1
                if budget[0] > MAX_RECORDS or len(path) > 64:
                    raise LegacyRetirementDenied("legacy_quarantine_limit")
                if type(record) is Message:
                    if record.ai is False and _tool_result(record.content):
                        if "image_data_url" in record.content:
                            slots.append((record.content, "image_data_url", path + ["content", "image_data_url"]))
                            changed_messages.append(record)
                        summary = _summary_tree(record.summary)
                        if summary is not None:
                            slots.append((summary, "image_data_url", path + ["summary", "image_data_url"]))
                            summaries.append((record, summary))
                            changed_messages.append(record)
                    continue
                keys = ("bulks", "topics", "current") if type(record) is History else ("records",) if type(record) is Bulk else ("messages",) if type(record) is Topic else ()
                for key in keys:
                    children = getattr(record, key)
                    if key == "current":
                        stack.append((children, path + [key]))
                    elif type(children) is list:
                        stack.extend((child, path + [key, index]) for index, child in enumerate(children))
                    else:
                        raise LegacyRetirementDenied("legacy_quarantine_ambiguous")
            agent = agent.data.get(Agent.DATA_NAME_SUBORDINATE)
        counts = _commit(context.id, slots, store or retain_private)
        for record, summary in summaries:
            record.summary = json.dumps(summary, ensure_ascii=False, separators=(",", ":"))
        for message in changed_messages:
            message.tokens = 0
        return counts


def retain_private(raw, *, root=None):
    """Content-addressed private recovery blobs; never returned or auto-restored."""
    from helpers import files
    root = root or files.get_abs_path()
    if not hasattr(os, "O_NOFOLLOW") or len(raw) > MAX_BYTES:
        raise LegacyRetirementDenied("legacy_quarantine_unavailable")
    fds = []
    try:
        fds.append(os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW))
        fds.append(os.open("usr", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fds[-1]))
        name = "browser_bridge_legacy_quarantine"
        try:
            os.mkdir(name, 0o700, dir_fd=fds[-1])
            os.fsync(fds[-1])
        except FileExistsError:
            pass
        fds.append(os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fds[-1]))
        directory = os.fstat(fds[-1])
        if directory.st_uid != os.getuid() or stat.S_IMODE(directory.st_mode) & 0o077:
            raise LegacyRetirementDenied("legacy_quarantine_unavailable")
        name = hashlib.sha256(raw).hexdigest() + ".json"
        try:
            fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=fds[-1])
        except FileExistsError:
            fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=fds[-1])
            try:
                info = os.fstat(fd)
                if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077 or info.st_size != len(raw):
                    raise LegacyRetirementDenied("legacy_quarantine_unavailable")
                with os.fdopen(fd, "rb", closefd=False) as reader:
                    if reader.read(MAX_BYTES + 1) != raw:
                        raise LegacyRetirementDenied("legacy_quarantine_changed")
            finally:
                os.close(fd)
            return
        with os.fdopen(fd, "wb") as writer:
            writer.write(raw)
            writer.flush()
            os.fsync(writer.fileno())
        os.fsync(fds[-1])
    except Exception:
        raise LegacyRetirementDenied("legacy_quarantine_unavailable") from None
    finally:
        for fd in reversed(fds):
            os.close(fd)


def sweep_loaded(offset=0):
    """One explicit bounded page; dormant chats use the lazy load hook."""
    from agent import AgentContext
    from helpers import persist_chat
    if not enabled() or type(offset) is not int or not 0 <= offset <= MAX_RECORDS:
        raise LegacyRetirementDenied()
    contexts = sorted(AgentContext.all(), key=lambda item: item.id)
    if len(contexts) > MAX_RECORDS:
        raise LegacyRetirementDenied("legacy_quarantine_limit")
    counts = {"context_keys": 0, "screenshots": 0, "processed": 0}
    for context in contexts[offset:offset + 20]:
        result = quarantine_context(context)
        persist_chat.save_tmp_chat(context)
        for key in ("context_keys", "screenshots"):
            counts[key] += result[key]
        counts["processed"] += 1
    following = offset + counts["processed"]
    return {"scope": "currently_loaded_contexts", **counts,
            "next_offset": following if following < len(contexts) else None,
            "dormant_chats": "quarantined_on_next_load", "activation_ready": False}
