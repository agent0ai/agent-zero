from helpers.extension import Extension
from helpers import plugins, files, runtime
from helpers import projects
from helpers.settings import get_settings
from agent import Agent, LoopData

from plugins._promptinclude.helpers.scanner import scan_promptinclude_files, ScanResult


class PromptInclude(Extension):

    async def execute(
        self,
        system_prompt: list[str] = [],
        loop_data: LoopData = LoopData(),
        **kwargs,
    ):
        if not self.agent:
            return

        config = plugins.get_plugin_config("_promptinclude", agent=self.agent) or {}
        scan_path = _resolve_workdir(self.agent)

        if not scan_path:
            return

        name_pattern = config.get("name_pattern", "*.promptinclude.md")
        result = await runtime.call_development_function(
            scan_promptinclude_files,
            scan_path,
            name_pattern=name_pattern,
            max_depth=config.get("max_depth", 10),
            max_file_tokens=config.get("max_file_tokens", 2000),
            max_file_count=config.get("max_file_count", 50),
            max_total_tokens=config.get("max_total_tokens", 8000),
            gitignore=config.get("gitignore", ""),
        )

        if not result["files"] and result["skipped_count"] == 0:
            prompt = self.agent.read_prompt(
                "agent.system.promptinclude.md",
                name_pattern=name_pattern,
                includes="",
            )
            system_prompt.append(prompt)
            return

        includes = _format_includes(self.agent, result)
        prompt = self.agent.read_prompt(
            "agent.system.promptinclude.md",
            name_pattern=name_pattern,
            includes=includes,
        )
        system_prompt.append(prompt)


def _resolve_workdir(agent: Agent) -> str:
    project_name = projects.get_context_project_name(agent.context)
    if project_name:
        folder = projects.get_project_folder(project_name)
        if runtime.is_development():
            folder = files.normalize_a0_path(folder)
        return folder
    return get_settings()["workdir_path"]


def _format_includes(agent: Agent, result: ScanResult) -> str:
    lines: list[str] = []

    for entry in result["files"]:
        if entry["status"] == "skipped":
            lines.append(f"{entry['path']} !!! skipped to fit")
            continue

        suffix = " !!! cropped to fit" if entry["status"] == "cropped" else ""
        block = agent.read_prompt(
            "fw.promptinclude.includes.md",
            path=entry["path"],
            suffix=suffix,
            content=entry["content"],
        )
        lines.append(block)

    if result["skipped_count"] > 0:
        lines.append(f"!!! {result['skipped_count']} more files skipped to fit")

    return "\n".join(lines)
