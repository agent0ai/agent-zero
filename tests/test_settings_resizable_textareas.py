import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SETTINGS_CSS = PROJECT_ROOT / "webui" / "css" / "settings.css"
LITELLM = PROJECT_ROOT / "webui" / "components" / "settings" / "external" / "litellm.html"
MODEL_FIELD = PROJECT_ROOT / "plugins" / "_model_config" / "webui" / "model-field.html"
SECRETS = PROJECT_ROOT / "webui" / "components" / "settings" / "external" / "secrets.html"


def test_resizable_textarea_rule_re_enables_the_vertical_grip() -> None:
    css = SETTINGS_CSS.read_text(encoding="utf-8")
    rule = re.search(r"textarea\.resizable-textarea \{([^}]*)\}", css)
    assert rule, "the shared resizable-textarea rule is missing"
    assert "resize: vertical" in rule.group(1)
    assert "transition: none" in rule.group(1)


def test_litellm_and_model_kwargs_textareas_keep_a_resize_grip() -> None:
    assert 'class="resizable-textarea"' in LITELLM.read_text(encoding="utf-8"), LITELLM.name
    assert 'class="resizable-textarea"' in MODEL_FIELD.read_text(encoding="utf-8"), MODEL_FIELD.name


def test_secrets_textareas_keep_a_resize_grip() -> None:
    markup = SECRETS.read_text(encoding="utf-8")
    assert markup.count('class="resizable-textarea"') == 2, SECRETS.name
