#!/bin/bash

# Wait until run_tunnel.py exists
echo "Starting tunnel API..."

sleep 1
while [ ! -f /a0/run_tunnel.py ]; do
    echo "Waiting for /a0/run_tunnel.py to be available..."
    sleep 1
done

cd /a0
exec depfix run /a0/run_tunnel.py \
    --dockerized=true \
    --port=80 \
    --tunnel_api_port=55520 \
    --host="0.0.0.0"
