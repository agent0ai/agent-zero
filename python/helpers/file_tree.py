from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
import os
from typing import Any, Callable, Iterable, Literal, Optional, Sequence

from pathspec import PathSpec

from python.helpers.files import get_abs_path

SORT_BY_NAME = "name"
SORT_BY_CREATED = "created"
SORT_BY_MODIFIED = "modified"

SORT_ASC = "asc"
SORT_DESC = "desc"

OUTPUT_MODE_STRING = "string"
OUTPUT_MODE_FLAT = "flat"
OUTPUT_MODE_NESTED = "nested"


def file_tree(
    relative_path: str,
    *,
    max_depth: int = 0,
    max_lines: int = 0,
    folders_first: bool = True,
    max_folders: int = 0,
    max_files: int = 0,
    sort: tuple[Literal["name", "created", "modified"], Literal["asc", "desc"]] = ("modified", "desc"),
    ignore: str | None = None,
    output_mode: Literal["string", "flat", "nested"] = OUTPUT_MODE_STRING,
) -> str | list[dict]:
    """Render a directory tree relative to the repository base path.

    Parameters:
        relative_path: Base directory (relative to project root) to scan with :func:`get_abs_path`.
        max_depth: Maximum depth of traversal (0 = unlimited). Depth starts at 1 for root entries.
        max_lines: Global limit for rendered lines (0 = unlimited). When exceeded, the current depth
            finishes rendering before deeper levels are skipped.
        folders_first: When True, folders render before files within each directory.
        max_folders: Optional per-directory cap (0 = unlimited) on rendered folder entries before adding a
            ``# N more folders`` comment. When only a single folder exceeds the limit and ``max_folders`` is greater than zero, that folder is rendered
            directly instead of emitting a summary comment.
        max_files: Optional per-directory cap (0 = unlimited) on rendered file entries before adding a ``# N more files`` comment.
            As with folders, a single excess file is rendered when ``max_files`` is greater than zero.
        sort: Tuple of ``(key, direction)`` where key is one of :data:`SORT_BY_NAME`,
            :data:`SORT_BY_CREATED`, or :data:`SORT_BY_MODIFIED`; direction is :data:`SORT_ASC`
            or :data:`SORT_DESC`.
        ignore: Inline ``.gitignore`` content or ``file:`` reference. Examples::

                ignore=\"\"\"\\n*.pyc\\n__pycache__/\\n!important.py\\n\"\"\"
                ignore=\"file:.gitignore\"         # relative to scan root
                ignore=\"file://.gitignore\"       # URI-style relative path
                ignore=\"file:/abs/path/.gitignore\"
                ignore=\"file:///abs/path/.gitignore\"

        output_mode: One of :data:`OUTPUT_MODE_STRING`, :data:`OUTPUT_MODE_FLAT`, or
            :data:`OUTPUT_MODE_NESTED`.

    Returns:
        ``OUTPUT_MODE_STRING`` → ``str``: multi-line ASCII tree.
        ``OUTPUT_MODE_FLAT`` → ``list[dict]``: flattened sequence of TreeItem dictionaries.
        ``OUTPUT_MODE_NESTED`` → ``list[dict]``: nested TreeItem dictionaries where folders
        include ``items`` arrays.

    Notes:
        * The utility is synchronous; avoid calling from latency-sensitive async loops.
        * The ASCII renderer walks the established tree depth-first so connectors reflect parent/child structure,
          while traversal and limit calculations remain breadth-first by depth. When ``max_lines`` is set, the number
          of non-comment entries (excluding the root banner) never exceeds that limit; informational summary comments
          are emitted in addition when necessary.
        * ``created`` and ``modified`` values in structured outputs are timezone-aware UTC
          :class:`datetime.datetime` objects::

                item = flat_items[0]
                iso = item[\"created\"].isoformat()
                epoch = item[\"created\"].timestamp()

    """
    abs_root = get_abs_path(relative_path)

    if not os.path.exists(abs_root):
        raise FileNotFoundError(f"Path does not exist: {relative_path!r}")
    if not os.path.isdir(abs_root):
        raise NotADirectoryError(f"Expected a directory, received: {relative_path!r}")

    sort_key, sort_direction = sort
    if sort_key not in {SORT_BY_NAME, SORT_BY_CREATED, SORT_BY_MODIFIED}:
        raise ValueError(f"Unsupported sort key: {sort_key!r}")
    if sort_direction not in {SORT_ASC, SORT_DESC}:
        raise ValueError(f"Unsupported sort direction: {sort_direction!r}")
    if output_mode not in {OUTPUT_MODE_STRING, OUTPUT_MODE_FLAT, OUTPUT_MODE_NESTED}:
        raise ValueError(f"Unsupported output mode: {output_mode!r}")
    if max_depth < 0:
        raise ValueError("max_depth must be >= 0")
    if max_lines < 0:
        raise ValueError("max_lines must be >= 0")

    ignore_spec = _resolve_ignore_patterns(ignore, abs_root)

    root_stat = os.stat(abs_root, follow_symlinks=False)
    root_name = os.path.basename(os.path.normpath(abs_root)) or os.path.basename(abs_root)
    root_node = _TreeEntry(
        name=root_name,
        level=0,
        item_type="folder",
        created=datetime.fromtimestamp(root_stat.st_ctime, tz=timezone.utc),
        modified=datetime.fromtimestamp(root_stat.st_mtime, tz=timezone.utc),
        parent=None,
        items=[],
        rel_path="",
    )

    queue: deque[tuple[_TreeEntry, str, int]] = deque([(root_node, abs_root, 1)])
    nodes_in_order: list[_TreeEntry] = []
    rendered_count = 0
    limit_reached = False
    visibility_cache: dict[str, bool] = {}

    def make_entry(entry: os.DirEntry, parent: _TreeEntry, level: int, item_type: Literal["file", "folder"]) -> _TreeEntry:
        stat = entry.stat(follow_symlinks=False)
        rel_path = os.path.relpath(entry.path, abs_root)
        rel_posix = _normalize_relative_path(rel_path)
        return _TreeEntry(
            name=entry.name,
            level=level,
            item_type=item_type,
            created=datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc),
            modified=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
            parent=parent,
            items=[] if item_type == "folder" else None,
            rel_path=rel_posix,
        )

    while queue and not limit_reached:
        parent_node, current_dir, level = queue.popleft()

        if max_depth and level > max_depth:
            continue

        remaining_depth = max_depth - level if max_depth else -1
        folders, files = _list_directory_children(
            current_dir,
            abs_root,
            ignore_spec,
            max_depth_remaining=remaining_depth,
            cache=visibility_cache,
        )

        folder_entries = [make_entry(folder, parent_node, level, "folder") for folder in folders]
        file_entries = [make_entry(file_entry, parent_node, level, "file") for file_entry in files]

        children = _apply_sorting_and_limits(
            folder_entries,
            file_entries,
            folders_first=folders_first,
            sort=sort,
            max_folders=max_folders,
            max_files=max_files,
            directory_node=parent_node,
        )

        trimmed_children: list[_TreeEntry] = []
        hidden_children_local: list[_TreeEntry] = []
        if max_lines and rendered_count >= max_lines:
            limit_reached = True
            hidden_children_local = children
        else:
            for index, child in enumerate(children):
                if max_lines and rendered_count >= max_lines:
                    limit_reached = True
                    hidden_children_local = children[index:]
                    break
                trimmed_children.append(child)
                nodes_in_order.append(child)
                is_global_summary = (
                    child.item_type == "comment"
                    and child.rel_path.endswith("#summary:limit")
                )
                if not is_global_summary:
                    rendered_count += 1
            if limit_reached and hidden_children_local:
                summary = _create_global_limit_comment(
                    parent_node,
                    hidden_children_local,
                )
                trimmed_children.append(summary)
                nodes_in_order.append(summary)

        parent_node.items = trimmed_children or None

        if limit_reached:
            break

        for child in trimmed_children:
            if child.item_type != "folder":
                continue
            if max_depth and level >= max_depth:
                continue
            child_abs = os.path.join(current_dir, child.name)
            queue.append((child, child_abs, level + 1))

    remaining_queue = list(queue) if limit_reached else []
    queue.clear()

    if limit_reached and remaining_queue:
        for folder_node, folder_path, _ in remaining_queue:
            summary = _create_folder_unprocessed_comment(
                folder_node,
                folder_path,
                abs_root,
                ignore_spec,
            )
            if summary is None:
                continue
            folder_node.items = (folder_node.items or []) + [summary]
            nodes_in_order.append(summary)

    visible_nodes = nodes_in_order

    visible_ids = {id(node) for node in visible_nodes}
    if visible_ids:
        _prune_to_visible(root_node, visible_ids)

    _mark_last_flags(root_node)
    _refresh_render_metadata(root_node)

    def iter_visible() -> Iterable[_TreeEntry]:
        for node in _iter_depth_first(root_node.items or []):
            if not visible_ids or id(node) in visible_ids:
                yield node

    if output_mode == OUTPUT_MODE_STRING:
        display_name = relative_path.strip() or root_name
        root_line = f"{display_name.rstrip(os.sep)}/"
        lines = [root_line]
        for node in iter_visible():
            lines.append(node.text)
        return "\n".join(lines)

    if output_mode == OUTPUT_MODE_FLAT:
        return _build_tree_items_flat(list(iter_visible()))

    return _to_nested_structure(root_node.items or [])


