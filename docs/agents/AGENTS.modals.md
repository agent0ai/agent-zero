# Agent Zero — Frontend Modals (stacked `openModal/closeModal`)

This document covers the stacked modal system used by Agent Zero’s frontend, implemented in:

- `webui/js/modals.js`
- `webui/css/modals.css`

It also defines conventions for writing modal components in `webui/components/modals/` and `webui/components/settings/`.

> Legacy note: there is an older overlay / teleport modal style in the codebase (e.g. `x-teleport` + `.modal-overlay`). Avoid it for new work. This doc is about the stacked modal system.

---

## Prerequisites & concepts (quick orientation)

### Alpine.js and `$store`

The UI uses Alpine.js for reactivity (`x-show`, `x-if`, `x-on`, `x-model`, …). Stores are registered via `createStore()` and read in HTML via `$store.<storeName>`.

- Alpine initialization + lifecycle directives: `webui/js/initFw.js`
- Store wrapper: `webui/js/AlpineStore.js`

### `<x-component>` and `importComponent()`

Agent Zero uses a custom `<x-component path="...">` tag that is populated by the component loader.

The modal system does not rely on `<x-component>` directly; instead it calls the same loader function:

- `importComponent(path, targetElement)` from `webui/js/components.js`

That loader fetches component HTML, injects its `<style>` and `<script>` tags, and supports nested components.

---

## Why a “stacked modal system”?

Agent Zero can open modals from many places (sidebar, settings, message actions), and sometimes a modal opens another modal.

The stacked system provides:

- A single modal container structure for consistent UI
- A stack so nested modals work predictably
- A single backdrop that always sits behind the active modal
- A content loader that supports component HTML + `<style>` + `<script type="module">` the same way `<x-component>` does

---

## Core API

File: `webui/js/modals.js`

### `openModal(modalPath): Promise<void>`

- Creates a new modal element and pushes it onto a stack.
- Loads modal contents into the modal body by calling the component loader (`importComponent`).
- Resolves the returned promise when the modal element is removed from the DOM.

Edge cases / failure behavior (current implementation):

- Invalid `modalPath` does not reject the returned promise. Instead, the modal remains open and shows an error message inside the modal body; the promise still resolves when the user closes the modal.
- Calling `openModal()` multiple times with the same `modalPath` creates multiple modal instances (no deduping).

Modal paths are component paths, e.g.:

- `modals/file-browser/file-browser.html`
- `modals/history/history.html`
- `settings/settings.html`

### `closeModal(modalPath?: string): void`

- If no path is passed, closes the top modal.
- If `modalPath` is passed, finds and closes that modal in the stack.

Edge cases / failure behavior:

- If the stack is empty, `closeModal()` is a no-op.
- If `modalPath` is provided but not found, it is a no-op.

### `scrollModal(id: string): void`

Scrolls within the top modal’s `.modal-scroll` to an element by id.

---

## Modal DOM structure (what `modals.js` creates)

When `openModal()` runs, it creates this outer shell:

- `.modal` (full-screen fixed overlay container)
  - `.modal-inner`
    - `.modal-header` (title + close button)
    - `.modal-scroll`
      - `.modal-bd` (where the component HTML is imported)
    - `.modal-footer-slot` (used when the modal provides a footer)

The component HTML is imported into `.modal-bd`.

The title is taken from `<title>` inside the imported document (fallback: the modalPath).

### Sizing and scrolling (CSS behavior)

File: `webui/css/modals.css`

- `.modal` is full-screen fixed positioning.
- `.modal-inner` is centered and constrained:
  - `width: 90%`
  - `max-width: 960px`
  - `max-height: 90vh`
- Tall modals scroll inside `.modal-scroll` (`overflow-y: auto`).
- If the modal provides a footer, `.modal-footer-slot` is pinned under the scroll area (the body scrolls; the footer doesn’t).

---

## Footer support (`data-modal-footer`)

Some modals want a footer that stays fixed while the body scrolls.

Pattern:

- In your modal component HTML, include a footer element marked with `data-modal-footer`.
- `modals.js` will move that element out of the scroll area and into `.modal-footer-slot`.
- `modals.js` adds `.modal-with-footer` to `.modal-inner` so CSS can lay out the scroll area correctly.

