"""Call a local handler: python -m helpers.socket_cli COMMAND '[JSON arguments]'"""

import argparse
import json
import math
import socket
import sys

from helpers.socket_api import (
    MAX_MESSAGE_BYTES, IO_TIMEOUT, decode_message, encode_message,
    error_response, get_socket_path,
)


def call(command: str, arguments: dict, *, path=None, timeout: float | None = None) -> dict:
    """Send one request; never retry a possibly completed operation."""
    if not isinstance(arguments, dict):
        raise ValueError("Arguments must be a JSON object")
    if timeout is not None and (not math.isfinite(timeout) or timeout <= 0):
        raise ValueError("timeout must be positive")
    request = encode_message({"command": command, "args": arguments})
    if len(request) > MAX_MESSAGE_BYTES:
        raise ValueError("Request exceeds the size limit")
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(IO_TIMEOUT)
        client.connect(str(path if path is not None else get_socket_path()))
        client.sendall(request)
        client.settimeout(timeout)
        with client.makefile("rb") as stream:
            raw = stream.readline(MAX_MESSAGE_BYTES + 1)
    if len(raw) > MAX_MESSAGE_BYTES or not raw.endswith(b"\n"):
        raise ValueError("Invalid or oversized socket response")
    response = decode_message(raw)
    if not isinstance(response, dict) or type(response.get("ok")) is not bool:
        raise ValueError("Invalid socket response envelope")
    if response["ok"]:
        if not isinstance(response.get("result"), dict):
            raise ValueError("Invalid socket result")
    else:
        error = response.get("error")
        if not isinstance(error, dict) or not all(isinstance(error.get(key), str) for key in ("code", "message")):
            raise ValueError("Invalid socket error")
    return response


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", help="Handler path, e.g. ping or plugins/example/handler")
    parser.add_argument("arguments", nargs="?", default="{}", help="JSON object; '-' reads it from stdin")
    parser.add_argument("--socket", help="Socket path (default: A0_SOCKET_PATH or tmp/socket/a0.sock)")
    parser.add_argument("--timeout", type=float, help="Response timeout in seconds (default: no deadline)")
    args = parser.parse_args(argv)
    try:
        raw = sys.stdin.buffer.read(MAX_MESSAGE_BYTES + 1) if args.arguments == "-" else args.arguments.encode("utf-8")
        if len(raw) > MAX_MESSAGE_BYTES:
            raise ValueError("Arguments exceed the size limit")
        arguments = decode_message(raw)
        if not isinstance(arguments, dict):
            raise ValueError("Arguments must be a JSON object")
    except (ValueError, UnicodeError, RecursionError) as exc:
        response = error_response("INVALID_ARGUMENT", str(exc))
    else:
        try:
            response = call(args.command, arguments, path=args.socket, timeout=args.timeout)
        except OSError as exc:
            print(f"Local socket connection failed: {exc}", file=sys.stderr)
            response = error_response("CONNECTION_ERROR", "Could not complete the local socket request.")
        except (ValueError, UnicodeError, RecursionError) as exc:
            response = error_response("PROTOCOL_ERROR", str(exc))
    print(json.dumps(response, ensure_ascii=False, allow_nan=False))
    return 0 if response["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
