import json
from pathlib import Path

_DIR = Path(__file__).parent.parent
_CFG = None
_TMPL = None
_CHECKLIST_GUIDANCE = None


def _load_config() -> dict:
    global _CFG
    if _CFG is not None:
        return _CFG

    path = _DIR / "webui" / "plugin-validator-checks.json"
    try:
        _CFG = json.loads(path.read_text())
        return _CFG
    except Exception as e:
        raise RuntimeError(f"Unable to load plugin validator checks: {e}") from e


def _load_template() -> str:
    global _TMPL
    if _TMPL is not None:
        return _TMPL

    path = _DIR / "webui" / "plugin-validator-prompt.md"
    try:
        _TMPL = path.read_text()
        return _TMPL
    except Exception as e:
        raise RuntimeError(f"Unable to load plugin validator prompt template: {e}") from e


def _load_guidance() -> str:
    global _CHECKLIST_GUIDANCE
    if _CHECKLIST_GUIDANCE is not None:
        return _CHECKLIST_GUIDANCE

    path = _DIR / "webui" / "plugin-validator-guidance.md"
    try:
        _CHECKLIST_GUIDANCE = path.read_text().strip()
        return _CHECKLIST_GUIDANCE
    except Exception as e:
        raise RuntimeError(f"Unable to load plugin validator guidance: {e}") from e


def _sanitize_target(value: str) -> str:
    return (value or "").strip().replace("{", "(").replace("}", ")")


def _target_reference(source_type: str, target: str) -> str:
    target = _sanitize_target(target)
    if source_type == "local" and target and "/" not in target and "\\" not in target:
        return f"usr/plugins/{target}/"
    return target


def _source_label(source_type: str) -> str:
    return {
        "local": "Local Plugin",
        "git": "Git Repository",
        "zip": "Uploaded ZIP",
    }.get(source_type, "Plugin Source")


def _source_instructions(source_type: str, target: str, cleanup_target: str | None = None) -> str:
    target_ref = _target_reference(source_type, target)
    cleanup_ref = _sanitize_target(cleanup_target or target_ref)

    if source_type == "git":
        return (
            f"Clone `{target_ref}` to a temporary directory outside the workspace, such as "
            "`/tmp/plugin-validate-$(date +%s)`. Validate the cloned files there. After the review, "
            "run `rm -rf /tmp/plugin-validate-*` and verify cleanup with `ls /tmp/plugin-validate-* 2>&1`."
        )

    if source_type == "zip":
        return (
            f"The ZIP has already been extracted to `{target_ref}`. Validate the plugin from that extracted "
            "directory only. Do not install or move it. After the review, delete that extracted directory "
            f"with `rm -rf \"{cleanup_ref}\"` and verify cleanup with `ls \"{cleanup_ref}\" 2>&1`."
        )

    return (
        f"Read the plugin directly from `{target_ref}`. Do not clone, move, or modify the plugin. "
        "No temporary cleanup is required for this source."
    )


def build_prompt(
    source_type: str,
    target: str,
    checks: list | None = None,
    cleanup_target: str | None = None,
) -> str:
    cfg = _load_config()
    ratings, all_checks = cfg["ratings"], cfg["checks"]
    keys = list(all_checks.keys()) if checks is None else [k for k in checks if k in all_checks]
    prompt_template = _load_template()

    subs = {
        "SOURCE_LABEL": _source_label(source_type),
        "TARGET_REFERENCE": _target_reference(source_type, target),
        "SOURCE_INSTRUCTIONS": _source_instructions(source_type, target, cleanup_target),
        "SELECTED_CHECKS": (
            "\n".join(f"- **{all_checks[k]['label']}**" for k in keys)
            if keys
            else "- (no validation phases selected)"
        ),
        "CHECK_DETAILS": (
            "\n\n".join(
                f"#### {c['label']}\n{c['detail']}\n\nCriteria:\n"
                + "\n".join(f"  - {ratings[level]['icon']} {desc}" for level, desc in c["criteria"].items())
                for c in (all_checks[k] for k in keys)
            )
            if keys
            else "(no validation phases selected)"
        ),
        "CHECKLIST_GUIDANCE": _load_guidance(),
        "STATUS_LEGEND": "\n".join(f"- {r['icon']} **{r['label']}**" for r in ratings.values()),
        "RATING_ICONS": "/".join(r["icon"] for r in ratings.values()),
        "RATING_PASS": ratings["pass"]["icon"],
        "RATING_WARNING": ratings["warning"]["icon"],
        "RATING_FAIL": ratings["fail"]["icon"],
    }
    prompt = prompt_template
    for key, val in subs.items():
        prompt = prompt.replace(f"{{{{{key}}}}}", val)
    return prompt
