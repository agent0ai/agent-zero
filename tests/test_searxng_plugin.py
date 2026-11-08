from __future__ import annotations

import asyncio
from pathlib import Path

from plugins._searxng.helpers.searxng import NOT_IMPLEMENTED_MESSAGE, search
from plugins._searxng.tools.search_engine import SearchEngine


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_search_engine_is_a_deterministic_placeholder() -> None:
    tool = SearchEngine(
        agent=None,  # type: ignore[arg-type]
        name="search_engine",
        method=None,
        args={},
        message="",
        loop_data=None,
    )

    response = asyncio.run(tool.execute(query="latest news", unexpected="ignored"))

    assert response.message == "the searxng plugin is not yet fully implemented"
    assert response.message == NOT_IMPLEMENTED_MESSAGE
    assert response.break_loop is False
    assert asyncio.run(search("anything")) == NOT_IMPLEMENTED_MESSAGE


def test_searxng_assets_are_plugin_owned() -> None:
    expected = [
        "plugins/_searxng/plugin.yaml",
        "plugins/_searxng/README.md",
        "plugins/_searxng/helpers/searxng.py",
        "plugins/_searxng/tools/search_engine.py",
        "plugins/_searxng/prompts/agent.system.tool.search_engine.md",
    ]
    removed_core = [
        "helpers/searxng.py",
        "helpers/searxng.py.dox.md",
        "tools/search_engine.py",
        "tools/search_engine.py.dox.md",
        "tools/knowledge_tool._py",
        "prompts/agent.system.tool.search_engine.md",
    ]

    for relative_path in expected:
        assert (PROJECT_ROOT / relative_path).is_file(), relative_path
    for relative_path in removed_core:
        assert not (PROJECT_ROOT / relative_path).exists(), relative_path


def test_outer_docker_images_have_no_searxng_runtime() -> None:
    removed_paths = [
        "docker/base/fs/ins/install_searxng.sh",
        "docker/base/fs/ins/install_searxng2.sh",
        "docker/base/fs/etc/searxng/settings.yml",
        "docker/base/fs/etc/searxng/limiter.toml",
        "docker/run/fs/exe/run_searxng.sh",
        "docker/run/fs/etc/searxng/settings.yml",
        "docker/run/fs/etc/searxng/limiter.toml",
    ]
    for relative_path in removed_paths:
        assert not (PROJECT_ROOT / relative_path).exists(), relative_path

    docker_files = [
        path
        for root in (
            PROJECT_ROOT / "docker" / "base",
            PROJECT_ROOT / "docker" / "run",
        )
        for path in root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    ]
    docker_files.append(PROJECT_ROOT / "DockerfileLocal")
    combined = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore") for path in docker_files
    )

    forbidden = [
        "install_searxng",
        "run_searxng",
        "SEARXNG_SETTINGS_PATH",
        "/etc/searxng",
        "/usr/local/searxng",
        "searx-pyenv",
        "[program:run_searxng]",
    ]
    for marker in forbidden:
        assert marker not in combined, marker


def test_readme_preserves_reimplementation_details() -> None:
    readme = (PROJECT_ROOT / "plugins/_searxng/README.md").read_text(encoding="utf-8")

    for detail in (
        "git`, `build-essential`, `libxslt-dev`, `zlib1g-dev`, `libffi-dev`, and `libssl-dev",
        "git clone https://github.com/searxng/searxng",
        "python3.13 -m venv /usr/local/searxng/searx-pyenv",
        "pip install --no-cache-dir -U pip setuptools wheel pyyaml lxml msgspec typing_extensions",
        "pip install --no-cache-dir --use-pep517 --no-build-isolation .",
        "http://localhost:55510/search",
        "SEARXNG_SETTINGS_PATH=/etc/searxng/settings.yml",
        'secret_key: "dummy"',
        "safe_search: 0",
        "radio browser",
        "wikidata",
        "trusted_proxies = [\"127.0.0.1\"]",
    ):
        assert detail in readme, detail
