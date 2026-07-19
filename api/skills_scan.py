from __future__ import annotations

import shutil
import time
import uuid
from pathlib import Path
from typing import Any

from helpers import files, skills
from helpers.api import ApiHandler, Request, Response
from helpers.skills_import import extract_skills_zip
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename


class SkillsScan(ApiHandler):
    """
    Prepare skill scan targets for the Settings > Skills scanner.
    """

    async def process(self, input: dict[str, Any], request: Request) -> dict[str, Any] | Response:
        if "skills_file" in request.files:
            return self._prepare_uploaded_archive(request.files["skills_file"])

        action = str(input.get("action") or "targets").strip().lower()
        if action == "targets":
            return self._list_installed_targets()

        return {"success": False, "error": "Invalid action"}

    def _list_installed_targets(self) -> dict[str, Any]:
        targets: list[dict[str, Any]] = []
        seen: set[str] = set()
        total_skills = 0

        for raw_root in skills.get_skill_roots():
            root = Path(raw_root)
            if not root.is_dir():
                continue

            skill_files = skills.discover_skill_md_files(root)
            if not skill_files:
                continue

            key = str(root.resolve())
            if key in seen:
                continue
            seen.add(key)

            skill_count = len(skill_files)
            total_skills += skill_count
            targets.append(
                {
                    "path": str(root),
                    "display_path": files.normalize_a0_path(str(root)),
                    "skill_count": skill_count,
                }
            )

        targets.sort(key=lambda item: item["path"])
        return {
            "success": True,
            "target_type": "installed",
            "target_label": "Installed Agent Zero skills",
            "targets": targets,
            "paths": [item["path"] for item in targets],
            "skill_count": total_skills,
        }

    def _prepare_uploaded_archive(self, skills_file: FileStorage) -> dict[str, Any]:
        if not skills_file.filename:
            return {"success": False, "error": "No file selected"}

        base = secure_filename(skills_file.filename)  # type: ignore[arg-type]
        if not base.lower().endswith(".zip"):
            return {"success": False, "error": "Skill scan uploads must be .zip files"}

        tmp_dir = Path(files.get_abs_path("tmp", "uploads"))
        tmp_dir.mkdir(parents=True, exist_ok=True)
        unique = uuid.uuid4().hex[:8]
        stamp = time.strftime("%Y%m%d_%H%M%S")
        tmp_path = tmp_dir / f"skills_scan_{stamp}_{unique}_{base}"
        skills_file.save(str(tmp_path))

        cleanup_root: Path | None = None
        try:
            scan_root, cleanup_root = extract_skills_zip(
                tmp_path,
                tmp_subdir="skill_scans",
                prefix=f"scan_{unique}",
            )
            skill_files = skills.discover_skill_md_files(scan_root)
            skill_entries = [
                {
                    "path": str(skill_md.parent),
                    "relative_path": str(skill_md.parent.relative_to(scan_root)),
                }
                for skill_md in skill_files
            ]
            warnings = []
            if not skill_entries:
                warnings.append("No SKILL.md files were found in the uploaded archive.")

            return {
                "success": True,
                "target_type": "uploaded_archive",
                "target_label": base,
                "paths": [str(scan_root)],
                "scan_path": str(scan_root),
                "display_path": files.normalize_a0_path(str(scan_root)),
                "cleanup_paths": [str(cleanup_root)],
                "skill_count": len(skill_entries),
                "skills": skill_entries,
                "warnings": warnings,
            }
        except Exception as exc:
            if cleanup_root:
                shutil.rmtree(cleanup_root, ignore_errors=True)
            return {"success": False, "error": f"Failed to prepare skill scan: {exc}"}
        finally:
            try:
                tmp_path.unlink(missing_ok=True)  # type: ignore[arg-type]
            except Exception:
                pass
