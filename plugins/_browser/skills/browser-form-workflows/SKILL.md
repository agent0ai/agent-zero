---
name: browser-form-workflows
description: Use for complex Agent Zero Browser form workflows involving selects, checkboxes, radios, file uploads, contenteditable fields, multi-step validation, or visually verified submission.
---

# Browser Forms

Use this skill for complex Browser form workflows where the page state may depend on selects, checkboxes, radios, file uploads, contenteditable fields, validation, or visual confirmation.

Start with `browser:content` to capture current refs, then use `browser:detail` on ambiguous fields before acting. Prefer ref-based form actions before coordinates.

Use `select_option`, `set_checked`, `upload_file`, `type`, `type_submit`, and `submit` for form interaction. Use coordinates only when no stable ref exists or the UI is intentionally canvas-like.

Use `browser:screenshot` plus `vision_load` when layout, visual validation, captcha-like UI, canvas content, or hidden state matters. Browser screenshots are not automatically loaded into model-visible history.

Verify after submission with `browser:content`, `browser:state`, or another explicit `browser:screenshot` plus `vision_load`.

Do not guess file paths for upload. Verify that every path exists before calling `upload_file`.