@dataclass(slots=True)
class _TreeEntry:
    name: str
    level: int
    item_type: Literal["file", "folder", "comment"]
    created: datetime
    modified: datetime
    parent: Optional["_TreeEntry"] = None
    items: Optional[list["_TreeEntry"]] = None
    is_last: bool = False
    rel_path: str = ""
    text: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "level": self.level,
            "type": self.item_type,
            "created": self.created,
            "modified": self.modified,
            "text": self.text,
            "items": [child.as_dict() for child in self.items] if self.items is not None else None,
        }


def _normalize_relative_path(path: str) -> str:
    normalized = path.replace(os.sep, "/")
    if normalized in {".", ""}:
        return ""
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def _directory_has_visible_entries(
    directory: str,
    root_abs_path: str,
    ignore_spec: PathSpec,
    cache: dict[str, bool],
    max_depth_remaining: int,
) -> bool:
    if max_depth_remaining == 0:
        return False

    cached = cache.get(directory)
    if cached is not None:
        return cached

    try:
        with os.scandir(directory) as iterator:
            for entry in iterator:
                rel_path = os.path.relpath(entry.path, root_abs_path)
                rel_posix = _normalize_relative_path(rel_path)
                is_dir = entry.is_dir(follow_symlinks=False)

                if is_dir:
                    ignored = ignore_spec.match_file(rel_posix) or ignore_spec.match_file(f"{rel_posix}/")
                    if ignored:
                        next_depth = max_depth_remaining - 1 if max_depth_remaining > 0 else -1
                        if next_depth == 0:
                            continue
                        if _directory_has_visible_entries(
                            entry.path,
                            root_abs_path,
                            ignore_spec,
                            cache,
                            next_depth,
                        ):
                            cache[directory] = True
                            return True
                        continue
                else:
                    if ignore_spec.match_file(rel_posix):
                        continue

                cache[directory] = True
                return True
    except FileNotFoundError:
        cache[directory] = False
        return False

    cache[directory] = False
    return False


