import unittest
from pathlib import Path


class TestFilesShortcutChordsStatic(unittest.TestCase):
    def test_select_all_matches_shared_chord_helper(self):
        store = Path("webui/components/modals/file-browser/file-browser-store.js").read_text()
        self.assertIn('matchesChordKey } from "/js/shortcut-keys.js"', store)
        self.assertIn('matchesChordKey(event, "a")', store)

    def test_dox_documents_layout_proof_select_all(self):
        dox = Path("webui/components/modals/file-browser/AGENTS.md").read_text()
        self.assertIn("shortcut-keys.js", dox)


if __name__ == "__main__":
    unittest.main()
