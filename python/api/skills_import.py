from __future__ import annotations

import os
import time
import uuid
from pathlib import Path

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from python.helpers import files
from python.helpers.api import ApiHandler, Request, Response
from python.helpers.skills_import import import_skills


class SkillsImport(ApiHandler):
    """
    Import an external skills pack (.zip) into usr/skills/<namespace>/...
    Performs the actual import (not dry-run).
    """

    async def process(self, input: dict, request: Request) -> dict | Response:
        if "skills_file" not in request.files:
            return {"success": False, "error": "No skills file provided"}

        skills_file: FileStorage = request.files["skills_file"]
        if not skills_file.filename:
            return {"success": False, "error": "No file selected"}

        ctxid = request.form.get("ctxid", "")
        if not ctxid:
            return {"success": False, "error": "No context id provided"}
        _context = self.use_context(ctxid)

        conflict = (request.form.get("conflict", "skip") or "skip").strip().lower()
        if conflict not in ("skip", "overwrite", "rename"):
            conflict = "skip"

        namespace = (request.form.get("namespace", "") or "").strip() or None
        project_name = (request.form.get("project_name", "") or "").strip() or None
        agent_profile = (request.form.get("agent_profile", "") or "").strip() or None

        # Save upload to a temp file so we can pass a filesystem path to the importer
        tmp_dir = Path(files.get_abs_path("tmp", "uploads"))
        tmp_dir.mkdir(parents=True, exist_ok=True)
        base = secure_filename(skills_file.filename)  # type: ignore[arg-type]
        if not base.lower().endswith(".zip"):
            base = f"{base}.zip"
        unique = uuid.uuid4().hex[:8]
        stamp = time.strftime("%Y%m%d_%H%M%S")
        tmp_path = tmp_dir / f"skills_import_{stamp}_{unique}_{base}"
        skills_file.save(str(tmp_path))

        try:
            result = import_skills(
                str(tmp_path),
                namespace=namespace,
                conflict=conflict,  # type: ignore[arg-type]
                dry_run=False,  # Actual import, not preview
                project_name=project_name,
                agent_profile=agent_profile,
            )

            imported = [files.deabsolute_path(str(p)) for p in result.imported]
            skipped = [files.deabsolute_path(str(p)) for p in result.skipped]
            dest_root = files.deabsolute_path(
                str(result.destination_root / result.namespace)
            )

            return {
                "success": True,
                "namespace": result.namespace,
                "destination": dest_root,
                "imported": imported,
                "skipped": skipped,
                "imported_count": len(imported),
                "skipped_count": len(skipped),
                "conflict_policy": conflict,
            }
        finally:
            try:
                tmp_path.unlink(missing_ok=True)  # type: ignore[arg-type]
            except Exception:
                pass
