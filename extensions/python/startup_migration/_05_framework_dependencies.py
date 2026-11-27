import importlib.metadata
from pathlib import Path
import shutil
import subprocess
import sys

from packaging.requirements import Requirement

from helpers import files, process, runtime
from helpers.extension import Extension
from helpers.print_style import PrintStyle


_REQUIREMENTS_FILE = Path(files.get_abs_path("requirements.txt"))
# Only update retired distributions on images that already have them installed.
_LEGACY = ("langchain>=1.5.2,<2", "langchain-community>=0.4.2,<1", "langchain-text-splitters>=1.1.3,<2")


class FrameworkDependencies(Extension):
    def execute(self, **kwargs):
        if not runtime.is_dockerized():
            return
        requirements = _requirements()
        outdated = _outdated(requirements)
        if not outdated:
            return
        uv = shutil.which("uv")
        if not uv:
            raise RuntimeError("Framework dependency update requires 'uv'.")
        PrintStyle.info("Updating framework dependencies:", ", ".join(outdated))
        subprocess.check_call(
            [uv, "pip", "install", "--no-cache", "--python", sys.executable,
             "-c", str(_REQUIREMENTS_FILE.parent / "docker/litellm-constraints.txt"), *map(str, requirements)],
            timeout=600,
        )
        outdated = _outdated(requirements)
        if outdated:
            raise RuntimeError(f"Framework dependencies still unavailable after installation: {outdated}")
        # Models were imported before startup migrations; load the upgraded SDKs.
        process.restart_process()


def _requirements() -> list[Requirement]:
    requirements = []
    for line in _REQUIREMENTS_FILE.read_text(encoding="utf-8").splitlines():
        line = line.partition("#")[0].strip()
        if line:
            requirement = Requirement(line)
            if not requirement.marker or requirement.marker.evaluate():
                requirements.append(requirement)
    for pin in _LEGACY:
        requirement = Requirement(pin)
        try:
            importlib.metadata.version(requirement.name)
        except importlib.metadata.PackageNotFoundError:
            continue
        requirements.append(requirement)
    return requirements


def _outdated(requirements: list[Requirement]) -> list[str]:
    outdated = []
    for requirement in requirements:
        try:
            installed = importlib.metadata.version(requirement.name)
        except importlib.metadata.PackageNotFoundError:
            installed = None
        if installed is None or installed not in requirement.specifier:
            outdated.append(str(requirement))
    return outdated
