from pathlib import Path

from python.helpers.api import ApiHandler, Request, Response
from python.helpers.skill_md_parser import parse_skill_md_file
from python.helpers.skill_registry import _manifest_from_frontmatter, get_registry
from python.helpers.skill_scanner import scan_skill


class SkillsInstall(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        path_str = input.get("path", "")
        if not path_str:
            return Response(response="Missing 'path' parameter", status=400, mimetype="text/plain")

        skill_dir = Path(path_str)
        skill_md = skill_dir / "SKILL.md"

        if not skill_md.is_file():
            return Response(
                response=f"No SKILL.md found at {skill_md}",
                status=404,
                mimetype="text/plain",
            )

        try:
            fm, _body = parse_skill_md_file(str(skill_md))
        except Exception as exc:
            return Response(response=f"Parse error: {exc}", status=400, mimetype="text/plain")

        manifest = _manifest_from_frontmatter(fm, skill_dir)
        if manifest is None:
            return Response(
                response="SKILL.md missing required fields (name, version, author)",
                status=400,
                mimetype="text/plain",
            )

        # Security scan before install
        scan_result = scan_skill(manifest)

        registry = get_registry()

        # Check dependencies
        missing_deps = registry.check_dependencies(manifest)

        registry.install(manifest)

        return {
            "installed": manifest.to_dict(),
            "scan": scan_result.to_dict(),
            "missing_dependencies": missing_deps,
        }
