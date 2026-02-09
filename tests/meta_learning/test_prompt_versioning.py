"""
Tests for Prompt Version Control System

Tests all functionality of the prompt versioning system including
backup, restore, diff, and version management operations.

Author: Agent Zero Meta-Learning System
Created: January 5, 2026
"""

import os
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from python.helpers.prompt_versioning import (
    PromptVersionManager,
    create_prompt_backup,
    rollback_prompts,
    list_prompt_versions
)


@pytest.fixture
def temp_prompts_dir():
    """Create a temporary prompts directory for testing"""
    temp_dir = tempfile.mkdtemp(prefix="test_prompts_")
    prompts_dir = Path(temp_dir) / "prompts"
    prompts_dir.mkdir()

    # Create some sample prompt files
    (prompts_dir / "agent.system.main.md").write_text("# Main System Prompt\nOriginal content")
    (prompts_dir / "agent.system.tools.md").write_text("# Tools\nTool instructions")
    (prompts_dir / "agent.system.memory.md").write_text("# Memory\nMemory instructions")

    yield prompts_dir

    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def version_manager(temp_prompts_dir):
    """Create a PromptVersionManager instance for testing"""
    return PromptVersionManager(prompts_dir=temp_prompts_dir)


class TestPromptVersionManager:
    """Test suite for PromptVersionManager"""

    def test_initialization(self, temp_prompts_dir):
        """Test that version manager initializes correctly"""
        manager = PromptVersionManager(prompts_dir=temp_prompts_dir)

        assert manager.prompts_dir == temp_prompts_dir
        assert manager.versions_dir == temp_prompts_dir / "versioned"
        assert manager.versions_dir.exists()

    def test_create_snapshot_basic(self, version_manager, temp_prompts_dir):
        """Test creating a basic snapshot"""
        version_id = version_manager.create_snapshot(label="test_snapshot")

        # Check version was created
        assert version_id == "test_snapshot"
        snapshot_dir = version_manager.versions_dir / version_id
        assert snapshot_dir.exists()

        # Check all files were copied
        assert (snapshot_dir / "agent.system.main.md").exists()
        assert (snapshot_dir / "agent.system.tools.md").exists()
        assert (snapshot_dir / "agent.system.memory.md").exists()

        # Check metadata
        metadata_file = snapshot_dir / "metadata.json"
        assert metadata_file.exists()

        import json
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

        assert metadata["version_id"] == "test_snapshot"
        assert metadata["label"] == "test_snapshot"
        assert metadata["file_count"] == 3
        assert "timestamp" in metadata

    def test_create_snapshot_auto_label(self, version_manager):
        """Test creating a snapshot with auto-generated label"""
        version_id = version_manager.create_snapshot()

        # Should be a timestamp
        assert len(version_id) == 15  # YYYYMMDD_HHMMSS
        assert version_id[:8].isdigit()  # Date part
        assert version_id[9:].isdigit()  # Time part
        assert version_id[8] == "_"

    def test_create_snapshot_with_changes(self, version_manager):
        """Test creating a snapshot with change tracking"""
        changes = [
            {
                "file": "agent.system.main.md",
                "description": "Added new instruction",
                "timestamp": datetime.now().isoformat()
            }
        ]

        version_id = version_manager.create_snapshot(label="with_changes", changes=changes)

        # Check changes are in metadata
        metadata = version_manager.get_version(version_id)
        assert metadata is not None
        assert len(metadata["changes"]) == 1
        assert metadata["changes"][0]["file"] == "agent.system.main.md"
        assert metadata["created_by"] == "meta_learning"

    def test_list_versions(self, version_manager):
        """Test listing versions"""
        # Create multiple versions
        version_manager.create_snapshot(label="version1")
        version_manager.create_snapshot(label="version2")
        version_manager.create_snapshot(label="version3")

        # List versions
        versions = version_manager.list_versions()

        assert len(versions) == 3
        # Should be sorted by timestamp (newest first)
        assert versions[0]["version_id"] == "version3"
        assert versions[1]["version_id"] == "version2"
        assert versions[2]["version_id"] == "version1"

    def test_list_versions_with_limit(self, version_manager):
        """Test listing versions with limit"""
        # Create 5 versions
        for i in range(5):
            version_manager.create_snapshot(label=f"version{i}")

        # Get only 3 most recent
        versions = version_manager.list_versions(limit=3)

        assert len(versions) == 3
        assert versions[0]["version_id"] == "version4"
        assert versions[2]["version_id"] == "version2"

    def test_get_version(self, version_manager):
        """Test getting specific version metadata"""
        version_id = version_manager.create_snapshot(label="test_version")

        metadata = version_manager.get_version(version_id)

        assert metadata is not None
        assert metadata["version_id"] == "test_version"
        assert metadata["file_count"] == 3

    def test_get_version_not_found(self, version_manager):
        """Test getting non-existent version"""
        metadata = version_manager.get_version("nonexistent")

        assert metadata is None

    def test_rollback(self, version_manager, temp_prompts_dir):
        """Test rolling back to a previous version"""
        # Create initial snapshot
        original_version = version_manager.create_snapshot(label="original")

        # Modify a file
        main_file = temp_prompts_dir / "agent.system.main.md"
        main_file.write_text("# Modified Content\nThis is different")

        # Rollback
        success = version_manager.rollback(original_version, create_backup=False)

        assert success is True

        # Check content was restored
        restored_content = main_file.read_text()
        assert "Original content" in restored_content
        assert "Modified Content" not in restored_content

    def test_rollback_with_backup(self, version_manager, temp_prompts_dir):
        """Test rollback creates backup of current state"""
        # Create initial snapshot
        original_version = version_manager.create_snapshot(label="original")

        # Modify a file
        main_file = temp_prompts_dir / "agent.system.main.md"
        modified_content = "# Modified Content\nThis is different"
        main_file.write_text(modified_content)

        # Count versions before rollback
        versions_before = len(version_manager.list_versions())

        # Rollback with backup
        success = version_manager.rollback(original_version, create_backup=True)

        assert success is True

        # Should have one more version (the backup)
        versions_after = len(version_manager.list_versions())
        assert versions_after == versions_before + 1

        # The newest version should be the pre-rollback backup
        latest_version = version_manager.list_versions()[0]
        assert "pre_rollback" in latest_version["version_id"]

    def test_rollback_nonexistent_version(self, version_manager):
        """Test rollback with non-existent version fails gracefully"""
        with pytest.raises(ValueError, match="Version .* not found"):
            version_manager.rollback("nonexistent_version")

    def test_get_diff_no_changes(self, version_manager):
        """Test diff between identical versions"""
        version_a = version_manager.create_snapshot(label="version_a")
        version_b = version_manager.create_snapshot(label="version_b")

        diffs = version_manager.get_diff(version_a, version_b)

        # No differences
        assert len(diffs) == 0

    def test_get_diff_modified_file(self, version_manager, temp_prompts_dir):
        """Test diff detects modified files"""
        # Create first version
        version_a = version_manager.create_snapshot(label="version_a")

        # Modify a file
        main_file = temp_prompts_dir / "agent.system.main.md"
        main_file.write_text("# Modified\nDifferent content now")

        # Create second version
        version_b = version_manager.create_snapshot(label="version_b")

        # Get diff
        diffs = version_manager.get_diff(version_a, version_b)

        assert len(diffs) == 1
        assert "agent.system.main.md" in diffs
        assert diffs["agent.system.main.md"]["status"] == "modified"
        assert diffs["agent.system.main.md"]["lines_a"] == 2
        assert diffs["agent.system.main.md"]["lines_b"] == 2

    def test_get_diff_added_file(self, version_manager, temp_prompts_dir):
        """Test diff detects added files"""
        # Create first version
        version_a = version_manager.create_snapshot(label="version_a")

        # Add a new file
        new_file = temp_prompts_dir / "agent.system.new.md"
        new_file.write_text("# New File\nThis is new")

        # Create second version
        version_b = version_manager.create_snapshot(label="version_b")

        # Get diff
        diffs = version_manager.get_diff(version_a, version_b)

        assert len(diffs) == 1
        assert "agent.system.new.md" in diffs
        assert diffs["agent.system.new.md"]["status"] == "added"
        assert diffs["agent.system.new.md"]["lines_b"] == 2

    def test_get_diff_deleted_file(self, version_manager, temp_prompts_dir):
        """Test diff detects deleted files"""
        # Create first version
        version_a = version_manager.create_snapshot(label="version_a")

        # Delete a file
        (temp_prompts_dir / "agent.system.memory.md").unlink()

        # Create second version
        version_b = version_manager.create_snapshot(label="version_b")

        # Get diff
        diffs = version_manager.get_diff(version_a, version_b)

        assert len(diffs) == 1
        assert "agent.system.memory.md" in diffs
        assert diffs["agent.system.memory.md"]["status"] == "deleted"
        assert diffs["agent.system.memory.md"]["lines_a"] == 2

    def test_apply_change(self, version_manager, temp_prompts_dir):
        """Test applying a change with automatic versioning"""
        new_content = "# Updated Main Prompt\nNew instructions here"

        # Apply change
        version_id = version_manager.apply_change(
            file_name="agent.system.main.md",
            content=new_content,
            change_description="Updated main prompt for better clarity"
        )

        # Check backup was created
        assert version_id is not None
        backup_metadata = version_manager.get_version(version_id)
        assert backup_metadata is not None
        assert len(backup_metadata["changes"]) == 1
        assert backup_metadata["changes"][0]["file"] == "agent.system.main.md"

        # Check change was applied
        main_file = temp_prompts_dir / "agent.system.main.md"
        assert main_file.read_text() == new_content

    def test_delete_old_versions(self, version_manager):
        """Test deleting old versions"""
        # Create 10 versions
        for i in range(10):
            version_manager.create_snapshot(label=f"version_{i}")

        # Delete old versions, keep only 5
        deleted_count = version_manager.delete_old_versions(keep_count=5)

        assert deleted_count == 5

        # Check only 5 versions remain
        remaining_versions = version_manager.list_versions()
        assert len(remaining_versions) == 5

        # Check newest 5 are kept
        assert remaining_versions[0]["version_id"] == "version_9"
        assert remaining_versions[4]["version_id"] == "version_5"

    def test_delete_old_versions_keep_all(self, version_manager):
        """Test delete old versions when count is below threshold"""
        # Create 3 versions
        for i in range(3):
            version_manager.create_snapshot(label=f"version_{i}")

        # Try to keep 5 (more than exist)
        deleted_count = version_manager.delete_old_versions(keep_count=5)

        assert deleted_count == 0

        # All versions should remain
        remaining_versions = version_manager.list_versions()
        assert len(remaining_versions) == 3

    def test_export_version(self, version_manager):
        """Test exporting a version to external directory"""
        # Create a version
        version_id = version_manager.create_snapshot(label="export_test")

        # Create temp export directory
        with tempfile.TemporaryDirectory() as export_dir:
            success = version_manager.export_version(version_id, export_dir)

            assert success is True

            # Check files were exported
            export_path = Path(export_dir)
            assert (export_path / "agent.system.main.md").exists()
            assert (export_path / "agent.system.tools.md").exists()
            assert (export_path / "metadata.json").exists()

    def test_export_version_nonexistent(self, version_manager):
        """Test exporting non-existent version fails"""
        with tempfile.TemporaryDirectory() as export_dir:
            with pytest.raises(ValueError, match="Version .* not found"):
                version_manager.export_version("nonexistent", export_dir)

    def test_safe_label_validation(self, version_manager):
        """Test label safety validation"""
        # Safe labels
        assert version_manager._is_safe_label("test_version") is True
        assert version_manager._is_safe_label("version-123") is True
        assert version_manager._is_safe_label("v1_2_3") is True

        # Unsafe labels
        assert version_manager._is_safe_label("test/version") is False
        assert version_manager._is_safe_label("test version") is False
        assert version_manager._is_safe_label("test\\version") is False


