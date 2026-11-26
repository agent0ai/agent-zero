"""Project-scoped native canvas viewer lifecycle."""

import atexit
from contextlib import suppress
from dataclasses import dataclass, field
import grp
import json
import os
from pathlib import Path
import pwd
import shutil
import signal
import socket
import subprocess
import tempfile
from threading import RLock, Timer
import time
import urllib.request
from uuid import uuid4

from helpers import files, login, team_access, team_projects, virtual_desktop
from helpers.file_browser import FileBrowser
from helpers.print_style import PrintStyle
from helpers.team_surface_proxy import ProjectWebProxy


_IDLE_SECONDS = 900
_MAX_VIEWERS = 4
_MODES = {"browser", "desktop"}
_lock = RLock()


@dataclass
class Viewer:
    token: str
    project: str
    project_id: str
    actor_id: str
    mode: str
    directory: Path
    process: subprocess.Popen
    uid: int
    display: int
    port: int
    files_fd: int
    proxy: ProjectWebProxy | None = None
    touched: float = field(default_factory=time.monotonic)
    copies: dict = field(default_factory=dict)

    def authorize(self, session) -> bool:
        scope = team_access.scope_for_session(session.get(login.TEAM_SESSION_KEY))
        if not scope or scope.account_id != self.actor_id or scope.project_ids.get(self.project) != self.project_id:
            return False
        if self.process.poll() is not None:
            return False
        self.touched = time.monotonic()
        return True

    def url(self) -> str:
        return virtual_desktop.session_url(self.token, title=self.mode.title(), printing=False, file_transfer=False)


_viewers: dict[tuple[str, str, str], Viewer] = {}
_reaper: Timer | None = None


def _stop_detached_processes(uid: int):
    for path in Path("/proc").iterdir():
        if not path.name.isdecimal():
            continue
        try:
            if path.stat().st_uid != uid:
                continue
            descriptor = os.pidfd_open(int(path.name))
            try:
                with (path / "status").open() as stream:
                    identity = next(line.split()[1] for line in stream if line.startswith("Uid:"))
                if identity == str(uid):
                    signal.pidfd_send_signal(descriptor, signal.SIGKILL)
            finally:
                os.close(descriptor)
        except (OSError, StopIteration):
            continue


def _stop(viewer: Viewer):
    virtual_desktop.unregister_session(viewer.token)
    with suppress(ProcessLookupError):
        os.killpg(viewer.process.pid, signal.SIGTERM)
    try:
        viewer.process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        with suppress(ProcessLookupError):
            os.killpg(viewer.process.pid, signal.SIGKILL)
        viewer.process.wait(timeout=2)
    _stop_detached_processes(viewer.uid)
    os.close(viewer.files_fd)
    if viewer.proxy:
        viewer.proxy.shutdown()
        viewer.proxy.server_close()
    shutil.rmtree(viewer.directory, ignore_errors=True)


@atexit.register
def _shutdown():
    if _reaper is not None:
        _reaper.cancel()
    for viewer in _viewers.values():
        _stop(viewer)
    _viewers.clear()


def _reap():
    for key, viewer in list(_viewers.items()):
        current_project = team_access.assigned_projects(viewer.actor_id).get(viewer.project)
        expired = time.monotonic() - viewer.touched > _IDLE_SECONDS
        if current_project != viewer.project_id or viewer.process.poll() is not None or expired:
            _viewers.pop(key)
            _stop(viewer)


def _schedule_reaper():
    global _reaper
    if _reaper is None and _viewers:
        _reaper = Timer(60, _reap_idle)
        _reaper.daemon = True
        _reaper.start()


def _reap_idle():
    global _reaper
    with _lock:
        _reaper = None
        _reap()
        _schedule_reaper()


def _local_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _viewer_uid() -> int:
    if os.geteuid() != 0 or not Path("/.dockerenv").is_file():
        raise RuntimeError("Project viewers require the team Docker runtime.")
    in_use = {viewer.uid for viewer in _viewers.values()}
    for uid in range(63100, 63200):
        if uid in in_use:
            continue
        name = f"a0-viewer-{uid}"
        try:
            group = grp.getgrgid(uid)
        except KeyError:
            subprocess.run(["/usr/sbin/groupadd", "-g", str(uid), name], check=True, capture_output=True, timeout=5)
        else:
            if group.gr_name != name:
                continue
        try:
            user = pwd.getpwuid(uid)
        except KeyError:
            subprocess.run([
                "/usr/sbin/useradd", "--uid", str(uid), "--gid", str(uid), "--no-create-home", "--no-log-init",
                "--home-dir", "/nonexistent", "--shell", "/usr/sbin/nologin", name,
            ], check=True, capture_output=True, timeout=5)
        else:
            if (user.pw_name, user.pw_gid, user.pw_shell) != (name, uid, "/usr/sbin/nologin"):
                continue
        return uid
    raise RuntimeError("No isolated viewer account is available.")


