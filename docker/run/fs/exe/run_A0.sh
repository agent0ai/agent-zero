#!/bin/bash

. "/ins/setup_venv.sh" "$@"
. "/ins/copy_A0.sh" "$@"
if [ -n "${PYTHONWARNINGS:-}" ]; then
    export PYTHONWARNINGS="${PYTHONWARNINGS},ignore:.*doesn't match a supported version.*:Warning"
else
    export PYTHONWARNINGS="ignore:.*doesn't match a supported version.*:Warning"
fi

if [ "${A0_SKIP_PREPARE:-1}" != "1" ]; then
    python /a0/prepare.py --dockerized=true
else
    echo "Skipping prepare.py (A0_SKIP_PREPARE=1)"
fi
# python /a0/preload.py --dockerized=true # no need to run preload if it's done during container build

echo "Starting A0..."
exec python /a0/run_ui.py \
    --dockerized=true \
    --port=80 \
    --host="0.0.0.0"
    # --code_exec_ssh_enabled=true \
    # --code_exec_ssh_addr="localhost" \
    # --code_exec_ssh_port=22 \
    # --code_exec_ssh_user="root" \
    # --code_exec_ssh_pass="toor"
