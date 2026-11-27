import importlib
from types import SimpleNamespace
from unittest.mock import Mock
import pytest

migration = importlib.import_module('extensions.python.startup_migration._26_retire_outer_features')


def test_retirement_preserves_documents_sessions_and_defers_unsaved_gui(monkeypatch, tmp_path):
    monkeypatch.setattr(migration.PrintStyle, 'warning', Mock())
    monkeypatch.setattr(migration.importlib.metadata, 'distributions', lambda: [])
    def absent(name):
        raise migration.importlib.metadata.PackageNotFoundError(name)
    monkeypatch.setattr(migration.importlib.metadata, 'version', absent)
    monkeypatch.setattr(migration.files, '_base_dir', str(tmp_path))
    monkeypatch.setattr(migration.os, 'geteuid', lambda: 0)
    monkeypatch.setattr(migration.shutil, 'which', lambda _: '/fixture')
    monkeypatch.setattr(migration.psutil, 'process_iter', lambda _: [SimpleNamespace(info={'name':'soffice.bin'})])
    apt = Mock()
    monkeypatch.setattr(migration.system_packages, 'run_runtime_apt', apt)
    caches = ['tmp/playwright', 'usr/plugins/_browser/playwright', 'usr/browser/playwright',
              'plugins/_whatsapp_integration/whatsapp-bridge/node_modules']
    for name in caches:
        cache = tmp_path / name
        cache.mkdir(parents=True)
        (cache / 'installed').touch()
    preserved = ['usr/plugins/_office/documents/history', 'tmp/browser/sessions/shared/cookie',
                 'tmp/whatsapp/session/creds.json', 'usr/downloads/browser/document',
                 'usr/plugins/_browser/other/keep']
    for name in preserved:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('keep')
    migration.retire()
    migration.retire()
    apt.assert_not_called()
    assert all(not (tmp_path / name).exists() for name in caches)
    assert all((tmp_path / name).read_text() == 'keep' for name in preserved)


def test_retirement_skips_linked_cache_and_parent(monkeypatch, tmp_path):
    monkeypatch.setattr(migration, 'PYTHON_PACKAGES', ())
    monkeypatch.setattr(migration, 'unused_scrapers', lambda: set())
    monkeypatch.setattr(migration.files, '_base_dir', str(tmp_path))
    monkeypatch.setattr(migration.os, 'geteuid', lambda: 1000)
    personal = tmp_path / 'personal'
    (personal / 'playwright').mkdir(parents=True)
    document = personal / 'playwright/document'
    document.write_text('keep')
    for relative in ('tmp/playwright', 'usr/browser'):
        link = tmp_path / relative
        link.parent.mkdir()
        link.symlink_to(personal, target_is_directory=True)

    migration.retire()

    assert (tmp_path / 'tmp/playwright').is_symlink()
    assert (tmp_path / 'usr/browser').is_symlink()
    assert document.read_text() == 'keep'


def test_service_retirement_restores_config_on_control_failure(monkeypatch, tmp_path):
    path = tmp_path / 'office.conf'; path.write_text('fixture config')
    monkeypatch.setattr(migration.shutil, 'which', lambda _: '/fixture')
    monkeypatch.setattr(migration.subprocess, 'run', Mock(side_effect=RuntimeError('fixture failure')))
    with pytest.raises(RuntimeError): migration.retire_service(path)
    assert path.read_text() == 'fixture config'
    monkeypatch.setattr(migration.subprocess, 'run', Mock())
    migration.retire_service(path)
    migration.retire_service(path)
    assert not path.exists() and path.with_suffix('.conf.before-tuxee').read_text() == 'fixture config'


def test_unused_scrapers_preserve_installed_consumers_and_their_dependencies(monkeypatch):
    def distribution(name, *requires):
        return SimpleNamespace(metadata={'Name': name}, requires=requires)
    packages = [
        distribution('custom-consumer', 'tldextract>=5'),
        distribution('tldextract', 'requests-file>=1', 'requests'),
        distribution('requests-file', 'requests'),
        distribution('requests'),
        distribution('newspaper3k', 'tldextract', 'jieba3k', 'cssselect', 'nltk'),
        distribution('jieba3k'), distribution('cssselect'), distribution('nltk'),
        distribution('pyreqwest_impersonate'),
        distribution('lxml', 'cssselect; extra == "cssselect"'),
    ]
    monkeypatch.setattr(migration.importlib.metadata, 'distributions', lambda: packages)
    assert migration.unused_scrapers() == {'newspaper3k', 'jieba3k', 'pyreqwest-impersonate'}
    packages.append(distribution('another-consumer', 'newspaper3k'))
    assert migration.unused_scrapers() == {'pyreqwest-impersonate'}


def test_browser_and_scraper_uninstall_is_scoped_and_idempotent(monkeypatch, tmp_path):
    packages = [SimpleNamespace(metadata={'Name': name}, requires=[]) for name in
                ('newspaper3k', 'jieba3k', 'pyreqwest-impersonate', 'patchright', 'playwright', 'Pillow', 'nltk')]
    monkeypatch.setattr(migration.importlib.metadata, 'distributions', lambda: packages)
    def version(name):
        if any(p.metadata['Name'] == name for p in packages):
            return '1.0'
        raise migration.importlib.metadata.PackageNotFoundError(name)
    monkeypatch.setattr(migration.importlib.metadata, 'version', version)
    monkeypatch.setattr(migration.files, '_base_dir', str(tmp_path))
    monkeypatch.setattr(migration.os, 'geteuid', lambda: 1000)
    calls = []
    def uninstall(command, **kwargs):
        calls.append(command)
        packages[:] = [p for p in packages if p.metadata['Name'] not in command[5:]]
    monkeypatch.setattr(migration.subprocess, 'run', uninstall)
    migration.retire()
    migration.retire()
    assert calls == [['uv', 'pip', 'uninstall', '--python', migration.sys.executable,
                      'jieba3k', 'newspaper3k', 'pyreqwest-impersonate', 'patchright', 'playwright']]
    assert {p.metadata['Name'] for p in packages} == {'Pillow', 'nltk'}
