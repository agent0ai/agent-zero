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


def test_refresh_keeps_platform_pins(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    requirements = tmp_path / "requirements.txt"
    original = 'pkg==1; sys_platform == "linux"\npkg==2; sys_platform != "linux"\n'
    original += "openai==2.54.0\nlitellm==1.108.12\n"
    requirements.write_text(original + "other==1\n")
    monkeypatch.setattr(update_reqs, "get_installed_version", lambda _: "3")
    update_reqs.update_requirements()
    assert requirements.read_text() == original + "other==3\n"
