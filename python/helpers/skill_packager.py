"""Package skills as .tar.gz archives with SHA256 integrity verification."""

from __future__ import annotations

import hashlib
import os
import tarfile
from pathlib import Path

# Files/dirs to include in a skill package.
INCLUDE_PATTERNS: set[str] = {
    "SKILL.md",
    "requirements.txt",
}
INCLUDE_EXTENSIONS: set[str] = {".py", ".md", ".txt", ".json", ".yaml", ".yml"}
INCLUDE_DIRS: set[str] = {"tests", "examples"}

# Paths and patterns to exclude.
EXCLUDE_NAMES: set[str] = {"__pycache__", ".git", ".env", ".venv", "node_modules"}
EXCLUDE_EXTENSIONS: set[str] = {".pyc", ".pyo", ".egg-info"}


class SkillPackager:
    """Package skills as .tar.gz with SHA256 integrity."""

    def package(self, skill_dir: Path, output_dir: Path | None = None) -> Path:
        """Create a .tar.gz package from a skill directory.

        Includes SKILL.md, *.py, requirements.txt, tests/, and examples/.
        Excludes __pycache__, .git, .env, and *.pyc files.
        """
        skill_dir = Path(skill_dir).resolve()
        if not skill_dir.is_dir():
            raise FileNotFoundError(f"Skill directory not found: {skill_dir}")

        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file():
            raise FileNotFoundError(f"SKILL.md not found in {skill_dir}")

        skill_name = skill_dir.name
        if output_dir is None:
            output_dir = skill_dir.parent
        output_dir = Path(output_dir).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        archive_path = output_dir / f"{skill_name}.tar.gz"

        with tarfile.open(archive_path, "w:gz") as tar:
            for root, dirs, files in os.walk(skill_dir):
                # Filter out excluded directories in-place.
                dirs[:] = [d for d in dirs if d not in EXCLUDE_NAMES and not d.startswith(".")]

                rel_root = Path(root).relative_to(skill_dir)

                for fname in sorted(files):
                    if self._should_exclude_file(fname):
                        continue
                    if not self._should_include_file(fname, rel_root):
                        continue

                    full_path = Path(root) / fname
                    arcname = str(Path(skill_name) / rel_root / fname)
                    tar.add(str(full_path), arcname=arcname)

        return archive_path

    def verify(self, package_path: Path, expected_sha256: str) -> bool:
        """Verify package integrity by comparing SHA256 hashes."""
        actual = self.get_sha256(package_path)
        return actual == expected_sha256.lower().strip()

    def extract(self, package_path: Path, target_dir: Path) -> Path:
        """Extract a skill package to the target directory.

        Returns the path to the extracted skill directory.
        """
        package_path = Path(package_path).resolve()
        target_dir = Path(target_dir).resolve()

        if not package_path.is_file():
            raise FileNotFoundError(f"Package not found: {package_path}")

        target_dir.mkdir(parents=True, exist_ok=True)

        with tarfile.open(package_path, "r:gz") as tar:
            # Security: check for path traversal attacks.
            for member in tar.getmembers():
                member_path = os.path.normpath(member.name)
                if member_path.startswith("..") or os.path.isabs(member_path):
                    raise ValueError(f"Unsafe path in archive: {member.name}")
            tar.extractall(target_dir, filter="data")

        # The top-level directory inside the archive is the skill name.
        stem = package_path.name.replace(".tar.gz", "")
        extracted = target_dir / stem
        return extracted

    def get_sha256(self, package_path: Path) -> str:
        """Calculate the SHA256 hash of a package file."""
        package_path = Path(package_path)
        if not package_path.is_file():
            raise FileNotFoundError(f"Package not found: {package_path}")

        sha256 = hashlib.sha256()
        with open(package_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    # -- internal helpers ---------------------------------------------------------

    @staticmethod
    def _should_exclude_file(fname: str) -> bool:
        """Return True if the file should be excluded from the package."""
        if fname in EXCLUDE_NAMES:
            return True
        if fname.startswith("."):
            return True
        _, ext = os.path.splitext(fname)
        return ext in EXCLUDE_EXTENSIONS

    @staticmethod
    def _should_include_file(fname: str, rel_root: Path) -> bool:
        """Return True if the file should be included in the package."""
        # Always include explicitly listed files.
        if fname in INCLUDE_PATTERNS:
            return True

        # Include files with allowed extensions.
        _, ext = os.path.splitext(fname)
        if ext in INCLUDE_EXTENSIONS:
            return True

        # Include anything inside explicitly included directories.
        parts = rel_root.parts
        return bool(parts and parts[0] in INCLUDE_DIRS)