def _launch(project, project_id, actor, mode):
    try:
        uid = _viewer_uid()
    except subprocess.SubprocessError as error:
        raise RuntimeError("The isolated viewer account could not be created.") from error
    root = Path(files.get_abs_path("tmp", "team-surfaces"))
    root.mkdir(mode=0o711, parents=True, exist_ok=True)
    for path in ("/tmp/.X11-unix", "/var/lib/xkb"):
        scratch = Path(path)
        scratch.mkdir(exist_ok=True, mode=0o1777)
        if scratch.is_symlink() or scratch.stat().st_uid != 0:
            raise RuntimeError("The display scratch directory is unavailable.")
        scratch.chmod(0o1777)
    directory = Path(tempfile.mkdtemp(prefix="viewer-", dir=root))
    directory.chmod(0o711)
    home = directory / "home"
    control = directory / "control"
    control.mkdir(mode=0o755)
    display = next(number for number in range(600, 900)
                   if all(viewer.display != number for viewer in _viewers.values())
                   and not Path(f"/tmp/.X{number}-lock").exists()
                   and not Path(f"/tmp/.X11-unix/X{number}").exists())
    for location in (home, home / "run", home / "Files"):
        location.mkdir(mode=0o700)
        os.chown(location, uid, uid)
    file_dir = os.open(home / "Files", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    port = _local_port()
    proxy = None
    try:
        chrome = ""
        if mode == "browser":
            candidates = sorted(Path(files.get_abs_path("tmp", "playwright")).glob("chromium-*/chrome-linux64/chrome"))
            if not candidates:
                raise RuntimeError("The bundled Chromium is unavailable.")
            chrome = str(candidates[-1])
            proxy = ProjectWebProxy()
        with (directory / "viewer.log").open("wb") as log:
            process = subprocess.Popen(
                [
                    "/usr/bin/python3", files.get_abs_path("helpers", "team_surface_sandbox.py"), mode, str(uid),
                    str(port), str(display), str(control), chrome,
                    str(proxy.server_address[1]) if proxy else "0",
                ],
                cwd=home,
                env={
                    "HOME": str(home), "PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "USER": f"a0-viewer-{uid}",
                    "TMPDIR": str(home / "run"), "XDG_RUNTIME_DIR": str(home / "run"),
                    "XAUTHORITY": str(home / ".Xauthority"), "GSETTINGS_BACKEND": "memory",
                },
                stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True,
            )
    except BaseException:
        os.close(file_dir)
        if proxy:
            proxy.shutdown()
            proxy.server_close()
        shutil.rmtree(directory, ignore_errors=True)
        raise
    viewer = Viewer(uuid4().hex, project, project_id, actor, mode, directory, process, uid, display, port, file_dir, proxy)
    deadline = time.monotonic() + 15
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        while process.poll() is None and time.monotonic() < deadline:
            try:
                with opener.open(f"http://127.0.0.1:{port}/index.html", timeout=0.6) as response:
                    if response.status == 200:
                        break
            except OSError:
                time.sleep(0.2)
        else:
            raise RuntimeError("The isolated viewer could not start.")
        virtual_desktop.register_session(
            token=viewer.token, host="127.0.0.1", port=port, title=mode.title(), owner="team-project",
            authorize=viewer.authorize,
        )
        return viewer
    except BaseException:
        try:
            PrintStyle.warning((directory / "viewer.log").read_text(errors="replace")[-2200:])
        except OSError:
            pass
        _stop(viewer)
        raise


def _send_path(viewer, filename):
    command = viewer.directory / "control" / "open.json"
    with tempfile.NamedTemporaryFile(dir=command.parent, delete=False, mode="w") as pending:
        try:
            json.dump({"id": uuid4().hex, "path": filename}, pending)
            pending.flush()
            os.fchmod(pending.fileno(), 0o644)
            os.replace(pending.name, command)
        finally:
            Path(pending.name).unlink(missing_ok=True)


def _open(viewer, path):
    parts = team_projects.file_parts(path)
    if path not in viewer.copies:
        filename = f"{uuid4().hex[:10]}-{parts[-1]}"
        with team_projects.open_directory(viewer.project, "workspace", parts[:-1]) as directory:
            with team_projects.open_file(directory, parts[-1]) as source:
                target = Path(f"/proc/self/fd/{viewer.files_fd}") / filename
                receipt = team_projects.write_stream_atomic(source, target, max_bytes=FileBrowser.max_file_bytes())
                os.chown(filename, viewer.uid, viewer.uid, dir_fd=viewer.files_fd, follow_symlinks=False)
        viewer.copies[path] = (filename, receipt["sha256"])
    _send_path(viewer, viewer.copies[path][0])


def _save(viewer, path):
    if viewer.mode != "desktop" or path not in viewer.copies:
        raise ValueError("Open the project document in Desktop first.")
    parts = team_projects.file_parts(path)
    filename, revision = viewer.copies[path]
    with team_projects.open_directory(viewer.project, "workspace", parts[:-1]) as target:
        with team_projects.open_file(viewer.files_fd, filename) as source:
            result = team_projects._save_stream(target, parts[-1], source, revision, FileBrowser.max_file_bytes())
    viewer.copies[path] = (filename, result["revision"])


def operation(scope, project, mode, action, path=""):
    if mode not in _MODES or action not in {"open", "save", "close"}:
        raise ValueError("Unknown project surface action.")
    with team_projects.project_lock(project, scope) as project_id, _lock:
        _reap()
        key = (scope.account_id, project_id, mode)
        viewer = _viewers.get(key)
        if action == "close":
            if viewer is not None:
                _viewers.pop(key)
                _stop(viewer)
            return {"ok": True}
        if viewer is None:
            if action == "save":
                raise ValueError("Open the project document in Desktop first.")
            if len(_viewers) >= _MAX_VIEWERS:
                raise RuntimeError("The local viewer capacity is in use.")
            viewer = _viewers[key] = _launch(project, project_id, scope.account_id, mode)
            _schedule_reaper()
        viewer.touched = time.monotonic()
        if path:
            with team_projects.activity(f"surface.{mode}.{action}", scope.account_id, project_id):
                if action == "save":
                    _save(viewer, path)
                else:
                    _open(viewer, path)
        return {"ok": True, "url": viewer.url()}
