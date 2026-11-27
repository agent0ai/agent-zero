#!/bin/bash
set -eu

if [[ ! -f /a0/run_ui.py ]]; then
    echo "ERROR: /a0/run_ui.py is missing. Mount persistent data at /a0/usr instead of /a0." >&2
    echo "For an old ./agent-zero:/a0 mount, use ./agent-zero/usr:/a0/usr. Keep a backup of the old folder." >&2
    exit 1
fi

# Tuxee removes its password inputs before running /init. Give both services
# the same input through a root-only file, consumed by Agent Zero's init script.
password_file=/run/a0-tuxee-root-password
if [[ -n "${ROOT_PASSWORD:-}" && -n "${ROOT_PASSWORD_FILE:-}" ]]; then
    echo 'Set only one of ROOT_PASSWORD and ROOT_PASSWORD_FILE' >&2
    exit 1
fi
umask 077
if [[ -n "${ROOT_PASSWORD_FILE:-}" ]]; then
    password=$(cat -- "$ROOT_PASSWORD_FILE")
elif [[ -n "${ROOT_PASSWORD:-}" ]]; then
    password=$ROOT_PASSWORD
else
    password=$(head -c 24 /dev/urandom | base64)
    [[ ${#password} -eq 32 ]]
fi
if [[ -z "$password" || "$password" == *$'\n'* || "$password" == *$'\r'* ]]; then
    echo 'Root password must be nonempty and contain no line breaks' >&2
    exit 1
fi
printf '%s\n' "$password" > "$password_file"
unset ROOT_PASSWORD
export ROOT_PASSWORD_FILE=$password_file
umask 022
exec /opt/tuxee/entrypoint.sh /opt/agent-zero/init "$@"
