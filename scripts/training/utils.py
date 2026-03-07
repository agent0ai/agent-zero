"""Shared utilities for the training data extraction pipeline."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import tiktoken

from .config import TAXONOMY_KEYWORDS

_ENCODER = tiktoken.get_encoding("cl100k_base")


# ── Data classes ──────────────────────────────────────────────────────────────


@dataclass
class CodeChunk:
    """A chunk extracted from a source code file."""

    source_file: str
    name: str  # function/class name
    content: str
    context: str = ""  # surrounding code for reference
    language: str = "javascript"
    chunk_type: str = "code"
    extra: dict = field(default_factory=dict)


@dataclass
class DocChunk:
    """A chunk extracted from a documentation file."""

    source_file: str
    heading: str
    content: str
    context: str = ""
    chunk_type: str = "documentation"
    extra: dict = field(default_factory=dict)


# ── File I/O ──────────────────────────────────────────────────────────────────


def read_file(path: str | Path) -> str:
    """Read a file and return its contents as a string."""
    return Path(path).read_text(encoding="utf-8", errors="replace")


def write_jsonl(records: list[dict], path: str | Path) -> None:
    """Write a list of dicts to a JSONL file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def read_jsonl(path: str | Path) -> list[dict]:
    """Read a JSONL file and return a list of dicts."""
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


# ── Token counting ────────────────────────────────────────────────────────────


def count_tokens(text: str) -> int:
    """Count tokens using tiktoken cl100k_base encoding."""
    return len(_ENCODER.encode(text, disallowed_special=()))


# ── Hashing / dedup ──────────────────────────────────────────────────────────


