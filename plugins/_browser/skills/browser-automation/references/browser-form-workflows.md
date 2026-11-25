# Browser Forms

Read this guide when the page state may depend on selects, checkboxes, radios, file uploads, contenteditable fields, validation, or visual confirmation.

Start with `browser:content` and use fresh refs or a selector to identify fields. Use `click` and `type` on those fields. Read a checkbox's current state before clicking it. For native selects or validation, inspect the control and its value with `evaluate`. Chromium trusted keyboard input is available through CDP `Input.dispatchKeyEvent`. Use `upload_file` for a file input with a verified file path.

Click the identified submit control once. Verify the resulting confirmation or validation message with `content`. Use `browser:screenshot` plus `vision_load` when layout or visual state matters.

When `cdp` is unavailable, read the browser controls reference in `browser-automation`. Where supported, use `select_option` for dropdowns and `set_checked` for checkboxes.
