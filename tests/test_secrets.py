from helpers import secrets


class _Context:
    def get_data(self, key: str):
        return None


def test_agent_secret_manager_masks_runtime_dotenv_values(monkeypatch):
    monkeypatch.setattr(secrets.SecretsManager, "_instances", {})
    monkeypatch.setattr(secrets.dotenv, "get_dotenv_file_path", lambda: "usr/.env")

    contents = {
        "usr/secrets.env": "PROJECT_SECRET=project-value\n",
        "usr/.env": "LLM_API_KEY=llm-secret-value\n",
    }
    monkeypatch.setattr(secrets.files, "read_file", contents.__getitem__)

    manager = secrets.get_secrets_manager(_Context())

    assert manager.mask_values("key=llm-secret-value") == (
        "key=§§secret(LLM_API_KEY)"
    )
