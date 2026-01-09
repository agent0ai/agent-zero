from __future__ import annotations

import argparse
import os
from collections.abc import Iterable
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
import sys
import time
from typing import Any, Callable, Dict, List, Optional

try:
    import pytest  # type: ignore
except ImportError:  # pragma: no cover
    pytest = None

if pytest is not None:
    pytestmark = pytest.mark.skip(reason="Visualization utility; excluded from automated test runs.")


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from python.helpers.file_tree import (
    OUTPUT_MODE_FLAT,
    OUTPUT_MODE_NESTED,
    OUTPUT_MODE_STRING,
    SORT_ASC,
    SORT_BY_CREATED,
    SORT_BY_MODIFIED,
    SORT_BY_NAME,
    SORT_DESC,
    file_tree,
)
from python.helpers.files import create_dir, delete_dir, get_abs_path, write_file


BASE_TEMP_ROOT = "tmp/tests/file_tree/visualize"


@dataclass(slots=True)
class Config:
    label: str
    params: Dict[str, Any]


SetupHook = Optional[Callable[[str], None]]


@dataclass(slots=True)
class Scenario:
    name: str
    description: str
    structure: Dict[str, Any]
    configs: List[Config] = field(default_factory=list)
    ignore_content: Optional[str] = None
    setup: SetupHook = None


def materialize_structure(base_rel: str, structure: Dict[str, Any]) -> None:
    for entry, value in structure.items():
        rel = os.path.join(base_rel, entry)
        if isinstance(value, dict):
            create_dir(rel)
            materialize_structure(rel, value)
        else:
            write_file(rel, "" if value is None else str(value))


def ensure_ignore_file(base_rel: str, content: str) -> None:
    write_file(os.path.join(base_rel, ".treeignore"), content.strip() + "\n")


def print_header(title: str, char: str = "=") -> None:
    print(char * 80)
    print(title)
    print(char * 80)


def print_flat(items: List[Dict[str, Any]]) -> None:
    print("level  type     name                   text")
    print("-" * 80)
    for item in items:
        level = item["level"]
        item_type = item["type"]
        name = item["name"]
        text = item["text"]
        print(f"{level:<5}  {item_type:<7}  {name:<20}  {text}")


def print_nested(items: List[Dict[str, Any]], root_label: str) -> None:
    print(root_label)

    def recurse(nodes: List[Dict[str, Any]], prefix: str) -> None:
        total = len(nodes)
        for index, node in enumerate(nodes):
            is_last = index == total - 1
            connector = "└── " if is_last else "├── "
            label = node["name"] + ("/" if node["type"] == "folder" else "")
            print(f"{prefix}{connector}{label}  [{node['type']}]")
            children = node.get("items") or []
            if children:
                child_prefix = prefix + ("    " if is_last else "│   ")
                recurse(children, child_prefix)

    recurse(items, "")


@contextmanager
def scenario_directory(name: str) -> Iterable[str]:
    rel_path = os.path.join(BASE_TEMP_ROOT, name)
    delete_dir(rel_path)
    create_dir(rel_path)
    try:
        yield rel_path
    finally:
        delete_dir(rel_path)


def _set_entry_times(relative_path: str, timestamp: float) -> None:
    abs_path = get_abs_path(relative_path)
    os.utime(abs_path, (timestamp, timestamp))
    time.sleep(0.01)


def _apply_timestamps(base_rel: str, paths: List[str], base_ts: Optional[float] = None) -> None:
    if base_ts is None:
        base_ts = time.time()
    for offset, rel in enumerate(paths, start=1):
        _set_entry_times(os.path.join(base_rel, rel), base_ts + offset)


def list_scenarios(scenarios: List[Scenario]) -> None:
    print("Available scenarios:")
    for scenario in scenarios:
        print(f"  - {scenario.name}: {scenario.description}")


