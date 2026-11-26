"""Launch the project viewer under a separate Linux user and kernel access rules."""

import ctypes as c
import errno
import json
import os
from pathlib import Path
import resource
import shlex
import socket
import subprocess
import sys
import time
from xml.etree import ElementTree


_CREATE_RULESET, _ADD_RULE, _RESTRICT_SELF = 444, 445, 446
_EXECUTE, _WRITE, _READ, _LIST = 1, 2, 4, 8
_REMOVE_FILE, _MAKE_FILE, _MAKE_SOCKET = 1 << 5, 1 << 8, 1 << 9
_FS_ACCESS = (1 << 16) - 1
_BIND, _CONNECT = 1, 2
_SCOPE_IPC = 3
_LIBC = c.CDLL(None, use_errno=True)


class Rules(c.Structure):
    _fields_ = [("fs", c.c_uint64), ("net", c.c_uint64), ("scope", c.c_uint64)]


class PathRule(c.Structure):
    _pack_ = 1
    _fields_ = [("access", c.c_uint64), ("fd", c.c_int32)]


class PortRule(c.Structure):
    _fields_ = [("access", c.c_uint64), ("port", c.c_uint64)]


class SeccompCompare(c.Structure):
    _fields_ = [("arg", c.c_uint), ("op", c.c_int), ("mask", c.c_uint64), ("value", c.c_uint64)]


def _check(result):
    if result < 0:
        code = c.get_errno()
        raise OSError(code, os.strerror(code))
    return result


def _restrict_network_sockets():
    lib = c.CDLL("libseccomp.so.2")
    lib.seccomp_init.restype = c.c_void_p
    lib.seccomp_rule_add_array.argtypes = [c.c_void_p, c.c_uint32, c.c_int, c.c_uint, c.POINTER(SeccompCompare)]
    lib.seccomp_load.argtypes = [c.c_void_p]
    lib.seccomp_release.argtypes = [c.c_void_p]
    context = lib.seccomp_init(0x7FFF0000)
    if not context:
        raise RuntimeError("Could not set browser socket policy.")
    try:
        socket_call = lib.seccomp_syscall_resolve_name(b"socket")
        deny = 0x00050000 | errno.EACCES
        # Desktop IPC continues through Unix sockets. Internet sockets use TCP only.
        for family in (socket.AF_INET, socket.AF_INET6, socket.AF_PACKET):
            if family == socket.AF_PACKET:
                comparisons = (SeccompCompare * 1)(SeccompCompare(0, 4, family, 0))
                result = lib.seccomp_rule_add_array(context, deny, socket_call, 1, comparisons)
                if result != 0:
                    raise RuntimeError("Could not restrict raw sockets.")
                continue
            for kind in (socket.SOCK_DGRAM, socket.SOCK_RAW):
                comparisons = (SeccompCompare * 2)(
                    SeccompCompare(0, 4, family, 0), SeccompCompare(1, 7, 0xF, kind),
                )
                if lib.seccomp_rule_add_array(context, deny, socket_call, 2, comparisons) != 0:
                    raise RuntimeError("Could not restrict Internet sockets.")
        if lib.seccomp_load(context) != 0:
            raise RuntimeError("Could not apply the socket policy.")
    finally:
        lib.seccomp_release(context)


def _allow_path(ruleset, path, access):
    path = Path(path)
    if not path.exists():
        return
    if not path.is_dir():
        access &= _EXECUTE | _READ | _WRITE
    descriptor = os.open(path, os.O_PATH | os.O_CLOEXEC)
    try:
        _check(_LIBC.syscall(_ADD_RULE, ruleset, 1, c.byref(PathRule(access, descriptor)), 0))
    finally:
        os.close(descriptor)


def _constrain(home, control, chrome, port, proxy_port):
    abi = _check(_LIBC.syscall(_CREATE_RULESET, 0, 0, 1))
    if abi < 6 or os.uname().machine not in {"x86_64", "aarch64"}:
        raise RuntimeError("Project surfaces require Linux Landlock ABI 6 or newer.")
    rules = Rules(_FS_ACCESS, _BIND | _CONNECT, _SCOPE_IPC)
    descriptor = _check(_LIBC.syscall(_CREATE_RULESET, c.byref(rules), c.sizeof(rules), 0))
    try:
        for path in (
            "/usr/bin", "/usr/sbin", "/usr/lib", "/usr/lib64", "/usr/libexec", "/usr/local/lib", "/usr/share", "/usr/include",
            "/etc/alternatives", "/etc/fonts", "/etc/ssl", "/etc/X11", "/etc/xdg", "/etc/xpra",
            "/etc/passwd", "/etc/group", "/etc/ld.so.cache", "/etc/localtime", "/etc/mime.types",
            "/etc/hosts", "/etc/nsswitch.conf", "/usr/local/share", "/proc", "/sys",
            "/etc/machine-id", "/var/lib/dbus/machine-id", "/etc/dconf", "/etc/dbus-1", "/etc/libreoffice",
        ):
            _allow_path(descriptor, path, _EXECUTE | _READ | _LIST)
        for path in ("/dev/null", "/dev/zero", "/dev/urandom", "/dev/random"):
            _allow_path(descriptor, path, _READ | _WRITE)
        for path in (home, "/tmp/.X11-unix", "/var/lib/xkb"):
            _allow_path(descriptor, path, rules.fs)
        # Xvfb uses a process-owned lock. LibreOffice also creates its local
        # instance socket in this sticky directory under the viewer's UID.
        scratch_access = _WRITE | _REMOVE_FILE | _MAKE_FILE
        if not chrome:
            scratch_access |= _MAKE_SOCKET
        _allow_path(descriptor, "/tmp", scratch_access)
        _allow_path(descriptor, control, _READ | _LIST)
        if chrome:
            _allow_path(descriptor, Path(chrome).parent, _EXECUTE | _READ | _LIST)
        for action, number in ((_BIND, port), (_CONNECT, proxy_port)):
            if number:
                _check(_LIBC.syscall(_ADD_RULE, descriptor, 2, c.byref(PortRule(action, number)), 0))
        _check(_LIBC.prctl(38, 1, 0, 0, 0))  # PR_SET_NO_NEW_PRIVS
        _check(_LIBC.syscall(_RESTRICT_SELF, descriptor, 0))
        _restrict_network_sockets()
    finally:
        os.close(descriptor)


