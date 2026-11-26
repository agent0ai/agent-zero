from helpers.extension import Extension
from agent import LoopData
from helpers import projects
from helpers import settings
from helpers import runtime
from helpers import file_tree
from helpers import files
from helpers import team_access, team_projects, team_runs

class IncludeWorkdirExtras(Extension):
    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        if not self.agent:
            return

        project_name = projects.get_context_project_name(self.agent.context)
        if team_access.is_team_chat(self.agent.context):
            _, scope = team_runs.executing_scope(self.agent.context)
            with team_projects.project_lock(project_name, scope):
                project = projects.load_basic_project_data(project_name)
                if project["file_structure"]["enabled"]:
                    entries = team_projects.file_action(project_name, "list", {"path": ""})["entries"]
                    paths = [item["name"] + ("/" if item["directory"] else "") for item in entries[:50]]
                    loop_data.extras_temporary["project_file_structure"] = "Project workspace entries:\n" + "\n".join(paths)
            return

        enabled = False
        max_depth = 0
        max_files = 0
        max_folders = 0
        max_lines = 0
        gitignore_raw = ""
        folder = ""
        file_structure = ""

        if project_name:
            project = projects.load_basic_project_data(project_name)
            enabled = project["file_structure"]["enabled"]
            
            if not enabled:
                return
            
            max_depth = project["file_structure"]["max_depth"]
            gitignore_raw = project["file_structure"]["gitignore"]

            folder = projects.get_project_folder(project_name)
            if runtime.is_development():
                folder = files.normalize_a0_path(folder)

            file_structure = projects.get_file_structure(
                project_name,
                output_mode=file_tree.OUTPUT_MODE_INDENT,
            )
        else:
            set = settings.get_settings_for_prompt()
            enabled = bool(set["workdir_show"])

            if not enabled:
                return
            
            max_depth = set["workdir_max_depth"]
            max_files = set["workdir_max_files"]
            max_folders = set["workdir_max_folders"]
            max_lines = set["workdir_max_lines"]
            gitignore_raw = set["workdir_gitignore"]

            folder = set["workdir_path"]
            scan_path = files.get_abs_path_development(folder)

            files.create_dir(scan_path)

            file_structure = str(
                file_tree.file_tree(
                    scan_path,
                    max_depth=max_depth,
                    max_files=max_files,
                    max_folders=max_folders,
                    max_lines=max_lines,
                    ignore=gitignore_raw,
                    output_mode=file_tree.OUTPUT_MODE_INDENT,
                )
            )

        gitignore = cleanup_gitignore(gitignore_raw)

        file_structure_prompt = self.agent.read_prompt(
            "agent.extras.workdir_structure.md",
            max_depth=max_depth,
            gitignore=gitignore,
            folder=folder,
            file_structure=file_structure,
        )

        loop_data.extras_temporary["project_file_structure"] = file_structure_prompt


def cleanup_gitignore(gitignore_raw: str) -> str:
    """Process gitignore: split lines, strip, remove comments, remove empty lines."""
    gitignore_lines = []
    for line in gitignore_raw.split('\n'):
        # Strip whitespace
        line = line.strip()
        # Remove inline comments (everything after #)
        if '#' in line:
            line = line.split('#')[0].strip()
        # Keep only non-empty lines
        if line:
            gitignore_lines.append(line)
    
    return '\n'.join(gitignore_lines) if gitignore_lines else "nothing ignored"
