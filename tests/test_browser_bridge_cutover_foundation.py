from __future__ import annotations

import json
from pathlib import Path

import pytest

from plugins._a0_connector.helpers import browser_bridge_cutover as cutover
from plugins._a0_connector.helpers.browser_bridge_cutover import (
    CUTOVER_CONTRACT,
    CUTOVER_SCHEMA_VERSION,
    CutoverState,
    LegacyDetectionState,
    build_cutover_foundation_status,
    can_transition_cutover,
    cutover_contract_schema,
    detect_legacy_browser_bridge,
    detect_legacy_browser_bridge_roots,
    detect_installed_legacy_browser_bridge,
)


FIXTURES = Path(__file__).parent / "fixtures" / "browser_bridge_cutover_v1"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_exact_legacy_fixture_matches_versioned_redacted_projection() -> None:
    report = detect_legacy_browser_bridge(FIXTURES / "legacy_exact")
    expected = json.loads((FIXTURES / "confirmed_public.json").read_text(encoding="utf-8"))

    assert report.state is LegacyDetectionState.CONFIRMED
    assert report.confirmed is True
    assert report.to_public_dict() == expected


def test_absent_and_corrupt_roots_fail_safe(tmp_path: Path) -> None:
    missing = detect_legacy_browser_bridge(tmp_path / "missing")
    assert missing.state is LegacyDetectionState.ABSENT
    assert missing.inspected_marker_count == 0

    corrupt = tmp_path / "corrupt"
    _write(corrupt / "plugin.yaml", "name: [unterminated")
    report = detect_legacy_browser_bridge(corrupt)
    assert report.state is LegacyDetectionState.PARTIAL
    assert report.reason_code == "legacy_bridge_fingerprint_incomplete"
    assert build_cutover_foundation_status(report)["state"] == "blocked"


def test_manifest_alone_or_one_marker_is_never_confirmation(tmp_path: Path) -> None:
    root = tmp_path / "partial"
    _write(root / "plugin.yaml", "name: chrome_extension\nversion: 1.0.0\n")
    _write(
        root / "tools/chrome_bridge.py",
        "class ChromeBridge:\n    value = enqueue_command\n",
    )

    report = detect_legacy_browser_bridge(root)
    assert report.state is LegacyDetectionState.PARTIAL
    assert report.manifest_matched is True
    assert report.matched_markers == ("legacy_tool",)


def test_matching_name_with_unrelated_structure_is_not_confirmed(tmp_path: Path) -> None:
    root = tmp_path / "false-positive"
    _write(root / "plugin.yaml", "name: chrome_extension\nversion: 1.0.0\n")
    _write(root / "tools/chrome_bridge.py", "class DifferentTool: pass\n")
    _write(root / "api/session_upsert.py", "# one route is insufficient\n")

    report = detect_legacy_browser_bridge(root)
    assert report.state is LegacyDetectionState.PARTIAL
    assert report.matched_markers == ()
    assert report.confirmed is False


def test_wrong_version_with_markers_is_partial_not_legacy_authority(tmp_path: Path) -> None:
    root = tmp_path / "wrong-version"
    _write(root / "plugin.yaml", "name: chrome_extension\nversion: 9.9.9\n")
    _write(
        root / "helpers/constants.py",
        'SOURCE_NAME = "chrome_extension"\n'
        'CTX_BROWSER_SESSION_ID = "chrome_browser_session_id"\n'
        'CTX_CHROME_CAPABILITIES = "chrome_extension_capabilities"\n',
    )
    _write(
        root / "default_config.yaml",
        "command_timeout_seconds: 30\nredelivery_seconds: 8\n"
        "stale_session_seconds: 600\nmax_inspect_nodes: 40\n"
        "prompt_guidance: legacy\n",
    )

    report = detect_legacy_browser_bridge(root)
    assert report.state is LegacyDetectionState.PARTIAL
    assert report.manifest_matched is False
    assert len(report.matched_markers) == 2


