from io import BytesIO
import json
import unittest
from unittest.mock import patch
from urllib.error import URLError

from plugins._plugin_installer.helpers.compatibility import get_plugin_compatibility, matches_version


class PluginCompatibilityTests(unittest.TestCase):
    def test_exact_versions_ranges_wildcards_and_alternatives(self):
        cases = [
            (None, "custom-fork", True), ("", "unknown", True), ([], "unknown", True),
            ("*", "custom-fork", True), ("3.0", "v3.0.0", True),
            ("v3.0", "v3.0+29", True), ("3.0", "3.1", False),
            (["2.15", "3.2"], "v3.2", True), (["2.15", "3.2"], "3.1", False),
            (">=3.0,<4.0", "v3.10", True), (">=3.0,<4.0", "4.0", False),
            (">=3.0,<=3.5", "3.5", True), (">3.0,!=3.2", "3.2", False),
            ("3.0 - 3.5", "3.0", True), ("3.0 - 3.5", "3.5", True),
            ("3.0 - 3.5", "3.6", False), ("v3.*", "3.10", True),
            ("3.1.*", "3.1.7", True), ("3.1.*", "3.10", False),
            (["2.15", ">=3.0,<4.0", "5.*"], "5.1", True),
            ("3.*", "3.0rc1", True), (">=3.0", "3.0rc1", False),
        ]
        for requirement, version, expected in cases:
            with self.subTest(requirement=requirement, version=version):
                self.assertEqual(matches_version(requirement, version), expected)

    def test_invalid_requirements_and_unknown_versions_do_not_claim_a_match(self):
        for requirement, version in [
            (3.0, "3.0"), (True, "3.0"), ({"min": "3"}, "3.0"),
            (["3.0", 4], "3.0"), ([""], "3.0"), (" ", "3.0"),
            (">=3.0,", "3.1"), ("3..*", "3.1"), ("^3.0", "3.0"),
            (["*", "broken"], "3.0"), (">=3.0", "custom-fork"),
        ]:
            with self.subTest(requirement=requirement, version=version):
                with self.assertRaises(ValueError):
                    matches_version(requirement, version)

    def check_manifest(self, content, version="v3.2"):
        with patch("urllib.request.urlopen", return_value=BytesIO(content)) as fetch:
            result = get_plugin_compatibility("https://github.com/example/plugin.git/", version)
        self.assertEqual(fetch.call_args.args[0].full_url,
                         "https://raw.githubusercontent.com/example/plugin/HEAD/plugin.yaml")
        self.assertEqual(result["current_version"], version)
        return result

    def test_reads_requirements_from_manifest_on_default_branch(self):
        result = self.check_manifest(b'name: example\na0_version: ["2.15", ">=3.0,<4.0"]\n')
        self.assertTrue(result["compatible"])
        self.assertEqual(result["a0_version"], ["2.15", ">=3.0,<4.0"])
        self.assertEqual(result["error"], "")
        result = self.check_manifest(b'a0_version: "4.*"\n')
        self.assertFalse(result["compatible"])

    def test_legacy_manifests_have_no_requirement(self):
        result = self.check_manifest(b'name: example\nversion: 1.0.0\n', "custom-fork")
        self.assertTrue(result["compatible"])
        self.assertIsNone(result["a0_version"])

    def test_v3_requirements_warn_on_v2_and_explicit_v2_alternatives_match(self):
        for requirement in ("3.*", ">=3.0,<4.0", "3.0 - 3.9"):
            with self.subTest(requirement=requirement):
                result = self.check_manifest(f'a0_version: "{requirement}"\n'.encode(), "v2.15")
                self.assertFalse(result["compatible"])
                self.assertEqual(result["a0_version"], requirement)
                self.assertEqual(result["error"], "")
        result = self.check_manifest(b'a0_version: ["2.*", "3.*"]\n', "v2.15")
        self.assertTrue(result["compatible"])

    def test_unknown_current_version_keeps_requirement_for_warning(self):
        result = self.check_manifest(b'a0_version: "3.*"\n', "custom-fork")
        self.assertIsNone(result["compatible"])
        self.assertEqual(result["a0_version"], "3.*")
        self.assertTrue(result["error"])

    def test_invalid_or_oversized_manifests_are_unverified(self):
        for content in [
            b'- not a mapping\n', b'a0_version: [', b'a0_version: 3.0\n',
            b'a0_version: [2026-01-01]\n', b'a0_version: &self [*self]\n', b'x' * 65537,
        ]:
            with self.subTest(content=content[:32]):
                result = self.check_manifest(content)
                self.assertIsNone(result["compatible"])
                self.assertTrue(result["error"])
                json.dumps(result)

    def test_fetch_failure_remains_an_advisory_unknown_result(self):
        with patch("urllib.request.urlopen", side_effect=URLError("offline")):
            result = get_plugin_compatibility("https://github.com/example/plugin", "v3.2")
        self.assertIsNone(result["compatible"])
        self.assertEqual(result["current_version"], "v3.2")
        self.assertIn("offline", result["error"])

    def test_only_github_repository_urls_can_trigger_manifest_fetch(self):
        for url in [
            "http://127.0.0.1/secret", "file:///etc/passwd", "https://github.com.evil.test/a/b",
            "https://github.com@evil.test/a/b", "https://github.com/a/b/tree/main",
            "https://github.com/../b", "https://github.com/a/..", "https://github.com/a/%2e%2e",
        ]:
            with self.subTest(url=url), patch("urllib.request.urlopen") as fetch:
                result = get_plugin_compatibility(url, "v3.2")
                fetch.assert_not_called()
                self.assertIsNone(result["compatible"])
                self.assertTrue(result["error"])


if __name__ == "__main__":
    unittest.main()
