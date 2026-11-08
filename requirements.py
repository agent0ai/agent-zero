from pathlib import Path
import sys

import depfix

def _activate():
    requirements = Path(__file__).with_name("requirements.txt")
    try:
        depfix.default_requirements(requirements)
    except depfix.SharedImportConflictError as error:
        import os

        bootstrap_names = {"depfix", "packaging", "pathspec", "platformdirs", "uv"}
        entrypoints = {"prepare.py", "preload.py", "run_ui.py", "run_tunnel.py"}
        script = Path(sys.argv[0]).resolve()
        if (
            script.parent != requirements.parent.resolve()
            or script.name not in entrypoints
            or error.manifest is None
            or os.environ.get("A0_DEPFIX_BOOTSTRAP") == str(error.manifest)
            or not error.candidates
            or any(item.partition(":")[0] not in bootstrap_names for item in error.candidates)
        ):
            raise

        # The verified graph must own the loader too; restart before application imports.
        # shortcut: pinned Depfix manifest/cache APIs; recheck them on dependency upgrades.
        from depfix.cache import Cache
        from depfix.manifest import load_manifest
        from depfix.settings import resolve_settings

        graph = load_manifest(error.manifest)
        cache = Cache(resolve_settings().cache_dir)
        pending = [node.id for node in graph.nodes if node.distribution == "depfix"]
        if not pending:
            raise
        visited = set()
        paths = []
        while pending:
            node_id = pending.pop()
            if node_id in visited:
                continue
            visited.add(node_id)
            node = graph.node_index[node_id]
            for category in ("purelib", "platlib"):
                path = cache.unpacked_path(node.artifact) / category
                if path.is_dir() and str(path) not in paths:
                    paths.append(str(path))
            pending.extend(node.dependencies.values())
        env = os.environ.copy()
        if env.get("PYTHONPATH"):
            paths.append(env["PYTHONPATH"])
        env["PYTHONPATH"] = os.pathsep.join(paths)
        env["A0_DEPFIX_BOOTSTRAP"] = str(error.manifest)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        os.execve(sys.executable, [sys.executable, *sys.orig_argv[1:]], env)


if sys.platform == "linux":
    import fcntl

    # Cold graph verification can outlast Depfix's cache-writer timeout.
    lock_path = Path(__file__).with_name("tmp") / "requirements.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        _activate()
else:
    _activate()
