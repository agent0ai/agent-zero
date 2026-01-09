from python.helpers.extension import Extension
from agent import LoopData
from python.helpers import projects


class IncludeProjectExtras(Extension):
    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):

        # active project
        project_name = projects.get_context_project_name(self.agent.context)
        if not project_name:
            return

        # project config
        project = projects.load_basic_project_data(project_name)

        # load file structure if enabled
        if project["file_structure"]["enabled"]:
            file_structure = projects.get_file_structure(project_name)
            gitignore = cleanup_gitignore(project["file_structure"]["gitignore"])

            # read prompt
            file_structure_prompt = self.agent.read_prompt(
                "agent.extras.project.file_structure.md",
                max_depth=project["file_structure"]["max_depth"],
                gitignore=gitignore,
                project_name=project_name,
                file_structure=file_structure,
            )
            # add file structure to the prompt
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
