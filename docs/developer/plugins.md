# Plugins

Most people should start with the practical guide:
[Create a Small Plugin](../guides/create-plugin.md).

Plugin architecture and source-linked internals live in
[DeepWiki for Agent Zero](https://deepwiki.com/agent0ai/agent-zero). This page
stays intentionally small so the repository does not maintain a second plugin
manual.

## What To Use

| Goal | Start here |
| --- | --- |
| Build your first plugin | [Create a Small Plugin](../guides/create-plugin.md) |
| Choose where plugin dependencies run | [Sandboxed plugin runtimes](plugin-sandboxes.md#choosing-dependency-location) |
| Understand how plugins are loaded | [DeepWiki](https://deepwiki.com/agent0ai/agent-zero) |
| Decide what is safe to publish | [Sharing and Safety](sharing-and-safety.md) |
| Contribute a plugin upstream | [Contributing Guide](../guides/contribution.md) |

## Minimum Local Plugin

A local plugin usually lives here:

```text
/a0/usr/plugins/<plugin_name>/
├── plugin.yaml
├── README.md
└── webui/
```

The smallest useful `plugin.yaml` looks like this:

```yaml
name: my_plugin
title: My Plugin
description: A short sentence that explains what it does.
version: 1.0.0
```

Ask Agent Zero to keep the first version small. A tiny plugin that does one
visible thing is easier to test, review, and share.

## Plugin Dependencies

Prefer existing sandbox/worker facilities for plugin-owned Python, Node and native
packages, including inference, browser/document/media workers and integration
clients. Keep lightweight tools, hooks, configuration and authenticated API/UI
adapters in the framework and call the guest. Install in the main environment
only when functionality must execute there; document that concrete need and keep
the dependency set minimal. Hooks still run in the framework.

Lifecycle hooks and management APIs own setup and cleanup. They can delegate to
automatic guest setup on first use, or at enablement/startup for features and
listeners that need early readiness; no manual post-install step is required.
Use the [sandbox guide](plugin-sandboxes.md#choosing-dependency-location) for the
existing pattern. Lazy setup reduces the shipped/default dependency footprint,
but may not reduce total disk usage after the feature is used.

## Sharing A Plugin

Before publishing a plugin:

- keep it in its own public repository;
- include a clear `README.md`;
- include a `LICENSE`;
- avoid secrets, local paths, and machine-specific files;
- explain what the plugin changes and how to remove it.

For Plugin Index submission, use the current instructions in the
[`agent0ai/a0-plugins`](https://github.com/agent0ai/a0-plugins) repository.

## Related

- [Create a Small Plugin](../guides/create-plugin.md)
- [Sharing and Safety](sharing-and-safety.md)
- [DeepWiki for Agent Zero](https://deepwiki.com/agent0ai/agent-zero)
