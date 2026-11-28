from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def read(*parts: str) -> str:
    return (PROJECT_ROOT / Path(*parts)).read_text(encoding="utf-8")


def test_drop_and_picker_paths_route_through_the_shared_gate():
    store_js = read("webui", "components", "chat", "attachments", "attachmentsStore.js")

    assert "async handleFiles(files)" in store_js
    assert "const acceptedFiles = await this.filterOversizedFiles(fileList);" in store_js
    assert store_js.count("this.handleFiles(files);") >= 2


def test_attachment_size_gate_uses_the_shared_limits_helper():
    store_js = read("webui", "components", "chat", "attachments", "attachmentsStore.js")
    helper_js = read("webui", "js", "workdir-file-limits.js")

    assert 'from "/js/workdir-file-limits.js"' in store_js
    assert "fetchWorkDirFileLimits()" in store_js
    assert 'fetchApi("/get_work_dir_files?limits=1")' not in store_js
    assert helper_js.count('fetchApi("/get_work_dir_files?limits=1")') == 1


def test_oversized_attachments_reject_per_file_with_notification():
    store_js = read("webui", "components", "chat", "attachments", "attachmentsStore.js")

    assert "file.size <= limitBytes" in store_js
    assert "toastFrontendError(" in store_js
    assert "exceeds the ${limitBytes / (1024 * 1024)} MiB attachment size limit." in store_js


def test_attachment_size_gate_fails_open_without_limits():
    store_js = read("webui", "components", "chat", "attachments", "attachmentsStore.js")

    assert "skipping the size check" in store_js
    assert "return files;" in store_js