def test_projection_is_deterministic_and_cannot_leak_source_values(tmp_path: Path) -> None:
    secret = "sentinel-token-do-not-project"
    sensitive_path = tmp_path / f"https-example.test-query-token-{secret}"
    _write(
        sensitive_path / "plugin.yaml",
        "name: chrome_extension\nversion: 1.0.0\n"
        f"description: https://example.test/?token={secret}\n",
    )
    _write(
        sensitive_path / "tools/chrome_bridge.py",
        f"# {secret}\nclass ChromeBridge:\n    value = enqueue_command\n",
    )

    first = detect_legacy_browser_bridge(sensitive_path).to_public_dict()
    second = detect_legacy_browser_bridge(sensitive_path).to_public_dict()
    serialized = json.dumps(first, sort_keys=True)

    assert first == second
    assert secret not in serialized
    assert "example.test" not in serialized
    assert str(sensitive_path) not in serialized
    assert set(first) == set(cutover_contract_schema()["projection_fields"])


def test_symlinked_markers_outside_root_are_rejected(tmp_path: Path) -> None:
    outside = tmp_path / "outside.py"
    outside.write_text("class ChromeBridge:\n    value = enqueue_command\n", encoding="utf-8")
    root = tmp_path / "candidate"
    _write(root / "plugin.yaml", "name: chrome_extension\nversion: 1.0.0\n")
    (root / "tools").mkdir(parents=True)
    (root / "tools" / "chrome_bridge.py").symlink_to(outside)

    report = detect_legacy_browser_bridge(root)
    assert report.state is LegacyDetectionState.PARTIAL
    assert report.matched_markers == ()


def test_symlinked_route_and_prompt_entries_are_not_structural_markers(
    tmp_path: Path,
) -> None:
    outside = tmp_path / "outside.txt"
    outside.write_text("fixture", encoding="utf-8")
    root = tmp_path / "candidate"
    _write(root / "plugin.yaml", "name: chrome_extension\nversion: 1.0.0\n")
    for relative_path in (
        "api/session_upsert.py",
        "api/command_pull.py",
        "api/command_result.py",
        "prompts/agent.system.tool.chrome_bridge.md",
        "prompts/fw.chrome.system_context.md",
    ):
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.symlink_to(outside)

    report = detect_legacy_browser_bridge(root)

    assert report.state is LegacyDetectionState.PARTIAL
    assert "legacy_command_routes" not in report.matched_markers
    assert "legacy_prompt_pair" not in report.matched_markers


def test_symlinked_root_is_unknown_and_blocks_cutover(tmp_path: Path) -> None:
    real_root = tmp_path / "real"
    _write(real_root / "plugin.yaml", "name: chrome_extension\nversion: 1.0.0\n")
    linked_root = tmp_path / "linked"
    linked_root.symlink_to(real_root, target_is_directory=True)

    report = detect_legacy_browser_bridge(linked_root)

    assert report.state is LegacyDetectionState.UNKNOWN
    assert report.reason_code == "legacy_bridge_root_untrusted"
    assert report.inspected_marker_count == 0
    status = build_cutover_foundation_status(report)
    assert status["state"] == "blocked"
    assert status["quarantine"]["state"] == "not_applied"


def test_unavailable_installed_root_discovery_is_unknown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unavailable_roots():
        yield from ()
        raise PermissionError("not public")

    monkeypatch.setattr(
        cutover,
        "_installed_legacy_plugin_roots",
        unavailable_roots,
    )

    report = detect_installed_legacy_browser_bridge()

    assert report.state is LegacyDetectionState.UNKNOWN
    assert report.reason_code == "legacy_bridge_detection_unavailable"
    assert build_cutover_foundation_status(report)["state"] == "blocked"


