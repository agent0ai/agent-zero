from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WHATS_NEW_PLUGIN = PROJECT_ROOT / "plugins/_whats_new"


def test_whats_new_modal_handles_empty_showcase_state():
    html = (WHATS_NEW_PLUGIN / "webui/main.html").read_text(encoding="utf-8")
    store = (WHATS_NEW_PLUGIN / "webui/whats-new-store.js").read_text(encoding="utf-8")
    slide_data = (WHATS_NEW_PLUGIN / "webui/whats-new-slides.js").read_text(
        encoding="utf-8"
    )

    assert "What's New in Agent Zero" in html
    assert "data-modal-footer" in html
    assert "btn btn-ok" in html
    assert "btn btn-field" in html
    assert "type=\"checkbox\"" in html
    assert "Don't show automatically again" in html
    assert "/plugins/_whats_new/webui/whats-new-store.js" in html
    assert "/plugins/_whats_new/webui/whats-new-slides.js" in store
    assert "a0_whats_new_never_show" in store
    assert "No new updates right now" in store
    assert "hasSlides()" in html + store
    assert "export const slides = [];" in slide_data

    old_cards = html + store + slide_data
    assert "Parallel tool calls and subagents" not in old_cards
    assert "Redesigned MCP configuration UI" not in old_cards
    assert "Skills Scanner powered by Snyk Agent Scan" not in old_cards
    assert "parallel-subs.webm" not in old_cards
    assert "mcp-servers.png" not in old_cards
    assert "skills-scanner.png" not in old_cards


def test_whats_new_legacy_modal_path_redirects_to_main_screen():
    html = (WHATS_NEW_PLUGIN / "webui/whats-new.html").read_text(encoding="utf-8")

    assert "/plugins/_whats_new/webui/main.html" in html
    assert "openModal(mainPath)" in html
    assert "What's New in Agent Zero" in html


def test_whats_new_startup_trigger_is_version_gated_with_opt_out():
    content = (
        WHATS_NEW_PLUGIN / "extensions/webui/initFw_end/whats-new.js"
    ).read_text(encoding="utf-8")

    assert "globalThis.gitinfo?.version" in content
    assert "a0_whats_new_seen_version" in content
    assert "a0_whats_new_never_show" in content
    assert "/plugins/_whats_new/webui/whats-new-slides.js" in content
    assert "slides.length" in content
    assert "/plugins/_whats_new/webui/main.html" in content
    assert "/plugins/_whats_new/webui/whats-new.html" in content
    assert "compareVersions" in content
    assert "storedSeenVersion" in content
    assert "shouldShowWhatsNew" in content
    assert "shouldNeverShow" in content
    assert "modal-closed" in content
    assert "markVersionSeen" in content


def test_whats_new_exposes_builtin_plugin_open_screen():
    assert (WHATS_NEW_PLUGIN / "webui/main.html").exists()


def test_whats_new_plugin_manifest_is_always_enabled():
    manifest = (WHATS_NEW_PLUGIN / "plugin.yaml").read_text(encoding="utf-8")

    assert "name: _whats_new" in manifest
    assert "always_enabled: true" in manifest
    assert "settings_sections: []" in manifest
