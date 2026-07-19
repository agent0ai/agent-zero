from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from plugins._memory.helpers.memory_quality import (
    filter_auto_memory_fragments,
    is_auto_fragment_worth_saving,
)


def test_auto_fragment_quality_keeps_durable_preferences_and_project_facts():
    assert is_auto_fragment_worth_saving(
        "User currently prefers concise technical answers with verification."
    )
    assert is_auto_fragment_worth_saving(
        "Project currently uses a configured live runtime for smoke checks."
    )
    assert is_auto_fragment_worth_saving(
        "Runtime-impacting plugin changes must be synced into the configured live environment before testing."
    )


def test_auto_fragment_quality_rejects_action_history_and_transient_artifacts():
    rejected = [
        "Agent created a temporary CLI demo file and ran a shell test.",
        "The user asked to build a tiny CLI todo app in Python.",
        "Temporary marker ABC123 was used in a memory test.",
        "The markdown-to-HTML script generated sample.html with 181 bytes.",
        "Fixed AsyncRaceError in primary_modules.py by adding a thread lock on line 123.",
        "The live UI was reachable at a machine-local endpoint during this session.",
        "Project repository path is a personal absolute path on this machine.",
    ]

    for memory in rejected:
        assert not is_auto_fragment_worth_saving(memory)


def test_auto_fragment_filter_normalizes_and_preserves_kept_order():
    memories = [
        "User currently prefers Linux paths in examples.",
        "Agent created a demo file and reported success.",
        "Project repository uses a configured source workspace.",
    ]

    assert filter_auto_memory_fragments(memories) == [
        "User currently prefers Linux paths in examples.",
        "Project repository uses a configured source workspace.",
    ]
