from python.helpers.demo_request_store import create_demo_request, list_demo_requests


def test_create_and_list_demo_requests(monkeypatch, tmp_path):
    store_path = tmp_path / "demo_requests.jsonl"
    monkeypatch.setenv("AGENT_JUMBO_DEMO_REQUESTS_PATH", str(store_path))

    create_demo_request(
        {
            "company": "Acme",
            "email": "ops@acme.example",
            "industry": "healthcare",
        }
    )
    create_demo_request(
        {
            "company": "Beta",
            "email": "team@beta.example",
            "industry": "finance",
        }
    )

    rows = list_demo_requests(limit=10)
    assert len(rows) == 2
    assert rows[0]["company"] == "Beta"
    assert rows[1]["company"] == "Acme"
    assert "id" in rows[0]
    assert "created_at" in rows[0]