def _create_summary_comment(parent: _TreeEntry, noun: str, count: int) -> _TreeEntry:
    label = noun
    if count == 1 and noun.endswith("s"):
        label = noun[:-1]
    elif count > 1 and not noun.endswith("s"):
        label = f"{noun}s"
    return _TreeEntry(
        name=f"{count} more {label}",
        level=parent.level + 1,
        item_type="comment",
        created=parent.created,
        modified=parent.modified,
        parent=parent,
        items=None,
        rel_path=f"{parent.rel_path}#summary:{noun}:{count}",
    )


def _create_global_limit_comment(parent: _TreeEntry, hidden_children: Sequence[_TreeEntry]) -> _TreeEntry:
    folders = sum(1 for child in hidden_children if child.item_type == "folder")
    files = sum(1 for child in hidden_children if child.item_type == "file")
    parts: list[str] = []
    if folders:
        label = "folder" if folders == 1 else "folders"
        parts.append(f"{folders} {label}")
    if files:
        label = "file" if files == 1 else "files"
        parts.append(f"{files} {label}")
    if not parts:
        remaining = len(hidden_children)
        label = "item" if remaining == 1 else "items"
        parts.append(f"{remaining} {label}")
    label_text = ", ".join(parts)
    return _TreeEntry(
        name=f"limit reached – hidden: {label_text}",
        level=parent.level + 1,
        item_type="comment",
        created=parent.created,
        modified=parent.modified,
        parent=parent,
        items=None,
        rel_path=f"{parent.rel_path}#summary:limit",
    )


