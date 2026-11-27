"""Paragraph, line and word splitting shared by knowledge import and the document worker."""
from collections import deque


def split_text(text, size=4000, overlap=200, separators=("\n\n", "\n", " ", "")):
    separator = next(s for s in separators if not s or s in text)
    if separator:
        first, *rest = text.split(separator)
        pieces = [first, *(separator + part for part in rest)]
    else:
        pieces = text
    remaining = separators[separators.index(separator) + 1:]
    result = []
    group = deque()
    length = 0

    def flush():
        chunk = "".join(group).strip()
        if chunk:
            result.append(chunk)

    for piece in pieces:
        if not piece:
            continue
        if len(piece) >= size:
            flush()
            group.clear()
            length = 0
            if remaining:
                result.extend(split_text(piece, size, overlap, remaining))
            else:
                result.append(piece)
            continue
        if length + len(piece) > size:
            flush()
            while group and (length > overlap or length + len(piece) > size):
                length -= len(group.popleft())
        group.append(piece)
        length += len(piece)
    flush()
    return result


def _number(config, key, minimum, default):
    try:
        value = int(config.get(key, default))
    except (TypeError, ValueError):
        return default
    return value if value >= minimum else default


def index_chunks(text, config):
    size = _number(config, "chunk_size", 1, 1000)
    overlap = min(_number(config, "chunk_overlap", 0, 100), size - 1)
    maximum = _number(config, "max_index_chunks", 0, 1200)
    chunks = split_text(text, size, overlap)
    if not maximum or len(chunks) <= maximum:
        return chunks
    ratio = min(overlap / size, 0.5)
    size = max(size + 1, int(len(text) / (maximum * (1 - ratio))) + 1)
    for _ in range(8):
        chunks = split_text(text, size, min(int(size * ratio), size - 1))
        if len(chunks) <= maximum or size >= len(text):
            break
        size = min(len(text), int(size * 1.25) + 1)
    return chunks
