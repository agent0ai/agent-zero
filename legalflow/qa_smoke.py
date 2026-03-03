from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import subprocess
import sys


DEFAULT_TESTS: tuple[str, ...] = (
    "tests/test_projects_legalflow_preset.py",
    "tests/test_research_citations_br.py",
    "tests/test_review_gate_export_e2e.py",
    "tests/test_public_corpus_parsers.py",
    "tests/test_public_corpus_ingest_idempotency.py",
)


def _repo_root() -> Path:
    # `legalflow/qa_smoke.py` -> repo root
    return Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    if importlib.util.find_spec("pytest") is None:
        print(
            "pytest is not installed. Install dev dependencies first, e.g.:\n"
            "  pip install -r requirements.txt -r requirements.dev.txt",
            file=sys.stderr,
        )
        return 2

    parser = argparse.ArgumentParser(
        prog="python -m legalflow.qa_smoke",
        description="Run a stable subset of LegalFlow regression checks (offline/fixture-driven).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Run pytest without -q.",
    )
    parser.add_argument(
        "pytest_args",
        nargs=argparse.REMAINDER,
        help="Extra pytest args after '--' (e.g. -- -k gatekeeper).",
    )
    args = parser.parse_args(argv)

    root = _repo_root()

    cmd: list[str] = [sys.executable, "-m", "pytest"]
    if not args.verbose:
        cmd.append("-q")
    cmd.extend(DEFAULT_TESTS)

    extra = list(args.pytest_args or [])
    if extra[:1] == ["--"]:
        extra = extra[1:]
    cmd.extend(extra)

    proc = subprocess.run(cmd, cwd=str(root))
    return int(proc.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
