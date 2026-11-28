import unittest
from pathlib import Path


class TestBrowserShortcutChordsStatic(unittest.TestCase):
    def test_viewer_chords_use_shared_chord_matching(self):
        helper = Path("webui/js/shortcut-keys.js").read_text()
        self.assertIn("export function matchesChordKey", helper)
        self.assertIn("`Key${expected.toUpperCase()}`", helper)
        self.assertIn('".": "Period"', helper)
        store = Path("plugins/_browser/webui/browser-store.js").read_text()
        self.assertIn('matchesChordKey } from "/js/shortcut-keys.js"', store)
        self.assertIn('matchesChordKey(event, ".")', store)
        self.assertIn("BROWSER_VISUAL_SHORTCUT_CODES.has(event?.code)", store)

    def test_viewer_iframe_translates_layout_mismatched_chords(self):
        vnc = Path("plugins/_browser/webui/vnc.js").read_text()
        self.assertIn("function viewerChordKey", vnc)
        self.assertIn("if (event.altKey) return null;", vnc)
        self.assertIn('"SuperLeft"', vnc)
        self.assertIn("KeyA: ", vnc)
        self.assertIn("keysymLookup.lookup(expected.codePointAt(0))", vnc)
        self.assertIn("stopImmediatePropagation", vnc)
        self.assertNotIn("browser-viewer-key", vnc)
        store = Path("plugins/_browser/webui/browser-store.js").read_text()
        panel = Path("plugins/_browser/webui/browser-panel.html").read_text()
        self.assertNotIn("browser-viewer-key", panel)
        self.assertNotIn("handleViewerChord", store)


if __name__ == "__main__":
    unittest.main()
