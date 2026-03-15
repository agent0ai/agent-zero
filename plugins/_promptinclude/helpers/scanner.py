"""Scan workdir for promptinclude files. No agent/tool dependencies."""

import fnmatch
import os
from typing import Literal, TypedDict

from pathspec import PathSpec

from helpers import tokens


# ------------------------------------------------------------------
# Types
# ------------------------------------------------------------------

class FileEntry(TypedDict):
    path: str
    content: str
    token_count: int
    status: Literal["ok", "cropped", "skipped"]


class ScanResult(TypedDict):
    files: list[FileEntry]
    skipped_count: int


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------

def scan_promptinclude_files(
    root: str,
    *,
    name_pattern: str = "*.promptinclude.md",
    max_depth: int = 10,
    max_file_tokens: int = 2000,
    max_file_count: int = 50,
    max_total_tokens: int = 8000,
    gitignore: str = "",
) -> ScanResult:
    ignore_spec = _build_ignore_spec(gitignore)
    matched = _find_matching_files(root, name_pattern, max_depth, ignore_spec)
    matched.sort()

    result_files: list[FileEntry] = []
    total_tokens_used = 0
    skipped_count = 0
    budget_exhausted = False

    for path in matched:
        if budget_exhausted or len(result_files) >= max_file_count:
            skipped_count += 1
            continue

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                raw = f.read()
        except (OSError, IOError):
            skipped_count += 1
            continue

        if not raw.strip():
            continue

        file_tokens = tokens.count_tokens(raw)

        # check if adding path line alone exceeds budget
        path_tokens = tokens.count_tokens(path) + 5  # overhead for formatting
        if total_tokens_used + path_tokens > max_total_tokens:
            skipped_count += 1
            budget_exhausted = True
            continue

        # per-file token cap
        capped = min(file_tokens, max_file_tokens)

        if total_tokens_used + path_tokens + capped > max_total_tokens:
            # try to fit partial
            remaining = max_total_tokens - total_tokens_used - path_tokens
            if remaining > 50:
                trimmed = tokens.trim_to_tokens(raw, remaining, direction="start")
                trimmed_count = tokens.count_tokens(trimmed)
                total_tokens_used += path_tokens + trimmed_count
                result_files.append(FileEntry(
                    path=path, content=trimmed,
                    token_count=trimmed_count, status="cropped",
                ))
            else:
                result_files.append(FileEntry(
                    path=path, content="",
                    token_count=0, status="skipped",
                ))
            budget_exhausted = True
            continue

        if capped < file_tokens:
            trimmed = tokens.trim_to_tokens(raw, max_file_tokens, direction="start")
            trimmed_count = tokens.count_tokens(trimmed)
            total_tokens_used += path_tokens + trimmed_count
            result_files.append(FileEntry(
                path=path, content=trimmed,
                token_count=trimmed_count, status="cropped",
            ))
        else:
            total_tokens_used += path_tokens + file_tokens
            result_files.append(FileEntry(
                path=path, content=raw,
                token_count=file_tokens, status="ok",
            ))

    # remaining unprocessed files from matched list
    remaining_unprocessed = len(matched) - len(result_files) - skipped_count
    if remaining_unprocessed > 0:
        skipped_count += remaining_unprocessed

    return ScanResult(files=result_files, skipped_count=skipped_count)


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------

def _build_ignore_spec(gitignore: str) -> PathSpec | None:
    if not gitignore or not gitignore.strip():
        return None
    lines = [
        line.strip()
        for line in gitignore.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    if not lines:
        return None
    return PathSpec.from_lines("gitwildmatch", lines)


def _find_matching_files(
    root: str,
    name_pattern: str,
    max_depth: int,
    ignore_spec: PathSpec | None,
) -> list[str]:
    root = os.path.abspath(root)
    if not os.path.isdir(root):
        return []

    results: list[str] = []

    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        depth = dirpath[len(root):].count(os.sep)
        if depth >= max_depth:
            dirnames.clear()
            continue

        # filter ignored dirs in-place
        if ignore_spec:
            filtered_dirs = []
            for d in dirnames:
                rel = os.path.relpath(os.path.join(dirpath, d), root)
                rel_posix = rel.replace(os.sep, "/")
                if ignore_spec.match_file(rel_posix) or ignore_spec.match_file(f"{rel_posix}/"):
                    continue
                filtered_dirs.append(d)
            dirnames[:] = filtered_dirs

        for fname in filenames:
            if not fnmatch.fnmatch(fname, name_pattern):
                continue
            full = os.path.join(dirpath, fname)
            if ignore_spec:
                rel = os.path.relpath(full, root)
                rel_posix = rel.replace(os.sep, "/")
                if ignore_spec.match_file(rel_posix):
                    continue
            results.append(full)

    return results
