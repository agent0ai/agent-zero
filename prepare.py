from python.helpers import dotenv, runtime, settings
import string
import random
import os
import subprocess
import sys
from python.helpers.print_style import PrintStyle


PrintStyle.standard("Preparing environment...")

try:

    runtime.initialize()

    # generate random root password if not set (for SSH)
    root_pass = dotenv.get_dotenv_value(dotenv.KEY_ROOT_PASSWORD)
    if not root_pass:
        root_pass = "".join(random.choices(string.ascii_letters + string.digits, k=32))
        PrintStyle.standard("Changing root password...")
    settings.set_root_password(root_pass)

except Exception as e:
    PrintStyle.error(f"Error in preload: {e}")


# ─── Telegram Bot Auto-Start ──────────────────────────────────────────────────

def start_telegram_daemon():
    DAEMON_SCRIPT = "/a0/usr/workdir/telegram/start_daemon.py"
    DAEMON_PROC   = "pip_telegram_daemon.py"
    PY            = sys.executable

    # 1. Install required packages if not already present
    PrintStyle.standard("Telegram: ensuring pip packages (openai, requests)...")
    try:
        subprocess.run(
            [PY, "-m", "pip", "install", "--quiet", "openai", "requests"],
            check=True,
            timeout=120,
        )
    except Exception as e:
        PrintStyle.error(f"Telegram: pip install failed: {e}")
        return

    # 2. Kill any stale daemon process
    PrintStyle.standard("Telegram: killing any stale daemon...")
    try:
        subprocess.run(
            ["pkill", "-f", DAEMON_PROC],
            timeout=5,
        )
    except Exception:
        pass  # pkill returns non-zero if nothing matched — that's fine

    # 3. Check the daemon script exists (volume must be mounted)
    if not os.path.isfile(DAEMON_SCRIPT):
        PrintStyle.error(
            f"Telegram: {DAEMON_SCRIPT} not found — "
            "is the usr/ volume mounted? Skipping daemon start."
        )
        return

    # 4. Launch start_daemon.py in the background
    #    start_daemon.py prints its own diagnostics to stdout (visible in container logs)
    #    and then opens /tmp/telegram_daemon.log itself for the actual daemon process.
    PrintStyle.standard(f"Telegram: launching daemon via {DAEMON_SCRIPT} ...")
    try:
        subprocess.Popen(
            [PY, DAEMON_SCRIPT],
            close_fds=True,
        )
        PrintStyle.standard("Telegram: daemon launched — logs at /tmp/telegram_daemon.log")
    except Exception as e:
        PrintStyle.error(f"Telegram: failed to launch daemon: {e}")


start_telegram_daemon()
