import os
import socket
import subprocess
import sys
import time
import urllib.request

import pytest


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _wait_for_server(url: str, timeout: float = 60.0) -> None:
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


def test_observability_workflow_ui_smoke():
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

            page.click("button#settings")
            page.click(".settings-tab:has-text('Developer')")
            page.wait_for_selector("text=External observability provider", timeout=10000)
            page.click("button:has-text('Open Observability')")

            page.wait_for_selector("text=Workflow Runs", timeout=10000)
            page.wait_for_selector("text=Save Run", timeout=10000)

            browser.close()
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
