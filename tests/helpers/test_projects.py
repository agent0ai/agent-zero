"""Tests for python/helpers/projects.py — project CRUD, file structure, listing, switching, knowledge mapping."""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import python.helpers.projects as _projects_mod

# --- Fixtures ---


@pytest.fixture
def projects_env(tmp_workdir):
    """Set up usr/projects structure and patch files module to use tmp_workdir."""
    usr = tmp_workdir / "usr"
    projects = usr / "projects"
    projects.mkdir(parents=True, exist_ok=True)

    def get_abs_path(*args):
        if not args or (len(args) == 1 and args[0] == ""):
            return str(tmp_workdir)
        return str(tmp_workdir / "/".join(str(a).lstrip("/") for a in args))

    with patch.object(_projects_mod.files, "get_abs_path", side_effect=get_abs_path):
        with patch.object(_projects_mod.files, "get_base_dir", return_value=str(tmp_workdir)):
            yield tmp_workdir


@pytest.fixture
def project_files(tmp_workdir, projects_env):
    """Patch files module functions for project operations."""
    projects_root = tmp_workdir / "usr" / "projects"

    def get_abs_path(*args):
        if not args or (len(args) == 1 and args[0] == ""):
            return str(tmp_workdir)
        first = str(args[0]).replace("\\", "/")
        if os.path.isabs(first):
            base = Path(first)
            rest = [str(a).replace("\\", "/").strip("/") for a in args[1:] if str(a)]
            return str(base / "/".join(rest)) if rest else str(base)
        parts = [str(a).replace("\\", "/").strip("/") for a in args if str(a)]
        return str(tmp_workdir / "/".join(parts)) if parts else str(tmp_workdir)

    def create_dir_safe(dst, rename_format="{name}_{number}"):
        p = Path(dst)
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)
            return str(p)
        base = p.parent / p.name
        i = 2
        while (base.parent / f"{base.name}_{i}").exists():
            i += 1
        new_path = base.parent / f"{base.name}_{i}"
        new_path.mkdir(parents=True, exist_ok=True)
        return str(new_path)

    def create_dir(rel_path):
        p = Path(get_abs_path(rel_path))
        p.mkdir(parents=True, exist_ok=True)

    with patch.object(_projects_mod.files, "get_abs_path", side_effect=get_abs_path):
        with patch.object(_projects_mod.files, "create_dir_safe", side_effect=create_dir_safe):
            with patch.object(_projects_mod.files, "create_dir", side_effect=create_dir):
                with patch.object(_projects_mod.files, "delete_dir") as mock_del:
                    with patch.object(_projects_mod.files, "read_file") as mock_read:
                        with patch.object(_projects_mod.files, "write_file") as mock_write:
                            with patch.object(_projects_mod.files, "basename", side_effect=lambda p, s=None: Path(p).name.removesuffix(s or "")):
                                with patch.object(_projects_mod.files, "exists", side_effect=lambda p: Path(p).exists()):
                                    yield {
                                        "delete_dir": mock_del,
                                        "read_file": mock_read,
                                        "write_file": mock_write,
                                        "projects_root": projects_root,
                                    }


def _make_project_structure(tmp_workdir, name, header_data=None):
    """Create project directory structure and header file."""
    from python.helpers.projects import (
        PROJECT_META_DIR,
        PROJECT_HEADER_FILE,
        PROJECT_INSTRUCTIONS_DIR,
        PROJECT_KNOWLEDGE_DIR,
    )

    proj = tmp_workdir / "usr" / "projects" / name
    proj.mkdir(parents=True, exist_ok=True)
    meta = proj / PROJECT_META_DIR
    meta.mkdir(exist_ok=True)
    (meta / PROJECT_INSTRUCTIONS_DIR).mkdir(exist_ok=True)
    (meta / PROJECT_KNOWLEDGE_DIR).mkdir(exist_ok=True)

    default_header = {
        "title": f"Project {name}",
        "description": "",
        "instructions": "",
        "color": "#333",
        "git_url": "",
        "memory": "own",
        "file_structure": {
            "enabled": True,
            "max_depth": 5,
            "max_files": 20,
            "max_folders": 20,
            "max_lines": 250,
            "gitignore": "",
        },
    }
    if header_data:
        default_header.update(header_data)

    import json

    (meta / PROJECT_HEADER_FILE).write_text(json.dumps(default_header))
    return proj


