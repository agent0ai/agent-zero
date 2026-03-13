# Agent Zero (Fork)

Custom fork of [agent0ai/agent-zero](https://github.com/agent0ai/agent-zero) for the AI Girlfriend platform (muza.live).

## Versioning

- Versions follow upstream tags: `v0.9.8.2` → `v0.9.8.3` → ...
- The hassio addon (`agent-zero-hassio`) version MUST match the fork tag. They never diverge.
- To release: tag the fork commit, then set the same version in `agent-zero-hassio/agent_zero/config.yaml`.

```
# Tag a release
git tag -a v0.9.8.4 -m "description"
git push origin v0.9.8.4

# Then update hassio config.yaml version to "0.9.8.4" and push
```

## Fork changes vs upstream

All fork-specific changes are on `main`. Key additions:
- Task self-recovery (ERROR and stuck RUNNING states)
- Skill installation via `/skill-install` chat command
- Structured RFC 3339 logging
- Accurate token counting via `litellm.token_counter`
- Truncation detection and retry for LLM streams
- Metrics persistence across container restarts

## Upstream sync

- Upstream remote: `upstream` → `https://github.com/agent0ai/agent-zero.git`
- Merge upstream changes carefully — fork diverges significantly in some areas.
