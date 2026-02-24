"""Archive Today.md to health_log_archives/Health Log YYYYMMDD.md"""
import os
import shutil
import time
import importlib.util
from python.helpers.tool import Tool, Response

_tools_dir = os.path.dirname(os.path.abspath(__file__))
_utils_path = os.path.join(_tools_dir, "_health_log_utils.py")
_spec = importlib.util.spec_from_file_location("_health_log_utils", _utils_path)
_utils = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_utils)
get_workdir_path = _utils.get_workdir_path
path_today_md = _utils.path_today_md
path_archives_dir = _utils.path_archives_dir


class HealthLogArchive(Tool):
    async def execute(
        self,
        workdir: str = "",
        date_yyyymmdd: str = "",
        backup: bool = True,
        **kwargs,
    ):
        workdir_path = get_workdir_path(workdir)
        today_path = path_today_md(workdir_path)
        archives_dir = path_archives_dir(workdir_path)

        if not date_yyyymmdd or len(date_yyyymmdd) != 8:
            return Response(
                message="Error: date_yyyymmdd required (format YYYYMMDD, e.g. 20260224)",
                break_loop=False,
            )

        if not os.path.exists(today_path):
            return Response(
                message=f"Error: Today.md not found at {today_path}",
                break_loop=False,
            )

        os.makedirs(archives_dir, exist_ok=True)
        archive_filename = f"Health Log {date_yyyymmdd}.md"
        archive_path = os.path.join(archives_dir, archive_filename)

        if backup:
            backup_path = f"{today_path}.bak.{int(time.time())}"
            try:
                shutil.copy2(today_path, backup_path)
            except Exception as e:
                pass  # non-fatal

        try:
            shutil.copy2(today_path, archive_path)
        except Exception as e:
            return Response(
                message=f"Error archiving: {e}",
                break_loop=False,
            )

        size = os.path.getsize(archive_path)
        return Response(
            message=f"Archived Today.md → {archive_filename} ({size} bytes)",
            break_loop=False,
        )