# --- get_projects_parent_folder, get_project_folder, get_project_meta_folder ---


class TestProjectPaths:
    def test_get_projects_parent_folder(self, projects_env, tmp_workdir):
        from python.helpers.projects import get_projects_parent_folder

        path = get_projects_parent_folder()
        assert "usr" in path
        assert "projects" in path

    def test_get_project_folder(self, projects_env):
        from python.helpers.projects import get_project_folder

        path = get_project_folder("myproj")
        assert "myproj" in path
        assert "projects" in path

    def test_get_project_meta_folder(self, projects_env):
        from python.helpers.projects import get_project_meta_folder

        path = get_project_meta_folder("myproj")
        assert ".a0proj" in path
        assert "myproj" in path


# --- create_project ---


class TestCreateProject:
    def test_create_project_creates_structure(self, tmp_workdir, project_files):
        from python.helpers.projects import create_project

        with patch.object(_projects_mod, "create_project_meta_folders"):
            with patch.object(_projects_mod.files, "exists", return_value=False):
                with patch.object(_projects_mod.dirty_json, "stringify", side_effect=lambda x: str(x)):
                    name = create_project(
                        "newproj",
                        {
                            "title": "New",
                            "description": "Desc",
                            "instructions": "",
                            "color": "#abc",
                            "git_url": "",
                            "memory": "own",
                            "file_structure": {
                                "enabled": True,
                                "max_depth": 5,
                                "max_files": 20,
                                "max_folders": 20,
                                "max_lines": 250,
                                "gitignore": "",
                            },
                        },
                    )
        assert name == "newproj"
        project_files["write_file"].assert_called()


# --- delete_project ---


class TestDeleteProject:
    def test_delete_project_calls_delete_dir_and_deactivate(self, tmp_workdir, project_files):
        from python.helpers.projects import delete_project

        with patch.object(_projects_mod, "deactivate_project_in_chats") as mock_deact:
            result = delete_project("oldproj")
        assert result == "oldproj"
        project_files["delete_dir"].assert_called_once()
        mock_deact.assert_called_once_with("oldproj")


# --- load_project_header, save_project_header ---


class TestProjectHeader:
    def test_load_project_header_returns_data_with_name(self, tmp_workdir):
        _make_project_structure(tmp_workdir, "proj1", {"title": "My Project"})

        with patch.object(_projects_mod.files, "get_abs_path") as mock_path:
            mock_path.side_effect = lambda *a: str(tmp_workdir / "usr" / "projects" / "proj1" / ".a0proj" / "project.json")
            with patch.object(_projects_mod.files, "read_file") as mock_read:
                mock_read.return_value = '{"title": "My Project", "description": ""}'
                with patch.object(_projects_mod.dirty_json, "parse", return_value={"title": "My Project", "description": ""}):
                    from python.helpers.projects import load_project_header

                    data = load_project_header("proj1")
                    assert data["name"] == "proj1"
                    assert data["title"] == "My Project"


# --- get_active_projects_list ---


class TestGetActiveProjectsList:
    def test_get_active_projects_list_returns_sorted_projects(self, tmp_workdir):
        _make_project_structure(tmp_workdir, "b_proj", {"title": "B"})
        _make_project_structure(tmp_workdir, "a_proj", {"title": "A"})

        with patch.object(_projects_mod.files, "get_abs_path") as mock_path:
            mock_path.return_value = str(tmp_workdir / "usr" / "projects")
            with patch.object(_projects_mod, "load_basic_project_data") as mock_load:
                mock_load.side_effect = lambda n: {
                    "title": "A" if "a" in n else "B",
                    "description": "",
                    "color": "",
                }
                with patch("os.listdir", return_value=["b_proj", "a_proj"]):
                    with patch("os.path.isdir", return_value=True):
                        from python.helpers.projects import get_active_projects_list

                        projects = get_active_projects_list()
                assert len(projects) == 2
                assert projects[0]["name"] == "a_proj"
                assert projects[1]["name"] == "b_proj"


