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

## Agent Zero Version Requirements

Use optional `a0_version` in the plugin repository's root `plugin.yaml` to
declare the supported **Agent Zero** versions. The existing `version` field
still describes the plugin's own release. Quote version requirements so YAML
does not interpret numbers or wildcards as another type.

```yaml
version: 1.0.0
a0_version: ">=3.0,<4.0"
```

| Value of `a0_version` | Allowed Agent Zero versions |
| --- | --- |
| `"3.0"` or `"==3.0"` | Exactly 3.0 (also 3.0.0) |
| `">=3.0,<4.0"` | At least 3.0, below 4.0; commas mean AND |
| `"3.0 - 3.5"` | Inclusive range from 3.0 through 3.5 |
| `"3.*"` or `"3.1.*"` | Any release with that numeric prefix |
| `["2.15", ">=3.0,<4.0", "5.*"]` | Any listed alternative; lists mean OR |
| `"*"`, omitted, `null`, `""`, or `[]` | No version restriction |

Comparisons use Python packaging version/specifier semantics: optional `v`
prefixes are accepted, versions compare numerically, and `>`, `>=`, `<`, `<=`,
`==`, `!=`, and `~=` are supported. Prereleases are considered but must satisfy
the comparisons (`3.0rc1` is below `3.0`). A build suffix such as `+29` does not
prevent a match against the corresponding public version. Use YAML lists for
alternatives, not npm `||`, `^`, or `x` syntax.

The Plugin Hub reads this field from the repository's default-branch manifest;
it does not require a duplicate field in the Plugin Index's `index.yaml`.
The detail page shows the allowed versions and the installed A0 release tag
reported by `helpers.git.get_version()`. Clicking Install checks the manifest
again. A mismatch shows a warning with both values and **Cancel** / **Install
Anyway**. Unreadable manifests, invalid requirements, or unrecognized fork
versions show an unverified-compatibility warning with the same choice.
The usual plugin security confirmation still applies after continuing.

This is an advisory Hub installation check, not a plugin loading or activation
restriction. Declare versions you have verified; a matching version is not a
guarantee that the plugin will work with a custom fork.

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
