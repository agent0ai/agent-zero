# socket_cli.py DOX

## Purpose and Ownership

- Own the standard-library client for local socket handlers; never initialize a second Agent Zero runtime.
- `call(command, arguments, path=..., timeout=None)` returns the server envelope, validating framing, size and result/error types. It raises on connection or protocol failure and never retries.
- `main(argv)` accepts `COMMAND [JSON_OBJECT]`, `-` for JSON from stdin, and optional `--socket PATH`/`--timeout SECONDS`. Defaults match the server through `A0_SOCKET_PATH` or framework-root `tmp/socket/a0.sock`.

## Contracts and Side Effects

- Print one JSON envelope on stdout and diagnostic connection details on stderr. Success exits 0; handler, argument, connection and protocol failures exit 1. Argparse usage errors exit 2 on stderr.
- Arguments must be an object and are forwarded unchanged. Reuse server limits and framing. Bound stdin and response reads; connect/send use `A0_SOCKET_IO_TIMEOUT`, while response reads have no default deadline. A positive finite `timeout` opts into a client response timeout.
- The client sends one request per connection. A lost response may follow a successful mutation; never retry automatically.
- Run with `python -m helpers.socket_cli ping`. No extra dependency, console-script installation or executable PATH modification is required.

## Verification

- `tests/test_socket_api.py` covers subprocess stdout, exit status, stdin arguments, unavailable servers and invalid server responses.