# --- load_basic_project_data, _normalizeBasicData ---


class TestLoadBasicProjectData:
    def test_load_basic_project_data_normalizes_fields(self, tmp_workdir):
        with patch.object(_projects_mod, "load_project_header") as mock_header:
            mock_header.return_value = {
                "name": "p1",
                "title": "T",
                "description": "D",
                "instructions": "I",
                "color": "c",
                "git_url": "u",
                "memory": "own",
            }
            with patch.object(_projects_mod.files, "read_file") as mock_read:
                mock_read.side_effect = Exception("no gitignore")
                from python.helpers.projects import load_basic_project_data

                data = load_basic_project_data("p1")
                assert data["title"] == "T"
                assert data["memory"] == "own"


# --- update_project ---


class TestUpdateProject:
    def test_update_project_merges_and_saves(self, tmp_workdir):
        with patch.object(_projects_mod, "load_edit_project_data") as mock_load:
            mock_load.return_value = {
                "name": "p1",
                "title": "Old",
                "description": "",
                "instructions": "",
                "variables": "",
                "secrets": "",
                "color": "",
                "git_url": "",
                "git_status": {},
                "instruction_files_count": 0,
                "knowledge_files_count": 0,
                "memory": "own",
                "file_structure": {},
                "subagents": {},
            }
            with patch.object(_projects_mod, "save_project_header") as mock_save_h:
                    with patch.object(_projects_mod, "save_project_variables"):
                        with patch.object(_projects_mod, "save_project_secrets"):
                            with patch.object(_projects_mod, "save_project_subagents"):
                                with patch.object(_projects_mod, "reactivate_project_in_chats"):
                                    from python.helpers.projects import update_project

                                    update_project("p1", {"title": "New Title"})
                                    mock_save_h.assert_called_once()
                                    call_args = mock_save_h.call_args[0][1]
                                    assert call_args["title"] == "New Title"


# --- get_additional_instructions_files ---


class TestGetAdditionalInstructionsFiles:
    def test_get_additional_instructions_returns_dict(self, tmp_workdir):
        proj = _make_project_structure(tmp_workdir, "p1")
        (proj / ".a0proj" / "instructions" / "extra.md").write_text("# Extra")

        with patch.object(_projects_mod.files, "get_abs_path") as mock_path:
            mock_path.side_effect = lambda *a: str(proj / ".a0proj" / "instructions")
            with patch.object(_projects_mod.files, "read_text_files_in_dir") as mock_read:
                mock_read.return_value = {"extra.md": "# Extra"}
                from python.helpers.projects import get_additional_instructions_files

                result = get_additional_instructions_files("p1")
                assert "extra.md" in result
                assert result["extra.md"] == "# Extra"


# --- get_context_project_name, get_context_memory_subdir ---


class TestContextProjectMapping:
    def test_get_context_project_name_returns_project_from_context(self):
        ctx = MagicMock()
        ctx.get_data.return_value = "myproj"
        from python.helpers.projects import get_context_project_name

        assert get_context_project_name(ctx) == "myproj"

    def test_get_context_project_name_returns_none_when_no_project(self):
        ctx = MagicMock()
        ctx.get_data.return_value = None
        from python.helpers.projects import get_context_project_name

        assert get_context_project_name(ctx) is None

    def test_get_context_memory_subdir_returns_subdir_for_own_memory(self):
        ctx = MagicMock()
        ctx.get_data.return_value = "myproj"
        with patch.object(_projects_mod, "load_basic_project_data") as mock_load:
            mock_load.return_value = {"memory": "own"}
            from python.helpers.projects import get_context_memory_subdir

            result = get_context_memory_subdir(ctx)
            assert result == "projects/myproj"

    def test_get_context_memory_subdir_returns_none_for_global_memory(self):
        ctx = MagicMock()
        ctx.get_data.return_value = "myproj"
        with patch.object(_projects_mod, "load_basic_project_data") as mock_load:
            mock_load.return_value = {"memory": "global"}
            from python.helpers.projects import get_context_memory_subdir

            assert get_context_memory_subdir(ctx) is None

    def test_get_context_memory_subdir_returns_none_when_no_project(self):
        ctx = MagicMock()
        ctx.get_data.return_value = None
        from python.helpers.projects import get_context_memory_subdir

        assert get_context_memory_subdir(ctx) is None


