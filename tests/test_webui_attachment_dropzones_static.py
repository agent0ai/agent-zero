from pathlib import Path
import re


PROJECT_ROOT = Path(__file__).resolve().parents[1]

ATTACHMENTS_STORE = PROJECT_ROOT.joinpath(
    "webui", "components", "chat", "attachments", "attachmentsStore.js"
)
OVERLAY_CSS = PROJECT_ROOT.joinpath("webui", "index.css")
SKILLS_IMPORT_HTML = PROJECT_ROOT.joinpath(
    "webui", "components", "settings", "skills", "import.html"
)
SKILLS_IMPORT_STORE = PROJECT_ROOT.joinpath(
    "webui", "components", "settings", "skills", "skills-import-store.js"
)


def test_drop_overlay_yields_to_registered_internal_dropzones() -> None:
    store = ATTACHMENTS_STORE.read_text(encoding="utf-8")

    assert 'closest?.("[data-internal-dropzone]")' in store
    assert "if (dragCounter === 1 && !this.isModalOpen() && !this.isInternalDropTarget(e))" in store
    assert "if (this.isModalOpen() || this.isInternalDropTarget(e)) this.hideDragDropOverlay();" in store
    assert "else this.showDragDropOverlay();" in store
    assert "if (this.isInternalDropTarget(e)) return;" in store


def test_drop_overlay_never_becomes_the_drop_target() -> None:
    css = OVERLAY_CSS.read_text(encoding="utf-8")
    rule = re.search(r"\.dragdrop-overlay \{[^}]*\}", css)

    assert rule, ".dragdrop-overlay rule missing from index.css"
    assert "pointer-events: none;" in rule.group(0)


def test_skills_import_dropzone_claims_external_file_drops() -> None:
    markup = SKILLS_IMPORT_HTML.read_text(encoding="utf-8")
    store = SKILLS_IMPORT_STORE.read_text(encoding="utf-8")

    assert 'data-internal-dropzone' in markup
    assert '@dragover.prevent="$store.skillsImportStore.setDragActive(true)"' in markup
    assert '@drop.prevent="$store.skillsImportStore.handleDrop($event)"' in markup
    assert 'handleDragLeave(event)' in store
    assert 'endsWith(".zip")' in store
    assert "await this.acceptSkillsFile(file);" in store
    assert "async acceptSkillsFile(file)" in store


def test_drop_overlay_yields_to_open_modals() -> None:
    store = ATTACHMENTS_STORE.read_text(encoding="utf-8")

    assert 'if (document.querySelector(".modal.show")) return true;' in store
    assert 'getComputedStyle(overlay).display !== "none"' in store
    assert "if (dragCounter === 1 && !this.isModalOpen() && !this.isInternalDropTarget(e))" in store
    assert "if (this.isModalOpen()) return;" in store
