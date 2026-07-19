from collections import deque
import json
import os
import queue
import re
import shutil
import subprocess
import threading
import time
import urllib.parse
import urllib.request
from pathlib import Path

from flaredantic import NotifyEvent

from helpers import cli_tunnel, files
from helpers.cli_tunnel import CliTunnelHelper


TAILSCALE_URL_RE = re.compile(r"https://[a-zA-Z0-9.-]+\.ts\.net[^\s\"']*")
TAILSCALE_LOGIN_URL_RE = re.compile(r"https://login\.tailscale\.com/[^\s\"']+")
TAILSCALE_STABLE_PACKAGES_URL = "https://pkgs.tailscale.com/stable/?v=latest"
TAILSCALE_UP_TIMEOUT = 180
TAILSCALE_FUNNEL_TIMEOUT = 300
TAILSCALE_FUNNEL_HTTPS_PORT = "443"
TAILSCALE_DAEMON_START_TIMEOUT = 12
TAILSCALE_RUNTIME_DIR = Path(files.get_abs_path("tmp", "tailscale"))
TAILSCALE_STATE_DIR = Path(files.get_abs_path("usr", "tailscale"))
TAILSCALE_SOCKET_PATH = TAILSCALE_RUNTIME_DIR / "tailscaled.sock"
TAILSCALE_DAEMON_LOG_PATH = TAILSCALE_RUNTIME_DIR / "tailscaled.log"
TAILSCALE_DAEMON_PID_PATH = TAILSCALE_RUNTIME_DIR / "tailscaled.pid"


def tailscale_arch():
    _, arch = cli_tunnel.platform_parts()
    return arch


def tailscale_archive_url():
    arch = tailscale_arch()
    with urllib.request.urlopen(TAILSCALE_STABLE_PACKAGES_URL, timeout=30) as response:
        html = response.read().decode("utf-8", errors="replace")
    pattern = re.compile(rf'href="([^"]*tailscale_[^"]+_{re.escape(arch)}\.tgz)"')
    match = pattern.search(html)
    if not match:
        raise RuntimeError(f"Could not find a Tailscale static binary for {arch}.")
    return urllib.parse.urljoin(TAILSCALE_STABLE_PACKAGES_URL, match.group(1))


def install_tailscale(notify=None):
    existing = shutil.which("tailscale")
    if existing and resolve_tailscaled_binary(existing):
        return existing

    install_path = cli_tunnel.RUNTIME_BIN_DIR / cli_tunnel.executable_name("tailscale")
    daemon_path = cli_tunnel.RUNTIME_BIN_DIR / cli_tunnel.executable_name("tailscaled")
    if install_path.exists() and daemon_path.exists():
        return str(install_path)

    download_url = tailscale_archive_url()
    archive_path = (
        cli_tunnel.RUNTIME_BIN_DIR
        / urllib.parse.urlparse(download_url).path.rsplit("/", 1)[-1]
    )
    cli_tunnel.download_file(download_url, archive_path, notify=notify)
    try:
        extracted = cli_tunnel.extract_named_members_from_tar(
            archive_path,
            cli_tunnel.RUNTIME_BIN_DIR,
            {"tailscale", "tailscaled"},
        )
        return str(extracted["tailscale"])
    finally:
        archive_path.unlink(missing_ok=True)


def resolve_tailscaled_binary(binary_path):
    sibling = Path(binary_path).with_name(cli_tunnel.executable_name("tailscaled"))
    if sibling.exists():
        return str(sibling)
    return shutil.which("tailscaled")


def notify_info(notify, message, data=None):
    if callable(notify):
        notify(NotifyEvent.INFO, message, data)


def tailscale_socket_args(socket_path=None):
    return ["--socket", str(socket_path)] if socket_path else []


def tailscale_command(binary_path, args, socket_path=None):
    return [binary_path, *tailscale_socket_args(socket_path), *args]


def tailscale_status(binary_path, socket_path=None):
    return subprocess.run(
        tailscale_command(binary_path, ["status", "--json"], socket_path),
        check=False,
        text=True,
        capture_output=True,
        timeout=12,
    )


