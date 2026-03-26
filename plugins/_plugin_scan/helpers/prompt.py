import json
from pathlib import Path

_DIR = Path(__file__).parent.parent
_CFG = None
_TMPL = None


def _load_config() -> dict:
    global _CFG
    if _CFG is not None:
        return _CFG

    path = _DIR / "webui" / "plugin-scan-checks.json"
    try:
        _CFG = json.loads(path.read_text())
        return _CFG
    except Exception as e:
        raise RuntimeError(f"Unable to load plugin scan checks: {e}") from e


def _load_template() -> str:
    global _TMPL
    if _TMPL is not None:
        return _TMPL

    path = _DIR / "webui" / "plugin-scan-prompt.md"
    try:
        _TMPL = path.read_text()
        return _TMPL
    except Exception as e:
        raise RuntimeError(f"Unable to load plugin scan prompt template: {e}") from e


def build_prompt(git_url: str, checks: list | None = None) -> str:
    cfg = _load_config()
    ratings, all_checks = cfg["ratings"], cfg["checks"]
    keys = list(all_checks.keys()) if checks is None else [k for k in checks if k in all_checks]
    prompt_template = _load_template()

    subs = {
        "GIT_URL": git_url,
        "SELECTED_CHECKS": (
            "\n".join(f"- **{all_checks[k]['label']}**" for k in keys)
            if keys
            else "- (no checks selected)"
        ),
        "CHECK_DETAILS": (
            "\n\n".join(
                f"#### {c['label']}\n{c['detail']}\n\nCriteria:\n"
                + "\n".join(f"  - {ratings[l]['icon']} {d}" for l, d in c["criteria"].items())
                for c in (all_checks[k] for k in keys)
            )
            if keys
            else "(no checks selected)"
        ),
        "STATUS_LEGEND": "\n".join(f"- {r['icon']} **{r['label']}**" for r in ratings.values()),
        "RATING_ICONS":   "/".join(r["icon"] for r in ratings.values()),
        "RATING_PASS":    ratings["pass"]["icon"],
        "RATING_WARNING": ratings["warning"]["icon"],
        "RATING_FAIL":    ratings["fail"]["icon"],
    }
    prompt = prompt_template
    for key, val in subs.items():
        prompt = prompt.replace(f"{{{{{key}}}}}", val)
    return prompt