def run_scenarios(selected: List[Scenario]) -> None:
    create_dir(BASE_TEMP_ROOT)
    for scenario in selected:
        print_header(f"Scenario: {scenario.name} — {scenario.description}")
        with scenario_directory(scenario.name) as base_rel:
            materialize_structure(base_rel, scenario.structure)

            if scenario.ignore_content:
                ensure_ignore_file(base_rel, scenario.ignore_content)

            if scenario.setup:
                scenario.setup(base_rel)

            for config in scenario.configs:
                print_header(f"Configuration: {config.label}", "-")
                params = {
                    "relative_path": base_rel,
                    "max_depth": 0,
                    "max_lines": 0,
                    "folders_first": True,
                    "max_folders": None,
                    "max_files": None,
                    "sort": (SORT_BY_MODIFIED, SORT_DESC),
                    **config.params,
                }
                output_mode = params.setdefault("output_mode", OUTPUT_MODE_STRING)
                print("Parameters:")
                print(f"  output_mode   : {output_mode}")
                print(f"  folders_first : {params['folders_first']}")
                sort_key, sort_dir = params["sort"]
                print(f"  sort          : key={sort_key}, direction={sort_dir}")
                print(f"  max_depth     : {params['max_depth']}")
                print(f"  max_lines     : {params['max_lines']}")
                print(f"  max_folders   : {params['max_folders']}")
                print(f"  max_files     : {params['max_files']}")
                print(f"  ignore        : {params.get('ignore')}")
                print()
                result = file_tree(**params)

                if output_mode == OUTPUT_MODE_STRING:
                    print(result)
                elif output_mode == OUTPUT_MODE_FLAT:
                    print_flat(result)  # type: ignore[arg-type]
                elif output_mode == OUTPUT_MODE_NESTED:
                    print_nested(result, f"{scenario.name}/")
                else:
                    print(f"(Unhandled output mode {output_mode!r})")

        print()


