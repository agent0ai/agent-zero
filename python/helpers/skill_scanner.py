"""Static-analysis security scanner for skills.

Scans Python source files for dangerous imports, function calls, and
capability mismatches.
"""

from __future__ import annotations

import ast
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from python.helpers.skill_registry import SkillManifest

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DANGEROUS_IMPORTS: set[str] = {"os", "subprocess", "shutil", "ctypes", "socket"}

DANGEROUS_CALLS: set[str] = {"eval", "exec", "compile", "__import__"}

# Maps capability keywords to the imports they are expected to use.
CAPABILITY_IMPORT_MAP: dict[str, set[str]] = {
    "filesystem": {"os", "shutil", "pathlib"},
    "network": {"socket", "http", "urllib", "requests", "httpx", "aiohttp"},
    "process": {"subprocess", "os"},
}


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Finding:
    severity: Severity
    category: str
    message: str
    file: str = ""
    line: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "severity": self.severity.value,
            "category": self.category,
            "message": self.message,
            "file": self.file,
            "line": self.line,
        }


@dataclass
class ScanResult:
    skill_name: str
    passed: bool = True
    findings: list[Finding] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_name": self.skill_name,
            "passed": self.passed,
            "findings": [f.to_dict() for f in self.findings],
        }


# ---------------------------------------------------------------------------
# AST visitor
# ---------------------------------------------------------------------------


class _SecurityVisitor(ast.NodeVisitor):
    """Walk the AST of a single Python file and collect findings."""

    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.findings: list[Finding] = []
        self.actual_imports: set[str] = set()

    # -- imports --------------------------------------------------------------

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            top = alias.name.split(".")[0]
            self.actual_imports.add(top)
            if top in DANGEROUS_IMPORTS:
                self.findings.append(
                    Finding(
                        severity=Severity.HIGH,
                        category="dangerous_import",
                        message=f"Import of dangerous module '{alias.name}'",
                        file=self.filename,
                        line=node.lineno,
                    )
                )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            top = node.module.split(".")[0]
            self.actual_imports.add(top)
            if top in DANGEROUS_IMPORTS:
                self.findings.append(
                    Finding(
                        severity=Severity.HIGH,
                        category="dangerous_import",
                        message=f"Import from dangerous module '{node.module}'",
                        file=self.filename,
                        line=node.lineno,
                    )
                )
        self.generic_visit(node)

    # -- calls ----------------------------------------------------------------

    def visit_Call(self, node: ast.Call) -> None:
        func_name: str | None = None
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr

        if func_name and func_name in DANGEROUS_CALLS:
            self.findings.append(
                Finding(
                    severity=Severity.CRITICAL,
                    category="dangerous_call",
                    message=f"Call to dangerous function '{func_name}()'",
                    file=self.filename,
                    line=node.lineno,
                )
            )
        self.generic_visit(node)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def scan_skill(manifest: SkillManifest) -> ScanResult:
    """Run a static-analysis security scan on the skill pointed to by
    *manifest* and return a :class:`ScanResult`."""
    result = ScanResult(skill_name=manifest.name)
    skill_dir = Path(manifest.path)

    if not skill_dir.is_dir():
        result.findings.append(
            Finding(
                severity=Severity.MEDIUM,
                category="missing_path",
                message=f"Skill directory does not exist: {skill_dir}",
            )
        )
        result.passed = False
        return result

    all_imports: set[str] = set()

    # Scan all Python files in the skill directory
    for root, _dirs, files in os.walk(skill_dir):
        for fname in sorted(files):
            if not fname.endswith(".py"):
                continue
            fpath = os.path.join(root, fname)
            rel = os.path.relpath(fpath, skill_dir)
            try:
                with open(fpath, encoding="utf-8") as fh:
                    source = fh.read()
                tree = ast.parse(source, filename=rel)
            except SyntaxError as exc:
                result.findings.append(
                    Finding(
                        severity=Severity.MEDIUM,
                        category="syntax_error",
                        message=f"Syntax error in {rel}: {exc}",
                        file=rel,
                        line=exc.lineno or 0,
                    )
                )
                continue
            except Exception as exc:
                result.findings.append(
                    Finding(
                        severity=Severity.LOW,
                        category="read_error",
                        message=f"Could not read {rel}: {exc}",
                        file=rel,
                    )
                )
                continue

            visitor = _SecurityVisitor(rel)
            visitor.visit(tree)
            result.findings.extend(visitor.findings)
            all_imports.update(visitor.actual_imports)

    # -- capability mismatch check -------------------------------------------
    declared_caps = {c.lower() for c in manifest.capabilities}
    for cap, expected_imports in CAPABILITY_IMPORT_MAP.items():
        used = all_imports & expected_imports
        if used and cap not in declared_caps:
            result.findings.append(
                Finding(
                    severity=Severity.MEDIUM,
                    category="undeclared_capability",
                    message=(f"Skill uses {used} but does not declare '{cap}' capability"),
                )
            )

    # Determine pass/fail
    if any(f.severity in (Severity.HIGH, Severity.CRITICAL) for f in result.findings):
        result.passed = False

    return result
