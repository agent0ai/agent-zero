from pathlib import Path

from python.helpers.api import ApiHandler, Request, Response
from python.helpers.skill_md_parser import parse_skill_md_file
from python.helpers.skill_registry import _manifest_from_frontmatter, get_registry
from python.helpers.skill_scanner import scan_skill


class SkillsScan(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        registry = get_registry()

        # Scan a specific skill by name (already registered)
        name = input.get("name", "")
        if name:
            manifest = registry.get(name)
            if manifest is None:
                return Response(
                    response=f"Skill '{name}' not found",
                    status=404,
                    mimetype="text/plain",
                )
            result = scan_skill(manifest)
            return result.to_dict()

        # Or scan by path (not yet registered)
        path_str = input.get("path", "")
        if path_str:
            skill_dir = Path(path_str)
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.is_file():
                return Response(
                    response=f"No SKILL.md at {skill_md}",
                    status=404,
                    mimetype="text/plain",
                )
            fm, _body = parse_skill_md_file(str(skill_md))
            manifest = _manifest_from_frontmatter(fm, skill_dir)
            if manifest is None:
                return Response(
                    response="SKILL.md missing required fields",
                    status=400,
                    mimetype="text/plain",
                )
            result = scan_skill(manifest)
            return result.to_dict()

        return Response(
            response="Provide 'name' or 'path' parameter",
            status=400,
            mimetype="text/plain",
        )