def build_scenarios() -> List[Scenario]:
    scenarios: List[Scenario] = []

    scenarios.append(
        Scenario(
            name="basic_breadth_first",
            description="Default breadth-first traversal with mixed folders/files",
            structure={
                "alpha": {"alpha_file.txt": "alpha", "nested": {"inner.txt": "inner"}},
                "beta": {"beta_file.txt": "beta"},
                "zeta": {},
                "a.txt": "A",
                "b.txt": "B",
            },
            configs=[
                Config(
                    "string • folders-first (name asc)",
                    {
                        "output_mode": OUTPUT_MODE_STRING,
                        "folders_first": True,
                        "sort": (SORT_BY_NAME, SORT_ASC),
                    },
                ),
                Config(
                    "string • folders-first disabled",
                    {
                        "output_mode": OUTPUT_MODE_STRING,
                        "folders_first": False,
                        "sort": (SORT_BY_NAME, SORT_ASC),
                    },
                ),
                Config(
                    "flat • folders-first",
                    {
                        "output_mode": OUTPUT_MODE_FLAT,
                        "folders_first": True,
                        "sort": (SORT_BY_NAME, SORT_ASC),
                    },
                ),
                Config(
                    "nested • folders-first",
                    {
                        "output_mode": OUTPUT_MODE_NESTED,
                        "folders_first": True,
                        "sort": (SORT_BY_NAME, SORT_ASC),
                    },
                ),
            ],
        )
    )

    def setup_sorting(base_rel: str) -> None:
        entries = [
            "folder_alpha",
            "folder_beta",
            "file_first.txt",
            "file_second.txt",
            "file_third.txt",
        ]
        for index, entry in enumerate(entries, start=1):
            abs_path = get_abs_path(os.path.join(base_rel, entry))
            timestamp = 200_000_0000 + index
            os.utime(abs_path, (timestamp, timestamp))

    scenarios.append(
        Scenario(
            name="sorting_variants",
            description="Demonstrate sorting by name and timestamp with folders/files",
            structure={
                "folder_alpha": {},
                "folder_beta": {},
                "file_first.txt": "",
                "file_second.txt": "",
                "file_third.txt": "",
            },
            configs=[
                Config(
                    "string • sort by name asc",
                    {
                        "output_mode": OUTPUT_MODE_STRING,
                        "folders_first": True,
                        "sort": (SORT_BY_NAME, SORT_ASC),
                    },
                ),
                Config(
                    "string • sort by created desc",
                    {
                        "output_mode": OUTPUT_MODE_STRING,
                        "folders_first": True,
                        "sort": (SORT_BY_CREATED, SORT_DESC),
                    },
                ),
                Config(
                    "flat • sort by modified asc",
                    {
                        "output_mode": OUTPUT_MODE_FLAT,
                        "folders_first": True,
                        "sort": (SORT_BY_MODIFIED, SORT_ASC),
                    },
                ),
            ],
            setup=setup_sorting,
        )
    )

    scenarios.append(
        Scenario(
            name="ignore_and_limits",
            description="Ignore file semantics with max_folders/max_files summaries",
            structure={
                "src": {
                    "main.py": "print('hello')",
                    "utils.py": "pass",
                    "tmp.tmp": "",
                    "cache": {"cached.txt": "", "keep.txt": ""},
                    "modules": {"a.py": "", "b.py": "", "c.py": ""},
                    "pkg": {"alpha.py": "", "beta.py": "", "gamma.py": ""},
                },
                "logs": {"2024.log": "", "2025.log": ""},
                "notes.md": "",
                "guide.md": "",
                "todo.md": "",
                "build.tmp": "",
                "archive": {},
                "assets": {},
                "sandbox": {},
                "vendor": {},
            },
            ignore_content="\n".join(
                ["*.tmp", "cache/", "!src/cache/keep.txt", "logs/", "!logs/2025.log"]
            ),
            configs=[
                Config(
                    "string • folders-first with summaries",
                    {
                        "output_mode": OUTPUT_MODE_STRING,
                        "folders_first": False,
                        "sort": (SORT_BY_NAME, SORT_ASC),
                        "max_folders": 1,
                        "max_files": 2,
                        "max_lines": 12,
                        "ignore": "file:.treeignore",
                    },
                ),
                Config(
                    "nested • inspect truncated branches & comments",
                    {
                        "output_mode": OUTPUT_MODE_NESTED,
                        "folders_first": False,
                        "sort": (SORT_BY_NAME, SORT_ASC),
                        "max_folders": 1,
                        "max_files": 2,
                        "max_lines": 12,
                        "ignore": "file:.treeignore",
                    },
                ),
            ],
        )
    )

    scenarios.append(
        Scenario(
            name="limits_exact_match",
            description="Per-directory limits exactly met (no summary comments)",
            structure={
                "pkg": {
                    "a.py": "",
                    "b.py": "",
                    "dir1": {},
                    "dir2": {},
                }
            },
            configs=[
                Config(
                    "string • exact matches (no summaries)",
                    {
                        "output_mode": OUTPUT_MODE_STRING,
                        "folders_first": True,
                        "sort": (SORT_BY_NAME, SORT_ASC),
                        "max_folders": 2,
                        "max_files": 2,
                    },
                ),
                Config(
                    "flat • exact matches (no summaries)",
                    {
                        "output_mode": OUTPUT_MODE_FLAT,
                        "folders_first": True,
                        "sort": (SORT_BY_NAME, SORT_ASC),
                        "max_folders": 2,
                        "max_files": 2,
                    },
                ),
            ],
        )
    )

    scenarios.append(
        Scenario(
            name="single_overflow",
            description="Single overflow entries promoted instead of summary comment",
            structure={
                "pkg": {
                    "dir_a": {},
                    "dir_b": {},
                    "file_a.txt": "",
                }
            },
            configs=[
                Config(
                    "string • single folder overflow",
                    {
                        "output_mode": OUTPUT_MODE_STRING,
                        "folders_first": True,
                        "sort": (SORT_BY_NAME, SORT_ASC),
                        "max_folders": 1,
                    },
                ),
                Config(
                    "string • single file overflow",
                    {
                        "output_mode": OUTPUT_MODE_STRING,
                        "folders_first": False,
                        "sort": (SORT_BY_NAME, SORT_ASC),
                        "max_files": 1,
                    },
                ),
                Config(
                    "flat • folders-first",
                    {
                        "output_mode": OUTPUT_MODE_FLAT,
                        "folders_first": True,
                        "sort": (SORT_BY_NAME, SORT_ASC),
                        "max_folders": 1,
                    },
                ),
            ],
        )
    )

    scenarios.append(
        Scenario(
            name="global_max_lines",
            description="Global max_lines finishing current depth before truncation",
            structure={
                "layer1_a": {
                    "layer2_a": {
                        "layer3_a": {
                            "layer4_a": {"layer5_a.txt": ""},
                        }
                    }
                },
                "layer1_b": {
                    "layer2_b": {
                        "layer3_b": {
                            "layer4_b": {"layer5_b.txt": ""},
                        }
                    }
                },
                "root_file.txt": "",
            },
            configs=[
                Config(
                    "string • max_lines=6",
                    {
                        "output_mode": OUTPUT_MODE_STRING,
                        "max_lines": 6,
                        "sort": (SORT_BY_NAME, SORT_ASC),
                    },
                ),
                Config(
                    "nested • max_lines=6",
                    {
                        "output_mode": OUTPUT_MODE_NESTED,
                        "max_lines": 6,
                        "folders_first": True,
                        "sort": (SORT_BY_NAME, SORT_ASC),
                    },
                ),
            ],
        )
    )

    scenarios.append(
        Scenario(
            name="flat_files_first_limits",
            description="Flat output with files-first ordering and per-directory summaries",
            structure={
                "dir1": {},
                "dir2": {},
                "dir3": {},
                "dir4": {},
                "a.txt": "",
                "b.txt": "",
                "c.txt": "",
            },
            configs=[
                Config(
                    "flat • files-first with limits",
                    {
                        "output_mode": OUTPUT_MODE_FLAT,
                        "folders_first": False,
                        "sort": (SORT_BY_NAME, SORT_ASC),
                        "max_folders": 1,
                        "max_files": 1,
                    },
                )
            ],
        )
    )

    scenarios.append(
        Scenario(
            name="flat_sort_created_max_lines",
            description="Flat output sorted by created time with global max_lines",
            structure={
                "dirA": {"inner.txt": ""},
                "file1.txt": "",
                "file2.txt": "",
                "file3.txt": "",
            },
            setup=lambda base_rel: _apply_timestamps(
                base_rel,
                [
                    "dirA",
                    os.path.join("dirA", "inner.txt"),
                    "file1.txt",
                    "file2.txt",
                    "file3.txt",
                ],
                base_ts=2_000_001_000,
            ),
            configs=[
                Config(
                    "flat • sort by created desc, max_lines=4",
                    {
                        "output_mode": OUTPUT_MODE_FLAT,
                        "folders_first": True,
                        "sort": (SORT_BY_CREATED, SORT_DESC),
                        "max_lines": 4,
                    },
                )
            ],
        )
    )

    scenarios.append(
        Scenario(
            name="nested_files_first_limits",
            description="Nested output with files-first ordering and per-directory summaries",
            structure={
                "dir": {"a.py": "", "b.py": "", "c.py": ""},
                "folder_a": {"inner.txt": ""},
                "folder_b": {},
                "folder_c": {},
            },
            configs=[
                Config(
                    "nested • files-first with limits",
                    {
                        "output_mode": OUTPUT_MODE_NESTED,
                        "folders_first": False,
                        "sort": (SORT_BY_NAME, SORT_ASC),
                        "max_folders": 1,
                        "max_files": 1,
                    },
                )
            ],
        )
    )

    scenarios.append(
        Scenario(
            name="nested_max_depth_sort",
            description="Nested output with created-time ordering and depth pruning",
            structure={
                "root": {
                    "branch": {
                        "leaf_a.txt": "",
                        "leaf_b.txt": "",
                    }
                },
                "alpha.txt": "",
            },
            setup=lambda base_rel: _apply_timestamps(
                base_rel,
                [
                    "root",
                    os.path.join("root", "branch"),
                    os.path.join("root", "branch", "leaf_a.txt"),
                    os.path.join("root", "branch", "leaf_b.txt"),
                    "alpha.txt",
                ],
                base_ts=2_000_010_000,
            ),
            configs=[
                Config(
                    "nested • sort by created asc, max_depth=2",
                    {
                        "output_mode": OUTPUT_MODE_NESTED,
                        "folders_first": True,
                        "sort": (SORT_BY_CREATED, SORT_ASC),
                        "max_depth": 2,
                    },
                )
            ],
        )
    )

    scenarios.append(
        Scenario(
            name="string_additional_limits",
            description="String output exercising files-first+max_lines and zero-limit semantics",
            structure={
                "dir": {"inner_a.txt": "", "inner_b.txt": ""},
                "alpha.txt": "",
                "beta.txt": "",
                "gamma.txt": "",
            },
            setup=lambda base_rel: _apply_timestamps(
                base_rel,
                [
                    "dir",
                    os.path.join("dir", "inner_a.txt"),
                    os.path.join("dir", "inner_b.txt"),
                    "alpha.txt",
                    "beta.txt",
                    "gamma.txt",
                ],
                base_ts=2_000_020_000,
            ),
            configs=[
                Config(
                    "string • files-first, sort=modified desc, max_lines=4",
                    {
                        "output_mode": OUTPUT_MODE_STRING,
                        "folders_first": False,
                        "sort": (SORT_BY_MODIFIED, SORT_DESC),
                        "max_lines": 4,
                    },
                ),
                Config(
                    "string • zero file limit acts unlimited",
                    {
                        "output_mode": OUTPUT_MODE_STRING,
                        "folders_first": True,
                        "sort": (SORT_BY_NAME, SORT_ASC),
                        "max_folders": 2,
                        "max_files": 0,
                    },
                ),
            ],
        )
    )

    stress_structure = {
        "level1_a": {
            "level2_a1": {
                "leaf_a1_1.txt": "",
                "leaf_a1_2.txt": "",
                "leaf_a1_3.txt": "",
            },
            "level2_a2": {
                "leaf_a2_1.txt": "",
                "leaf_a2_2.txt": "",
                "leaf_a2_3.txt": "",
            },
            "level2_a3": {
                "subfolder_a3": {
                    "deep_a3_1.txt": "",
                    "deep_a3_2.txt": "",
                    "deep_a3_3.txt": "",
                    "subsubfolder_a3": {
                        "deep_a3_4.txt": "",
                        "deep_a3_5.txt": "",
                    },
                    "subsubfolder_a3_extra": {
                        "deep_a3_extra_1.txt": "",
                        "deep_a3_extra_2.txt": "",
                    },
                },
                "subfolder_a3_extra": {
                    "deep_extra_1.txt": "",
                    "deep_extra_2.txt": "",
                },
                "subfolder_a3_more": {
                    "deep_more_1.txt": "",
                },
            },
        },
        "level1_b": {
            "level2_b1": {
                "leaf_b1_1.txt": "",
                "leaf_b1_2.txt": "",
            },
            "level2_b2": {
                "leaf_b2_1.txt": "",
                "leaf_b2_2.txt": "",
                "leaf_b2_3.txt": "",
                "leaf_b2_4.txt": "",
                "leaf_b2_5.txt": "",
            },
            "level2_b3": {
                "subfolder_b3": {
                    "deep_b3_1.txt": "",
                    "deep_b3_2.txt": "",
                    "deep_b3_3.txt": "",
                    "deep_b3_4.txt": "",
                },
                "subfolder_b3_extra": {
                    "deeper_b3_extra.txt": "",
                    "deeper_b3_extra_2.txt": "",
                },
            },
        },
        "level1_c": {
            "level2_c1": {
                "leaf_c1_1.txt": "",
                "leaf_c1_2.txt": "",
                "leaf_c1_3.txt": "",
                "leaf_c1_4.txt": "",
                "leaf_c1_5.txt": "",
            },
            "level2_c2": {
                "subfolder_c2": {
                    "deep_c2_1.txt": "",
                    "deep_c2_2.txt": "",
                },
                "subfolder_c2_extra": {
                    "deep_c2_extra_1.txt": "",
                },
            },
        },
        "level1_d": {
            "level2_d1": {
                "leaf_d1_1.txt": "",
                "leaf_d1_2.txt": "",
                "leaf_d1_3.txt": "",
            },
            "level2_d2": {
                "subfolder_d2": {
                    "deep_d2_1.txt": "",
                    "deep_d2_2.txt": "",
                },
            },
        },
        "root_file.txt": "",
        "root_notes.md": "",
        "root_file_2.txt": "",
        "root_file_3.txt": "",
    }

    scenarios.append(
        Scenario(
            name="mixed_limits_baseline",
            description="Full structure without truncation for comparison",
            structure=stress_structure,
            configs=[
                Config(
                    "string • no limits baseline",
                    {
                        "output_mode": OUTPUT_MODE_STRING,
                        "folders_first": True,
                        "sort": (SORT_BY_NAME, SORT_ASC),
                    },
                ),
                Config(
                    "flat • no limits baseline",
                    {
                        "output_mode": OUTPUT_MODE_FLAT,
                        "folders_first": True,
                        "sort": (SORT_BY_NAME, SORT_ASC),
                    },
                ),
                Config(
                    "nested • no limits baseline",
                    {
                        "output_mode": OUTPUT_MODE_NESTED,
                        "folders_first": True,
                        "sort": (SORT_BY_NAME, SORT_ASC),
                    },
                ),
            ],
        )
    )

    scenarios.append(
        Scenario(
            name="mixed_limits_stress",
            description="Same structure with local and global limits applied",
            structure=stress_structure,
            configs=[
                Config(
                    "string • mixed local/global limits stress",
                    {
                        "output_mode": OUTPUT_MODE_STRING,
                        "folders_first": True,
                        "sort": (SORT_BY_NAME, SORT_ASC),
                        "max_folders": 2,
                        "max_files": 2,
                        "max_lines": 19,
                    },
                ),
                Config(
                    "flat • mixed limits stress",
                    {
                        "output_mode": OUTPUT_MODE_FLAT,
                        "folders_first": True,
                        "sort": (SORT_BY_NAME, SORT_ASC),
                        "max_folders": 2,
                        "max_files": 2,
                        "max_lines": 19,
                    },
                ),
                Config(
                    "nested • mixed limits stress",
                    {
                        "output_mode": OUTPUT_MODE_NESTED,
                        "folders_first": True,
                        "sort": (SORT_BY_NAME, SORT_ASC),
                        "max_folders": 2,
                        "max_files": 2,
                        "max_lines": 19,
                    },
                ),
            ],
        )
    )

    return scenarios


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Visualize file_tree() outputs across configurations."
    )
    parser.add_argument(
        "--scenario",
        action="append",
        dest="scenarios",
        help="Scenario name to run (repeat for multiple). Default: run all.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available scenarios and exit.",
    )
    return parser.parse_args()


def main() -> None:
    scenarios = build_scenarios()
    args = parse_args()

    if args.list:
        list_scenarios(scenarios)
        return

    if args.scenarios:
        name_map = {scenario.name: scenario for scenario in scenarios}
        unknown = [name for name in args.scenarios if name not in name_map]
        if unknown:
            raise SystemExit(f"Unknown scenario(s): {', '.join(unknown)}")
        selected = [name_map[name] for name in args.scenarios]
    else:
        selected = scenarios

    run_scenarios(selected)


if __name__ == "__main__":
    main()
