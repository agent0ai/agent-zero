# Installer Menu, Management, and Tag Selection Improvements

## Goal

Add an interactive installer flow that detects running Agent Zero containers, offers install-or-manage choices, supports basic container management actions, and lets new installs choose an image tag with a safe `latest` default.

## Steps

1. **Refactor entrypoint and running-container menu** — Add function-based flow control and detect running Agent Zero containers after Docker checks. When containers are running, show Install vs Manage; otherwise continue directly with installation.
2. **Implement install flow with Docker Hub tag selection** — Expand the install path to create a new named instance, fetch available tags from Docker Hub, and let users select one before configuration prompts. Keep `latest` as the fallback when no selection is made or tag lookup fails.
3. **Implement manage flow start/stop/open actions** — Build the manage path to list existing Agent Zero containers, let users choose one, and execute Start, Stop, or Open in browser actions from a small action menu.
4. **Run final regression and UX validation** — Execute syntax and flow checks with mocked commands, fix any prompt routing/default issues, and ensure error handling remains robust without broadening scope.

## Acceptance Criteria

- [ ] Running-container branch: When at least one Agent Zero container is running, the script shows Install and Manage options; when none are running, it skips this menu and starts install flow.
- [ ] Tag selection behavior: Install flow lists Docker Hub tags and defaults to `latest` when the user gives no tag input or tag retrieval fails.
- [ ] New-instance isolation: New installs write compose config under `~/.agentzero/<container_name>/docker-compose.yml` and use `agent0ai/agent-zero:<selected_tag>`.
- [ ] Management actions: Manage flow can select a container and execute Open in browser, Start, and Stop actions correctly.
- [ ] Script quality: `sh -n install.sh` passes (and `dash -n install.sh` passes when dash exists), confirming POSIX-safe syntax.
- [ ] Scope discipline: Implementation touches `install.sh` only.
