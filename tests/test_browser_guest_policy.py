"""Run in the provisioned Browser guest with PYTHONPATH=/app python test_browser_guest_policy.py."""
import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


@unittest.skipUnless(Path('/worker/boot.sh').is_file() and Path('/plugin/sandbox/rpc.py').is_file(),
                     'requires the provisioned A0 Browser guest')
class BrowserPolicyTest(unittest.IsolatedAsyncioTestCase):
    async def test_chromium_applies_command_line_warning_policy(self):
        from plugins._browser.helpers.config import CHROMIUM_EXECUTABLE
        from plugins._browser.sandbox.cdp import CDPContext

        profile = self.enterContext(TemporaryDirectory())
        browser = await CDPContext.launch(CHROMIUM_EXECUTABLE, [
            '--headless', '--no-sandbox', '--disable-dev-shm-usage', f'--user-data-dir={profile}', 'about:blank',
        ])
        self.addAsyncCleanup(browser.close)
        page = browser.pages[0]
        await page.goto('chrome://policy/')
        async with asyncio.timeout(10):
            while True:
                cells = await page.evaluate("""() => {
                    const root = document.querySelector('policy-app')?.shadowRoot || document;
                    const table = root.querySelector('policy-table');
                    for (const row of table?.shadowRoot?.querySelectorAll('policy-row') || []) {
                        const cells = row.shadowRoot?.querySelector('.policy.row');
                        if (cells?.querySelector('#name')?.textContent === 'CommandLineFlagSecurityWarningsEnabled')
                            return ['.value', '.source', '.messages'].map(s => cells.querySelector(s).innerText);
                    }
                    return null;
                }""")
                if cells is not None:
                    break
                await asyncio.sleep(0.05)
        self.assertEqual(cells, ['false', 'Platform', 'OK'])


if __name__ == '__main__':
    unittest.main()