def tailscale_funnel_help(binary_path, socket_path=None):
    return subprocess.run(
        tailscale_command(binary_path, ["funnel", "--help"], socket_path),
        check=False,
        text=True,
        capture_output=True,
        timeout=12,
    )


def compact_output(lines):
    return " ".join(line.strip() for line in lines if line and line.strip())


def tailscale_daemon_hint(output):
    lowered = output.lower()
    return any(
        marker in lowered
        for marker in (
            "failed to connect to local tailscaled",
            "tailscaled.sock",
            "no such file or directory",
            "connection refused",
            "is tailscaled running",
        )
    )


def tailscale_daemon_ready(binary_path, socket_path):
    completed = tailscale_status(binary_path, socket_path=socket_path)
    output = compact_output([completed.stderr, completed.stdout])
    return not tailscale_daemon_hint(output)


def read_recent_tailscaled_log():
    if not TAILSCALE_DAEMON_LOG_PATH.exists():
        return ""
    try:
        lines = TAILSCALE_DAEMON_LOG_PATH.read_text(
            encoding="utf-8",
            errors="replace",
        ).splitlines()
    except OSError:
        return ""
    return compact_output(lines[-12:])


def start_tailscaled(binary_path, notify=None):
    daemon_path = resolve_tailscaled_binary(binary_path)
    if not daemon_path:
        raise RuntimeError(
            "Tailscale was prepared, but Agent Zero could not find the "
            "`tailscaled` daemon binary. Try Tailscale Remote Control again so "
            "Agent Zero can re-download the static Tailscale package."
        )

    if tailscale_daemon_ready(binary_path, TAILSCALE_SOCKET_PATH):
        return TAILSCALE_SOCKET_PATH

    TAILSCALE_RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    TAILSCALE_STATE_DIR.mkdir(parents=True, exist_ok=True)
    TAILSCALE_SOCKET_PATH.unlink(missing_ok=True)

    notify_info(
        notify,
        "Starting Tailscale's background service inside this container...",
    )

    log_handle = TAILSCALE_DAEMON_LOG_PATH.open("ab")
    process = subprocess.Popen(
        [
            daemon_path,
            "--tun=userspace-networking",
            "--socket",
            str(TAILSCALE_SOCKET_PATH),
            "--statedir",
            str(TAILSCALE_STATE_DIR),
            "--state",
            str(TAILSCALE_STATE_DIR / "tailscaled.state"),
        ],
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
        close_fds=True,
    )
    log_handle.close()
    TAILSCALE_DAEMON_PID_PATH.write_text(str(process.pid), encoding="utf-8")

    deadline = time.monotonic() + TAILSCALE_DAEMON_START_TIMEOUT
    while time.monotonic() < deadline:
        if process.poll() is not None:
            break
        if tailscale_daemon_ready(binary_path, TAILSCALE_SOCKET_PATH):
            notify_info(notify, "Tailscale background service is running.")
            return TAILSCALE_SOCKET_PATH
        time.sleep(0.25)

    details = read_recent_tailscaled_log()
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)
    TAILSCALE_DAEMON_PID_PATH.unlink(missing_ok=True)
    message = (
        "Agent Zero downloaded Tailscale, but could not start the `tailscaled` "
        "background service in this container."
    )
    if details:
        message = f"{message} Details: {details}"
    raise RuntimeError(message)


def stop_managed_tailscaled():
    if not TAILSCALE_DAEMON_PID_PATH.exists():
        return
    try:
        pid = int(TAILSCALE_DAEMON_PID_PATH.read_text(encoding="utf-8").strip())
    except Exception:
        TAILSCALE_DAEMON_PID_PATH.unlink(missing_ok=True)
        return
    try:
        cmdline = Path(f"/proc/{pid}/cmdline").read_bytes().decode(
            "utf-8",
            errors="replace",
        )
    except Exception:
        cmdline = ""
    if "tailscaled" in cmdline:
        try:
            os.kill(pid, 15)
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                try:
                    os.kill(pid, 0)
                except ProcessLookupError:
                    break
                time.sleep(0.1)
            else:
                os.kill(pid, 9)
        except ProcessLookupError:
            pass
        except PermissionError:
            pass
    TAILSCALE_DAEMON_PID_PATH.unlink(missing_ok=True)
    TAILSCALE_SOCKET_PATH.unlink(missing_ok=True)


