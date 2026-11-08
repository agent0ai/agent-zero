from helpers import files, migration


def test_cleanup_obsolete_preserves_both_log_locations(tmp_path, monkeypatch):
    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "old.html").write_text("old log", encoding="utf-8")
    current = tmp_path / "usr/logs"
    current.mkdir(parents=True)
    (current / "old.html").write_text("different existing log", encoding="utf-8")
    (current / "current.log").write_text("current log", encoding="utf-8")
    (tmp_path / "memory").mkdir()
    keep = tmp_path / "keep.txt"
    keep.write_text("keep", encoding="utf-8")
    monkeypatch.setattr(files, "_base_dir", str(tmp_path))

    migration._cleanup_obsolete()
    migration._cleanup_obsolete()

    assert (logs / "old.html").read_text() == "old log"
    assert (current / "old.html").read_text() == "different existing log"
    assert (current / "current.log").read_text() == "current log"
    assert not (tmp_path / "memory").exists()
    assert keep.exists()


def test_user_data_migration_leaves_legacy_log_symlink_untouched(tmp_path, monkeypatch):
    old_storage = tmp_path / "old-storage"
    old_storage.mkdir()
    (old_storage / "old.html").write_text("historical", encoding="utf-8")
    (tmp_path / "logs").symlink_to(old_storage, target_is_directory=True)
    monkeypatch.setattr(files, "_base_dir", str(tmp_path))

    migration.migrate_user_data()
    migration.migrate_user_data()

    assert (tmp_path / "logs").is_symlink()
    assert (old_storage / "old.html").read_text() == "historical"
