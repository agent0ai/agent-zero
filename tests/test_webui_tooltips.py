"""Touch taps must activate controls without leaving Bootstrap tooltips open."""

import mimetypes
from pathlib import Path
from urllib.parse import urlparse

import pytest


playwright = pytest.importorskip("playwright.sync_api")
WEBUI = Path(__file__).resolve().parents[1] / "webui"


def test_touch_taps_suppress_tooltips_and_mouse_hover_still_works():
    html = """<!doctype html><html><head>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <script src="/vendor/bootstrap/bootstrap.bundle.min.js"></script>
      </head><body>
      <button title="Helpful description" onclick="window.clicks++">Action</button>
      <script>window.clicks = 0;</script>
      </body></html>"""

    def serve(route):
        path = urlparse(route.request.url).path
        if path == "/":
            route.fulfill(content_type="text/html", body=html)
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
                pytest.skip("Install a Playwright Chromium browser to run DOM regressions.")
            raise
        try:
            for touch in (True, False):
                context = browser.new_context(
                    viewport={"width": 390, "height": 844},
                    is_mobile=touch, has_touch=touch,
                )
                page = context.new_page()
                page.route("**/*", serve)
                page.goto("http://tooltips.test/")
                page.evaluate("""async () => {
                  window.tooltips = (await import('/components/tooltips/tooltip-store.js')).store;
                  tooltips.init();
                }""")
                button = page.get_by_role("button", name="Action")
                if touch:
                    button.tap()
                    assert page.evaluate("window.clicks") == 1
                    playwright.expect(page.locator(".tooltip")).to_have_count(0)
                    # Also covers a delayed or programmatic show after the tap.
                    button.evaluate("el => bootstrap.Tooltip.getInstance(el).show()")
                    playwright.expect(page.locator(".tooltip")).to_have_count(0)
                    assert button.get_attribute("title") is None
                    assert button.get_attribute("aria-describedby") is None
                else:
                    button.hover()
                    playwright.expect(page.locator(".tooltip.show")).to_have_count(1)
                    page.mouse.move(300, 400)
                    playwright.expect(page.locator(".tooltip")).to_have_count(0)
                    button.focus()
                    page.keyboard.press("Enter")
                    assert page.evaluate("window.clicks") == 1
                page.evaluate("tooltips.cleanup()")
                context.close()
        finally:
            browser.close()
