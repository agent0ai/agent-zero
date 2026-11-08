import importlib.metadata
import update_reqs


def test_version_lookup_does_not_require_setuptools(monkeypatch):
    def version(name):
        if name == "missing":
            raise importlib.metadata.PackageNotFoundError(name)
        return "1.2.3"
    monkeypatch.setattr(update_reqs.importlib.metadata, "version", version)
    assert update_reqs.get_installed_version("installed") == "1.2.3"
    assert update_reqs.get_installed_version("missing") is None
