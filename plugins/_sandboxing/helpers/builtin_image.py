"""Package the bundled sandbox image, or build it lazily through gVisor."""
from __future__ import annotations

import argparse
import dataclasses
from pathlib import Path
import tempfile
import uuid

BUILTIN_IMAGE = "agent-zero-sandbox:1"
BUNDLE_PATH = Path("/opt/agent-zero/sandbox-image")
PYTHON_IMAGE = "docker.io/library/python:3.13-slim-bookworm"
NODE_IMAGE = "docker.io/library/node:22-bookworm-slim"
ENVIRONMENT = (
    "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
    "LANG=C.UTF-8",
    "PIP_ROOT_USER_ACTION=ignore",
)


def package_rootfs(images, rootfs: Path, layout: Path, architecture: str) -> None:
    """Write a standard OCI layout from a stopped, trusted build filesystem."""
    layout.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="sandbox-layer-", dir=layout.parent) as temporary:
        layer = Path(temporary) / "rootfs.tar"
        commands = [
            ["tar", "--sort=name", "--numeric-owner", "-C", str(rootfs), "-cf", str(layer), "."],
            [str(images.config.umoci), "init", "--layout", str(layout)],
            [str(images.config.umoci), "new", "--image", f"{layout}:image"],
            [str(images.config.umoci), "raw", "add-layer", "--image", f"{layout}:image", str(layer)],
            [str(images.config.umoci), "config", "--image", f"{layout}:image",
             "--architecture", architecture, "--os", "linux",
             "--config.workingdir", "/workspace", "--config.cmd", "/bin/bash",
             *[argument for value in ENVIRONMENT for argument in ("--config.env", value)]],
            [str(images.config.umoci), "gc", "--layout", str(layout)],
        ]
        for command in commands:
            images._run(command, timeout=images.config.unpack_timeout, operation="package default sandbox image")


def build_image(images, directory: Path) -> Path:
    """Build without host package installs, a Docker daemon, or shared user data."""
    from plugins._sandboxing.helpers.images import SandboxImageError, SandboxImageManager
    from plugins._sandboxing.helpers.manager import SandboxConfig, SandboxError, SandboxManager, SandboxMount

    recipe = Path(__file__).resolve().parents[3] / "docker" / "sandbox"
    if not (recipe / "install.sh").is_file():
        raise SandboxImageError(f"default sandbox image recipe is missing at {recipe}")
    sources = SandboxImageManager(dataclasses.replace(
        images.config, cache_dir=directory / "sources", default_image=PYTHON_IMAGE,
    ))
    node = sources.ensure(NODE_IMAGE)
    with tempfile.TemporaryDirectory(prefix="a0-image-") as runtime:
        manager = SandboxManager(SandboxConfig(
            runsc=images.config.runsc,
            instances_dir=directory / "instances",
            runsc_root=Path(runtime),
            shared_dir=directory / "shared",
            default_image=PYTHON_IMAGE,
            instance_id=uuid.uuid4().hex[:12],
        ), sources)
        try:
            manager.create("build", service=True, share_usr=False, mounts=[
                SandboxMount(recipe, "/build"),
                SandboxMount(node.rootfs / "usr/local", "/node"),
            ])
            result = manager.exec("build", ["/bin/sh", "/build/install.sh"], timeout=images.config.pull_timeout)
            if result.exit_code:
                raise SandboxImageError(f"default sandbox image build failed: {result.stdout[-2000:]}\n{result.stderr[-2000:]}")
            manager.stop("build")
            layout = directory / "layout"
            package_rootfs(images, manager.config.instances_dir / "build/rootfs", layout, node.architecture)
            return layout
        except SandboxError as exc:
            raise SandboxImageError(f"cannot build default sandbox image: {exc}") from exc
        finally:
            manager.delete("build", missing_ok=True)


def main() -> None:
    from plugins._sandboxing.helpers.images import SandboxImageConfig, SandboxImageManager

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rootfs", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--architecture", choices=("amd64", "arm64"), required=True)
    args = parser.parse_args()
    images = SandboxImageManager(SandboxImageConfig(
        skopeo=Path("/usr/bin/skopeo"), umoci=Path("/usr/bin/umoci"),
        cache_dir=args.output.parent, default_image=BUILTIN_IMAGE,
    ))
    package_rootfs(images, args.rootfs, args.output, args.architecture)


if __name__ == "__main__":
    main()
