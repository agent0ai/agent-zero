import os
import platform
import queue
import shutil
import subprocess
import tarfile
import tempfile
import threading
import time
import urllib.request
import zipfile
from collections import deque
from pathlib import Path

from flaredantic import NotifyEvent

from helpers import files
from helpers.tunnel_common import TunnelHelper


RUNTIME_BIN_DIR = Path(files.get_abs_path("tmp", "bin"))


def executable_name(name):
    return f"{name}.exe" if platform.system().lower() == "windows" else name


def chmod_executable(path):
    if platform.system().lower() != "windows":
        path.chmod(0o755)


def notify_download(notify, message, data=None):
    if callable(notify):
        notify(NotifyEvent.DOWNLOADING, message, data)


def notify_download_complete(notify, message, data=None):
    if callable(notify):
        notify(NotifyEvent.DOWNLOAD_COMPLETE, message, data)


def download_file(url, destination, notify=None):
    destination.parent.mkdir(parents=True, exist_ok=True)
    notify_download(notify, f"Downloading {url}")
    temp_fd, temp_name = tempfile.mkstemp(
        prefix=f"{destination.name}.",
        suffix=".download",
        dir=str(destination.parent),
    )
    os.close(temp_fd)
    temp_path = Path(temp_name)
    try:
        with urllib.request.urlopen(url, timeout=60) as response:
            with temp_path.open("wb") as handle:
                shutil.copyfileobj(response, handle)
        temp_path.replace(destination)
        notify_download_complete(notify, f"Downloaded {destination.name}")
        return destination
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise


def platform_parts():
    system = platform.system().lower()
    machine = platform.machine().lower()
    if machine in {"x86_64", "amd64"}:
        arch = "amd64"
    elif machine in {"aarch64", "arm64"}:
        arch = "arm64"
    elif machine in {"i386", "i686", "x86"}:
        arch = "386"
    elif machine.startswith("arm"):
        arch = "arm"
    else:
        raise RuntimeError(f"Unsupported CPU architecture for tunnel binary: {machine}")

    if system not in {"linux", "darwin", "windows"}:
        raise RuntimeError(f"Unsupported operating system for tunnel binary: {system}")
    return system, arch


def extract_named_members_from_tar(archive_path, destination_dir, member_names):
    destination_dir.mkdir(parents=True, exist_ok=True)
    extracted = {}
    wanted = set(member_names)
    with tarfile.open(archive_path, "r:*") as archive:
        for member in archive.getmembers():
            member_name = Path(member.name).name
            if member_name not in wanted or not member.isfile():
                continue
            target = destination_dir / executable_name(member_name)
            source = archive.extractfile(member)
            if source is None:
                continue
            with source, target.open("wb") as handle:
                shutil.copyfileobj(source, handle)
            chmod_executable(target)
            extracted[member_name] = target
    missing = wanted - set(extracted)
    if missing:
        raise RuntimeError(
            f"Archive {archive_path.name} did not contain expected binaries: "
            f"{', '.join(sorted(missing))}."
        )
    return extracted


def extract_named_members_from_zip(archive_path, destination_dir, member_names):
    destination_dir.mkdir(parents=True, exist_ok=True)
    extracted = {}
    wanted = set(member_names)
    with zipfile.ZipFile(archive_path) as archive:
        for member in archive.infolist():
            member_name = Path(member.filename).name
            normalized_name = member_name.removesuffix(".exe")
            if normalized_name not in wanted or member.is_dir():
                continue
            target = destination_dir / executable_name(normalized_name)
            with archive.open(member) as source, target.open("wb") as handle:
                shutil.copyfileobj(source, handle)
            chmod_executable(target)
            extracted[normalized_name] = target
    missing = wanted - set(extracted)
    if missing:
        raise RuntimeError(
            f"Archive {archive_path.name} did not contain expected binaries: "
            f"{', '.join(sorted(missing))}."
        )
    return extracted


class CliTunnelHelper(TunnelHelper):
    label = "CLI tunnel"

    def __init__(
        self,
        *,
        label,
        binary,
        port,
        command,
        url_pattern,
        missing_binary_message,
        shutdown_command=None,
        timeout=30,
        notify=None,
        binary_resolver=None,
        preflight=None,
        output_handler=None,
    ):
        super().__init__(port, notify=notify)
        self.label = label
        self.binary = binary
        self.command = command
        self.url_pattern = url_pattern
        self.missing_binary_message = missing_binary_message
        self.shutdown_command = shutdown_command
        self.timeout = timeout
        self.tunnel_process = None
        self.binary_path = None
        self.binary_resolver = binary_resolver
        self.preflight = preflight
        self.command_prefix = []
        self.output_handler = output_handler

    def _extract_url(self, line):
        match = self.url_pattern.search(line)
        if not match:
            return None
        return match.group(1 if match.lastindex else 0).rstrip(".,)")

    def start(self):
        binary_path = (
            self.binary_resolver(self._notify)
            if callable(self.binary_resolver)
            else shutil.which(self.binary)
        )
        if not binary_path:
            raise RuntimeError(self.missing_binary_message)
        self.binary_path = binary_path
        if callable(self.preflight):
            preflight_result = self.preflight(binary_path, notify=self._notify)
            if isinstance(preflight_result, dict):
                self.command_prefix = list(preflight_result.get("command_prefix") or [])

        command = [binary_path, *self.command_prefix, *self.command[1:]]
        self.notify_starting(self.label)
        self.tunnel_process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        output_queue = queue.Queue()

        def read_output():
            if self.tunnel_process is None or self.tunnel_process.stdout is None:
                return
            for line in self.tunnel_process.stdout:
                output_queue.put(line)

        threading.Thread(target=read_output, daemon=True).start()

        deadline = time.monotonic() + self.timeout
        recent_output = deque(maxlen=8)
        while time.monotonic() < deadline:
            try:
                line = output_queue.get(timeout=0.1)
            except queue.Empty:
                if self.tunnel_process.poll() is not None:
                    break
                continue

            cleaned_line = line.strip()
            if cleaned_line:
                recent_output.append(cleaned_line)
                if callable(self.output_handler):
                    try:
                        self.output_handler(cleaned_line, self._notify)
                    except Exception:
                        pass
            url = self._extract_url(cleaned_line)
            if url:
                self.tunnel_url = url
                self.notify_url_ready(self.label, url)
                return self.tunnel_url

        details = " ".join(recent_output)
        if self.tunnel_process.poll() is not None:
            raise RuntimeError(
                f"{self.label} exited before it reported a remote URL."
                + (f" Output: {details}" if details else "")
            )
        self._terminate_process()
        raise RuntimeError(
            f"{self.label} did not report a remote URL within {self.timeout} seconds."
            + (f" Output: {details}" if details else "")
        )

    def _terminate_process(self):
        if not self.tunnel_process or self.tunnel_process.poll() is not None:
            return
        self.tunnel_process.terminate()
        try:
            self.tunnel_process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            self.tunnel_process.kill()
            self.tunnel_process.wait(timeout=3)

    def stop(self):
        self._terminate_process()

        if self.shutdown_command:
            binary_path = self.binary_path or shutil.which(self.binary)
            if binary_path:
                subprocess.run(
                    [binary_path, *self.command_prefix, *self.shutdown_command[1:]],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=10,
                )
        self.tunnel_url = None
        self.notify_stopped(self.label)
        return True