def _office_launch(home: Path, path: Path) -> list[str]:
    profile = home / "office"
    user = profile / "user"
    user.mkdir(parents=True, exist_ok=True)
    settings = user / "registrymodifications.xcu"
    if not settings.exists():
        namespace = "http://openoffice.org/2001/registry"
        ElementTree.register_namespace("oor", namespace)
        root = ElementTree.Element(f"{{{namespace}}}items")
        for path_name, options in (
            ("/org.openoffice.Setup/Product", ("WhatsNew",)),
            ("/org.openoffice.Office.Common/Misc", ("ShowTipOfTheDay", "CrashReport")),
        ):
            item = ElementTree.SubElement(root, "item", {f"{{{namespace}}}path": path_name})
            for name in options:
                prop = ElementTree.SubElement(item, "prop", {f"{{{namespace}}}name": name, f"{{{namespace}}}op": "fuse"})
                ElementTree.SubElement(prop, "value").text = "false"
        ElementTree.ElementTree(root).write(settings, encoding="utf-8", xml_declaration=True)
    package_cache = home / "office-package-cache"
    package_cache.mkdir(mode=0o700, exist_ok=True)
    return [
        "env", "SAL_USE_VCLPLUGIN=gen", "libreoffice", "--norestore",
        f"-env:UserInstallation={profile.as_uri()}",
        f"-env:UNO_SHARED_PACKAGES_CACHE={package_cache.as_uri()}", str(path),
    ]


def main():
    mode, raw_uid, raw_port, raw_display, control, chrome, raw_proxy = sys.argv[1:]
    uid, port, display, proxy = map(int, (raw_uid, raw_port, raw_display, raw_proxy))
    home = Path(os.environ["HOME"])
    os.setgroups([])
    os.setgid(uid)
    os.setuid(uid)
    os.umask(0o077)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_NPROC, (256, 256))
    _constrain(home, control, chrome, port, proxy)
    xserver = "Xvfb -screen 0 1280x760x24 -nolisten tcp -auth $XAUTHORITY"
    child = ["startxfce4"]
    if mode == "browser":
        child = [
            chrome, "--no-sandbox", "--disable-dev-shm-usage", "--disable-quic",
            "--disable-background-networking", "--no-first-run", "--no-default-browser-check",
            "--password-store=basic", f"--user-data-dir={home / 'chromium'}",
            f"--proxy-server=http://127.0.0.1:{proxy}", "--proxy-bypass-list=<-loopback>",
            "--start-maximized", "about:blank",
        ]
    else:
        bus_socket = home / "run" / "desktop-bus"
        bus_address = f"unix:path={bus_socket}"
        bus = subprocess.Popen(["dbus-daemon", "--session", "--nofork", f"--address={bus_address}"])
        for _ in range(40):
            if bus_socket.is_socket():
                break
            if bus.poll() is not None:
                raise RuntimeError("The project session bus stopped during startup.")
            time.sleep(0.05)
        else:
            raise RuntimeError("The project session bus could not start.")
        os.environ["DBUS_SESSION_BUS_ADDRESS"] = bus_address
        child = ["env", f"DBUS_SESSION_BUS_ADDRESS={bus_address}", "GSETTINGS_BACKEND=memory", "startxfce4"]
    command = [
        "xpra", "start-desktop", f":{display}", "--daemon=no", "--systemd-run=no", "--mdns=no", "--source=", "--ssh-upgrade=no",
        f"--xvfb={xserver}", "--resize-display=no", "--html=on", f"--bind-tcp=127.0.0.1:{port}",
        f"--socket-dir={home / 'run'}", f"--socket-dirs={home / 'run'}", "--dbus-launch=",
        "--pulseaudio=no", "--speaker=off", "--microphone=off", "--mmap=no", "--webcam=no",
        "--notifications=no", "--printing=no", "--file-transfer=no", "--open-files=no",
        "--open-url=no", "--start-new-commands=no", "--clipboard=no", "--exit-with-children=yes",
        f"--start-child={shlex.join(child)}",
    ]
    server = subprocess.Popen(command)
    last_command = None
    while server.poll() is None:
        try:
            request = json.loads((Path(control) / "open.json").read_text())
        except (OSError, ValueError):
            request = {}
        if request and request["id"] != last_command:
            last_command = request["id"]
            path = home / "Files" / request["path"]
            if mode == "browser":
                launch = [*child[:-1], path.as_uri()]
            elif path.suffix.lower() in {".odt", ".ods", ".odp", ".docx", ".xlsx", ".pptx"}:
                launch = _office_launch(home, path)
            else:
                launch = ["xdg-open", str(path)]
            subprocess.Popen(launch, env={**os.environ, "DISPLAY": f":{display}"})
        time.sleep(0.25)
    raise SystemExit(server.returncode)


if __name__ == "__main__":
    main()
