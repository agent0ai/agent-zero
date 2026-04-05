"""
Prompt Version Control System

Manages versioning, backup, and rollback of Agent Zero's prompt files.
Enables safe experimentation with prompt refinements from meta-learning.

Author: Agent Zero Meta-Learning System
Created: January 5, 2026
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from python.helpers import files


class PromptVersionManager:
    """Manage prompt versions with backup and rollback capabilities"""

    def __init__(self, prompts_dir: Optional[Path] = None, versions_dir: Optional[Path] = None):
        """
        Initialize prompt version manager

        Args:
            prompts_dir: Directory containing prompt files (default: prompts/)
            versions_dir: Directory for version backups (default: prompts/versioned/)
        """
        self.prompts_dir = Path(prompts_dir) if prompts_dir else Path(files.get_abs_path(".", "prompts"))
        self.versions_dir = Path(versions_dir) if versions_dir else self.prompts_dir / "versioned"
        self.versions_dir.mkdir(parents=True, exist_ok=True)

    def create_snapshot(self, label: Optional[str] = None, changes: Optional[List[Dict]] = None) -> str:
        """
        Create a full snapshot of all prompt files

        Args:
            label: Optional label for this version (default: timestamp-based)
            changes: Optional list of changes being applied (for tracking)

        Returns:
            version_id: Unique identifier for this snapshot
        """
        # Generate version ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        version_id = label if label and self._is_safe_label(label) else timestamp

        # Create snapshot directory
        snapshot_dir = self.versions_dir / version_id
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        # Copy all prompt files
        file_count = 0
        for prompt_file in self.prompts_dir.glob("*.md"):
            dest = snapshot_dir / prompt_file.name
            shutil.copy2(prompt_file, dest)
            file_count += 1

        # Save metadata
        metadata = {
            "version_id": version_id,
            "timestamp": datetime.now().isoformat(),
            "label": label,
            "file_count": file_count,
            "changes": changes or [],
            "created_by": "meta_learning" if changes else "manual"
        }

        metadata_file = snapshot_dir / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)

        return version_id

    def list_versions(self, limit: int = 50) -> List[Dict]:
        """
        List all prompt versions with metadata

        Args:
            limit: Maximum number of versions to return

        Returns:
            List of version metadata dictionaries, sorted by timestamp (newest first)
        """
        versions = []

        for version_dir in self.versions_dir.iterdir():
            if not version_dir.is_dir():
                continue

            metadata_file = version_dir / "metadata.json"
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        versions.append(metadata)
                except Exception as e:
                    # Skip corrupted metadata files
                    print(f"Warning: Could not read metadata for {version_dir.name}: {e}")
                    continue

        # Sort by timestamp (newest first)
        versions.sort(key=lambda v: v.get("timestamp", ""), reverse=True)

        return versions[:limit]

    def get_version(self, version_id: str) -> Optional[Dict]:
        """
        Get metadata for a specific version

        Args:
            version_id: Version identifier

        Returns:
            Version metadata dict or None if not found
        """
        version_dir = self.versions_dir / version_id
        metadata_file = version_dir / "metadata.json"

        if not metadata_file.exists():
            return None

        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None

    def rollback(self, version_id: str, create_backup: bool = True) -> bool:
        """
        Rollback to a previous version

        Args:
            version_id: Version to restore
            create_backup: Create backup of current state before rollback (recommended)

        Returns:
            Success status
        """
        version_dir = self.versions_dir / version_id

        if not version_dir.exists():
            raise ValueError(f"Version {version_id} not found")

        # Create backup of current state first
        if create_backup:
            backup_id = self.create_snapshot(label=f"pre_rollback_{version_id}")
            print(f"Created backup: {backup_id}")

        # Restore files from version
        restored_count = 0
        for prompt_file in version_dir.glob("*.md"):
            dest = self.prompts_dir / prompt_file.name
            shutil.copy2(prompt_file, dest)
            restored_count += 1

        print(f"Restored {restored_count} prompt files from version {version_id}")
        return True

    def get_diff(self, version_a: str, version_b: str) -> Dict[str, Dict]:
        """
        Compare two versions and return differences

        Args:
            version_a: First version ID
            version_b: Second version ID

        Returns:
            Dictionary mapping filenames to diff information
        """
        dir_a = self.versions_dir / version_a
        dir_b = self.versions_dir / version_b

        if not dir_a.exists():
            raise ValueError(f"Version {version_a} not found")
        if not dir_b.exists():
            raise ValueError(f"Version {version_b} not found")

        diffs = {}

        # Get all prompt files from both versions
        files_a = {f.name for f in dir_a.glob("*.md")}
        files_b = {f.name for f in dir_b.glob("*.md")}

        # Files in both versions (potentially modified)
        common_files = files_a & files_b
        for filename in common_files:
            content_a = (dir_a / filename).read_text(encoding='utf-8')
            content_b = (dir_b / filename).read_text(encoding='utf-8')

            if content_a != content_b:
                diffs[filename] = {
                    "status": "modified",
                    "lines_a": len(content_a.splitlines()),
                    "lines_b": len(content_b.splitlines()),
                    "size_a": len(content_a),
                    "size_b": len(content_b)
                }

        # Files only in version A (deleted in B)
        for filename in files_a - files_b:
            diffs[filename] = {
                "status": "deleted",
                "lines_a": len((dir_a / filename).read_text(encoding='utf-8').splitlines()),
                "size_a": (dir_a / filename).stat().st_size
            }

        # Files only in version B (added)
        for filename in files_b - files_a:
            diffs[filename] = {
                "status": "added",
                "lines_b": len((dir_b / filename).read_text(encoding='utf-8').splitlines()),
                "size_b": (dir_b / filename).stat().st_size
            }

        return diffs

    def apply_change(self, file_name: str, content: str, change_description: str = "") -> str:
        """
        Apply a change to a prompt file with automatic versioning

        Args:
            file_name: Name of the prompt file (e.g., "agent.system.main.md")
            content: New content for the file
            change_description: Description of the change (for metadata)

        Returns:
            version_id: ID of the backup version created before change
        """
        # Create backup first
        version_id = self.create_snapshot(
            label=None,  # Auto-generated timestamp
            changes=[{
                "file": file_name,
                "description": change_description,
                "timestamp": datetime.now().isoformat()
            }]
        )

        # Apply change
        file_path = self.prompts_dir / file_name
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"Applied change to {file_name}, backup version: {version_id}")
        return version_id

    def delete_old_versions(self, keep_count: int = 50) -> int:
        """
        Delete old versions, keeping only the most recent ones

        Args:
            keep_count: Number of versions to keep

        Returns:
            Number of versions deleted
        """
        versions = self.list_versions(limit=1000)  # Get all versions

        if len(versions) <= keep_count:
            return 0

        # Delete oldest versions
        versions_to_delete = versions[keep_count:]
        deleted_count = 0

        for version in versions_to_delete:
            version_id = version["version_id"]
            version_dir = self.versions_dir / version_id

            if version_dir.exists():
                shutil.rmtree(version_dir)
                deleted_count += 1

        return deleted_count

    def export_version(self, version_id: str, export_path: str) -> bool:
        """
        Export a version to a specified directory

        Args:
            version_id: Version to export
            export_path: Destination directory

        Returns:
            Success status
        """
        version_dir = self.versions_dir / version_id

        if not version_dir.exists():
            raise ValueError(f"Version {version_id} not found")

        export_dir = Path(export_path)
        export_dir.mkdir(parents=True, exist_ok=True)

        # Copy all files
        for item in version_dir.iterdir():
            dest = export_dir / item.name
            if item.is_file():
                shutil.copy2(item, dest)

        return True

    def _is_safe_label(self, label: str) -> bool:
        """
        Check if a label is safe for use as a directory name

        Args:
            label: Label to validate

        Returns:
            True if safe, False otherwise
        """
        # Allow alphanumeric, underscore, hyphen
        return all(c.isalnum() or c in ['_', '-'] for c in label)


# Convenience functions for common operations

def create_prompt_backup(label: Optional[str] = None) -> str:
    """
    Quick backup of current prompt state

    Args:
        label: Optional label for this backup

    Returns:
        version_id: Backup version ID
    """
    manager = PromptVersionManager()
    return manager.create_snapshot(label=label)


def rollback_prompts(version_id: str) -> bool:
    """
    Quick rollback to a previous version

    Args:
        version_id: Version to restore

    Returns:
        Success status
    """
    manager = PromptVersionManager()
    return manager.rollback(version_id)


def list_prompt_versions(limit: int = 20) -> List[Dict]:
    """
    Quick list of recent prompt versions

    Args:
        limit: Number of versions to return

    Returns:
        List of version metadata
    """
    manager = PromptVersionManager()
    return manager.list_versions(limit=limit)
