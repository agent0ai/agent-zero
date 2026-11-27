import ntpath
from pathlib import Path
import tempfile
import unittest

from helpers.security import safe_filename


class UploadFilenameTests(unittest.TestCase):
    def test_untrusted_names_remain_single_path_components(self):
        names = (
            "../../../../api/payload.py",
            r"..\..\..\..\api\payload.py",
            "/absolute/payload.py",
            r"C:\absolute\payload.py",
            "bad\x00name\n.txt",
            "report.pdf",
            "résumé 你好.txt",
            "",
            ".",
            "..",
            "   ",
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in names:
                for prefix in ("", "tg_test_12345678_", "tg_../../bot_12345678_"):
                    with self.subTest(name=name, prefix=prefix):
                        cleaned = safe_filename(prefix + name)
                        if cleaned is None:
                            self.assertFalse(prefix)
                            self.assertIn(name, ("", ".", "..", "   "))
                            continue
                        self.assertEqual(Path(cleaned).name, cleaned)
                        self.assertEqual(ntpath.basename(cleaned), cleaned)
                        self.assertNotIn(cleaned, (".", ".."))
                        self.assertNotIn("\x00", cleaned)
                        target = root / cleaned
                        self.assertEqual(target.resolve().parent, root.resolve())
                        target.write_bytes(b"attachment")
                        self.assertEqual(target.read_bytes(), b"attachment")

    def test_normal_names_are_preserved(self):
        for name in ("report.pdf", "archive.tar.gz", "résumé 你好.txt"):
            with self.subTest(name=name):
                self.assertEqual(safe_filename(name), name)


if __name__ == "__main__":
    unittest.main()