# --- create_project_meta_folders ---


class TestCreateProjectMetaFolders:
    def test_create_project_meta_folders_creates_instructions_and_knowledge(self, tmp_workdir):
        proj = tmp_workdir / "usr" / "projects" / "newproj"
        proj.mkdir(parents=True, exist_ok=True)

        def path_side(*args):
            parts = [str(proj)]
            for a in args:
                p = str(a).replace("\\", "/").strip("/")
                if p:
                    parts.append(p)
            return str(Path(*parts))

        area_main = MagicMock()
        area_main.value = "main"
        area_frag = MagicMock()
        area_frag.value = "fragments"
        area_sol = MagicMock()
        area_sol.value = "solutions"
        fake_areas = [area_main, area_frag, area_sol]

        with patch.object(_projects_mod.files, "get_abs_path", side_effect=path_side):
            with patch.object(_projects_mod.files, "create_dir") as mock_create:
                with patch("python.helpers.memory.Memory") as mock_mem:
                    mock_mem.Area = fake_areas
                    from python.helpers.projects import create_project_meta_folders

                    create_project_meta_folders("newproj")
                assert mock_create.call_count >= 2


# --- get_knowledge_files_count ---


class TestGetKnowledgeFilesCount:
    def test_get_knowledge_files_count_returns_count(self, tmp_workdir):
        proj = _make_project_structure(tmp_workdir, "p1")
        (proj / ".a0proj" / "knowledge" / "doc1.txt").write_text("x")
        (proj / ".a0proj" / "knowledge" / "doc2.txt").write_text("y")

        with patch.object(_projects_mod.files, "get_abs_path") as mock_path:
            mock_path.return_value = str(proj / ".a0proj" / "knowledge")
            with patch.object(_projects_mod.files, "list_files_in_dir_recursively") as mock_list:
                mock_list.return_value = ["doc1.txt", "doc2.txt"]
                from python.helpers.projects import get_knowledge_files_count

                assert get_knowledge_files_count("p1") == 2


# --- get_file_structure ---


class TestGetFileStructure:
    def test_get_file_structure_returns_tree_string(self, tmp_workdir):
        with patch.object(_projects_mod, "get_project_folder", return_value=str(tmp_workdir)):
            with patch.object(_projects_mod, "load_basic_project_data") as mock_load:
                mock_load.return_value = {
                    "file_structure": {
                        "max_depth": 5,
                        "max_files": 20,
                        "max_folders": 20,
                        "max_lines": 250,
                        "gitignore": "",
                    }
                }
                with patch.object(_projects_mod.file_tree, "file_tree") as mock_tree:
                    mock_tree.return_value = "src/\n  main.py"
                    from python.helpers.projects import get_file_structure

                    result = get_file_structure("p1")
                    assert "src" in result or "main.py" in result or "Empty" in result

    def test_get_file_structure_appends_empty_when_tree_empty(self, tmp_workdir):
        with patch.object(_projects_mod, "get_project_folder", return_value=str(tmp_workdir)):
            with patch.object(_projects_mod, "load_basic_project_data") as mock_load:
                mock_load.return_value = {
                    "file_structure": {
                        "max_depth": 5,
                        "max_files": 20,
                        "max_folders": 20,
                        "max_lines": 250,
                        "gitignore": "",
                    }
                }
                with patch.object(_projects_mod.file_tree, "file_tree", return_value=""):
                    from python.helpers.projects import get_file_structure

                    result = get_file_structure("p1")
                    assert "Empty" in result