def tailscale_up_failure_message(output, *, timed_out=False):
    details = compact_output(output)
    if tailscale_daemon_hint(details):
        message = (
            "Agent Zero started Tailscale and ran `tailscale up`, but the "
            "Tailscale background service stopped responding."
        )
    elif timed_out:
        message = (
            "Agent Zero ran `tailscale up`, but it did not finish before the "
            "setup timeout. If a Tailscale login link was shown, approve this "
            "container in your browser, then start Remote Control again."
        )
    else:
        message = (
            "Agent Zero ran `tailscale up`, but Tailscale did not finish joining "
            "this container to your tailnet. Complete any Tailscale login or "
            "admin approval it requested, then try Tailscale Remote Control again."
        )
    if details:
        message = f"{message} Details: {details}"
    return message


def run_tailscale_up(
    binary_path,
    notify=None,
    timeout=TAILSCALE_UP_TIMEOUT,
    socket_path=None,
):
    notify_info(
        notify,
        "Tailscale needs this container to join your tailnet. Running `tailscale up` now...",
    )
    process = subprocess.Popen(
        tailscale_command(binary_path, ["up"], socket_path),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    output_queue = queue.Queue()

    def read_output():
        if process.stdout is None:
            return
        for line in process.stdout:
            output_queue.put(line)

    reader = threading.Thread(target=read_output, daemon=True)
    reader.start()
    deadline = time.monotonic() + timeout
    recent_output = deque(maxlen=10)
    login_announced = False

    def record_line(line):
        nonlocal login_announced
        cleaned = line.strip()
        if not cleaned:
            return
        recent_output.append(cleaned)
        login_match = TAILSCALE_LOGIN_URL_RE.search(cleaned)
        if login_match and not login_announced:
            login_url = login_match.group(0).rstrip(".,)")
            notify_info(
                notify,
                "Open the Tailscale login link and approve this container. "
                "Agent Zero will continue when Tailscale finishes setup.",
                {"provider": "tailscale", "url": login_url},
            )
            login_announced = True

    while True:
        try:
            record_line(output_queue.get(timeout=0.1))
        except queue.Empty:
            if process.poll() is not None:
                reader.join(timeout=1)
                while True:
                    try:
                        record_line(output_queue.get_nowait())
                    except queue.Empty:
                        break
                break
            if time.monotonic() >= deadline:
                process.terminate()
                try:
                    process.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=3)
                reader.join(timeout=1)
                while True:
                    try:
                        record_line(output_queue.get_nowait())
                    except queue.Empty:
                        break
                raise RuntimeError(
                    tailscale_up_failure_message(recent_output, timed_out=True)
                )
            continue

    returncode = process.wait(timeout=3)
    if returncode != 0:
        raise RuntimeError(tailscale_up_failure_message(recent_output))

    notify_info(
        notify,
        "Tailscale setup completed. Checking the tailnet connection...",
    )


def ensure_tailscale_funnel_command(binary_path, socket_path=None):
    completed = tailscale_funnel_help(binary_path, socket_path=socket_path)
    output = compact_output([completed.stderr, completed.stdout])
    if completed.returncode == 0 and "tailscale funnel" in output.lower():
        return

    details = f" Details: {output}" if output else ""
    raise RuntimeError(
        "Agent Zero prepared Tailscale, but this Tailscale binary does not "
        "support `tailscale funnel`. Tailscale Remote Control needs Tailscale "
        "v1.38.3 or newer with Funnel support enabled for your tailnet."
        f"{details}"
    )


