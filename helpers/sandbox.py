"""Shared sandbox API and CLI: python -m helpers.sandbox --help."""
from __future__ import annotations

import argparse
import dataclasses
import json
import time
from pathlib import Path

from plugins._sandboxing.helpers.images import SandboxImageError, image_info_dict
from plugins._sandboxing.helpers.manager import SandboxError, SandboxManager, SandboxMount, sandbox_info_dict


def get_manager() -> SandboxManager:
    from plugins._sandboxing.helpers.runtime import get_manager as configured_manager
    return configured_manager()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    commands.add_parser("list", help="List this Agent Zero instance's sandboxes")
    commands.add_parser("restore", help="Restore standalone sandboxes marked as running")
    image_import = commands.add_parser("import-image", help="Import a docker save archive into the sandbox image cache")
    image_import.add_argument("archive", type=Path)
    image_import.add_argument("reference", help="Cache reference, for example agent-zero-sandbox:local")
    create = commands.add_parser("create")
    create.add_argument("name")
    create.add_argument("--image", default="", help="Registry image; defaults to system configuration")
    create.add_argument("--standalone", action="store_true", help="Run detached; survive the caller and restore on A0 startup")
    create.add_argument("--network", choices=("host", "none"), default="host", help="host: internet and host loopback; none: offline")
    create.add_argument("--no-usr", action="store_true", help="Do not share Agent Zero usr/ at /a0/usr")
    create.add_argument("--host-root", action="store_true", help="Explicitly expose the host root at /host")
    create.add_argument("--temporary", action="store_true", help="Expire after the configured idle lifetime")
    create.add_argument("--command", nargs=argparse.REMAINDER, default=[])
    for action in ("inspect", "disk-usage", "start", "stop", "restart", "delete", "exec"):
        command = commands.add_parser(action)
        command.add_argument("name")
        if action == "exec":
            command.add_argument("argv", nargs=argparse.REMAINDER)
        if action == "delete":
            command.add_argument("--yes", action="store_true", required=True)
    args = parser.parse_args(argv)
    from helpers import dotenv
    dotenv.load_dotenv()
    try:
        manager = get_manager()
        if args.action == "list":
            result = [sandbox_info_dict(item) for item in manager.list()]
        elif args.action == "restore":
            result = manager.restore_standalone()
        elif args.action == "import-image":
            result = image_info_dict(manager.images.import_archive(args.archive, args.reference))
        elif args.action == "create":
            result = sandbox_info_dict(manager.create(
                args.name, image=args.image, standalone=args.standalone,
                sandbox_type="temporary" if args.temporary else "permanent",
                network=args.network, share_usr=not args.no_usr, host_root=args.host_root,
                command=args.command,
            ))
        elif args.action == "exec":
            result = dataclasses.asdict(manager.exec(args.name, args.argv))
        elif args.action == "delete":
            result = {"deleted": manager.delete(args.name)}
        elif args.action == "disk-usage":
            result = {"name": args.name, "size_bytes": manager.disk_usage(args.name)}
        else:
            result = sandbox_info_dict(getattr(manager, args.action)(args.name))
        print(json.dumps(result, indent=2), flush=True)
        if args.action in {"create", "start", "restart"} and not result.get("standalone"):
            try:
                while manager.is_running(args.name):
                    time.sleep(1)
            except KeyboardInterrupt:
                manager.stop(args.name)
                return 130
        return int(result.get("exit_code", 0)) if isinstance(result, dict) else 0
    except (SandboxError, SandboxImageError, OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
