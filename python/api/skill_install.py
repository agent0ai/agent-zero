from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import re

from python.helpers.api import ApiHandler, Input, Output, Request, Response
from python.helpers import files, projects


class SkillInstall(ApiHandler):
    """
    Install skills from a GitHub repository (skills.sh format).
    Clones the repo, finds SKILL.md files, copies them into the
    appropriate skills directory (project-scoped or global).
    """

    async def process(self, input: Input, request: Request) -> Output:
        source = (input.get("source") or "").strip()
        if not source:
            return {"ok": False, "error": "source is required"}

        ctxid = (input.get("ctxid") or "").strip()

        try:
            owner, repo, skill_name = self._parse_source(source)
        except ValueError as e:
            return {"ok": False, "error": str(e)}

        target_dir, target_label = self._resolve_target(ctxid, owner, repo)

        clone_url = f"https://github.com/{owner}/{repo}.git"
        tmp_dir = None

        try:
            tmp_dir = tempfile.mkdtemp(prefix="skill_install_")
            clone_dest = os.path.join(tmp_dir, repo)

            result = subprocess.run(
                ["git", "clone", "--depth=1", clone_url, clone_dest],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode != 0:
                stderr = result.stderr.strip()
                return {"ok": False, "error": f"git clone failed: {stderr}"}

            skill_dirs = self._find_skills(clone_dest)
            if not skill_dirs:
                return {
                    "ok": False,
                    "error": f"No SKILL.md files found in {owner}/{repo}",
                }

            if skill_name:
                skill_dirs = [
                    d for d in skill_dirs
                    if d["name"].lower() == skill_name.lower()
                ]
                if not skill_dirs:
                    return {
                        "ok": False,
                        "error": f"Skill '{skill_name}' not found in {owner}/{repo}",
                    }

            installed = []
            skipped = []

            for skill in skill_dirs:
                dest = os.path.join(target_dir, skill["name"])
                if os.path.exists(dest):
                    skipped.append(skill["name"])
                    continue
                shutil.copytree(skill["path"], dest)
                self._normalize_skill_md(dest, skill["original_filename"])
                installed.append(skill["name"])

            return {
                "ok": True,
                "installed": installed,
                "skipped": skipped,
                "target": target_label,
                "source": f"{owner}/{repo}",
            }

        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "git clone timed out (60s)"}
        except Exception as e:
            return {"ok": False, "error": str(e)}
        finally:
            if tmp_dir and os.path.exists(tmp_dir):
                shutil.rmtree(tmp_dir, ignore_errors=True)

    def _parse_source(self, source: str) -> tuple[str, str, str | None]:
        source = re.sub(r"^https?://(www\.)?skills\.sh/", "", source)
        source = source.strip("/")

        parts = source.split("/")
        if len(parts) < 2:
            raise ValueError(
                "Expected format: owner/repo or owner/repo/skill-name"
            )

        owner = parts[0]
        repo = parts[1]
        skill_name = "/".join(parts[2:]) if len(parts) > 2 else None

        if not re.match(r"^[a-zA-Z0-9._-]+$", owner):
            raise ValueError(f"Invalid owner: {owner}")
        if not re.match(r"^[a-zA-Z0-9._-]+$", repo):
            raise ValueError(f"Invalid repo: {repo}")

        return owner, repo, skill_name

    def _resolve_target(
        self, ctxid: str, owner: str, repo: str
    ) -> tuple[str, str]:
        namespace = f"{owner}-{repo}"
        project_name = None

        if ctxid:
            from agent import AgentContext

            ctx = AgentContext.get(ctxid)
            if ctx:
                project_name = projects.get_context_project_name(ctx)

        if project_name:
            base = projects.get_project_meta_folder(project_name, "skills")
            target_dir = os.path.join(base, namespace)
            target_label = f"project:{project_name}"
        else:
            target_dir = files.get_abs_path("usr", "skills", namespace)
            target_label = "global"

        os.makedirs(target_dir, exist_ok=True)
        return target_dir, target_label

    def _find_skills(self, clone_dir: str) -> list[dict]:
        skills_found = []
        for root, _dirs, filenames in os.walk(clone_dir):
            for f in filenames:
                if f.upper() == "SKILL.MD":
                    skill_path = root
                    skill_name = os.path.basename(root)
                    if skill_name == os.path.basename(clone_dir):
                        skill_name = "default"
                    skills_found.append({
                        "name": skill_name,
                        "path": skill_path,
                        "original_filename": f,
                    })
        return skills_found

    @staticmethod
    def _normalize_skill_md(dest_dir: str, original_filename: str) -> None:
        """Rename skill.md / Skill.md etc. to SKILL.md for discovery."""
        if original_filename == "SKILL.md":
            return
        src = os.path.join(dest_dir, original_filename)
        dst = os.path.join(dest_dir, "SKILL.md")
        if os.path.exists(src):
            os.rename(src, dst)
