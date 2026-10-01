"""Exercise the settings shell with Alpine and touch input, without live user data."""

import mimetypes
from pathlib import Path
from urllib.parse import urlparse

import pytest

playwright = pytest.importorskip("playwright.sync_api")
WEBUI = Path(__file__).resolve().parents[1] / "webui"


def test_mobile_navigation_and_save_without_file_browser_store():
    body = (WEBUI / "components/settings/settings.html").read_text().split("<body>")[1].split("</body>")[0]
    html = """<!doctype html><html><head>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <link rel="stylesheet" href="/index.css">
      <link rel="stylesheet" href="/css/modals.css">
      <link rel="stylesheet" href="/css/settings.css">
      </head><body>
      <div class="modal-inner settings-modal modal-with-footer">
        <div class="modal-header">Settings</div>
        <div class="modal-scroll"><div class="modal-bd">""" + body + """</div></div>
        <div class="modal-footer-slot"></div>
      </div>
      <script type="module">
        import { store } from '/components/settings/settings-store.js';
        window.closeCount = 0;
        window.closeModal = () => window.closeCount++;
        await import('/vendor/alpine/alpine.min.js');
        await new Promise(requestAnimationFrame);
        for (const tab of store.navItems) {
          const panel = document.querySelector(`[data-settings-tab="${tab.id}"]`);
          panel.innerHTML = tab.sections.map(section =>
            `<section class="section" id="${section.id}" style="height:500px">${section.label}</section>`
          ).join('');
        }
      </script></body></html>"""
    modules = {
        "/components/canvas/right-canvas-store.js": "export const store = { surfaces: [] };",
        "/components/sidebar/bottom/preferences/preferences-store.js": """
            export const store = { uiVisibilitySnapshot: () => ({}), setUiVisibility() {} };
        """,
        "/components/notifications/notification-store.js": """
            export const store = { notifications: [], addFrontendToastOnly() {} };
        """,
        "/js/api.js": """
            window.saved = [];
            export async function callJsonApi(endpoint, data) {
              if (endpoint === 'settings_get') return { settings: { timezone: 'auto' } };
              window.saved.push(data);
              return new Promise(resolve => window.finishSave = () => resolve(data));
            }
        """,
    }

    def serve(route):
        path = urlparse(route.request.url).path
        if path == "/":
            route.fulfill(content_type="text/html", body=html)
        elif path in modules:
            route.fulfill(content_type="text/javascript", body=modules[path])
        else:
            asset = WEBUI / path.lstrip("/")
            if asset.is_file():
                route.fulfill(path=asset, content_type=mimetypes.guess_type(asset)[0])
            else:
                route.abort()

    with playwright.sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except playwright.Error as error:
            if "Executable doesn't exist" in str(error):
                pytest.skip("An installed Playwright Chromium browser is required.")
            raise
        try:
            page = browser.new_page(viewport={"width": 393, "height": 852}, is_mobile=True, has_touch=True)
            page.route("**/*", serve)
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto("http://settings.test/")
            save = page.get_by_role("button", name="Save", exact=True)
            playwright.expect(save).to_be_visible()
            page.evaluate("document.querySelector('.modal-footer-slot').append(document.querySelector('[data-modal-footer]'))")
            assert page.evaluate("Alpine.store('fileBrowser') === undefined")
            playwright.expect(save).to_be_enabled()
            save.tap()
            page.wait_for_function("window.saved.length === 1")
            playwright.expect(save).to_be_disabled()
            page.evaluate("window.finishSave()")
            page.wait_for_function("window.closeCount === 1")
            playwright.expect(save).to_be_enabled()

            page.evaluate("Alpine.store('fileBrowser', { savingTextLimit: true })")
            playwright.expect(save).to_be_disabled()
            page.evaluate("Alpine.store('fileBrowser').savingTextLimit = false")
            playwright.expect(save).to_be_enabled()
            page.get_by_role("button", name="Cancel", exact=True).tap()
            assert page.evaluate("window.closeCount") == 2

            picker = page.get_by_role("combobox", name="Settings section")
            playwright.expect(picker).to_have_value("section-agent-config")
            picker.select_option("section-interface")
            page.wait_for_function("Alpine.store('settings').activeSection === 'section-interface'")
            picker.select_option("section-auth")
            page.wait_for_function("Alpine.store('settings').activeTab === 'external'")
            playwright.expect(picker).to_have_value("section-auth")
            assert page.locator(".settings-tabs-container").bounding_box()["height"] < 80
            assert save.bounding_box()["y"] + save.bounding_box()["height"] <= 852

            page.set_viewport_size({"width": 1280, "height": 900})
            playwright.expect(picker).to_be_hidden()
            search = page.get_by_role("searchbox", name="Search settings")
            search.fill("Locale")
            page.get_by_role("link", name="Locale", exact=True).click()
            page.wait_for_function("Alpine.store('settings').activeSection === 'section-locale'")
            page.set_viewport_size({"width": 393, "height": 500})
            playwright.expect(picker).to_have_value("section-locale")
            assert save.bounding_box()["y"] + save.bounding_box()["height"] <= 500
            assert not errors
        finally:
            browser.close()
