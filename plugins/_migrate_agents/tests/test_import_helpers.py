from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from plugins._migrate_agents.api import migration_import
from plugins._migrate_agents.helpers.migration import Project


class ImportHelperTests(unittest.TestCase):
    def test_import_projects_uses_unique_native_names_and_maps_chats(self):
        project = Project("project-1", "Acme App", "/work/acme", ["chat-1", "chat-2"])
        with tempfile.TemporaryDirectory() as root:
            Path(root, "codex_acme_app").mkdir()
            with (
                patch.object(migration_import.a0_projects, "get_projects_parent_folder", return_value=root),
                patch.object(migration_import.a0_projects, "create_project", return_value="codex_acme_app_2") as create,
            ):
                names, mapping = migration_import.import_projects("codex", [project])

        self.assertEqual(names, ["codex_acme_app_2"])
        self.assertEqual(mapping, {"chat-1": "codex_acme_app_2", "chat-2": "codex_acme_app_2"})
        payload = create.call_args.args[1]
        self.assertEqual(payload["title"], "Acme App")
        self.assertIn("/work/acme", payload["description"])
        self.assertNotIn("secret", payload)


if __name__ == "__main__":
    unittest.main()
