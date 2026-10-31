"""Literal title and message search over the conversations shown in the sidebar."""

import re


def _excerpt(text, needle):
    position = text.casefold().find(needle)
    offset, start = 0, None
    for index, char in enumerate(text):
        end = offset + len(char.casefold())
        if start is None and end > position:
            start = index
        if end >= position + len(needle):
            stop = index + 1
            break
        offset = end
    left, right = max(0, start - 32), min(len(text), stop + 140)
    if left and (space := text.find(" ", left, start)) >= 0:
        left = space + 1
    if right < len(text) and (space := text.rfind(" ", stop, right)) >= 0:
        right = space
    raw = " ".join(text[left:right].split())
    plain = re.sub(r"(?m)^\s{0,3}(?:#{1,6}\s+|>\s?|[-*+]\s+|\d+[.)]\s+)", "", text[left:right])
    plain = re.sub(r"!?\[([^\]\n]*)\]\([^)\n]*\)", r"\1", plain)
    plain = re.sub(r"(\*\*|__|~~|`+)(?=\S)(.+?)(?<=\S)\1", r"\2", plain)
    plain = " ".join(plain.split())
    needle = " ".join(needle.split())
    # A literal query may target markup or a URL removed from the preview.
    if needle not in plain.casefold():
        plain = raw
    plain = ("… " if left else "") + plain + (" …" if right < len(text) else "")

    # Split on the server: casefold expansions and UTF-16 offsets must not shift highlights.
    owners = [index for index, char in enumerate(plain) for _ in char.casefold()]
    folded, parts, cursor, offset = plain.casefold(), [], 0, 0
    while (position := folded.find(needle, offset)) >= 0:
        start, stop = owners[position], owners[position + len(needle) - 1] + 1
        if start > cursor:
            parts.append({"text": plain[cursor:start], "match": False})
        if stop > cursor:
            parts.append({"text": plain[max(start, cursor):stop], "match": True})
        cursor, offset = stop, position + len(needle)
    if cursor < len(plain):
        parts.append({"text": plain[cursor:], "match": False})
    return parts


def search_contexts(contexts, query, titles):
    needle = query.casefold()
    matches = []
    for context in contexts:
        title = titles.get(context.id, context.name or "")
        if needle in title.casefold():
            matches.append({"id": context.id, "title": True, "parts": _excerpt(title, needle)})
            continue
        for entry in reversed(tuple(context.log.logs)):
            text = entry.content
            if not isinstance(text, str):
                continue
            if needle not in text.casefold():
                continue
            matches.append({"id": context.id, "title": False, "parts": _excerpt(text, needle)})
            break
    return matches
