from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import pytest

from plugins._sandboxing.helpers import builtin_image
from plugins._sandboxing.helpers.images import SandboxImageError
from plugins._sandboxing.helpers.runtime import normalize_config
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
            rootfs = Path(argv[-1])
            (rootfs / "bin").mkdir(parents=True)
            for shell in ("sh", "bash"):
                (rootfs / "bin" / shell).touch()
        if "runtime-config" in argv:
            Path(argv[-1]).write_text(json.dumps({"process": {"env": list(builtin_image.ENVIRONMENT)}}))
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
    dockerfile = (root / "Dockerfile").read_text()
    assert f"FROM {builtin_image.PYTHON_IMAGE.removeprefix('docker.io/library/')} AS sandbox-rootfs" in dockerfile
    assert f"FROM {builtin_image.NODE_IMAGE.removeprefix('docker.io/library/')} AS node-runtime" in dockerfile
    assert "source=docker/sandbox/install.sh" in dockerfile
    recipe = (root / "docker/sandbox/install.sh").read_text()
    assert "git --version" in recipe
    assert "rg --version" in recipe
    assert f"--output {builtin_image.BUNDLE_PATH}" in dockerfile
    assert f"chmod -R a+rX {builtin_image.BUNDLE_PATH}" in dockerfile
    assert f"default_image: {builtin_image.BUILTIN_IMAGE}" in (root / "plugins/_sandboxing/default_config.yaml").read_text()


@pytest.mark.parametrize("legacy", builtin_image.LEGACY_BUILTIN_IMAGES)
def test_legacy_default_preserves_pinned_images(manager, monkeypatch, legacy):
    assert normalize_config({"default_image": legacy})["default_image"] == builtin_image.BUILTIN_IMAGE
    assert normalize_config({"default_image": "my-image:1"})["default_image"] == "my-image:1"

    def no_pull(*args, **kwargs):
        pytest.fail("Legacy built-in images must resolve from the local cache")

    monkeypatch.setattr(manager.images, "_pull_locked", no_pull)
    assert manager.images.ensure(legacy, digest=IMAGE_DIGEST).digest == IMAGE_DIGEST
    with pytest.raises(SandboxImageError, match="pinned legacy"):
        manager.images.ensure(legacy, digest="sha256:" + "b" * 64)


def test_package_stopped_overlay(tmp_path):
    import os
    import subprocess
    import tarfile

    lower = tmp_path / 'base'
    upper = tmp_path / 'fs'
    markers = tmp_path / 'cow/whiteouts'
    lower.mkdir()
    upper.mkdir()
    markers.mkdir(parents=True)
    (lower / 'keep').write_text('original')
    os.link(lower / 'keep', lower / 'alias')
    (lower / 'symlink').symlink_to('/keep')
    for path in ('changed', 'deleted'):
        (lower / path).write_text('original')
    (upper / 'changed').write_text('private')
    (upper / '-new\nfile').touch()
    (markers / 'deleted').mkdir(mode=0o1700)
    (lower / 'opaque').mkdir()
    (lower / 'opaque/old').touch()
    (upper / 'opaque').mkdir()
    (markers / 'opaque').mkdir(mode=0o1700)
    archive = tmp_path / 'layer.tar'
    inputs = builtin_image._layer_inputs(upper, lower, tmp_path)
    subprocess.run(['tar', '-cf', archive, *inputs], check=True)
    with tarfile.open(archive) as tar:
        assert set(tar.getnames()) == {'.', './keep', './alias', './symlink', './changed', './-new\nfile', './opaque'}
        assert tar.extractfile('./keep').read() == b'original'
        assert tar.extractfile('./changed').read() == b'private'
        assert tar.getmember('./symlink').linkname == '/keep'
        assert tar.getmember('./keep').islnk() or tar.getmember('./alias').islnk()
