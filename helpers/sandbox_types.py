"""Types shared with workers across bundled plugin reloads."""
from dataclasses import dataclass
from pathlib import Path


class SandboxError(RuntimeError):
    """A safe, user-facing sandbox management error."""


@dataclass(frozen=True, slots=True)
class SandboxMount:
    source: Path
    destination: str
    read_only: bool = True
