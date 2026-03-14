from python.helpers.demo_request_store import create_demo_request, list_demo_requests


def test_demo_request_requires_company_and_email_convention(monkeypatch, tmp_path):
    """
    Guardrail test for expected API/tool convention.
    Store layer allows flexible payloads, but callers should provide
    company and email for request validity.
    """
    store_path = tmp_path / "demo_requests.jsonl"
    monkeypatch.setenv("AGENT_JUMBO_DEMO_REQUESTS_PATH", str(store_path))

    record = create_demo_request({"company": "Acme", "email": "ops@acme.example"})
    assert record["company"] == "Acme"
    assert record["email"] == "ops@acme.example"


def test_demo_request_list_limit(monkeypatch, tmp_path):
    store_path = tmp_path / "demo_requests.jsonl"
    monkeypatch.setenv("AGENT_JUMBO_DEMO_REQUESTS_PATH", str(store_path))

    for i in range(5):
        create_demo_request({"company": f"C{i}", "email": f"u{i}@example.com"})

    rows = list_demo_requests(limit=2)
    assert len(rows) == 2
    assert rows[0]["company"] == "C4"
    assert rows[1]["company"] == "C3"
