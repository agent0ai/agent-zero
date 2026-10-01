# Agent Client Protocol

`_a0_acp` is the bundled Agent Client Protocol bridge. ACP-capable editors
start the local connector with:

```bash
a0 acp --host http://localhost:32081
```

The connector owns editor-hosted files and terminal access. The Agent Zero
runtime owns ACP session metadata, history, modes, and model settings. The
default transport is the connector; the hidden `transport: container` setting
is only a compatibility fallback for an already configured legacy `a0_acp`
plugin inside the selected container.

On startup, Agent Zero removes retired `usr/plugins/a0_acp` installations and
their project or agent overrides. The bundled `_a0_acp` configuration is kept.
