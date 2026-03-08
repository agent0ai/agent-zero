from types import SimpleNamespace

from python.helpers.mcp_handler import MCPConfig


def _dummy_server(name: str = "demo"):
    return SimpleNamespace(
        name=name,
        description="dummy",
        type="stdio",
        disabled=False,
        command="echo",
        args=[],
        env={},
        encoding="utf-8",
        encoding_error_handler="strict",
        init_timeout=0,
        tool_timeout=0,
        get_tools=lambda: [],
        get_cached_tool_count=lambda: 0,
        get_error=lambda: "",
        get_log=lambda: "",
    )


def test_mcp_tools_prompt_cache_hit_and_force_refresh(monkeypatch):
    cfg = MCPConfig(servers_list=[])
    cfg.servers = [_dummy_server()]

    calls = {"count": 0}

    def fake_get_tools_prompt(self, server_name: str = "") -> str:
        calls["count"] += 1
        return f"PROMPT::{server_name or 'all'}"

    monkeypatch.setattr(MCPConfig, "get_tools_prompt", fake_get_tools_prompt)

    first = cfg.get_tools_prompt_cached()
    second = cfg.get_tools_prompt_cached()
    third = cfg.get_tools_prompt_cached(force_refresh=True)

    assert first == "PROMPT::all"
    assert second == "PROMPT::all"
    assert third == "PROMPT::all"
    assert calls["count"] == 2  # first build + forced refresh

    stats = cfg.get_tools_prompt_cache_stats()
    assert stats["hits"] >= 1
    assert stats["misses"] >= 1
    assert stats["rebuilds"] >= 1


def test_mcp_tools_prompt_cache_invalidation_on_reinit(monkeypatch):
    cfg = MCPConfig(servers_list=[])
    cfg.servers = [_dummy_server()]

    monkeypatch.setattr(MCPConfig, "get_tools_prompt", lambda self, server_name="": "PROMPT")
    assert cfg.get_tools_prompt_cached() == "PROMPT"
    assert cfg.get_tools_prompt_cache_stats()["entries"] == 1

    # Reinit is what MCPConfig.update() does internally.
    cfg.__init__(servers_list=[])
    stats = cfg.get_tools_prompt_cache_stats()
    assert stats["entries"] == 0
    assert stats["invalidations"] >= 1