def _create_folder_unprocessed_comment(
    folder_node: _TreeEntry,
    folder_path: str,
    abs_root: str,
    ignore_spec: Optional[PathSpec],
) -> Optional[_TreeEntry]:
    try:
        folders, files = _list_directory_children(
            folder_path,
            abs_root,
            ignore_spec,
            max_depth_remaining=-1,
            cache={},
        )
    except FileNotFoundError:
        return None

    hidden_entries: list[_TreeEntry] = []
    for entry in folders:
        stat = entry.stat(follow_symlinks=False)
        hidden_entries.append(
            _TreeEntry(
                name=entry.name,
                level=folder_node.level + 1,
                item_type="folder",
                created=datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc),
                modified=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
                parent=folder_node,
                items=None,
                rel_path=os.path.join(folder_node.rel_path, entry.name),
            )
        )
    for entry in files:
        stat = entry.stat(follow_symlinks=False)
        hidden_entries.append(
            _TreeEntry(
                name=entry.name,
                level=folder_node.level + 1,
                item_type="file",
                created=datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc),
                modified=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
                parent=folder_node,
                items=None,
                rel_path=os.path.join(folder_node.rel_path, entry.name),
            )
        )

    if not hidden_entries:
        return None

    return _create_global_limit_comment(folder_node, hidden_entries)


def _prune_to_visible(node: _TreeEntry, visible_ids: set[int]) -> None:
    if node.items is None:
        return
    filtered: list[_TreeEntry] = []
    for child in node.items:
        if not visible_ids or id(child) in visible_ids:
            _prune_to_visible(child, visible_ids)
            filtered.append(child)
    node.items = filtered or None


def _mark_last_flags(node: _TreeEntry) -> None:
    if node.items is None:
        return
    total = len(node.items)
    for index, child in enumerate(node.items):
        child.is_last = index == total - 1
        _mark_last_flags(child)


def _refresh_render_metadata(node: _TreeEntry) -> None:
    if node.items is None:
        return
    for child in node.items:
        child.text = _format_line(child)
        _refresh_render_metadata(child)


