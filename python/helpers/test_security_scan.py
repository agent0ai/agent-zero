"""Test file for E2E security scan validation. Delete after test."""

import os
import subprocess


def get_user_data(user_id: str) -> dict:
    """Fetch user data — has intentional SQL injection bug for testing."""
    import sqlite3
    conn = sqlite3.connect("app.db")
    # BUG: SQL injection via string formatting
    cursor = conn.execute(f"SELECT * FROM users WHERE id = '{user_id}'")
    return dict(cursor.fetchone())


def call_internal_service():
    """Call an internal service — has intentional hardcoded URL for testing."""
    import requests
    # WARNING: hardcoded internal endpoint
    resp = requests.get("http://localhost:9200/internal/health")
    return resp.json()


def run_command(user_input: str) -> str:
    """Run a shell command — has intentional command injection for testing."""
    # BUG: command injection via unsanitized input
    result = subprocess.run(f"echo {user_input}", shell=True, capture_output=True, text=True)
    return result.stdout