# --- build_system_prompt_vars ---


class TestBuildSystemPromptVars:
    def test_build_system_prompt_vars_includes_project_data(self, tmp_workdir):
        with patch.object(_projects_mod, "load_basic_project_data") as mock_load:
            mock_load.return_value = {
                "title": "MyApp",
                "description": "A cool app",
                "instructions": "Do X",
                "git_url": "https://github.com/foo/bar",
                "file_structure": {},
            }
            with patch.object(_projects_mod, "get_additional_instructions_files", return_value={}):
                with patch.object(_projects_mod, "get_project_folder", return_value="/a0/projects/myapp"):
                    with patch.object(_projects_mod.files, "normalize_a0_path", return_value="/a0/projects/myapp"):
                        from python.helpers.projects import build_system_prompt_vars

                        vars = build_system_prompt_vars("myapp")
                        assert vars["project_name"] == "MyApp"
                        assert vars["project_description"] == "A cool app"
                        assert vars["project_instructions"] == "Do X"
                        assert vars["project_git_url"] == "https://github.com/foo/bar"


# --- load_project_variables, save_project_variables ---


class TestProjectVariables:
    def test_load_project_variables_returns_content(self):
        with patch.object(_projects_mod.files, "get_abs_path", return_value="/tmp/vars.env"):
            with patch.object(_projects_mod.files, "read_file", return_value="FOO=bar"):
                from python.helpers.projects import load_project_variables

                assert load_project_variables("p1") == "FOO=bar"

    def test_load_project_variables_returns_empty_on_error(self):
        with patch.object(_projects_mod.files, "get_abs_path", return_value="/tmp/vars.env"):
            with patch.object(_projects_mod.files, "read_file", side_effect=FileNotFoundError):
                from python.helpers.projects import load_project_variables

                assert load_project_variables("p1") == ""


# --- activate_project, deactivate_project ---


class TestActivateDeactivateProject:
    def test_activate_project_raises_when_context_not_found(self):
        with patch("agent.AgentContext") as mock_ctx:
            mock_ctx.get.return_value = None
            with patch.object(_projects_mod, "load_edit_project_data", return_value={"title": "P", "color": ""}):
                with pytest.raises(Exception, match="Context not found"):
                    from python.helpers.projects import activate_project

                    activate_project("ctx-1", "myproj")

    def test_deactivate_project_raises_when_context_not_found(self):
        with patch("agent.AgentContext") as mock_ctx:
            mock_ctx.get.return_value = None
            with pytest.raises(Exception, match="Context not found"):
                from python.helpers.projects import deactivate_project

                deactivate_project("ctx-1")


# --- clone_git_project ---


class TestCloneGitProject:
    def test_clone_git_project_creates_project_from_repo(self, tmp_workdir):
        with patch.object(_projects_mod.files, "create_dir_safe") as mock_create:
            mock_create.return_value = str(tmp_workdir / "usr" / "projects" / "cloned")
            with patch("python.helpers.git.clone_repo"):
                with patch("python.helpers.git.strip_auth_from_url", return_value="https://github.com/foo/bar"):
                    with patch("os.path.exists", return_value=False):
                        with patch.object(_projects_mod, "create_project_meta_folders"):
                            with patch.object(_projects_mod, "save_project_header"):
                                with patch.object(_projects_mod.dirty_json, "parse", side_effect=Exception):
                                    from python.helpers.projects import clone_git_project

                                    basic = {
                                        "title": "Cloned",
                                        "description": "",
                                        "instructions": "",
                                        "color": "",
                                        "git_url": "",
                                        "memory": "own",
                                        "file_structure": {
                                            "enabled": True,
                                            "max_depth": 5,
                                            "max_files": 20,
                                            "max_folders": 20,
                                            "max_lines": 250,
                                            "gitignore": "",
                                        },
                                    }
                                    name = clone_git_project(
                                        "cloned",
                                        "https://github.com/foo/bar",
                                        "token",
                                        basic,
                                    )
                                    assert name == "cloned"
