# Agent Zero on Docker Swarm + Tailnet

This guide deploys **Agent Zero only** (no OpenClaw) using Docker Swarm and exposes it on your Tailscale tailnet.

## Prerequisites

- Docker Engine installed and running
- `docker` CLI access for your user
- Tailscale installed and authenticated (`tailscale up`)

## Files Added

- `docker/swarm/agent-zero-stack.yml` – Swarm stack definition
- `scripts/deploy_agent_zero_swarm.sh` – deploy/status/remove helper
- `scripts/expose_agent_zero_tailnet.sh` – tailnet exposure helper

## 1) Deploy the Swarm stack

From the repository root:

```bash
bash scripts/deploy_agent_zero_swarm.sh deploy
```

What it does:

- Initializes swarm if not active
- Deploys stack `agent-zero`
- Publishes Agent Zero on host port `5000` (default)

Open locally:

- `http://<swarm-node-ip>:5000`

### Optional deployment variables

```bash
AGENT_ZERO_REPLICAS=3 \
AGENT_ZERO_PUBLISHED_PORT=5000 \
AGENT_ZERO_IMAGE=frdel/agent-zero-run:latest \
bash scripts/deploy_agent_zero_swarm.sh deploy
```

Check service state:

```bash
bash scripts/deploy_agent_zero_swarm.sh status
```

Remove stack:

```bash
bash scripts/deploy_agent_zero_swarm.sh remove
```

## 2) Expose Agent Zero on Tailnet

After stack deployment:

```bash
AGENT_ZERO_PUBLISHED_PORT=5000 bash scripts/expose_agent_zero_tailnet.sh up
```

This configures:

- `tailscale serve` to proxy tailnet HTTPS traffic to `http://127.0.0.1:5000`

Check serve status:

```bash
bash scripts/expose_agent_zero_tailnet.sh status
```

Disable exposure:

```bash
bash scripts/expose_agent_zero_tailnet.sh down
```

## Notes for multi-replica runs

- Default is `AGENT_ZERO_REPLICAS=1`.
- Increasing replicas creates multiple container instances behind Swarm ingress.
- Agent Zero data under `/a0` is backed by a Docker named volume (`agent_zero_data`). For true multi-node persistent behavior, use shared storage (NFS, CSI, etc.) and update the volume driver/config accordingly.
