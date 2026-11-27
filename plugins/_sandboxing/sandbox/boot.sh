#!/bin/sh
set -eu
mkdir -p /var/lib/a0-worker /app/plugins
rm -f /var/lib/a0-worker/ready.json /var/lib/a0-worker/response.json /var/lib/a0-worker/progress.json
fingerprint=$({ cat /plugin/sandbox/requirements.txt /worker/constraints.txt /worker/python.sh; find /plugin/sandbox -maxdepth 1 -name 'install*' -type f -exec sha256sum {} \; | sort; find /support -type f -exec sha256sum {} \; | sort; } | sha256sum | cut -d ' ' -f 1)
if [ ! -f /var/lib/a0-worker/installed ] || [ "$(cat /var/lib/a0-worker/installed)" != "$fingerprint" ]; then
    python /worker/progress.py installing 'Installing sandbox dependencies'
    sh /plugin/sandbox/install.sh > /var/lib/a0-worker/install.log 2>&1
    echo "$fingerprint" > /var/lib/a0-worker/installed
fi
python /worker/progress.py starting_worker 'Starting sandbox worker'
export PYTHONPATH=/app
export PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=${OMP_NUM_THREADS:-2}
export MKL_NUM_THREADS=${MKL_NUM_THREADS:-2}
export OPENBLAS_NUM_THREADS=${OPENBLAS_NUM_THREADS:-2}
export PATH=/opt/runtime/bin:$PATH
exec python /worker/worker.py