def _resolve_ignore_patterns(ignore: str | None, root_abs_path: str) -> Optional[PathSpec]:
    if ignore is None:
        return None

    content: str
    if ignore.startswith("file:"):
        reference = ignore[5:]
        if reference.startswith("///"):
            reference_path = reference[2:]
        elif reference.startswith("//"):
            reference_path = os.path.join(root_abs_path, reference[2:])
        elif reference.startswith("/"):
            reference_path = reference
        else:
            reference_path = os.path.join(root_abs_path, reference)

        try:
            with open(reference_path, "r", encoding="utf-8") as handle:
                content = handle.read()
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"Ignore file not found: {reference_path}") from exc
    else:
        content = ignore

    lines = [
        line.strip()
        for line in content.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

    if not lines:
        return None

    return PathSpec.from_lines("gitwildmatch", lines)


def _list_directory_children(
    directory: str,
    root_abs_path: str,
    ignore_spec: Optional[PathSpec],
    *,
    max_depth_remaining: int,
    cache: dict[str, bool],
) -> tuple[list[os.DirEntry], list[os.DirEntry]]:
    folders: list[os.DirEntry] = []
    files: list[os.DirEntry] = []

    try:
        with os.scandir(directory) as iterator:
            for entry in iterator:
                if entry.name in (".", ".."):
                    continue
                rel_path = os.path.relpath(entry.path, root_abs_path)
                rel_posix = _normalize_relative_path(rel_path)
                is_directory = entry.is_dir(follow_symlinks=False)

                if ignore_spec:
                    if is_directory:
                        ignored = ignore_spec.match_file(rel_posix) or ignore_spec.match_file(f"{rel_posix}/")
                        if ignored:
                            if _directory_has_visible_entries(
                                entry.path,
                                root_abs_path,
                                ignore_spec,
                                cache,
                                max_depth_remaining - 1,
                            ):
                                folders.append(entry)
                            continue
                    else:
                        if ignore_spec.match_file(rel_posix):
                            continue

                if is_directory:
                    folders.append(entry)
                else:
                    files.append(entry)
    except FileNotFoundError:
        return ([], [])

    return (folders, files)


def _apply_sorting_and_limits(
    folders: list[_TreeEntry],
    files: list[_TreeEntry],
    *,
    folders_first: bool,
    sort: tuple[str, str],
    max_folders: int | None,
    max_files: int | None,
    directory_node: _TreeEntry,
) -> list[_TreeEntry]:
    sort_key, sort_dir = sort
    reverse = sort_dir == SORT_DESC

    def key_fn(node: _TreeEntry):
        if sort_key == SORT_BY_NAME:
            return node.name.casefold()
        if sort_key == SORT_BY_CREATED:
            return node.created
        return node.modified

    folders_sorted = sorted(folders, key=key_fn, reverse=reverse)
    files_sorted = sorted(files, key=key_fn, reverse=reverse)
    combined: list[_TreeEntry] = []

    def append_group(group: list[_TreeEntry], limit: int | None, noun: str) -> None:
        if limit == 0:
            limit = None
        if not group:
            return
        if limit is None:
            combined.extend(group)
            return

        limit = max(limit, 0)
        visible = group[:limit]
        combined.extend(visible)

        overflow = group[limit:]
        if not overflow:
            return

        combined.append(
            _create_summary_comment(
                directory_node,
                noun,
                len(overflow),
            )
        )

    if folders_first:
        append_group(folders_sorted, max_folders, "folder")
        append_group(files_sorted, max_files, "file")
    else:
        append_group(files_sorted, max_files, "file")
        append_group(folders_sorted, max_folders, "folder")

    return combined


def _format_line(node: _TreeEntry) -> str:
    segments: list[str] = []
    ancestor = node.parent
    while ancestor and ancestor.parent is not None:
        segments.append("    " if ancestor.is_last else "│   ")
        ancestor = ancestor.parent
    segments.reverse()

    connector = "└── " if node.is_last else "├── "
    if node.item_type == "folder":
        label = f"{node.name}/"
    elif node.item_type == "comment":
        label = f"# {node.name}"
    else:
        label = node.name

    return "".join(segments) + connector + label


def _build_tree_items_flat(items: Sequence[_TreeEntry]) -> list[dict]:
    return [
        {
            "name": node.name,
            "level": node.level,
            "type": node.item_type,
            "created": node.created,
            "modified": node.modified,
            "text": node.text,
            "items": None,
        }
        for node in items
    ]


def _to_nested_structure(items: Sequence[_TreeEntry]) -> list[dict]:
    def convert(node: _TreeEntry) -> dict:
        children = None
        if node.items is not None:
            children = [convert(child) for child in node.items]
        return {
            "name": node.name,
            "level": node.level,
            "type": node.item_type,
            "created": node.created,
            "modified": node.modified,
            "text": node.text,
            "items": children,
        }

    return [convert(item) for item in items]


def _iter_depth_first(items: Sequence[_TreeEntry]) -> Iterable[_TreeEntry]:
    for node in items:
        yield node
        if node.items:
            yield from _iter_depth_first(node.items)
