import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from plugins._plugin_scan.helpers.prompt import build_prompt


def test_plugin_scan_prompt_calibrates_provider_credentials_as_expected_behavior():
    prompt = build_prompt(
        "https://github.com/example/provider-plugin",
        checks=["remoteComms", "secrets"],
    )

    assert "Classify by demonstrated risk, not by the mere presence of a capability." in prompt
    assert "adds `conf/model_providers.yaml`" in prompt
    assert "provider credentials when those capabilities are transparent" in prompt
    assert (
        "No secret access, or credential access is narrow, user-supplied/provider-specific, "
        "and justified by the declared purpose"
    ) in prompt
    assert (
        "No network calls, or network calls are transparent and necessary for the declared plugin purpose"
        in prompt
    )


def test_plugin_scan_prompt_calibrates_common_plugin_capabilities_as_expected_behavior():
    prompt = build_prompt(
        "https://github.com/example/plugin",
        checks=["structure", "codeReview", "agentManipulation", "obfuscation"],
    )

    assert (
        "A plugin can legitimately add tools, prompts, API handlers, hooks, settings, "
        "dependencies, scheduled jobs, network clients, subprocess calls, filesystem access"
    ) in prompt
    assert "Treat expected filesystem access as 🟢" in prompt
    assert "Treat expected subprocess use as 🟢" in prompt
    assert "Treat prompt/system text as 🟢" in prompt
    assert "ordinary minified/vendor/generated frontend assets" in prompt
    assert "normal plugin prompt templates, tool instructions, README usage examples" in prompt
    assert "fixed subprocess commands, dependency installation hooks" in prompt


def test_plugin_scan_prompt_requires_file_paths_only_for_warning_or_fail_findings():
    prompt = build_prompt(
        "https://github.com/example/provider-plugin",
        checks=["secrets"],
    )

    assert "Every 🟡 or 🔴 finding has a concrete file path and line range" in prompt
    assert "Expected plugin capabilities were not treated as findings" in prompt
    assert "Each check has a concrete finding with file path" not in prompt
