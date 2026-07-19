from helpers import files, migration


def test_cleanup_obsolete_removes_legacy_logs(tmp_path, monkeypatch):
    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "old.html").write_text("old log", encoding="utf-8")
    keep = tmp_path / "keep.txt"
    keep.write_text("keep", encoding="utf-8")
    monkeypatch.setattr(files, "_base_dir", str(tmp_path))

    migration._cleanup_obsolete()
    migration._cleanup_obsolete()

    assert not logs.exists()
    assert keep.exists()
