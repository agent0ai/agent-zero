from python.helpers import file_tree, files
from python.helpers.api import ApiHandler, Request, Response


class SettingsWorkdirFileStructure(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        workdir_path = input.get("workdir_path", "")
        workdir_path = files.get_abs_path_development(workdir_path)
        if not workdir_path:
            raise Exception("workdir_path is required")

        tree = str(
            file_tree.file_tree(
                workdir_path,
                max_depth=int(input.get("workdir_max_depth", 0) or 0),
                max_files=int(input.get("workdir_max_files", 0) or 0),
                max_folders=int(input.get("workdir_max_folders", 0) or 0),
                max_lines=int(input.get("workdir_max_lines", 0) or 0),
                ignore=input.get("workdir_gitignore", "") or "",
                output_mode=file_tree.OUTPUT_MODE_STRING,
            )
        )

        if "\n" not in tree:
            tree += "\n # Empty"

        return {"data": tree}

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["POST"]
