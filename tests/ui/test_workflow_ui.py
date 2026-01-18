"""
Playwright UI tests for Workflow Engine Dashboard.
Tests the workflow dashboard UI components and interactions.

Uses data-testid selectors for reliable, refactor-safe testing.
"""

import os
import socket
import subprocess
import sys
import time
import urllib.request

import pytest


def _find_free_port() -> int:
    """Find an available port for the test server"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _wait_for_server(url: str, timeout: float = 90.0) -> None:
    """Wait for the UI server to become available"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    return
        except Exception:
            time.sleep(0.5)
    raise TimeoutError(f"Server did not become ready at {url}")


def _start_ui_server(port: int) -> subprocess.Popen:
    """Start the Agent Zero UI server for testing"""
    env = os.environ.copy()
    env["WEB_UI_HOST"] = "127.0.0.1"
    env["WEB_UI_PORT"] = str(port)
    env["AUTH_LOGIN"] = ""
    env["AUTH_PASSWORD"] = ""
    env["TOKENIZERS_PARALLELISM"] = "false"
    return subprocess.Popen(
        [sys.executable, "run_ui.py"],
        env=env,
        cwd=os.getcwd(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def _navigate_to_workflows(page):
    """Helper to navigate to the Workflows dashboard"""
    page.wait_for_function("window.Alpine && Alpine.store('dashboardRouter')", timeout=10000)
    # Navigate to Workflows dashboard from sidebar
    page.wait_for_selector(".dashboard-nav-btn:has-text('Workflows')", timeout=10000)
    page.click(".dashboard-nav-btn:has-text('Workflows')")

    # Wait for the dashboard to load
    page.wait_for_selector("[data-testid='workflow-dashboard']", timeout=10000)


def test_workflow_dashboard_loads():
    """Test that workflow dashboard loads successfully with all required elements"""
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        pytest.skip("Playwright not available")

    port = _find_free_port()
    base_url = f"http://127.0.0.1:{port}"
    proc = _start_ui_server(port)
    try:
        _wait_for_server(base_url, timeout=90)

        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
            except Exception:
                pytest.skip("Playwright browser not installed")
            page = browser.new_page()
            page.goto(base_url, wait_until="domcontentloaded")

            _navigate_to_workflows(page)

            # Verify dashboard container exists
            dashboard = page.locator("[data-testid='workflow-dashboard']")
            assert dashboard.count() == 1, "Dashboard container should exist"

            # Verify tabs exist
            tabs = page.locator("[data-testid='workflow-tabs']")
            assert tabs.count() == 1, "Tabs container should exist"

            # Verify all 4 tab buttons exist
            assert page.locator("[data-testid='tab-dashboard']").count() == 1
            assert page.locator("[data-testid='tab-workflows']").count() == 1
            assert page.locator("[data-testid='tab-training']").count() == 1
            assert page.locator("[data-testid='tab-skills']").count() == 1

            # Verify refresh button exists
            refresh_btn = page.locator("[data-testid='refresh-button']")
            assert refresh_btn.count() == 1, "Refresh button should exist"

            browser.close()
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


def test_workflow_tab_navigation():
    """Test navigation between workflow dashboard tabs with proper view switching"""
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        pytest.skip("Playwright not available")

    port = _find_free_port()
    base_url = f"http://127.0.0.1:{port}"
    proc = _start_ui_server(port)
    try:
        _wait_for_server(base_url, timeout=90)

        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
            except Exception:
                pytest.skip("Playwright browser not installed")
            page = browser.new_page()
            page.goto(base_url, wait_until="domcontentloaded")

            _navigate_to_workflows(page)

            # Test Dashboard tab (default) - should show stats
            dashboard_tab = page.locator("[data-testid='tab-dashboard']")
            dashboard_tab.click()
            page.wait_for_timeout(500)

            # Verify dashboard view is visible
            dashboard_view = page.locator("[data-testid='view-dashboard']")
            assert dashboard_view.is_visible(), "Dashboard view should be visible after clicking Dashboard tab"

            # Verify stats section exists
            stats = page.locator("[data-testid='workflow-stats']")
            assert stats.is_visible(), "Stats section should be visible in dashboard view"

            # Test Workflows tab
            workflows_tab = page.locator("[data-testid='tab-workflows']")
            workflows_tab.click()
            page.wait_for_timeout(500)

            workflows_view = page.locator("[data-testid='view-workflows']")
            assert workflows_view.is_visible(), "Workflows view should be visible after clicking Workflows tab"

            # Verify workflow list panel exists
            workflow_list_panel = page.locator("[data-testid='workflow-list-panel']")
            assert workflow_list_panel.is_visible(), "Workflow list panel should be visible"

            # Test Training tab
            training_tab = page.locator("[data-testid='tab-training']")
            training_tab.click()
            page.wait_for_timeout(500)

            training_view = page.locator("[data-testid='view-training']")
            assert training_view.is_visible(), "Training view should be visible after clicking Training tab"

            # Test Skills tab
            skills_tab = page.locator("[data-testid='tab-skills']")
            skills_tab.click()
            page.wait_for_timeout(500)

            skills_view = page.locator("[data-testid='view-skills']")
            assert skills_view.is_visible(), "Skills view should be visible after clicking Skills tab"

            browser.close()
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


def test_workflow_dashboard_stats_display():
    """Test that dashboard stats section displays correctly with all stat cards"""
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        pytest.skip("Playwright not available")

    port = _find_free_port()
    base_url = f"http://127.0.0.1:{port}"
    proc = _start_ui_server(port)
    try:
        _wait_for_server(base_url, timeout=90)

        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
            except Exception:
                pytest.skip("Playwright browser not installed")
            page = browser.new_page()
            page.goto(base_url, wait_until="domcontentloaded")

            _navigate_to_workflows(page)

            # Verify stats section exists
            stats_section = page.locator("[data-testid='workflow-stats']")
            assert stats_section.count() == 1, "Stats section should exist"
            assert stats_section.is_visible(), "Stats section should be visible"

            # Verify all 4 stat cards exist
            assert page.locator("[data-testid='stat-workflows']").count() == 1, "Workflows stat card should exist"
            assert page.locator("[data-testid='stat-executions']").count() == 1, "Executions stat card should exist"
            assert page.locator("[data-testid='stat-skills']").count() == 1, "Skills stat card should exist"
            assert (
                page.locator("[data-testid='stat-learning-paths']").count() == 1
            ), "Learning paths stat card should exist"

            # Verify stat values exist (may be 0 on fresh install)
            assert page.locator("[data-testid='stat-workflows-value']").count() == 1
            assert page.locator("[data-testid='stat-executions-value']").count() == 1
            assert page.locator("[data-testid='stat-skills-value']").count() == 1
            assert page.locator("[data-testid='stat-learning-paths-value']").count() == 1

            browser.close()
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


def test_workflow_refresh_button():
    """Test that refresh button exists, is clickable, and triggers data reload"""
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        pytest.skip("Playwright not available")

    port = _find_free_port()
    base_url = f"http://127.0.0.1:{port}"
    proc = _start_ui_server(port)
    try:
        _wait_for_server(base_url, timeout=90)

        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
            except Exception:
                pytest.skip("Playwright browser not installed")
            page = browser.new_page()
            page.goto(base_url, wait_until="domcontentloaded")

            _navigate_to_workflows(page)

            # Verify refresh button exists
            refresh_btn = page.locator("[data-testid='refresh-button']")
            assert refresh_btn.count() == 1, "Refresh button should exist"
            assert refresh_btn.is_visible(), "Refresh button should be visible"

            # Click refresh button
            refresh_btn.click()

            # Button may briefly show loading state - wait for it to complete
            page.wait_for_function(
                "!document.querySelector(\"[data-testid='refresh-button']\").disabled",
                timeout=5000,
            )

            # Verify button is still present and enabled after refresh
            assert refresh_btn.is_visible(), "Refresh button should still be visible after click"
            assert refresh_btn.is_enabled(), "Refresh button should be enabled after refresh completes"

            browser.close()
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


def test_workflow_empty_state():
    """Test that empty state messages are displayed correctly on fresh install"""
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        pytest.skip("Playwright not available")

    port = _find_free_port()
    base_url = f"http://127.0.0.1:{port}"
    proc = _start_ui_server(port)
    try:
        _wait_for_server(base_url, timeout=90)

        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
            except Exception:
                pytest.skip("Playwright browser not installed")
            page = browser.new_page()
            page.goto(base_url, wait_until="domcontentloaded")

            _navigate_to_workflows(page)

            # Wait for data to load
            page.wait_for_timeout(2000)

            # Check that error element exists but is NOT visible (no errors on fresh install)
            error_element = page.locator("[data-testid='workflow-error']")
            assert error_element.count() == 1, "Error element should exist in DOM"
            # Note: Element may be hidden via x-show, so we check visibility
            is_error_visible = error_element.is_visible()
            # On fresh install, there should be no errors
            assert not is_error_visible, "No error should be visible on fresh install"

            # Switch to Workflows tab and check empty state
            page.locator("[data-testid='tab-workflows']").click()
            page.wait_for_timeout(500)

            # Either workflows list or empty message should be visible
            workflow_list = page.locator("[data-testid='workflow-list']")
            workflow_empty = page.locator("[data-testid='workflow-list-empty']")
            assert (
                workflow_list.count() == 1 or workflow_empty.count() == 1
            ), "Either workflow list or empty message should exist"

            # Switch to Skills tab and check empty state
            page.locator("[data-testid='tab-skills']").click()
            page.wait_for_timeout(500)

            # Either skills grid or empty message should be visible
            skills_grid = page.locator("[data-testid='skills-grid']")
            skills_empty = page.locator("[data-testid='skills-empty']")
            assert (
                skills_grid.count() == 1 or skills_empty.count() == 1
            ), "Either skills grid or empty message should exist"

            browser.close()
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


def test_workflow_mermaid_container_exists():
    """Test that Mermaid diagram container is present in Workflows view"""
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        pytest.skip("Playwright not available")

    port = _find_free_port()
    base_url = f"http://127.0.0.1:{port}"
    proc = _start_ui_server(port)
    try:
        _wait_for_server(base_url, timeout=90)

        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
            except Exception:
                pytest.skip("Playwright browser not installed")
            page = browser.new_page()
            page.goto(base_url, wait_until="domcontentloaded")

            _navigate_to_workflows(page)

            # Switch to Workflows tab
            page.locator("[data-testid='tab-workflows']").click()
            page.wait_for_timeout(500)

            # Verify workflows view is visible
            workflows_view = page.locator("[data-testid='view-workflows']")
            assert workflows_view.is_visible(), "Workflows view should be visible"

            # Verify mermaid container exists in DOM (may be hidden if no workflow selected)
            mermaid_container = page.locator("[data-testid='mermaid-container']")
            assert mermaid_container.count() == 1, "Mermaid container should exist in DOM"

            # Verify diagram wrapper exists
            diagram_wrapper = page.locator("[data-testid='workflow-diagram']")
            assert diagram_wrapper.count() == 1, "Workflow diagram wrapper should exist"

            browser.close()
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


def test_workflow_ui_no_console_errors():
    """Test that the workflow UI loads without critical JavaScript console errors"""
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        pytest.skip("Playwright not available")

    port = _find_free_port()
    base_url = f"http://127.0.0.1:{port}"
    proc = _start_ui_server(port)
    try:
        _wait_for_server(base_url, timeout=90)

        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
            except Exception:
                pytest.skip("Playwright browser not installed")

            # Capture console messages
            console_errors = []
            page = browser.new_page()
            page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)

            page.goto(base_url, wait_until="domcontentloaded")

            _navigate_to_workflows(page)

            # Navigate through all tabs to exercise the UI
            page.locator("[data-testid='tab-workflows']").click()
            page.wait_for_timeout(500)
            page.locator("[data-testid='tab-training']").click()
            page.wait_for_timeout(500)
            page.locator("[data-testid='tab-skills']").click()
            page.wait_for_timeout(500)
            page.locator("[data-testid='tab-dashboard']").click()
            page.wait_for_timeout(500)

            # Filter out expected/benign errors
            critical_errors = [
                e
                for e in console_errors
                if "404" not in str(e.text)
                and "favicon" not in str(e.text).lower()
                and "mermaid" not in str(e.text).lower()
            ]

            # Fail on critical errors
            assert len(critical_errors) == 0, f"Console errors found: {[e.text for e in critical_errors]}"

            browser.close()
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


def test_workflow_settings_persistence():
    """Test that workflow dashboard can be navigated away from and back without errors"""
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        pytest.skip("Playwright not available")

    port = _find_free_port()
    base_url = f"http://127.0.0.1:{port}"
    proc = _start_ui_server(port)
    try:
        _wait_for_server(base_url, timeout=90)

        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
            except Exception:
                pytest.skip("Playwright browser not installed")
            page = browser.new_page()
            page.goto(base_url, wait_until="domcontentloaded")

            _navigate_to_workflows(page)

            # Verify we're on workflow dashboard
            dashboard = page.locator("[data-testid='workflow-dashboard']")
            assert dashboard.is_visible(), "Dashboard should be visible initially"

            # Switch to Skills tab to change state
            page.locator("[data-testid='tab-skills']").click()
            page.wait_for_timeout(500)

            # Navigate away by closing the dashboard
            page.click(".dashboard-back-btn")
            page.wait_for_timeout(500)

            # Verify workflows dashboard is no longer visible
            assert not dashboard.is_visible(), "Dashboard should not be visible after closing"

            # Navigate back to Workflows
            _navigate_to_workflows(page)

            # Verify dashboard is visible again
            dashboard = page.locator("[data-testid='workflow-dashboard']")
            assert dashboard.is_visible(), "Dashboard should be visible after navigating back"

            # Verify all elements are still present
            assert page.locator("[data-testid='workflow-tabs']").is_visible()
            assert page.locator("[data-testid='refresh-button']").is_visible()

            browser.close()
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
