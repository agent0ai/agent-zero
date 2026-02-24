"""Shared utilities for health_log_* tools."""
import os
from python.helpers import settings, files


def get_workdir_path(workdir: str | None = None) -> str:
    """Resolve workdir path. Uses workdir arg if provided, else settings.workdir_path."""
    if workdir and str(workdir).strip():
        path = str(workdir).strip()
        if not os.path.isabs(path):
            path = files.get_abs_path(path)
        return path
    set = settings.get_settings()
    path = set.get("workdir_path") or ""
    if not path:
        path = files.get_abs_path_dockerized("usr/workdir")
    return str(path)


def path_today_md(workdir: str) -> str:
    return os.path.join(workdir, "Today.md")


def path_archives_dir(workdir: str) -> str:
    return os.path.join(workdir, "health_log_archives")


def path_supplements_md(workdir: str) -> str:
    return os.path.join(workdir, "Supplements.md")


def path_macros_md(workdir: str) -> str:
    return os.path.join(workdir, "MacrosAndRecipes.md")


def path_exercise_progression_md(workdir: str) -> str:
    return os.path.join(workdir, "Exercise Progression.md")


def path_todays_routine_md(workdir: str) -> str:
    return os.path.join(workdir, "Today's Routine.md")