class TestConvenienceFunctions:
    """Test suite for convenience functions"""

    def test_create_prompt_backup(self, temp_prompts_dir, monkeypatch):
        """Test quick backup function"""
        # Monkeypatch to use our temp directory
        def mock_get_abs_path(base, rel):
            return str(temp_prompts_dir)

        from python.helpers import files
        monkeypatch.setattr(files, "get_abs_path", mock_get_abs_path)

        version_id = create_prompt_backup(label="quick_backup")

        assert version_id is not None
        manager = PromptVersionManager(prompts_dir=temp_prompts_dir)
        metadata = manager.get_version(version_id)
        assert metadata is not None

    def test_rollback_prompts(self, temp_prompts_dir, monkeypatch):
        """Test quick rollback function"""
        # Monkeypatch to use our temp directory
        def mock_get_abs_path(base, rel):
            return str(temp_prompts_dir)

        from python.helpers import files
        monkeypatch.setattr(files, "get_abs_path", mock_get_abs_path)

        # Create a version first
        manager = PromptVersionManager(prompts_dir=temp_prompts_dir)
        version_id = manager.create_snapshot(label="rollback_test")

        # Rollback
        success = rollback_prompts(version_id)

        assert success is True

    def test_list_prompt_versions(self, temp_prompts_dir, monkeypatch):
        """Test quick list function"""
        # Monkeypatch to use our temp directory
        def mock_get_abs_path(base, rel):
            return str(temp_prompts_dir)

        from python.helpers import files
        monkeypatch.setattr(files, "get_abs_path", mock_get_abs_path)

        # Create some versions
        manager = PromptVersionManager(prompts_dir=temp_prompts_dir)
        manager.create_snapshot(label="v1")
        manager.create_snapshot(label="v2")

        # List versions
        versions = list_prompt_versions(limit=10)

        assert len(versions) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
