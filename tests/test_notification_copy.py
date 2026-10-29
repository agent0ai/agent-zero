"""Copy actions stay usable on long toasts without opening or dismissing them."""

import mimetypes
from pathlib import Path
from urllib.parse import urlparse

import pytest


playwright = pytest.importorskip("playwright.sync_api")
WEBUI = Path(__file__).resolve().parents[1] / "webui"


@pytest.mark.parametrize("width", [1100, 320])
def test_toast_copy_keeps_full_text_and_controls_visible(width):
    component = (WEBUI / "components/notifications/notification-toast-stack.html").read_text()
    body = component.split("<body>")[1].split("</body>")[0]
    html = """<!doctype html><html><head>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <link rel="stylesheet" href="/index.css">
      <link rel="stylesheet" href="/vendor/google/google-icons.css">
      <link rel="stylesheet" href="/components/messages/action-buttons/simple-action-buttons.css">
      <script type="module">
        import { store } from '/components/notifications/notification-store.js';
        window.store = store;
        window.modalOpens = 0;
        document.addEventListener('alpine:init', () => {
          Alpine.directive('create', (_el, { expression }, { evaluateLater }) => {
            evaluateLater(expression)();
          });
        });
        await import('/vendor/alpine/alpine.min.js');
      </script>
      </head><body><button id="outside">Outside</button>""" + body + "</body></html>"

    def serve(route):
        path = urlparse(route.request.url).path
        if path == "/":
            route.fulfill(content_type="text/html", body=html)
        elif path == "/js/modals.js":
            route.fulfill(content_type="text/javascript", body="export async function openModal() { window.modalOpens++; }")
        elif path == "/js/extensions.js":
            route.fulfill(content_type="text/javascript", body="""
              export async function callJsExtensions(point, data) {
                (window.notificationEvents ??= []).push({ point, ...structuredClone(data) });
                data.notification.title = 'Extension-owned copy';
              }
            """)
        else:
            asset = WEBUI / path.lstrip("/")
            route.fulfill(path=asset, content_type=mimetypes.guess_type(asset)[0])

    with playwright.sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except playwright.Error as error:
            if "Executable doesn't exist" in str(error):
                pytest.skip("Install a Playwright Chromium browser to run DOM regressions.")
            raise
        try:
            page = browser.new_page(viewport={"width": width, "height": 720})
            page.route("**/*", serve)
            page.goto("https://toast.test/")
            page.wait_for_function("window.Alpine && window.store")
            page.evaluate("""() => {
              navigator.clipboard.writeText = async text => { window.copied = text; };
              store.addFrontendToastOnly('error', '<b>Failure &amp; details</b><br>' +
                'Long traceback line<br>'.repeat(40) + 'x'.repeat(500) + '<br>LAST LINE', 'Error title', 60);
              store.addFrontendToastOnly('info', 'Other message', '', 60);
            }""")
            toast = page.locator(".toast-item").filter(has_text="Error title")
            content = toast.locator(".toast-content")
            copy = toast.get_by_role("button", name="Copy", exact=True)
            dismiss = toast.get_by_role("button", name="Dismiss", exact=True)
            playwright.expect(copy).to_be_visible()
            expected = "Error title\nFailure & details\n" + "Long traceback line\n" * 40 + "x" * 500 + "\nLAST LINE"
            assert content.inner_text() == expected
            events = page.evaluate("window.notificationEvents")
            assert [event["source"] for event in events] == ["frontend", "frontend"]
            assert all(event["point"] == "notification_received" for event in events)
            assert events[0]["notification"]["title"] == "Error title"
            before = copy.bounding_box()
            text_box = content.bounding_box()
            assert copy.inner_text().endswith("Copy")
            assert before["x"] == text_box["x"]
            assert before["y"] >= text_box["y"] + text_box["height"]
            assert dismiss.bounding_box()["y"] < before["y"]
            assert content.evaluate("el => el.scrollHeight > el.clientHeight")
            assert content.evaluate("el => el.scrollWidth <= el.clientWidth")
            content.evaluate("el => { el.scrollTop = el.scrollHeight; }")
            assert content.evaluate("el => el.scrollTop > 0")
            assert copy.bounding_box() == before
            assert toast.bounding_box()["x"] >= 0
            assert dismiss.bounding_box()["x"] + dismiss.bounding_box()["width"] <= width

            copy.click()
            playwright.expect(copy.locator("x-icon")).to_have_attribute("name", "check")
            assert page.evaluate("window.copied") == expected
            assert page.evaluate("window.modalOpens") == 0
            playwright.expect(page.locator(".toast-item")).to_have_count(2)

            # Focus keeps the toast alive even after the pointer leaves it.
            page.mouse.move(0, 0)
            assert page.evaluate("store.toastStack[0].autoRemoveTimer") is None
            dismiss.focus()
            assert page.evaluate("store.toastStack[0].autoRemoveTimer") is None
            page.locator("#outside").focus()
            assert page.evaluate("store.toastStack[0].autoRemoveTimer !== null")

            page.locator(".toast-item").filter(has_text="Other message").get_by_role("button", name="Copy").click()
            assert page.evaluate("window.copied") == "Other message"

            page.evaluate("() => { navigator.clipboard.writeText = async () => { throw new Error('Clipboard denied'); }; }")
            copy.focus()
            copy.press("Enter")
            playwright.expect(copy.locator("x-icon")).to_have_attribute("name", "error")
            playwright.expect(toast).to_be_visible()
            assert page.evaluate("window.modalOpens") == 0

            # Exercise the shared fallback without relying on a host clipboard.
            page.evaluate("""() => {
              Object.defineProperty(navigator, 'clipboard', { value: undefined });
              document.execCommand = command => {
                if (command !== 'copy') throw new Error(command);
                window.copied = document.activeElement.value;
                return true;
              };
            }""")
            copy.click()
            assert page.evaluate("window.copied") == expected
            playwright.expect(page.locator("textarea")).to_have_count(0)
            dismiss.click()
            playwright.expect(toast).to_have_count(0)
            playwright.expect(page.locator(".toast-item")).to_have_count(1)
            page.evaluate("""() => {
              store.addOrUpdateNotification({ id: 'backend-test', title: 'Backend error', message: 'Details' });
            }""")
            assert page.evaluate("window.notificationEvents.at(-1).source") == "backend"
            assert page.evaluate("store.notifications[0].title") == "Backend error"
            for notification_id, title, action, notification_type in [
                ("plugins_frontend_reload", "Plugin update", "Reload page", "info"),
                ("update_check_available", "Newer version available", "Open updater", "info"),
                ("oauth-codex-reconnect", "Reconnect Codex", "Open OAuth settings", "warning"),
                (None, "Agent saved.", "Test in new chat", "success"),
            ]:
                page.evaluate("""sample => {
                  const message = `<div><button @click.stop="window.nestedAction = true">${sample.action}</button></div>`;
                  window.nestedAction = false;
                  if (sample.id) {
                    store.addToToastStack({ ...sample, message, display_time: 0 });
                  } else {
                    store.addFrontendToastOnly(sample.type, message, sample.title, 0, 'agent-editor-saved');
                  }
                }""", {"id": notification_id, "title": title, "action": action, "type": notification_type})
                action_toast = page.locator(".toast-item").filter(has_text=title)
                action_copy = action_toast.get_by_role("button", name="Copy", include_hidden=True)
                playwright.expect(action_copy).to_be_hidden()
                action_toast.get_by_role("button", name=action, exact=True).click()
                assert page.evaluate("window.nestedAction")
                assert page.evaluate("window.modalOpens") == 0
                if notification_id == "plugins_frontend_reload":
                    page.evaluate("""() => {
                      store.toastStack.find(toast => toast.id === 'plugins_frontend_reload').message = 'Plain update text';
                    }""")
                    playwright.expect(action_copy).to_be_visible()
                    page.evaluate("""() => {
                      store.toastStack.find(toast => toast.id === 'plugins_frontend_reload').message = '<button>Reload page</button>';
                    }""")
                    playwright.expect(action_copy).to_be_hidden()
                action_toast.get_by_role("button", name="Dismiss").click()
                playwright.expect(action_toast).to_have_count(0)
                playwright.expect(page.locator(".toast-item").filter(has_text="Other message").get_by_role("button", name="Copy")).to_be_visible()
        finally:
            browser.close()