Example patterns in the repo:

- `webui/components/settings/settings.html` (Save / Cancel footer)
- `webui/components/modals/file-browser/file-browser.html`
- `webui/components/modals/scheduler/scheduler-modal.html`

### Practical advice

- The footer element must exist *after the component is loaded*, but `modals.js` uses a `requestAnimationFrame` to let Alpine mount first.
- If you conditionally render the footer, keep it stable (don't constantly create/destroy it) or you'll fight the relocation.

---

## Shared CSS and button conventions

File: `webui/css/modals.css`

Modals should reuse shared CSS classes rather than redefining common styles. The modal system provides base classes for buttons, footers, and layout that work consistently across all modals.

### Button classes

Use these standard button classes for modal actions:

| Class | Use case | Visual style |
|-------|----------|--------------|
| `btn btn-ok` | Positive/confirmatory actions (Save, Create, Confirm) | Solid blue background, white text |
| `btn btn-cancel` | Dismissive/negative actions (Cancel, Close, Delete) | Transparent with accent border |

Footer button order convention: positive action first (left), negative action second (right).

Example footer markup:

```html
<div class="modal-footer" data-modal-footer>
  <button class="btn btn-ok" @click="$store.myStore.save()">Save</button>
  <button class="btn btn-cancel" @click="window.closeModal('...')">Cancel</button>
</div>
```

### Available shared classes

Before writing component-specific CSS, check `webui/css/modals.css` for:

- `.btn`, `.btn-ok`, `.btn-cancel`, `.btn-field` — button styles
- `.modal-footer` — footer container layout
- `.section`, `.section-title`, `.section-description` — content sections
- `.loading` — shimmer loading placeholder
- `.toolbar-button`, `.toolbar-group` — editor toolbar elements
- Range input styling for sliders

### When to add component-specific CSS

Add styles in your component's `<style>` tag only when:

- The style is truly unique to that component's layout/behavior
- No existing shared class covers the use case
- You need to override a shared class for a specific context (use sparingly)

Avoid redefining `.btn`, `.modal-footer`, or other shared classes in component CSS—this creates inconsistency and maintenance burden.

---

## Closing behavior (what users expect)

### Close by button

The shell provides a close button (`.modal-close`) that always closes the top modal.

### Close by Escape

`Escape` closes the top modal only (stack semantics).

### Close by click-outside

To avoid accidental close during drag/select, the shell only closes on click-outside when:

- both `mousedown` and `mouseup` occurred on the modal container itself (`.modal`), not on inner content.

---

## Stacking + backdrop + z-index

File: `webui/js/modals.js`

- A single `.modal-backdrop` is used for all modals.
- Z-index logic:
  - Base z-index for modals is `3000`
  - Each modal gets `base + index*20`
  - Backdrop sits below the top modal, and between the top two when multiple modals are open.

Outcome:

- Nested modals don’t “flatten” into each other.
- The backdrop always darkens the page behind the active modal without hiding lower modals incorrectly.

### Floating no-backdrop modals

Use `.modal-floating` on the outer `.modal` when a modal should behave like a floating utility panel instead of a blocking dialog. This is for special live surfaces where the user should keep seeing and interacting with the chat or dashboard behind the panel. The Browser now primarily lives in the Canvas, Agent Zero's right-side workspace for live surfaces, but its floating/windowed surface follows the same non-blocking modal contract.

Working contract:

- `.modal-floating` suppresses the shared `.modal-backdrop` for that modal.
- `.modal-floating` makes the full-screen `.modal` shell pointer-transparent.
- `.modal-floating .modal-inner` remains pointer-active, so the floating panel itself still receives clicks, keyboard focus, drag handlers, resize handles, and form input.
- Floating modal sizing, dragging, and resizing are still component-owned unless promoted to shared modal CSS later. The modal system only provides the backdrop and pointer-event behavior.

Good to know:

- A floating modal does not close by clicking the page behind it, because those clicks pass through to the app. Keep an obvious close button in the modal header.
- If a floating modal opens another normal modal, the normal modal can still use the backdrop; stacking remains governed by the shared z-index logic.
- Use `.modal-no-backdrop` only when a component needs backdrop suppression without click-through floating behavior. Prefer `.modal-floating` for utility panels.
- Do not use `.modal-floating` for destructive confirmations, settings forms, auth, import/export, or workflows that require the user to finish or dismiss the dialog before interacting with the rest of the app.

---

## Writing a modal component (conventions)

### File location

Prefer:

- `webui/components/modals/<name>/<name>.html` (+ optional `*-store.js`)

Settings uses:

- `webui/components/settings/settings.html` and nested settings components.

### Recommended HTML skeleton

Use this structure:

- `<head><title>...</title>`
- A `<script type="module">` that imports your store (so it registers before Alpine evaluates bindings)
- `<body>` with:
  - a single root wrapper
  - Alpine lifecycle hooks (`x-create`/`x-init` + `x-destroy`) to run open/cleanup logic
- A `<style>` tag at the bottom of the component file containing all modal-specific styling

Good examples:

- `webui/components/modals/history/history.html`
- `webui/components/modals/context/context.html`
- `webui/components/modals/scheduler/scheduler-modal.html`

### Store conventions

- Define stores via `createStore()` from `webui/js/AlpineStore.js`.
- UI reads state through `$store.<storeName>`.
- Prefer a small public API:
  - `open()` / `openModal()` to open the modal
  - `destroy()` / `cleanup()` to reset transient state

---

## “Don’t” list (keeps the system sane)

- Don’t add `document.addEventListener('alpine:init', ...)` blocks inside component HTML — it conflicts with `initFw.js` ordering and can register handlers twice when components are reloaded.
- Don’t manually manipulate `.modal-inner` or `.modal-scroll` structure — `modals.js` owns the shell and footer-slot mechanics; manual changes create layout/scroll bugs.
- Don’t introduce a new modal overlay system; keep the stack, mixed systems break z-index/backdrop expectations and make nested modals unreliable.
- Don’t assume a modal is the only one open; always write logic that behaves correctly when stacked — `Escape`/close behavior, z-index, and focus should all be “top modal wins”.
- Don’t open a new modal synchronously from another modal’s close handler — it can race stack removal and produce transient z-index/backdrop glitches; schedule via `requestAnimationFrame` if needed.
- Don’t store sensitive data in modal stores without explicit cleanup — stores often outlive a modal’s DOM and can leak values across reopen.
- Don’t rely on modal state persisting across close/reopen cycles — design stores so `open()` rehydrates and `destroy()`/`cleanup()` resets transient state.

---

## Debugging checklist

### Modal opens but content never appears

- Verify the path passed to `openModal()` is correct and resolves under `webui/components/`.
- Check browser console for fetch/import errors.
- If you use `<script type="module" src="...">` in the component, ensure the URL is correct.

### Footer is inside the scroll area (not pinned)

- Ensure your footer element has the `data-modal-footer` attribute.
- Ensure it exists after the component loads (if you gate it behind `x-if`, ensure the store is available).

### Closing behavior is weird with nested modals

- Remember `Escape` closes only the top modal.
- `closeModal('some/path.html')` closes that modal wherever it is in the stack.

### Modal opens but `$store.someStore` is undefined

- Ensure the modal HTML imports its store in a `<script type="module">` block (so the store registers before Alpine evaluates bindings).
- Ensure the store name matches what the markup reads (store registered as `createStore("history", ...)` is accessed as `$store.history`).
- If you guard with `<template x-if="$store.someStore">`, verify you’re using the correct store key and not a stale name.

### Modal won’t close / UI feels “stuck”

- `closeModal()` removes the modal element immediately; if your store keeps polling or timers alive, the UI may still feel active—ensure you have `x-destroy` cleanup (`destroy()`/`cleanup()`).
- As a last resort, inspect and remove leftover modal nodes in DevTools (`document.querySelectorAll('.modal').forEach(m => m.remove())`) and reset any store state that assumes the modal is open.

### Inspecting stack/z-index issues

- In DevTools Elements:
  - inspect `.modal` elements (multiple means you have a stack)
  - check the `style="z-index: ..."` on `.modal-inner`
  - verify `.modal-backdrop` exists and sits between modals when stacked
- If the footer is not pinned, confirm your footer element has `data-modal-footer` and that `.modal-inner` has `.modal-with-footer`.
