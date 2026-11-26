"""Keep separate paths when team members attach a folder."""

import shutil

import pytest

from test_chat_loading_refresh import run_module


@pytest.mark.skipif(not shutil.which("node"), reason="Node.js is required")
def test_shared_folder_deduplication_preserves_relative_paths():
    run_module(
        "webui/components/chat/attachments/attachmentsStore.js",
        """
const createStore = (_name, model) => model;
const chats = { selected: '', selectedContext: null };
const projects = { teamProjectName: 'shared' };
const getStore = name => name === 'chats' ? chats : projects;
""",
        """
const first = { name: 'overview.txt', file: { size: 5, webkitRelativePath: 'root/a/overview.txt' } };
const second = { name: 'overview.txt', file: { size: 5, webkitRelativePath: 'root/b/overview.txt' } };
store.addAttachment(first);

globalThis.runtimeInfo = { teamRole: 'member' };
assert.equal(store.validateDuplicates(second), true);
assert.equal(store.validateDuplicates(first), false);

globalThis.runtimeInfo.teamRole = 'admin';
assert.equal(store.validateDuplicates(second), true);
chats.selected = 'existing-shared';
chats.selectedContext = { team_chat: true };
assert.equal(store.validateDuplicates(second), true);
chats.selectedContext = { team_chat: false };
assert.equal(store.validateDuplicates(second), false);

globalThis.runtimeInfo.teamRole = '';
assert.equal(store.validateDuplicates(second), false);
""",
    )
