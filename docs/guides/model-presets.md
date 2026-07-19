# Model Presets

Model Presets are named, reusable model setups. Every setup contains a main,
utility, and embedding model.

Use them when you want to switch a chat between setups such as "fast", "cheap",
"local", "balanced", or "maximum power" without rebuilding the settings each
time.

## Choose A Preset

The preset menu is the first dropdown on the left side of the chat status bar.
Its closed label shows the preset and the short main-model name, without the
provider prefix.

![Model preset selector](../res/usage/webui/model-preset-selector.png)

1. Open a chat.
2. Click the current preset name.
3. Choose the preset you want.

The selected preset affects the current chat. Choose **Use scoped preset** to
return the chat to the default selected for its project and agent profile. If no
more specific choice exists, Agent Zero uses the global preset.

The **Default** preset is always available. You can edit its models, but you
cannot rename or delete it.

## Initial Presets

When no saved preset collection exists at startup, Agent Zero downloads the
curated **Default**, **Efficiency**, and **Power** presets from the public
[`agent0ai/a0-presets`](https://github.com/agent0ai/a0-presets) repository. If
GitHub is unavailable or the file is invalid, Agent Zero saves its bundled
plugin fallback instead. Existing saved presets short-circuit this check and
are never replaced.

## Edit Presets

Click **Edit presets** from the same menu.

From this screen you can:

- rename presets;
- choose the main model;
- choose the utility model;
- choose the embedding model;
- enter the shared API key for each model provider;
- open API key settings;
- add or delete presets (except **Default**);
- save the preset list.

Think of a preset as a label on a model setup.

| Field | Simple meaning |
| --- | --- |
| **Main model** | The model that does the main conversation and reasoning. |
| **Utility model** | A smaller helper model for lighter internal tasks. |
| **Embedding model** | The model that creates vectors for memory and knowledge retrieval. |

The editor presents each preset as one complete setup. Internally, an existing
non-default preset may inherit omitted advanced values from **Default**.

## Add A Preset

Click **Add**, give it a name, choose models, then click **Save**.

Good preset names are easy to spot quickly:

- `Max Power`
- `Balanced`
- `Fast Cheap`
- `Local Private`
- `GPT-5 Mini`
- `Claude Opus`
- `Kimi Budget`

Some people prefer names based on purpose. Others prefer names that look like
the model they use most. Both are fine. The important thing is that your eyes
can find the right option quickly.

## A Simple Starting Set

If you are not sure what to create, start with three presets:

| Preset | Use it for |
| --- | --- |
| **Best** | Hard work where quality matters more than cost or speed. |
| **Balanced** | Everyday chats, coding, writing, and research. |
| **Cheap** | Simple tasks, quick drafts, summaries, and tests. |

You can always rename them later.

## Choose Defaults For New Chats

In **Settings → Agent → Models**, choose the global preset used by new chats.
The summary shows its main, utility, and embedding models. Changing it also
applies that preset to the currently open chat.

Use **Per-project / agent** to open the full Model Configuration plugin. Its
scope selector lets you choose a different default preset for a project, an
agent profile, or their combination. These scopes store only the preset choice;
editing a preset updates every scope that uses it.

## How Presets Fit With Other Controls

| Control | What it changes |
| --- | --- |
| **Model Preset** | Which main, utility, and embedding models power the chat. |
| **Agent Profile** | The agent's role, tone, and prompt behavior. |
| **Project** | Workspace, files, memory, secrets, and project instructions. |
| **Skill** | A specific procedure added to prompt protocol. |

For example, you can use the same "Researcher" Agent Profile with a cheaper
preset for simple questions and a stronger preset for difficult investigations.
