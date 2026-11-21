"""Regression tests: subagent prompt file names keep their own identity.

Names that only differ in non-latin characters used to collapse to the same
underscore-only file name, so saving an agent silently kept just the last
prompt and the agent reloaded the wrong prompt set.
"""

from __future__ import annotations

import os

from helpers import files, subagents

PROMPTS = {
    "研究员.md": "你是研究员，负责收集资料。",
    "开发者.md": "你是开发者，负责实现功能。",
}


def test_non_ascii_prompt_names_keep_their_own_files(monkeypatch, tmp_path):
    monkeypatch.setattr(files, "_base_dir", str(tmp_path))
    agent = subagents.SubAgent(context="probe", title="localizer", description="")
    agent.prompts = dict(PROMPTS)

    subagents.save_agent_data("localizer", agent)

    prompts_dir = files.get_abs_path(subagents.USER_AGENTS_DIR, "localizer", "prompts")
    assert sorted(os.listdir(prompts_dir)) == sorted(PROMPTS)

    loaded = subagents._load_agent_data_from_dir(
        subagents.USER_AGENTS_DIR, "localizer", origin="user"
    )
    assert dict(loaded.prompts or {}) == PROMPTS


def test_safe_file_name_keeps_unicode_letters_and_removes_unsafe_characters():
    assert files.safe_file_name("报告 v2.md") == "报告_v2.md"
    assert files.safe_file_name("naïve-résumé.PDF") == "naïve-résumé.PDF"
    assert files.safe_file_name("../etc/passwd") == ".._etc_passwd"
    assert files.safe_file_name('a?b*c:d.txt') == "a_b_c_d.txt"
    assert files.safe_file_name("\x00name") == "_name"
    assert "/" not in files.safe_file_name("a/b")
    assert "\\" not in files.safe_file_name("a\\b")