def test_unavailable_fingerprint_read_is_unknown(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = tmp_path / "candidate"
    root.mkdir()
    monkeypatch.setattr(cutover, "_read_yaml_mapping", lambda *_args: ({}, True))

    report = detect_legacy_browser_bridge(root)

    assert report.state is LegacyDetectionState.UNKNOWN
    assert report.reason_code == "legacy_bridge_detection_unavailable"


def test_any_unavailable_marker_blocks_otherwise_sufficient_fingerprint(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = tmp_path / "candidate"
    _write(root / "plugin.yaml", "name: chrome_extension\nversion: 1.0.0\n")
    monkeypatch.setattr(
        cutover,
        "_STRUCTURAL_MARKERS",
        {
            "marker_one": lambda _root_fd: cutover._MarkerInspection(matched=True),
            "marker_two": lambda _root_fd: cutover._MarkerInspection(matched=True),
            "unavailable": lambda _root_fd: cutover._MarkerInspection(
                matched=False,
                unavailable=True,
            ),
        },
    )

    report = detect_legacy_browser_bridge(root)

    assert report.state is LegacyDetectionState.UNKNOWN
    assert build_cutover_foundation_status(report)["state"] == "blocked"


def test_fingerprint_reads_share_one_anchored_root_descriptor(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    root = tmp_path / "candidate"
    _write(root / "plugin.yaml", "name: chrome_extension\nversion: 1.0.0\n")
    observed_root_fds: list[int] = []
    original_read_yaml = cutover._read_yaml_mapping

    def read_yaml(root_fd: int, relative_path: str):
        observed_root_fds.append(root_fd)
        return original_read_yaml(root_fd, relative_path)

    monkeypatch.setattr(cutover, "_read_yaml_mapping", read_yaml)
    monkeypatch.setattr(
        cutover,
        "_STRUCTURAL_MARKERS",
        {
            "marker_one": lambda root_fd: (
                observed_root_fds.append(root_fd)
                or cutover._MarkerInspection(matched=False)
            ),
            "marker_two": lambda root_fd: (
                observed_root_fds.append(root_fd)
                or cutover._MarkerInspection(matched=False)
            ),
        },
    )

    detect_legacy_browser_bridge(root)

    assert len(observed_root_fds) == 3
    assert len(set(observed_root_fds)) == 1


def test_cutover_schema_and_transition_graph_are_versioned_and_fail_closed() -> None:
    schema = cutover_contract_schema()
    assert schema["contract"] == CUTOVER_CONTRACT
    assert schema["schema_version"] == CUTOVER_SCHEMA_VERSION
    assert schema["minimum_structural_markers"] == 2

    assert can_transition_cutover(CutoverState.NOT_DETECTED, CutoverState.LEGACY_DETECTED)
    assert can_transition_cutover(CutoverState.DRAINING_LEGACY, CutoverState.BLOCKED)
    assert can_transition_cutover(CutoverState.VERIFYING, CutoverState.COMPLETE)
    assert not can_transition_cutover(CutoverState.NOT_DETECTED, CutoverState.COMPLETE)
    assert not can_transition_cutover(CutoverState.COMPLETE, CutoverState.CANCELED)
    assert not can_transition_cutover(CutoverState.CANCELED, CutoverState.LEGACY_DETECTED)


def test_root_selection_and_foundation_status_never_claim_quarantine(tmp_path: Path) -> None:
    detection = detect_legacy_browser_bridge_roots(
        [tmp_path / "absent", FIXTURES / "legacy_exact"]
    )

    status = build_cutover_foundation_status(detection)

    assert status["state"] == "legacy_detected"
    assert status["legacy"]["state"] == "confirmed"
    assert status["quarantine"] == {
        "state": "not_applied",
        "reason_code": "foundation_detection_only",
    }


def test_higher_priority_partial_root_blocks_shadowed_confirmed_copy(
    tmp_path: Path,
) -> None:
    partial = tmp_path / "partial"
    _write(partial / "plugin.yaml", "name: chrome_extension\nversion: 1.0.0\n")
    detection = detect_legacy_browser_bridge_roots(
        [partial, FIXTURES / "legacy_exact"]
    )

    status = build_cutover_foundation_status(detection)

    assert status["state"] == "blocked"
    assert status["legacy"]["state"] == "partial"
    assert status["quarantine"] == {
        "state": "not_applied",
        "reason_code": "legacy_bridge_fingerprint_incomplete",
    }
