from pathlib import Path
import shutil
import subprocess

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def read(*parts: str) -> str:
    return PROJECT_ROOT.joinpath(*parts).read_text(encoding="utf-8")


def extract_js_function(source: str, name: str) -> str:
    start = source.find(f"function {name}(")
    if start < 0:
        raise AssertionError(f"Could not find JavaScript function: {name}")
    brace = source.find("{", start)
    if brace < 0:
        raise AssertionError(f"Could not find opening brace for JavaScript function: {name}")
    depth = 0
    quote = ""
    escape = False
    line_comment = False
    block_comment = False
    regex_literal = False
    regex_char_class = False
    index = brace

    while index < len(source):
        char = source[index]
        next_char = source[index + 1] if index + 1 < len(source) else ""

        if line_comment:
            line_comment = char != "\n"
        elif block_comment:
            if char == "*" and next_char == "/":
                block_comment = False
                index += 1
        elif regex_literal:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == "[":
                regex_char_class = True
            elif char == "]":
                regex_char_class = False
            elif char == "/" and not regex_char_class:
                regex_literal = False
        elif quote:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == quote:
                quote = ""
        elif char == "/" and next_char == "/":
            line_comment = True
            index += 1
        elif char == "/" and next_char == "*":
            block_comment = True
            index += 1
        elif char == "/" and previous_non_space(source, index) in {"=", "(", ",", ":"}:
            regex_literal = True
            regex_char_class = False
        elif char in {"'", '"', "`"}:
            quote = char
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[start:index + 1]

        index += 1

    raise AssertionError(f"Could not find complete JavaScript function: {name}")


def previous_non_space(source: str, index: int) -> str:
    cursor = index - 1
    while cursor >= 0 and source[cursor].isspace():
        cursor -= 1
    return source[cursor] if cursor >= 0 else ""


def test_notification_store_supports_persistent_grouped_toasts():
    store = read("webui", "components", "notifications", "notification-store.js")
    api = read("api", "notification_create.py")

    assert "isPersistentToast(toast)" in store
    assert "return this.getToastDisplayTime(toast) <= 0;" in store
    assert store.count("if (this.isPersistentToast(toast)) return;") >= 2
    assert "this.restartToastTimer(toast.toastId);" in store
    assert "this.removeFromToastStack(existingToast.toastId);" in store
    assert "if display_time < 0:" in api
    assert "if display_time <= 0:" not in api


def test_backup_zip_downloads_emit_grouped_preparing_and_downloading_toasts():
    store = read("webui", "components", "settings", "backup", "backup-store.js")

    assert 'window.toastFrontendInfo?.("Preparing download...", "Download", 0, group, undefined, true);' in store
    assert 'window.toastFrontendInfo?.("Downloading...", "Download", 3, group, undefined, true);' in store
    assert 'window.toastFrontendError?.(message || "Download failed", "Download Error", 8, group, undefined, true);' in store
    assert 'this.createDownloadToastGroup("backup-create")' in store
    assert 'this.createDownloadToastGroup("backup-download")' in store

    create_start = store.index("async createBackup()")
    create_prepare = store.index("this.showDownloadPreparingToast(downloadToastGroup);", create_start)
    create_fetch = store.index("const response = await fetchApi('/backup_create'", create_start)
    assert create_prepare < create_fetch

    download_start = store.index("async downloadBackup")
    download_prepare = store.index("this.showDownloadPreparingToast(downloadToastGroup);", download_start)
    download_fetch = store.index("const response = await fetchApi('/backup_download'", download_start)
    assert download_prepare < download_fetch


def test_file_browser_zip_downloads_emit_grouped_preparing_and_downloading_toasts():
    store = read("webui", "components", "modals", "file-browser", "file-browser-store.js")

    assert 'window.toastFrontendInfo?.("Preparing download...", "Download", 0, group, undefined, true);' in store
    assert 'window.toastFrontendInfo?.("Downloading...", "Download", 3, group, undefined, true);' in store
    assert 'this.createDownloadToastGroup("file-browser-bulk-download")' in store
    assert 'this.createDownloadToastGroup("file-browser-directory-download")' in store
    assert "if (file.is_dir) {" in store
    assert "return this.downloadDirectory(file);" in store
    assert "link.download = file.name;" in store

    bulk_start = store.index("async bulkDownloadFiles()")
    bulk_prepare = store.index("this.showDownloadPreparingToast(downloadToastGroup);", bulk_start)
    bulk_fetch = store.index('const resp = await fetchApi("/download_work_dir_files"', bulk_start)
    assert bulk_prepare < bulk_fetch

    directory_start = store.index("async downloadDirectory(file)")
    directory_prepare = store.index("this.showDownloadPreparingToast(downloadToastGroup);", directory_start)
    directory_fetch = store.index("const resp = await fetchApi(`/download_work_dir_file", directory_start)
    assert directory_prepare < directory_fetch


def test_message_path_links_keep_spaces_in_file_names():
    # This regression executes convertPathsToLinks with Node.js to catch browser-path parsing drift.
    if not shutil.which("node"):
        pytest.skip("Node.js is required to execute the message path-linking regression.")

    messages = read("webui", "js", "messages.js")
    function_source = extract_js_function(messages, "convertPathsToLinks")

    script = f"""
{function_source}

function assertIncludes(value, expected) {{
  if (!value.includes(expected)) {{
    throw new Error(`Expected ${{JSON.stringify(value)}} to include ${{JSON.stringify(expected)}}`);
  }}
}}

function assertNotIncludes(value, expected) {{
  if (value.includes(expected)) {{
    throw new Error(`Expected ${{JSON.stringify(value)}} not to include ${{JSON.stringify(expected)}}`);
  }}
}}

const spaced = convertPathsToLinks("Location: /a0/usr/workdir/New Document.md");
assertIncludes(spaced, 'data-path="/a0/usr/workdir/New Document.md"');
assertIncludes(spaced, '>New Document.md</a>');
assertNotIncludes(spaced, '>New</a> Document.md');

const sentence = convertPathsToLinks("Saved at /a0/usr/workdir/New Document.md and ready.");
assertIncludes(sentence, 'data-path="/a0/usr/workdir/New Document.md"');
assertNotIncludes(sentence, 'and ready</a>');

const directory = convertPathsToLinks("Directory: /a0/usr/workdir is ready");
assertIncludes(directory, 'data-path="/a0/usr/workdir"');
"""
    subprocess.run(["node", "-e", script], check=True, text=True)
