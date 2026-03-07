#!/bin/bash

# Wait until run_tunnel.py exists
echo "Starting tunnel API..."

sleep 1
while [ ! -f /a0/run_tunnel.py ]; do
    echo "Waiting for /a0/run_tunnel.py to be available..."
    sleep 1
done
while [ ! -f /a0/python/api/tunnel.py ]; do
    echo "Waiting for /a0/python/api/tunnel.py to be available..."
    sleep 1
done

. "/ins/setup_venv.sh" "$@"
if [ -n "${PYTHONWARNINGS:-}" ]; then
    export PYTHONWARNINGS="${PYTHONWARNINGS},ignore:.*doesn't match a supported version.*:Warning"
else
    export PYTHONWARNINGS="ignore:.*doesn't match a supported version.*:Warning"
fi

cd /a0 || exit 1
export PYTHONPATH=/a0:${PYTHONPATH}

exec python run_tunnel.py \
    --dockerized=true \
    --port=80 \
    --tunnel_api_port=55520 \
    --host="0.0.0.0" \
    --code_exec_docker_enabled=false \
    --code_exec_ssh_enabled=true \
    # --code_exec_ssh_addr="localhost" \
    # --code_exec_ssh_port=22 \
    # --code_exec_ssh_user="root" \
    # --code_exec_ssh_pass="toor"