def content_hash(text: str) -> str:
    """SHA-256 hash of text content for deduplication."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


# ── Chunking ──────────────────────────────────────────────────────────────────


def chunk_by_function(code: str, language: str = "javascript") -> list[CodeChunk]:
    """Split source code into chunks by function/class definition.

    Supports JavaScript (function, class, const/let arrow functions)
    and Python (def, class).
    """
    if language == "python":
        return _chunk_python(code)
    return _chunk_javascript(code)


def _chunk_javascript(code: str) -> list[CodeChunk]:
    """Chunk JavaScript/Node.js code by function/class boundaries."""
    chunks: list[CodeChunk] = []
    lines = code.split("\n")

    # Patterns for JS function/class boundaries
    patterns = [
        re.compile(r"^\s*(export\s+)?(default\s+)?class\s+(\w+)"),
        re.compile(r"^\s*(export\s+)?(default\s+)?function\s+(\w+)"),
        re.compile(r"^\s*(export\s+)?(const|let|var)\s+(\w+)\s*=\s*(async\s+)?\("),
        re.compile(r"^\s*(export\s+)?(const|let|var)\s+(\w+)\s*=\s*(async\s+)?function"),
        re.compile(r"^\s*(async\s+)?(\w+)\s*\(.*\)\s*\{"),
    ]

    boundaries: list[tuple[int, str]] = []
    for i, line in enumerate(lines):
        for pat in patterns:
            m = pat.match(line)
            if m:
                name = m.group(m.lastindex) if m.lastindex else "unknown"
                # Use the last named group that's an identifier
                for g in reversed(m.groups()):
                    if (
                        g
                        and re.match(r"^\w+$", g)
                        and g not in ("export", "default", "const", "let", "var", "async", "function")
                    ):
                        name = g
                        break
                boundaries.append((i, name))
                break

    if not boundaries:
        # No functions found — return whole file as one chunk
        if code.strip():
            chunks.append(
                CodeChunk(
                    source_file="",
                    name="module",
                    content=code,
                    language="javascript",
                )
            )
        return chunks

    for idx, (start, name) in enumerate(boundaries):
        end = boundaries[idx + 1][0] if idx + 1 < len(boundaries) else len(lines)
        chunk_content = "\n".join(lines[start:end]).strip()
        # Context: 3 lines before the function start
        ctx_start = max(0, start - 3)
        context = "\n".join(lines[ctx_start:start]).strip()
        if chunk_content:
            chunks.append(
                CodeChunk(
                    source_file="",
                    name=name,
                    content=chunk_content,
                    context=context,
                    language="javascript",
                )
            )

    return chunks


def _chunk_python(code: str) -> list[CodeChunk]:
    """Chunk Python code by function/class boundaries."""
    chunks: list[CodeChunk] = []
    lines = code.split("\n")

    patterns = [
        re.compile(r"^(class)\s+(\w+)"),
        re.compile(r"^(def)\s+(\w+)"),
        re.compile(r"^(async\s+def)\s+(\w+)"),
    ]

    boundaries: list[tuple[int, str]] = []
    for i, line in enumerate(lines):
        for pat in patterns:
            m = pat.match(line)
            if m:
                boundaries.append((i, m.group(2)))
                break

    if not boundaries:
        if code.strip():
            chunks.append(
                CodeChunk(
                    source_file="",
                    name="module",
                    content=code,
                    language="python",
                )
            )
        return chunks

    for idx, (start, name) in enumerate(boundaries):
        end = boundaries[idx + 1][0] if idx + 1 < len(boundaries) else len(lines)
        chunk_content = "\n".join(lines[start:end]).strip()
        ctx_start = max(0, start - 3)
        context = "\n".join(lines[ctx_start:start]).strip()
        if chunk_content:
            chunks.append(
                CodeChunk(
                    source_file="",
                    name=name,
                    content=chunk_content,
                    context=context,
                    language="python",
                )
            )

    return chunks


def chunk_by_heading(markdown: str, level: int = 2) -> list[DocChunk]:
    """Split markdown into chunks by heading level (default H2)."""
    prefix = "#" * level + " "
    lines = markdown.split("\n")
    chunks: list[DocChunk] = []

    current_heading = "Introduction"
    current_lines: list[str] = []

    for line in lines:
        if line.startswith(prefix):
            # Save previous chunk
            content = "\n".join(current_lines).strip()
            if content:
                chunks.append(
                    DocChunk(
                        source_file="",
                        heading=current_heading,
                        content=content,
                    )
                )
            current_heading = line[len(prefix) :].strip()
            current_lines = []
        else:
            current_lines.append(line)

    # Save last chunk
    content = "\n".join(current_lines).strip()
    if content:
        chunks.append(
            DocChunk(
                source_file="",
                heading=current_heading,
                content=content,
            )
        )

    return chunks


# ── Taxonomy classification ──────────────────────────────────────────────────


def classify_taxonomy(text: str, extra_context: str = "") -> str:
    """Classify text into a taxonomy category using keyword matching.

    Returns the best-matching taxonomy path (e.g.,
    'skills.architecture_design.microservices_decomposition').
    Falls back to 'knowledge.technology_preferences.framework_selection_criteria'
    if no keywords match.
    """
    combined = (text + " " + extra_context).lower()
    best_category = ""
    best_score = 0

    for category, keywords in TAXONOMY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw.lower() in combined)
        if score > best_score:
            best_score = score
            best_category = category

    return best_category or "knowledge.technology_preferences.framework_selection_criteria"


# ── Chunk → dict conversion ─────────────────────────────────────────────────


def chunk_to_record(
    chunk: CodeChunk | DocChunk,
    taxonomy_category: str | None = None,
    **extra_fields: str,
) -> dict:
    """Convert a chunk dataclass to a JSONL-ready dict."""
    text = chunk.content
    category = taxonomy_category or classify_taxonomy(text, getattr(chunk, "context", ""))
    record = {
        "source_file": chunk.source_file,
        "chunk_type": chunk.chunk_type,
        "taxonomy_category": category,
        "content": chunk.content,
        "context": getattr(chunk, "context", ""),
        "token_count": count_tokens(text),
    }
    record.update(chunk.extra)
    record.update(extra_fields)
    return record
