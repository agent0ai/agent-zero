from helpers import file_tree as file_tree_module


def test_file_tree_skips_entries_deleted_after_scan(monkeypatch, tmp_path):
    workdir = tmp_path / "work"
    workdir.mkdir()

    class VanishedEntry:
        name = "state.json"
        path = str(workdir / name)

        @staticmethod
        def stat(*, follow_symlinks):
            raise FileNotFoundError

    monkeypatch.setattr(
        file_tree_module.files_helper,
        "get_abs_path",
        lambda relative_path: str(workdir),
    )
    monkeypatch.setattr(
        file_tree_module.files_helper,
        "get_abs_path_dockerized",
        lambda relative_path: "/work",
    )
    monkeypatch.setattr(
        file_tree_module,
        "_list_directory_children",
        lambda *args, **kwargs: ([], [VanishedEntry()]),
    )

    assert file_tree_module.file_tree("work", max_depth=1) == "/work/"
