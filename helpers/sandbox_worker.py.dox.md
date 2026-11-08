# Plugin sandbox workers

`SandboxWorker` owns lazy child sandbox creation, private JSON requests, bounded
no-symlink response reads, cancellation, serialization and idle shutdown. Plugin
installers and model processes run in the guest; files persist after stopping.
It does not create listening ports or expose Agent Zero's usr directory. Inputs
live below masked manager state and are mounted read-only. No application secrets
or inherited host environment are sent to workers. Plugin lifecycle hooks stop
their worker on disable; uninstall may delete the owned sandbox through manager.

`call` is blocking; `acall` offloads it and propagates cancellation to sandbox stop.
First-use setup has a separate 30-minute deadline; request timeout begins after
setup. Responses are capped at 128 MiB. `process_command` in the manager supports
browser driver pipes whose lifetime is owned by the browser adapter.

`status()` returns setup state/stage/message, timestamps, elapsed time and output
inactivity without acquiring the setup/request lock or launching a guest. It reads
at most 4 KiB each of boot-matched progress and the private installation log through
the manager's no-symlink reader; raw log text is never returned. Installer fingerprints cover install scripts and read-only support files. Installer stages
come from `plugins/_sandboxing/sandbox/progress.py`. Readiness remains boot-scoped;
errors survive cleanup until the next attempt. Liveness polling uses `is_running`
once per second rather than recursively measuring disk usage.

Verify with `tests/test_sandbox_workers.py` and real plugin sandbox smoke checks.
