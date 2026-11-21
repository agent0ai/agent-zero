"""Run inside the provisioned Browser worker with PLAYWRIGHT_BROWSERS_PATH=/opt/browsers."""
from pathlib import Path
import unittest


@unittest.skipUnless(Path('/worker/boot.sh').is_file() and Path('/plugin/sandbox/rpc.py').is_file(),
                     'requires the provisioned A0 Browser guest')
class BrowserPolicyTest(unittest.TestCase):
    def test_chromium_applies_command_line_warning_policy(self):
        from patchright.sync_api import sync_playwright

        with sync_playwright() as driver:
            browser = driver.chromium.launch(executable_path=driver.chromium.executable_path)
            try:
                page = browser.new_page()
                page.goto('chrome://policy/')
                name = page.get_by_text('CommandLineFlagSecurityWarningsEnabled', exact=True)
                row = page.locator('policy-row').filter(has=name).locator('.policy.row')
                self.assertEqual(row.locator('.value').inner_text(), 'false')
                self.assertEqual(row.locator('.source').inner_text(), 'Platform')
                self.assertEqual(row.locator('.messages').inner_text(), 'OK')
            finally:
                browser.close()


if __name__ == '__main__':
    unittest.main()
