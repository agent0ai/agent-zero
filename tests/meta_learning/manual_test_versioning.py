#!/usr/bin/env python3
"""
Manual test script for prompt versioning system

Run this script to validate prompt versioning functionality.
Performs basic smoke tests without requiring pytest.

Usage:
    python tests/meta_learning/manual_test_versioning.py
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from python.helpers.prompt_versioning import PromptVersionManager
import tempfile
import shutil


def test_basic_functionality():
    """Test basic prompt versioning operations"""
    print("=" * 60)
    print("MANUAL TEST: Prompt Versioning System")
    print("=" * 60)

    # Create temp directory
    temp_dir = tempfile.mkdtemp(prefix="test_prompts_")
    prompts_dir = Path(temp_dir) / "prompts"
    prompts_dir.mkdir()

    try:
        # Create sample prompt files
        print("\n1. Creating sample prompt files...")
        (prompts_dir / "agent.system.main.md").write_text("# Main System Prompt\nOriginal content")
        (prompts_dir / "agent.system.tools.md").write_text("# Tools\nTool instructions")
        print("   ✓ Created 2 sample prompt files")

        # Initialize version manager
        print("\n2. Initializing PromptVersionManager...")
        manager = PromptVersionManager(prompts_dir=prompts_dir)
        print(f"   ✓ Prompts directory: {manager.prompts_dir}")
        print(f"   ✓ Versions directory: {manager.versions_dir}")

        # Create snapshot
        print("\n3. Creating first snapshot...")
        version1 = manager.create_snapshot(label="test_version_1")
        print(f"   ✓ Created snapshot: {version1}")

        # Verify snapshot files
        snapshot_dir = manager.versions_dir / version1
        assert snapshot_dir.exists(), "Snapshot directory should exist"
        assert (snapshot_dir / "agent.system.main.md").exists(), "Main prompt should be backed up"
        assert (snapshot_dir / "metadata.json").exists(), "Metadata should exist"
        print("   ✓ Verified snapshot files exist")

        # Modify a file
        print("\n4. Modifying prompt file...")
        main_file = prompts_dir / "agent.system.main.md"
        main_file.write_text("# Modified Content\nThis is different")
        print("   ✓ Modified agent.system.main.md")

        # Create second snapshot
        print("\n5. Creating second snapshot...")
        version2 = manager.create_snapshot(label="test_version_2")
        print(f"   ✓ Created snapshot: {version2}")

        # List versions
        print("\n6. Listing versions...")
        versions = manager.list_versions()
        print(f"   ✓ Found {len(versions)} versions")
        for v in versions:
            print(f"     - {v['version_id']} ({v['file_count']} files)")

        # Test diff
        print("\n7. Testing diff between versions...")
        diffs = manager.get_diff(version1, version2)
        print(f"   ✓ Found {len(diffs)} changed files")
        for filename, diff_info in diffs.items():
            print(f"     - {filename}: {diff_info['status']}")

        # Test rollback
        print("\n8. Testing rollback to version 1...")
        success = manager.rollback(version1, create_backup=False)
        assert success, "Rollback should succeed"
        print("   ✓ Rollback successful")

        # Verify rollback worked
        restored_content = main_file.read_text()
        assert "Original content" in restored_content, "Content should be restored"
        assert "Modified Content" not in restored_content, "Modified content should be gone"
        print("   ✓ Verified content was restored")

        # Test apply_change
        print("\n9. Testing apply_change with automatic versioning...")
        new_content = "# Updated Prompt\nNew content via apply_change"
        backup_version = manager.apply_change(
            file_name="agent.system.main.md",
            content=new_content,
            change_description="Test change application"
        )
        print(f"   ✓ Change applied, backup created: {backup_version}")

        # Verify change was applied
        assert main_file.read_text() == new_content, "Content should be updated"
        print("   ✓ Verified new content was applied")

        # Test delete old versions
        print("\n10. Testing delete old versions...")
        # Create more versions
        for i in range(5):
            manager.create_snapshot(label=f"extra_version_{i}")

        total_before = len(manager.list_versions())
        deleted = manager.delete_old_versions(keep_count=3)
        total_after = len(manager.list_versions())

        print(f"   ✓ Had {total_before} versions, deleted {deleted}, now have {total_after}")
        assert total_after == 3, "Should keep exactly 3 versions"

        # Test export (use a version that still exists)
        print("\n11. Testing version export...")
        export_dir = Path(temp_dir) / "export"
        export_dir.mkdir()
        # Get the most recent version (which should still exist)
        remaining_versions = manager.list_versions()
        latest_version = remaining_versions[0]["version_id"]
        manager.export_version(latest_version, str(export_dir))
        assert (export_dir / "agent.system.main.md").exists(), "Exported file should exist"
        print(f"   ✓ Version {latest_version} exported successfully")

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup
        print("\n12. Cleaning up temporary files...")
        shutil.rmtree(temp_dir)
        print("   ✓ Cleanup complete")


if __name__ == "__main__":
    success = test_basic_functionality()
    sys.exit(0 if success else 1)
