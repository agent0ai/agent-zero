from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import pytest

from plugins._sandboxing.helpers import builtin_image
from plugins._sandboxing.helpers.images import SandboxImageError
from tests.test_sandboxing import IMAGE_DIGEST, manager


@pytest.mark.parametrize("bundle_state", ["ready", "missing", "broken"])
def test_default_image_uses_bundle_or_builds_once_then_reuses_cache(manager, monkeypatch, tmp_path, bundle_state):
    images = manager.images
    images.config = dataclasses.replace(images.config, default_image=builtin_image.BUILTIN_IMAGE)
    bundle = tmp_path / "bundled"
    monkeypatch.setattr(builtin_image, "BUNDLE_PATH", bundle)
    if bundle_state != "missing":
        bundle.mkdir()
    builds = []
    sources = []

    def build(images, directory):
        builds.append(directory)
        return directory / "rebuilt"

    def run(argv, **kwargs):
        if "inspect" in argv:
            sources.append(argv[-1])
            if bundle_state == "broken" and argv[-1] == f"oci:{bundle}:image":
                raise SandboxImageError("damaged bundle")
            return 0, json.dumps({"Digest": IMAGE_DIGEST, "Os": "linux", "Architecture": "amd64"}), "", False
        if "unpack" in argv:
            unpacked = Path(argv[-1])
            (unpacked / "rootfs/bin").mkdir(parents=True)
            for shell in ("sh", "bash"):
                (unpacked / "rootfs/bin" / shell).touch()
            (unpacked / "config.json").write_text(json.dumps({"process": {"env": list(builtin_image.ENVIRONMENT)}}))
        return 0, "", "", False

    # Remove the fixture's image so the real unpack/validation/cache path runs.
    images.delete(IMAGE_DIGEST)
    monkeypatch.setattr(images, "_run", run)
    monkeypatch.setattr(builtin_image, "build_image", build)
    first = images.ensure()
    assert first.reference == builtin_image.BUILTIN_IMAGE
    assert first.environment == builtin_image.ENVIRONMENT
    assert len(builds) == (0 if bundle_state == "ready" else 1)
    calls = len(sources)
    assert images.ensure().digest == first.digest
    assert len(sources) == calls
    assert all(source.startswith("oci:") for source in sources)
    assert not list(images.config.cache_dir.glob(".pull-*"))


def test_failed_default_build_leaves_no_cache_alias(manager, monkeypatch, tmp_path):
    images = manager.images
    monkeypatch.setattr(builtin_image, "BUNDLE_PATH", tmp_path / "missing")

    def fail(*args):
        raise SandboxImageError("build failed")

    monkeypatch.setattr(builtin_image, "build_image", fail)
    with pytest.raises(SandboxImageError, match="build failed"):
        images.ensure(builtin_image.BUILTIN_IMAGE)
    with pytest.raises(SandboxImageError, match="not cached"):
        images.inspect(builtin_image.BUILTIN_IMAGE)
    assert not list(images.config.cache_dir.glob(".pull-*"))


def test_rebuilt_default_never_replaces_a_missing_pinned_digest(manager, monkeypatch, tmp_path):
    images = manager.images
    monkeypatch.setattr(builtin_image, "BUNDLE_PATH", tmp_path / "missing")
    monkeypatch.setattr(builtin_image, "build_image", lambda images, directory: directory / "layout")
    monkeypatch.setattr(images, "_run", lambda *args, **kwargs: (
        0, json.dumps({"Digest": IMAGE_DIGEST}), "", False,
    ))
    expected = "sha256:" + "b" * 64
    with pytest.raises(SandboxImageError, match=f"expected {expected}"):
        images.ensure(builtin_image.BUILTIN_IMAGE, digest=expected)
    assert images.inspect(IMAGE_DIGEST).digest == IMAGE_DIGEST


def test_docker_builds_bundle_the_same_recipe_as_lazy_builds():
    root = Path(__file__).resolve().parents[1]
    for name in ("DockerfileLocal", "docker/run/Dockerfile"):
        dockerfile = (root / name).read_text()
        assert f"FROM {builtin_image.PYTHON_IMAGE.removeprefix('docker.io/library/')} AS sandbox-rootfs" in dockerfile
        assert f"FROM {builtin_image.NODE_IMAGE.removeprefix('docker.io/library/')} AS sandbox-node" in dockerfile
        assert "/docker/sandbox/install.sh" in dockerfile
        assert f"--output {builtin_image.BUNDLE_PATH}" in dockerfile
        assert f"chmod -R a+rX {builtin_image.BUNDLE_PATH}" in dockerfile
    assert f"default_image: {builtin_image.BUILTIN_IMAGE}" in (root / "plugins/_sandboxing/default_config.yaml").read_text()
