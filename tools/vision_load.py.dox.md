# vision_load.py DOX

## Purpose

- Own the `vision_load.py` agent tool.
- This module loads images into model-visible content for vision-capable models.
- Keep this file-level DOX profile synchronized with `vision_load.py` because this directory is intentionally flat.

## Ownership

- `vision_load.py` owns the runtime implementation.
- `vision_load.py.dox.md` owns durable notes about responsibilities, contracts, side effects, and verification for that implementation.
- Classes:
- `VisionLoad` (`Tool`)
  - `async execute(self, paths: list[str]=..., **kwargs) -> Response`
  - `async after_execution(self, response: Response, **kwargs)`
- Notable constants/configuration names: `TOKENS_ESTIMATE`.

## Runtime Contracts

- Tool modules must define `helpers.tool.Tool` subclasses and return `helpers.tool.Response` from `execute(...)`.
- Update this file whenever tool arguments, output shape, `break_loop` behavior, intervention handling, prompt instructions, or side effects change.
- `VisionLoad` is a `Tool`.
- `VisionLoad` defines `execute(...)`.
- Observed side-effect areas: filesystem writes, model calls, plugin state, settings/state persistence, secret handling.
- Imported dependency areas include: `helpers`, `helpers.print_style`, `helpers.tool`, `mimetypes`.

## Key Concepts

- Important called helpers/classes observed in the source: `self._get_max_embeds`, `Response`, `str.strip`, `self._context_id`, `chat_media.infer_source`, `chat_media.category_for_source`, `chat_media.save_image_base64`, `chat_media.save_image_data_url`, `chat_media.materialize_image_ref`, `str.strip.lower`, `ephemeral_images.is_ref`, `cls._is_data_image_url`, `self._is_data_image_url`, `plugins.get_plugin_config`, `images.to_data_url`, `normalized.startswith`, `ephemeral_images.display_ref`, `join`, `self.agent.hist_add_tool_result`, `history.RawMessage`.
- Keep request/response, tool, or helper semantics documented here at the same time as source changes.

## Work Guidance

- Keep tool output concise, model-readable, and safe for history persistence.
- Coordinate argument or behavior changes with prompt tool instructions and skill guidance.
- Respect intervention flow for long-running, external, or user-visible operations.

## Verification

- Run targeted tool and prompt-contract tests for changed behavior; smoke-test agent execution when no focused test exists.
- Related tests observed by source search:
  - `tests/test_browser_agent_regressions.py`
  - `tests/test_host_browser_connector.py`
  - `tests/test_office_desktop_state.py`
  - `tests/test_vision_load_image_refs.py`

## Child DOX Index

No child DOX files.
