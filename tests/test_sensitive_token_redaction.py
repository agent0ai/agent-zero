from python.helpers.log import Log
from python.helpers.strings import redact_sensitive_tokens


def test_redact_sensitive_tokens_masks_github_pat_formats():
    raw = "token=ghp_abcdefghijklmnopqrstuvwxyz123456 and github_pat_ABCDEFGHIJKLMNOPQRSTUVWXYZ123456"
    redacted = redact_sensitive_tokens(raw)

    assert "ghp_abcdefghijklmnopqrstuvwxyz123456" not in redacted  # pragma: allowlist secret
    assert "github_pat_ABCDEFGHIJKLMNOPQRSTUVWXYZ123456" not in redacted  # pragma: allowlist secret
    assert "[REDACTED]" in redacted


def test_redact_sensitive_tokens_masks_all_supported_github_prefixes():
    raw = (
        "gho_abcdefghijklmnopqrstuvwxyz123456 "
        "ghu_abcdefghijklmnopqrstuvwxyz123456 "
        "ghs_abcdefghijklmnopqrstuvwxyz123456 "
        "ghr_abcdefghijklmnopqrstuvwxyz123456"  # pragma: allowlist secret
    )
    redacted = redact_sensitive_tokens(raw)

    assert "gho_abcdefghijklmnopqrstuvwxyz123456" not in redacted  # pragma: allowlist secret
    assert "ghu_abcdefghijklmnopqrstuvwxyz123456" not in redacted  # pragma: allowlist secret
    assert "ghs_abcdefghijklmnopqrstuvwxyz123456" not in redacted  # pragma: allowlist secret
    assert "ghr_abcdefghijklmnopqrstuvwxyz123456" not in redacted  # pragma: allowlist secret
    assert redacted.count("[REDACTED]") == 4


def test_redact_sensitive_tokens_does_not_mutate_secret_placeholders():
    raw = "Use §§secret(GITHUB_PAT), ****PSWD****, and ************ placeholders."
    redacted = redact_sensitive_tokens(raw)
    assert redacted == raw


def test_log_masks_tokens_in_content_and_kvps_without_secrets_context():
    token = "ghp_abcdefghijklmnopqrstuvwxyz123456"
    lg = Log()
    item = lg.log(
        type="user",
        heading="User message",
        content=f"here is token {token}",
        kvps={"auth": token, "nested": {"pat": "github_pat_ABCDEFGHIJKLMNOPQRSTUVWXYZ123456"}},
    )

    out = item.output()
    assert token not in out["content"]
    assert "[REDACTED]" in out["content"]

    kvps = out["kvps"]
    assert token not in str(kvps)
    assert "github_pat_ABCDEFGHIJKLMNOPQRSTUVWXYZ123456" not in str(kvps)
    assert "[REDACTED]" in str(kvps)


def test_log_masks_tokens_inside_nested_list_structures():
    token = "ghs_abcdefghijklmnopqrstuvwxyz123456"
    lg = Log()
    item = lg.log(
        type="tool",
        heading="Tool output",
        content="ok",
        kvps={"results": ["safe", token, {"auth": token}]},
    )
    out = item.output()
    kvps = out["kvps"]
    assert token not in str(kvps)
    assert "[REDACTED]" in str(kvps)
