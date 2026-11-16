"""Exercise update hooks with real Git checkouts and hook subprocesses."""
import importlib.util
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch
import zipfile


MANAGER = Path(__file__).resolve().parents[1] / "docker/run/fs/exe/self_update_manager.py"


class UpdateHookTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        spec = importlib.util.spec_from_file_location("update_hooks_test_manager", MANAGER)
        self.manager = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.manager)
        self.manager.REPO_DIR = self.repo
        self.manager.STATUS_FILE = self.root / "status.yaml"
        self.manager.LOG_FILE = self.root / "update.log"
        self.manager.TRIGGER_FILE = self.root / "request.yaml"
        self.runtime = self.root / "self_update_manager.py"
        self.runtime.write_bytes(MANAGER.read_bytes())
        self.manager.__file__ = str(self.runtime)
        self.logger = self.manager.AttemptLogger(self.manager.LOG_FILE)
        self.logger.reset()
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.name", "Update test")
        self.git("config", "user.email", "update@example.invalid")
        (self.repo / ".gitignore").write_text("usr/\n__pycache__/\n")
        (self.repo / "release.txt").write_text("old")
        (self.repo / "usr").mkdir()
        (self.repo / "usr/user.txt").write_text("keep me")
        self.git("add", ".")
        self.git("commit", "-qm", "old release")
        self.git("tag", "v3.0")
        self.old = self.git("rev-parse", "HEAD")
        self.request = {
            "branch": "main", "tag": "v3.1", "backup_usr": True,
            "backup_path": str(self.root / "backups"), "backup_name": "usr.zip",
        }

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.repo), *args], text=True).strip()

    def release(self, hooks):
        (self.repo / "release.txt").write_text("new")
        for name, content in hooks.items():
            path = self.repo / "docker/run/update" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        self.git("add", ".")
        self.git("commit", "-qm", "new release")
        self.git("tag", "v3.1")
        self.new = self.git("rev-parse", "HEAD")
        remote = self.root / "remote.git"
        subprocess.run(["git", "clone", "-q", "--bare", str(self.repo), str(remote)], check=True)
        self.manager.OFFICIAL_REPO_URL = str(remote)
        self.git("checkout", "-q", "-B", "main", self.old)

    def execute(self, healthy=True):
        launches = []

        def launch(*args):
            launches.append((self.repo / "release.txt").read_text())
            return Mock()

        with patch.object(self.manager, "launch_ui_process", side_effect=launch), \
             patch.object(self.manager, "wait_for_health", side_effect=[(healthy, "health result"), (True, {})]), \
             patch.object(self.manager, "terminate_process"), \
             patch.object(self.manager, "refresh_codex_cli"):
            self.manager.execute_pending_update(self.request, logger=self.logger)
        return self.manager.load_yaml(self.manager.STATUS_FILE), launches

    def event_script(self, label):
        return (
            "import os\nfrom pathlib import Path\n"
            "with Path('usr/events').open('a') as f:\n"
            f"    f.write({label!r} + ':' + Path('release.txt').read_text() + ':' + "
            "os.environ['A0_UPDATE_SOURCE_VERSION'] + ':' + os.environ['A0_UPDATE_TARGET_VERSION'] + '\\n')\n"
            f"print({label!r}, flush=True)\n"
        )

    def test_target_hooks_run_in_order_around_checkout_and_preserve_user_data(self):
        self.release({
            "before/20_second.py": self.event_script("second"),
            "before/10_first.py": self.event_script("first"),
            "after/10_system.sh": "set -eu\ntest \"$(cat release.txt)\" = new\necho shell >> usr/events\n",
            "after/20_last.py": self.event_script("last"),
        })
        # Untracked hook files must not execute, even when they have an earlier name.
        local = self.repo / "docker/run/update/before/00_local.py"
        local.parent.mkdir(parents=True)
        local.write_text("raise RuntimeError('untrusted local hook')")
        result, launches = self.execute()
        self.assertEqual(result["status"], "success")
        self.assertEqual(launches, ["new"])
        self.assertEqual((self.repo / "usr/events").read_text().splitlines(), [
            "first:old:v3.0:v3.1", "second:old:v3.0:v3.1", "shell", "last:new:v3.0:v3.1",
        ])
        self.assertEqual((self.repo / "usr/user.txt").read_text(), "keep me")
        with zipfile.ZipFile(result["backup_zip_path"]) as backup:
            self.assertEqual(backup.read("usr/user.txt"), b"keep me")
            self.assertNotIn("usr/events", backup.namelist())
        self.assertIn("first", self.manager.LOG_FILE.read_text())

    def test_before_failure_aborts_and_restores_local_changes(self):
        self.release({"before/10_fail.py": "raise RuntimeError('system check failed')\n"})
        (self.repo / "release.txt").write_text("local changes")
        result, launches = self.execute()
        self.assertEqual(result["status"], "failed")
        self.assertEqual(self.git("rev-parse", "HEAD"), self.old)
        self.assertEqual(launches, ["local changes"])
        self.assertIn("before/10_fail.py", result["error"])

    def test_after_failure_rolls_back_before_launching_ui(self):
        self.release({"after/10_fail.sh": "echo failed-check\nexit 7\n"})
        result, launches = self.execute()
        self.assertEqual(result["status"], "rolled_back")
        self.assertEqual(launches, ["old"])
        self.assertEqual(self.git("rev-parse", "HEAD"), self.old)
        self.assertIn("failed-check", self.manager.LOG_FILE.read_text())

    def test_health_failure_rolls_back_without_running_hooks_again(self):
        self.release({"after/10_record.py": self.event_script("after")})
        result, launches = self.execute(healthy=False)
        self.assertEqual(result["status"], "rolled_back")
        self.assertEqual(launches, ["new", "old"])
        self.assertEqual((self.repo / "usr/events").read_text(), "after:new:v3.0:v3.1\n")

    def test_release_without_hooks_works(self):
        self.release({})
        result, launches = self.execute()
        self.assertEqual(result["status"], "success")
        self.assertEqual(launches, ["new"])

    def test_hook_timeout_aborts_update(self):
        self.release({"before/10_slow.py": (
            "import subprocess, sys, time\nfrom pathlib import Path\n"
            "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])\n"
            "Path('usr/child-pid').write_text(str(child.pid))\ntime.sleep(60)\n"
        )})
        self.manager.UPDATE_HOOK_TIMEOUT_SECONDS = 0.5
        result, launches = self.execute()
        self.assertEqual(result["status"], "failed")
        self.assertIn("timed out", result["error"])
        self.assertEqual(launches, ["old"])
        pid = (self.repo / "usr/child-pid").read_text()
        status = Path(f"/proc/{pid}/stat")
        if status.exists():
            self.assertIn(status.read_text().split()[2], {"Z", "X"})

    def test_symlink_hook_is_rejected(self):
        self.release({"before/10_link.py": "pass\n"})
        self.git("checkout", "-q", "-B", "main", self.new)
        path = self.repo / "docker/run/update/before/10_link.py"
        path.unlink()
        path.symlink_to("/tmp/untrusted.py")
        self.git("add", ".")
        self.git("commit", "-qm", "symlink hook")
        target = {"expected_commit": self.git("rev-parse", "HEAD"), "expected_short_tag": "v3.1"}
        with self.assertRaisesRegex(RuntimeError, "regular file"):
            self.manager.run_update_hooks("before", {"commit": self.old, "short_tag": "v3.0"}, target, self.logger)

    def test_invalid_replacement_never_overwrites_runtime(self):
        original = self.runtime.read_bytes()
        for source in ("invalid python!", "raise RuntimeError('cannot import')", "def execute_pending_update(data): pass"):
            with self.subTest(source=source):
                candidate = self.root / "candidate.py"
                candidate.write_text(source)
                with self.assertRaises((SyntaxError, RuntimeError, TypeError)):
                    self.manager.replace_update_manager(candidate, self.logger)
                self.assertEqual(self.runtime.read_bytes(), original)
                self.assertFalse(self.runtime.with_name(self.runtime.name + ".before-update-backup").exists())

    def test_replacement_preserves_mode_and_can_restore(self):
        original = self.runtime.read_bytes()
        self.runtime.chmod(0o750)
        candidate = self.root / "candidate.py"
        candidate.write_text("def execute_pending_update(data, *, logger, prepared=None): return 'new updater'\n")
        replacement, backup = self.manager.replace_update_manager(candidate, self.logger)
        self.assertEqual(replacement.execute_pending_update({}, logger=self.logger, prepared={}), "new updater")
        self.assertEqual(backup.read_bytes(), original)
        self.assertEqual(self.runtime.stat().st_mode & 0o777, 0o750)
        self.manager.restore_update_manager(backup, self.logger)
        self.assertEqual(self.runtime.read_bytes(), original)

    def test_unexpected_replacement_failure_restores_checkout_and_updater(self):
        original = self.runtime.read_bytes()
        candidate = (
            "import subprocess\n"
            "def execute_pending_update(data, *, logger, prepared=None):\n"
            f"    subprocess.run(['git', '-C', {str(self.repo)!r}, 'checkout', '-B', 'main', "
            "prepared['resolved_target']['expected_commit']], check=True)\n"
            "    raise RuntimeError('replacement failed unexpectedly')\n"
        )
        self.release({"before/10_replace.py": (
            "import os\nfrom pathlib import Path\n"
            f"Path(os.environ['A0_UPDATE_UPDATER_CANDIDATE']).write_text({candidate!r})\n"
        )})
        result, launches = self.execute()
        self.assertEqual(result["status"], "rolled_back")
        self.assertEqual(launches, ["old"])
        self.assertEqual(self.runtime.read_bytes(), original)
        self.assertEqual(self.git("rev-parse", "HEAD"), self.old)

    def test_critical_replacement_continues_same_attempt_and_rolls_back_on_failure(self):
        self.check_critical_replacement("after")

    def test_critical_replacement_is_restored_on_health_failure(self):
        self.check_critical_replacement("health")

    def test_critical_replacement_is_retained_on_success(self):
        self.check_critical_replacement(None)

    def check_critical_replacement(self, failure):
        original = self.runtime.read_bytes()
        # Use the real updater, with only UI startup/health replaced for this isolated fixture.
        candidate = MANAGER.read_text().split('if __name__ == "__main__":')[0]
        candidate += f"\nREPO_DIR = Path({str(self.repo)!r})\nSTATUS_FILE = Path({str(self.manager.STATUS_FILE)!r})\n"
        candidate += "\ndef launch_ui_process(*args): return None\n"
        candidate += "def terminate_process(*args): pass\n"
        candidate += "def refresh_codex_cli(*args): pass\n"
        candidate += (
            "def wait_for_health(*args, **kwargs): return (REPO_DIR / 'release.txt').read_text() == 'old', 'health result'\n"
            if failure == "health" else "def wait_for_health(*args, **kwargs): return True, {}\n"
        )
        self.release({
            "before/10_replace.py": self.event_script("before") +
                f"Path(os.environ['A0_UPDATE_UPDATER_CANDIDATE']).write_text({candidate!r})\n",
            "after/10_check.py": self.event_script("after") +
                ("raise RuntimeError('after failed')\n" if failure == "after" else ""),
        })
        result, launches = self.execute()
        self.assertEqual(result["status"], "rolled_back" if failure else "success")
        self.assertEqual(launches, [])  # The replacement performed checkout/rollback/startup.
        self.assertEqual(self.runtime.read_bytes(), original if failure else candidate.encode())
        self.assertEqual(self.git("rev-parse", "HEAD"), self.old if failure else self.new)
        self.assertEqual((self.repo / "usr/events").read_text().splitlines(), [
            "before:old:v3.0:v3.1", "after:new:v3.0:v3.1",
        ])
        self.assertEqual(len(list((self.root / "backups").iterdir())), 1)

    def test_real_ui_process_becomes_healthy_after_hooks(self):
        (self.repo / "run_ui.py").write_text('''
import json, os, subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args): pass
    def do_GET(self):
        payload = {'gitinfo': {
            'short_tag': subprocess.check_output(['git', 'describe', '--tags', '--abbrev=0'], text=True).strip(),
            'commit_hash': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
        }}
        self.send_response(200)
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode())
HTTPServer(('127.0.0.1', int(os.environ['A0_TEST_UI_PORT'])), Handler).serve_forever()
''')
        (self.repo / "prepare.py").write_text(
            "from pathlib import Path\nassert Path('usr/events').read_text() == 'after:new:v3.0:v3.1\\n'\n"
        )
        self.release({"after/10_system.py": self.event_script("after")})
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        self.manager.DEFAULT_HEALTH_URL = f"http://127.0.0.1:{port}/api/health"
        self.manager.DEFAULT_HEALTH_TIMEOUT_SECONDS = 5
        self.manager.DEFAULT_HEALTH_POLL_INTERVAL_SECONDS = 0.02
        with patch.dict(os.environ, {"A0_TEST_UI_PORT": str(port)}), \
             patch.object(self.manager, "refresh_codex_cli"):
            process = self.manager.execute_pending_update(self.request, logger=self.logger)
            try:
                result = self.manager.load_yaml(self.manager.STATUS_FILE)
                self.assertEqual(result["status"], "success")
                self.assertIsNone(process.poll())
            finally:
                self.manager.terminate_process(process)


if __name__ == "__main__":
    unittest.main()
