#!/bin/bash
set -eu

password_file=/run/a0-tuxee-root-password
ROOT_PASSWORD=$(cat -- "$password_file")
rm -f -- "$password_file"
export ROOT_PASSWORD

requested=${A0_NOFILE_LIMIT:-65535}
hard=$(ulimit -Hn)
if [[ "$requested" =~ ^[0-9]+$ ]] && [ "$requested" -gt 0 ]; then
    if [[ "$hard" != unlimited ]] && [ "$requested" -gt "$hard" ]; then
        requested=$hard
    fi
    soft=$(ulimit -Sn)
    if [[ "$soft" != unlimited ]] && [ "$requested" -gt "$soft" ]; then
        ulimit -Sn "$requested" || true
    fi
else
    echo "Warning: invalid A0_NOFILE_LIMIT='$requested'; keeping the open file limit." >&2
fi

cp -r --no-preserve=ownership,mode /per/* /
chmod 444 /root/.bashrc /root/.profile
mkdir -p /a0/usr/uploads
marker=/var/lib/apt/a0-initial-update-started
if [[ ! -e "$marker" ]]; then
    touch "$marker"
    apt-get update >/dev/null 2>&1 &
fi

# Give each attempt its own process group so a failed bootstrap cannot leave its UI behind.
set -m
pid=
stop() {
    trap '' INT TERM
    if [[ -n "$pid" ]]; then
        kill -TERM -- "-$pid" 2>/dev/null || true
        wait "$pid" || true
    fi
    exit 0
}
trap stop INT TERM

while true; do
    /exe/run_A0.sh &
    pid=$!
    status=0
    wait "$pid" || status=$?
    kill -TERM -- "-$pid" 2>/dev/null || true
    pid=
    echo "Agent Zero exited (status $status); restarting in 1 second" >&2
    sleep 1
done
