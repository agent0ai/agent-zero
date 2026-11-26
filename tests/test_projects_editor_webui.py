import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BASIC_DATA = PROJECT_ROOT / "webui" / "components" / "projects" / "project-edit-basic-data.html"
EDITORS = [
    PROJECT_ROOT / "webui" / "components" / "projects" / "project-edit-instructions.html",
    PROJECT_ROOT / "webui" / "components" / "projects" / "project-edit-secrets.html",
    PROJECT_ROOT / "webui" / "components" / "projects" / "project-edit-file-structure.html",
]


def test_project_form_textareas_keep_a_vertical_resize_grip() -> None:
    markup = BASIC_DATA.read_text(encoding="utf-8")
    rule = re.search(r"\.projects-form-textarea \{([^}]*)\}", markup)
    assert rule, "the shared textarea rule is missing"
    assert "resize: vertical" in rule.group(1)
    assert "transition: none" in rule.group(1)
    for editor in EDITORS:
        assert 'class="projects-form-textarea"' in editor.read_text(encoding="utf-8"), editor.name
