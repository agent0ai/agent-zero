import json
from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from helpers import projects
import plugins._memory.helpers.auto_dream as auto_dream_helper
import plugins._memory.helpers.memory as memory_helper
from plugins._memory.helpers.auto_dream import (
    DreamMemoryFile,
    clear_autodream_knowledge_import_cache,
    extract_first_user_prompt,
    find_orphan_candidates,
    render_auto_dream_log_entry,
    render_memory_index,
    select_memory_file_name,
    should_run_auto_dream,
)
from plugins._memory.helpers.knowledge_import import (
    load_autodream_markdown_documents,
)


def test_extract_first_user_prompt_prefers_first_human_message():
    history_payload = {
        "bulks": [],
        "topics": [],
        "current": {
            "_cls": "Topic",
            "summary": "",
            "messages": [
                {"_cls": "Message", "ai": False, "content": "First prompt", "summary": ""},
                {"_cls": "Message", "ai": True, "content": "Assistant reply", "summary": ""},
                {"_cls": "Message", "ai": False, "content": "Follow up", "summary": ""},
            ],
        },
    }

    assert extract_first_user_prompt(history_payload) == "First prompt"


def test_render_memory_index_keeps_one_line_per_memory():
    files = [
        DreamMemoryFile(
            file_name="alpha.md",
            title="Alpha",
            description="First durable memory",
            updated_at=datetime(2026, 3, 25, tzinfo=timezone.utc),
            content="# Alpha",
        ),
        DreamMemoryFile(
            file_name="beta.md",
            title="Beta",
            description="Second durable memory",
            updated_at=datetime(2026, 3, 24, tzinfo=timezone.utc),
            content="# Beta",
        ),
    ]

    rendered = render_memory_index(files, line_limit=10)

    assert "- [Alpha](memories/alpha.md): First durable memory" in rendered
    assert "- [Beta](memories/beta.md): Second durable memory" in rendered
    assert len(rendered.strip().splitlines()) <= 10


def test_should_run_auto_dream_uses_session_or_time_threshold():
    recent = 2
    last_dream_at = datetime.now(timezone.utc)

    assert should_run_auto_dream(None, recent, min_hours=8, min_sessions=3) is True
    assert should_run_auto_dream(last_dream_at, recent, min_hours=8, min_sessions=2) is True
    assert should_run_auto_dream(last_dream_at, recent, min_hours=8, min_sessions=3) is False


def test_select_memory_file_name_uses_title_for_new_files_and_existing_path_for_updates():
    existing = {"platform_decisions.md"}

    assert (
        select_memory_file_name("session-wrapup.md", "Platform Decisions", set())
        == "platform_decisions.md"
    )
    assert (
        select_memory_file_name("platform_decisions.md", "Fresh Title", existing)
        == "platform_decisions.md"
    )
    assert (
        select_memory_file_name("", "Platform Decisions", existing)
        == "platform_decisions.md"
    )


def test_render_auto_dream_log_entry_includes_inputs_and_orphan_hints():
    entry = render_auto_dream_log_entry(
        summary="Consolidated deployment notes.",
        created_files=["deploy-checklist.md"],
        updated_files=["architecture.md"],
        deleted_files=[],
        run_metadata={
            "memory_scope": {
                "canonical_name": "agent-zero",
                "memory_subdir": "projects/agent-zero",
            },
            "recent_session_count": 2,
            "recent_vector_count": 5,
            "related_vector_count": 3,
            "orphan_candidates": [
                {
                    "memory_subdir": "projects/agent-zero-old",
                    "memory_file_count": 2,
                }
            ],
        },
    )

    assert "- Summary: Consolidated deployment notes." in entry
    assert "- Scope: agent-zero (projects/agent-zero)" in entry
    assert "- Inputs: 2 sessions, 5 recent vector memories, 3 related vector memories" in entry
    assert "- Created: deploy-checklist.md" in entry
    assert "- Updated: architecture.md" in entry
    assert "- Rename / orphan hints: projects/agent-zero-old (2 files)" in entry


def test_find_orphan_candidates_scans_similar_project_memory_folders(tmp_path, monkeypatch):
    projects_root = tmp_path / "projects"
    current = projects_root / "my-new-project"
    orphan = projects_root / "my-old-project"
    unrelated = projects_root / "totally-different"

    for base in [current, orphan, unrelated]:
        (base / ".a0proj" / "memory" / "autodream" / "memories").mkdir(parents=True)

    (orphan / ".a0proj" / "memory" / "autodream" / "memories" / "context.md").write_text(
        "# Orphaned memory\n",
        encoding="utf-8",
    )
    (unrelated / ".a0proj" / "memory" / "autodream" / "memories" / "other.md").write_text(
        "# Unrelated memory\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(projects, "get_projects_parent_folder", lambda: str(projects_root))
    monkeypatch.setattr(
        projects,
        "get_project_meta",
        lambda name, *sub_dirs: str(projects_root / name / ".a0proj" / Path(*sub_dirs)),
    )

    candidates = find_orphan_candidates("projects/my-new-project")

    assert len(candidates) == 1
    assert candidates[0]["memory_subdir"] == "projects/my-old-project"
    assert candidates[0]["memory_file_count"] == 1


def test_load_autodream_markdown_documents_promotes_frontmatter_metadata(tmp_path):
    path = tmp_path / "memory.md"
    path.write_text(
        "---\n"
        "title: Alpha\n"
        "description: Durable note\n"
        "grounding: grounded\n"
        "source_memory_ids:\n"
        "  - mem-1\n"
        "---\n\n"
        "# Alpha\n\n"
        "Body text.\n",
        encoding="utf-8",
    )

    documents, metadata = load_autodream_markdown_documents(str(path))

    assert len(documents) == 1
    assert documents[0].page_content.startswith("# Alpha")
    assert metadata["autodream_file"] is True
    assert metadata["title"] == "Alpha"
    assert metadata["grounding"] == "grounded"
    assert metadata["source_memory_ids"] == ["mem-1"]


def test_clear_autodream_knowledge_import_cache_removes_only_autodream_entries(
    tmp_path, monkeypatch
):
    db_dir = tmp_path / "db"
    db_dir.mkdir()
    autodream_dir = tmp_path / "autodream" / "memories"
    autodream_dir.mkdir(parents=True)
    other_dir = tmp_path / "knowledge"
    other_dir.mkdir()

    autodream_file = autodream_dir / "alpha.md"
    autodream_file.write_text("# Alpha\n", encoding="utf-8")
    other_file = other_dir / "beta.md"
    other_file.write_text("# Beta\n", encoding="utf-8")

    index_path = db_dir / "knowledge_import.json"
    index_path.write_text(
        json.dumps(
            {
                str(autodream_file): {"file": str(autodream_file), "ids": ["a"]},
                str(other_file): {"file": str(other_file), "ids": ["b"]},
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(memory_helper, "abs_db_dir", lambda _subdir: str(db_dir))
    monkeypatch.setattr(
        auto_dream_helper,
        "get_autodream_memories_dir",
        lambda _subdir: str(autodream_dir),
    )

    clear_autodream_knowledge_import_cache("default")

    filtered = json.loads(index_path.read_text(encoding="utf-8"))
    assert str(autodream_file) not in filtered
    assert str(other_file) in filtered
