import mimetypes
import re
from pathlib import Path
from urllib.parse import urlparse

import pytest


playwright = pytest.importorskip("playwright.sync_api")
WEBUI = Path(__file__).resolve().parents[1] / "webui"
SELECTOR = WEBUI / "components" / "projects" / "project-selector.html"

PROJECTS_STUB = """import { createStore } from '/js/AlpineStore.js';
export const store = createStore('projects', {
  projectList: Array.from({ length: 25 }, (_, index) => ({ name: `p${index}`, title: `Project ${index}` })),
  loadProjectsList() {},
  openProjectsModal() {},
  editActiveProject() {},
  deactivateProject() {},
  activateProject() {},
});
"""

CHATS_STUB = """import { createStore } from '/js/AlpineStore.js';
export const store = createStore('chats', {
  selectedContext: { project: { name: 'p0', title: 'Project 0' } },
});
"""


def component_parts():
    markup = SELECTOR.read_text(encoding="utf-8")
    body = re.search(r"<body>(.*)</body>", markup, re.S).group(1)
    style = re.search(r"<style>(.*)</style>", markup, re.S).group(1)
    return body, style


def page_html(style):
    return f"""<!doctype html><html><head>
      <link rel="stylesheet" href="/index.css">
      <link rel="stylesheet" href="/vendor/google/google-icons.css">
      <style>{style}</style>
      <style>
        body {{ margin: 0; }}
        #host {{ margin-top: 200px; }}
      </style>
      <script type="module">
        await import('/components/projects/projects-store.js');
        await import('/components/sidebar/chats/chats-store.js');
        await import('/vendor/alpine/alpine.min.js');
        const markup = await (await fetch('/component.html')).text();
        const host = document.createElement('div');
        host.id = 'host';
        host.innerHTML = markup.trim();
        document.body.append(host);
        Alpine.initTree(host);
        window.componentMounted = true;
      </script>
      </head><body></body></html>"""


def serve_assets(html, body):
    def serve(route):
        path = urlparse(route.request.url).path
        if path == "/":
            route.fulfill(content_type="text/html", body=html)
        elif path == "/component.html":
            route.fulfill(content_type="text/html", body=body)
        elif path == "/components/projects/projects-store.js":
            route.fulfill(content_type="text/javascript", body=PROJECTS_STUB)
        elif path == "/components/sidebar/chats/chats-store.js":
            route.fulfill(content_type="text/javascript", body=CHATS_STUB)
        else:
            asset = WEBUI / path.lstrip("/")
            if asset.is_file():
                route.fulfill(path=asset, content_type=mimetypes.guess_type(asset)[0])
            else:
                route.abort()

    return serve


def test_project_menu_stays_inside_a_short_window():
    body, style = component_parts()
    with playwright.sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except playwright.Error as error:
            if "Executable doesn't exist" in str(error):
                pytest.skip("Install a Playwright Chromium browser to run DOM regressions.")
            raise
        try:
            page = browser.new_page(viewport={"width": 900, "height": 420})
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.route("**/*", serve_assets(page_html(style), body))
            page.goto("http://projects.test/")
            page.wait_for_function("window.componentMounted === true")
            trigger = page.locator(".project-dropdown-button").first
            trigger.click()
            menu = page.locator(".project-dropdown-container .dropdown-menu")
            playwright.expect(menu).to_be_visible()
            trigger_box = trigger.bounding_box()
            assert trigger_box["y"] + trigger_box["height"] > 200, trigger_box
            assert menu.bounding_box()["y"] + menu.bounding_box()["height"] <= 420, menu.bounding_box()
            assert menu.evaluate("el => el.scrollHeight > el.clientHeight")
            last = menu.locator(".dropdown-item").last
            last.scroll_into_view_if_needed()
            playwright.expect(last).to_be_visible()
            last_box = last.bounding_box()
            assert last_box["y"] + last_box["height"] <= 420, last_box
            page.set_viewport_size({"width": 900, "height": 320})
            page.evaluate("window.dispatchEvent(new Event('resize'))")
            menu_box = menu.bounding_box()
            assert menu_box["y"] + menu_box["height"] <= 320, menu_box
            last.scroll_into_view_if_needed()
            last_box = last.bounding_box()
            assert last_box["y"] + last_box["height"] <= 320, last_box
            assert not errors, errors
        finally:
            browser.close()


def test_project_selector_sizes_the_menu_from_the_trigger():
    markup = SELECTOR.read_text(encoding="utf-8")
    assert "this.$el.getBoundingClientRect()" in markup
    assert "window.innerHeight - rect.bottom" in markup
    assert "--project-dropdown-available-height" in markup
    assert "max-height: min(70vh, var(--project-dropdown-available-height, 70vh));" in markup
    assert markup.count("@click=\"toggleDropdown()\"") == 2
    assert '@resize.window="open && resizeDropdown()"' in markup
