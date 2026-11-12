"""Expire snapshot ancestry without modifying workspace files or discarding retained trees."""

import base64
import json
import os
from pathlib import Path
import signal
import subprocess


def _git(repo: Path, *args: str, input: bytes | None = None, timeout: int = 20) -> bytes:
    env = os.environ.copy()
    for name in ("GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES"):
        env.pop(name, None)
    with subprocess.Popen(
        ["git", f"--git-dir={repo}", *args], stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, start_new_session=True,
    ) as process:
        try:
            stdout, stderr = process.communicate(input, timeout=timeout)
        except subprocess.TimeoutExpired:
            # GC spawns pack/repack children that must stop before the workspace lock releases.
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate()
            raise
        if process.returncode:
            raise RuntimeError(stderr.decode("utf-8", "replace").strip())
        return stdout


def object_stats(repo: Path) -> dict[str, int]:
    values = {}
    for line in _git(repo, "count-objects", "-v").decode().splitlines():
        key, _, value = line.partition(": ")
        if value.isdigit():
            values[key] = int(value)
    return {
        "bytes": 1024 * (values.get("size", 0) + values.get("size-pack", 0)),
        "loose_count": values.get("count", 0),
        "loose_kib": values.get("size", 0),
    }


def compact_repository(repo: Path, *, max_snapshots: int, max_age_days: int, now: float) -> dict[str, int]:
    """Caller holds the workspace lock through ref replacement, index reset and GC."""
    current_ref = "refs/heads/current"
    preserved_prefix = "refs/a0-time-travel/preserved/"
    stats = {"repositories_compacted": 0, "commits_expired": 0, "gc_runs": 0, "bytes_reclaimed": 0}
    if not (repo / "HEAD").is_file():
        return stats
    if repo.is_symlink() or any((repo / name).is_symlink() for name in ("objects", "refs")):
        raise RuntimeError("History storage contains a symlink; cleanup skipped.")
    if _git(repo, "symbolic-ref", "HEAD").decode().strip() != current_ref:
        raise RuntimeError("History HEAD is not attached to the current snapshot; cleanup skipped.")
    refs = dict(line.split() for line in _git(repo, "for-each-ref", "--format=%(refname) %(objectname)").decode().splitlines())
    if not refs:
        return stats
    if current_ref not in refs or any(ref != current_ref and not ref.startswith(preserved_prefix) for ref in refs):
        raise RuntimeError("History contains unmanaged references; cleanup skipped.")
    records = []
    for line in _git(repo, "log", "--all", "--date-order", "--format=%H %T %ct %P").decode().splitlines():
        commit, tree, stamp, *parents = line.split()
        if len(parents) > 1:
            raise RuntimeError("History contains merge commits; cleanup skipped.")
        records.append((commit, tree, int(stamp), parents[0] if parents else ""))
    cutoff = now - max_age_days * 86400 if max_age_days else float("-inf")
    recent = [record[0] for record in records if record[2] >= cutoff]
    if max_snapshots:
        recent = recent[:max_snapshots]
    keep = set(recent) | {refs[current_ref]}
    pending = repo.parent / "compaction.pending"
    before = object_stats(repo)
    mapping: dict[str, str] = {}
    checkpoints: dict[str, str] = {}

    def rewrite(commit: str, parent: str, *, checkpoint: bool = False) -> str:
        raw = _git(repo, "cat-file", "commit", commit)
        header, body = raw.split(b"\n\n", 1)
        lines = header.splitlines()
        if any(not line.startswith((b"tree ", b"parent ", b"author ", b"committer ", b"encoding ")) for line in lines):
            raise RuntimeError("History contains unsupported commit headers; cleanup skipped.")
        lines = [line for line in lines if not line.startswith(b"parent ")]
        if parent:
            lines.insert(1, f"parent {parent}".encode())
        if checkpoint:
            metadata = base64.b64encode(json.dumps({"retention_checkpoint": True}).encode())
            body = b"History checkpoint\n\nA0-Time-Travel-Metadata: " + metadata + b"\n"
        rewritten = b"\n".join(lines) + b"\n\n" + body
        if rewritten == raw:
            return commit
        pending.write_text("History compaction requires garbage collection.\n")
        return _git(repo, "hash-object", "-t", "commit", "-w", "--stdin", input=rewritten).decode().strip()

    if len(keep) < len(records):
        for commit, _tree, _stamp, parent in reversed(records):
            if commit not in keep:
                continue
            if not parent:
                mapping[commit] = commit
                continue
            if parent in keep:
                new_parent = mapping[parent]
            else:
                if parent not in checkpoints:
                    checkpoints[parent] = rewrite(parent, "", checkpoint=True)
                new_parent = checkpoints[parent]
            mapping[commit] = commit if new_parent == parent else rewrite(commit, new_parent)
        commands = ["start"]
        for ref, old in refs.items():
            if old not in keep:
                commands.append(f"delete {ref} {old}")
            elif mapping[old] != old:
                commands.append(f"update {ref} {mapping[old]} {old}")
        if len(commands) > 1:
            pending.write_text("History compaction requires garbage collection.\n")
            commands.extend(["prepare", "commit"])
            _git(repo, "update-ref", "--stdin", input=("\n".join(commands) + "\n").encode())
            stats["repositories_compacted"] = 1
            stats["commits_expired"] = len(records) - len(keep)

    if pending.exists() or before["loose_count"] > 256 or before["loose_kib"] > 65536:
        # The index and reflogs can otherwise keep expired blobs alive after ref replacement.
        _git(repo, "read-tree", current_ref)
        _git(repo, "reflog", "expire", "--expire=now", "--expire-unreachable=now", "--all")
        _git(repo, "-c", "pack.threads=1", "gc", "--prune=now", timeout=120)
        pending.unlink(missing_ok=True)
        stats["gc_runs"] = 1
        stats["bytes_reclaimed"] = max(0, before["bytes"] - object_stats(repo)["bytes"])
    return stats