def ensure_tailscale_ready(binary_path, notify=None):
    socket_path = None
    completed = tailscale_status(binary_path)
    if completed.returncode != 0 and tailscale_daemon_hint(
        compact_output([completed.stderr, completed.stdout])
    ):
        socket_path = start_tailscaled(binary_path, notify=notify)
        completed = tailscale_status(binary_path, socket_path=socket_path)

    if completed.returncode != 0:
        run_tailscale_up(binary_path, notify=notify, socket_path=socket_path)
        completed = tailscale_status(binary_path, socket_path=socket_path)
        if completed.returncode != 0:
            details = compact_output([completed.stderr, completed.stdout])
            message = (
                "Agent Zero ran `tailscale up`, but Tailscale status is still "
                "not available. Tailscale may still need browser approval, admin "
                "approval, or a running `tailscaled` service."
            )
            if details:
                message = f"{message} Details: {details}"
            raise RuntimeError(message)

    try:
        payload = json.loads(completed.stdout or "{}")
    except json.JSONDecodeError:
        ensure_tailscale_funnel_command(binary_path, socket_path=socket_path)
        return {"command_prefix": tailscale_socket_args(socket_path)}

    backend_state = str(payload.get("BackendState") or "").lower()
    if backend_state and backend_state != "running":
        run_tailscale_up(binary_path, notify=notify, socket_path=socket_path)
        completed = tailscale_status(binary_path, socket_path=socket_path)
        try:
            payload = json.loads(completed.stdout or "{}")
        except json.JSONDecodeError:
            ensure_tailscale_funnel_command(binary_path, socket_path=socket_path)
            return {"command_prefix": tailscale_socket_args(socket_path)}
        backend_state = str(payload.get("BackendState") or "").lower()
        if backend_state and backend_state != "running":
            raise RuntimeError(
                "Agent Zero ran `tailscale up`, but this node is still not ready "
                "for Tailscale Funnel "
                f"(state: {backend_state}). Complete Tailscale sign-in or admin "
                "approval, then try again."
            )

    ensure_tailscale_funnel_command(binary_path, socket_path=socket_path)
    return {"command_prefix": tailscale_socket_args(socket_path)}


class TailscaleTunnel(CliTunnelHelper):
    def __init__(self, port, notify=None):
        target = f"http://127.0.0.1:{port}"
        self._announced_login_urls = set()
        super().__init__(
            label="Tailscale Funnel",
            binary="tailscale",
            port=port,
            command=[
                "tailscale",
                "funnel",
                "--yes",
                f"--https={TAILSCALE_FUNNEL_HTTPS_PORT}",
                target,
            ],
            url_pattern=TAILSCALE_URL_RE,
            missing_binary_message=(
                "Tailscale could not be prepared in this environment. Install "
                "Tailscale, make sure the `tailscaled` service is available to "
                "this container, enable Funnel for the tailnet, then try again."
            ),
            shutdown_command=[
                "tailscale",
                "funnel",
                "--yes",
                f"--https={TAILSCALE_FUNNEL_HTTPS_PORT}",
                target,
                "off",
            ],
            timeout=TAILSCALE_FUNNEL_TIMEOUT,
            binary_resolver=lambda notify_callback: install_tailscale(
                notify=notify_callback
            ),
            preflight=ensure_tailscale_ready,
            output_handler=self._handle_tailscale_output,
            notify=notify,
        )

    def _handle_tailscale_output(self, line, notify=None):
        login_match = TAILSCALE_LOGIN_URL_RE.search(line)
        if not login_match:
            return
        login_url = login_match.group(0).rstrip(".,)")
        if login_url in self._announced_login_urls:
            return
        self._announced_login_urls.add(login_url)
        notify_info(
            notify,
            "Open the Tailscale approval link to finish sign-in or enable Funnel. "
            "Agent Zero will continue when Tailscale reports the public URL.",
            {"provider": "tailscale", "url": login_url},
        )

    def stop(self):
        try:
            return super().stop()
        finally:
            if self.command_prefix:
                stop_managed_tailscaled()
