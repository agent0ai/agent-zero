"""Advisory Agent Zero version requirements from a Hub plugin's manifest."""

import re
import urllib.request
from urllib.parse import urlsplit

from packaging.specifiers import SpecifierSet
from packaging.version import Version

from helpers import yaml


def matches_version(requirement: str | list[str] | None, current_version: str) -> bool:
    """Match alternatives (OR), with comma-separated comparisons inside each (AND)."""
    if requirement is None or requirement == "" or requirement == []:
        return True
    alternatives = [requirement] if isinstance(requirement, str) else requirement
    if not isinstance(alternatives, list) or not all(isinstance(item, str) and item.strip() for item in alternatives):
        raise ValueError("a0_version must be a quoted version requirement or a list of them")

    specs = []
    for alternative in alternatives:
        if alternative.strip() == "*":
            specs.append(None)
            continue
        # A spaced hyphen denotes an inclusive range, not a prerelease suffix.
        interval = re.fullmatch(r"\s*(\S+)\s+-\s+(\S+)\s*", alternative)
        if interval:
            alternative = f">={interval[1]},<={interval[2]}"
        clauses = []
        for clause in alternative.split(","):
            clause = clause.strip()
            if not clause:
                raise ValueError("Empty comparison in a0_version")
            clauses.append(clause if clause[0] in "<>=!~" else f"=={clause}")
        specs.append(SpecifierSet(",".join(clauses)))

    if None in specs:
        return True
    version = Version(current_version)
    return any(spec.contains(version, prereleases=True) for spec in specs)


def get_plugin_compatibility(git_url: str, current_version: str) -> dict:
    """Read default-branch plugin.yaml without cloning or executing plugin code."""
    result = {"a0_version": None, "current_version": current_version, "compatible": None, "error": ""}
    try:
        url = urlsplit(git_url)
        path = re.fullmatch(r"/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)/?", url.path)
        if url.scheme != "https" or url.hostname != "github.com" or not path:
            raise ValueError("Compatibility checks require a GitHub repository URL")
        owner, repo = path.groups()
        repo = repo.removesuffix(".git")
        if owner in (".", "..") or repo in ("", ".", ".."):
            raise ValueError("Invalid GitHub repository URL")
        request = urllib.request.Request(
            f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/plugin.yaml",
            headers={"User-Agent": "AgentZero"},
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            content = response.read(65537)
        if len(content) > 65536:
            raise ValueError("Plugin manifest exceeds 64 KiB")
        manifest = yaml.loads(content.decode("utf-8"))
        if not isinstance(manifest, dict):
            raise ValueError("Plugin manifest must be a YAML mapping")
        requirement = manifest.get("a0_version")
        if requirement is not None and not isinstance(requirement, str) and not (
            isinstance(requirement, list) and all(isinstance(item, str) for item in requirement)
        ):
            raise ValueError("a0_version must be a quoted version requirement or a list of them")
        result["a0_version"] = requirement
        result["compatible"] = matches_version(result["a0_version"], current_version)
    except Exception as error:
        result["error"] = str(error)
    return result
