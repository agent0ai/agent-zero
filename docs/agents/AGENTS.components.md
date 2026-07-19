# Agent Zero Component System

> Generated from codebase reconnaissance on 2026-01-10
> Scope: `webui/components/` - Self-contained Alpine.js component architecture

## Quick Reference

| Aspect | Value |
|--------|-------|
| Tech Stack | Alpine.js, ES Modules, CSS Variables |
| Component Tag | `<x-component path="...">` |
| State Management | `createStore(name, model)` from `/js/AlpineStore.js` |
| Modals | `openModal(path)` / `closeModal()` from `/js/modals.js` |
| API Layer | `callJsonApi()` / `fetchApi()` from `/js/api.js` |

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Component Structure](#2-component-structure)
3. [Store Pattern](#3-store-pattern)
4. [Lifecycle Management](#4-lifecycle-management)
5. [Integration Layer](#5-integration-layer)
6. [Alpine.js Directives](#6-alpinejs-directives)
7. [Patterns and Conventions](#7-patterns-and-conventions)
8. [Pitfalls and Anti-Patterns](#8-pitfalls-and-anti-patterns)
9. [Porting Guide](#9-porting-guide)

---

## 1. Architecture Overview

### Core Files (Integration Layer)

| File | Purpose |
|------|---------|
| `/js/components.js` | Component loader - hydrates `<x-component>` tags |
| `/js/AlpineStore.js` | Store factory with Alpine proxy |
| `/js/modals.js` | Modal stack management |
| `/js/initFw.js` | Bootstrap: loads Alpine, registers custom directives |
| `/js/api.js` | CSRF-protected API client (`callJsonApi`, `fetchApi`) |

### Component Resolution

```
<x-component path="sidebar/left-sidebar.html">
                    ↓
    Resolves to: components/sidebar/left-sidebar.html
                    ↓
    Loader: importComponent() fetches, parses, injects
```

- Path auto-prefixes `components/` if not present
- Component HTML cached after first fetch
- Module scripts cached by virtual URL
- MutationObserver auto-loads dynamically inserted components

### Data Flow

```
Component HTML
    ↓
imports Store module
    ↓
createStore() registers with Alpine
    ↓
Template binds via $store.name
    ↓
User actions → store methods → state updates → reactive UI
```

---

## 2. Component Structure

### Anatomy of a Component

```html
<html>
<head>
  <!-- Module imports MUST be in <head> -->
  <script type="module">
    import { store } from "/components/feature/feature-store.js";
  </script>
</head>

<body>
  <!-- Store gate: prevents render until store registered -->
  <div x-data>
    <template x-if="$store.featureStore">
      <!-- Single root element inside template (mandatory) -->
      <div class="feature-container">
        <p x-text="$store.featureStore.value"></p>
        <button @click="$store.featureStore.action()">Do Thing</button>
      </div>
    </template>
  </div>

  <!-- Inline styles scoped to component -->
  <style>
    .feature-container {
      color: var(--color-text);
    }
  </style>
</body>
</html>
```

### Key Rules

| Rule | Rationale |
|------|-----------|
| Scripts in `<head>`, content in `<body>` | Loader extracts separately |
| Use `type="module"` for scripts | Enables ES imports, caching |
| Wrap with `x-data` + `x-if="$store.X"` | Prevents render before store ready |
| `<template>` has ONE root element | Alpine limitation |
| Styles inline in component | Self-contained, no global CSS files |

### Nesting Components

```html
<div class="parent-container">
  <x-component path="child/child-component.html"></x-component>
</div>
```

Components can nest other components. Loader recursively processes `x-component` tags.

---

## 3. Store Pattern

### Creating a Store

```javascript
// /components/feature/feature-store.js
import { createStore } from "/js/AlpineStore.js";

const model = {
  // State
  items: [],
  loading: false,
  _initialized: false,

  // Lifecycle (called once by Alpine when store registers)
  init() {
    if (this._initialized) return;
    this._initialized = true;
    this.load();
  },

  // Actions
  async load() {
    this.loading = true;
    // ... fetch data
    this.loading = false;
  },

  // Computed-like getters (Alpine reactivity works)
  get itemCount() {
    return this.items.length;
  }
};

export const store = createStore("featureStore", model);
```

### Store Proxy Behavior

`createStore()` returns a proxy that:
- Before Alpine boots: reads/writes directly to `model` object
- After Alpine boots: reads/writes through `Alpine.store(name)`

This enables safe module-level initialization before Alpine loads.

### Store Access

| Context | Syntax |
|---------|--------|
| Template (Alpine) | `$store.featureStore.prop` |
| Module import | `import { store } from "./feature-store.js"; store.prop` |
| Global (avoid) | `Alpine.store("featureStore").prop` |

Prefer module imports over global lookups.

### Persistence Helpers

```javascript
import { saveState, loadState } from "/js/AlpineStore.js";

// Save to localStorage (exclude functions automatically)
const snapshot = saveState(store, [], ["transientField"]);
localStorage.setItem("myStore", JSON.stringify(snapshot));

// Restore
const saved = JSON.parse(localStorage.getItem("myStore"));
loadState(store, saved);
```

---

## 4. Lifecycle Management

### Custom Alpine Directives

Registered in `/js/initFw.js`:

| Directive | When Fires | Use Case |
|-----------|------------|----------|
| `x-create` | Once on mount | Initialize, subscribe to events |
| `x-destroy` | On unmount/cleanup | Unsubscribe, clear timers |
| `x-every-second` | Every 1s while mounted | Polling, countdowns |
| `x-every-minute` | Every 60s while mounted | Low-frequency updates |
| `x-every-hour` | Every 3600s while mounted | Rare periodic tasks |

### Usage Pattern

```html
<div
  x-create="$store.myStore.onOpen()"
  x-destroy="$store.myStore.cleanup()"
>
  <!-- content -->
</div>
```

### Store Lifecycle Pattern

```javascript
const model = {
  _initialized: false,
  resizeHandler: null,

  init() {
    // Guard: runs only once per app lifetime
    if (this._initialized) return;
    this._initialized = true;
    // Global setup: event listeners, intervals
    this.resizeHandler = () => this.handleResize();
    window.addEventListener("resize", this.resizeHandler);
  },

  // Called via x-create when component mounts (can run multiple times)
  onOpen() {
    this.loadData();
  },

  // Called via x-destroy when component unmounts
  cleanup() {
    // Clear component-specific state, not global listeners
  },

  // For full teardown (rarely needed)
  destroy() {
    if (this.resizeHandler) {
      window.removeEventListener("resize", this.resizeHandler);
      this.resizeHandler = null;
    }
    this._initialized = false;
  }
};
```

Key distinction:
- `init()` → once per app load (store registration)
- `onOpen()` → each time component mounts (modal opens, etc.)
- `cleanup()`/`destroy()` → teardown resources

---

## 5. Integration Layer

### API Calls

```javascript
import { callJsonApi, fetchApi } from "/js/api.js";

// JSON POST with CSRF
const result = await callJsonApi("/endpoint", { key: "value" });

// Raw fetch with CSRF
const response = await fetchApi("/endpoint", {
  method: "GET",
  headers: { "Accept": "application/json" }
});
```

- `callJsonApi`: JSON-in, JSON-out, throws on non-2xx
- `fetchApi`: Adds CSRF header, handles 403 retry, redirects to `/login`

### Modals

```javascript
import { openModal, closeModal } from "/js/modals.js";

// Open (returns Promise that resolves when modal closes)
await openModal("feature/feature-modal.html");

// Close topmost modal
closeModal();

// Close specific modal by path
closeModal("feature/feature-modal.html");
```

Modal component receives title from `<title>` tag:
```html
<head>
  <title>My Modal Title</title>
</head>
```

Modal footer (outside scroll area):
```html
<div data-modal-footer>
  <button @click="closeModal()">Close</button>
</div>
```

### Attribute Inheritance

Parent `x-component` attributes accessible via `globalThis.xAttrs(element)`:

```html
<!-- Parent -->
<x-component path="child.html" mydata='{"id": 123}'></x-component>

<!-- Child can access -->
<script type="module">
  const attrs = globalThis.xAttrs(document.currentScript);
  console.log(attrs.mydata.id); // 123
</script>
```

---

## 6. Alpine.js Directives

### Common Patterns

| Pattern | Syntax |
|---------|--------|
| Reactive text | `x-text="$store.s.value"` |
| Conditional render | `x-if="$store.s.condition"` |
| Visibility toggle | `x-show="$store.s.visible"` |
| Class binding | `:class="{'active': $store.s.isActive}"` |
| Event handler | `@click="$store.s.action()"` |
| Two-way bind | `x-model="$store.s.inputValue"` |
| List iteration | `<template x-for="item in $store.s.items">` |
| Init expression | `x-init="$store.s.load()"` |

### Store Gating (Critical Pattern)

```html
<div x-data>
  <template x-if="$store.myStore">
    <!-- Renders only when store exists -->
  </template>
</div>
```

Always gate components that depend on stores. Prevents errors during initial load race.

---

## 7. Patterns and Conventions

### ✅ DO

| Pattern | Example |
|---------|---------|
| Self-contained components | All HTML/CSS/JS in one component folder |
| Module imports with absolute paths | `import { store } from "/components/..."` |
| CSS variables for theming | `color: var(--color-text)` |
| Guard `init()` with `_initialized` | Prevents duplicate setup |
| Use `display: contents` for flex chains | Wrapper doesn't break parent flex |
| Inline component styles | `<style>` in component `<body>` |
| Import stores in `<head>` | Ensures registration before render |
| Name stores uniquely | `createStore("featureStore", ...)` |

### CSS Variable Theming

```css
.component {
  background: var(--color-panel);
  color: var(--color-text);
  border: 1px solid var(--color-border);
  padding: var(--spacing-md);
  transition: all var(--transition-speed) ease-in-out;
  font-size: var(--font-size-normal);
}
```

### Flex Chain Preservation

When `x-component` wrapper would break flex layout:

```css
#parent-container > x-component,
#parent-container > x-component > div[x-data] {
  display: contents;
}
```

---

## 8. Pitfalls and Anti-Patterns

### 🚫 DON'T

| Anti-Pattern | Why | Fix |
|--------------|-----|-----|
| Global CSS files | Breaks encapsulation | Inline styles per component |
| `window.Alpine.store()` lookups | Timing issues, coupling | Import store module directly |
| Call `init()` from `x-init` | Runs multiple times | Use guard, or use `x-create` for per-mount |
| Multiple roots in `<template>` | Alpine breaks | Wrap in single `<div>` |
| `.catch(() => null)` for errors | Hides bugs | Let errors surface, use notifications |
| Scripts outside `<head>` | May not load before template | Move to `<head>` with `type="module"` |
| Hardcoded colors | Breaks theming | Use CSS variables |
| Relative imports `./file.js` | Path resolution issues | Use absolute `/components/...` |

### Common Mistakes

Race condition: store not ready
```html
<!-- ❌ BAD: No gate -->
<div x-data>
  <p x-text="$store.myStore.value"></p>
</div>

<!-- ✅ GOOD: Store gate -->
<div x-data>
  <template x-if="$store.myStore">
    <p x-text="$store.myStore.value"></p>
  </template>
</div>
```

Duplicate initialization
```javascript
// ❌ BAD: Runs every time store accessed
init() {
  window.addEventListener("resize", this.handler);
}

// ✅ GOOD: Guard pattern
init() {
  if (this._initialized) return;
  this._initialized = true;
  window.addEventListener("resize", this.handler);
}
```

Leaking listeners
```javascript
// ❌ BAD: No cleanup
init() {
  this.interval = setInterval(() => this.tick(), 1000);
}

// ✅ GOOD: With cleanup
init() {
  this.interval = setInterval(() => this.tick(), 1000);
},
destroy() {
  clearInterval(this.interval);
}
```

---

## 9. Porting Guide

### Minimum Requirements for External Apps

1. Files to copy:
   ```
   /js/components.js      # Component loader
   /js/AlpineStore.js     # Store factory
   /js/modals.js          # Modal system (optional)
   /js/initFw.js          # Alpine bootstrap + directives
   ```

2. Dependencies:
   - Alpine.js (vendor or CDN)
   - CSS variables (define your theme)

3. Bootstrap sequence:
   ```javascript
   // initFw.js pattern:
   await import("path/to/alpine.min.js");

   // Register custom directives
   Alpine.directive("destroy", ...);
   Alpine.directive("create", ...);
   // etc.
   ```

4. HTML entry point:
   ```html
   <script type="module" src="/js/initFw.js"></script>
   <x-component path="app/root.html"></x-component>
   ```

### Adaptation Checklist

- [ ] Define CSS variables for theming (`--color-*`, `--spacing-*`, etc.)
- [ ] Set up component directory structure
- [ ] Configure build tool to serve `/components/` path (or adjust loader)
- [ ] Create API wrapper matching your backend (replace `api.js`)
- [ ] Test MutationObserver behavior with your router/SPA framework
- [ ] Verify module caching behavior in production build

### Integration with Frameworks

| Framework | Consideration |
|-----------|--------------|
| Vanilla/Static | Works directly, include initFw.js |
| Electron | Works, may need CSP adjustments for Blob URLs |
| React/Vue | Mount Alpine in specific container, avoid conflicts |
| SPA Routers | MutationObserver handles dynamic inserts |

---

## Directory Structure Reference

```
webui/components/
├── _examples/               # Reference implementations
│   ├── _example-component.html
│   └── _example-store.js
├── chat/
│   ├── input/
│   │   ├── chat-bar.html
│   │   └── input-store.js
│   └── ...
├── sidebar/
│   ├── sidebar-store.js
│   ├── left-sidebar.html
│   └── chats/
│       └── chats-list.html
├── modals/
│   └── file-browser/
│       ├── file-browser.html
│       └── file-browser-store.js
├── notifications/
│   ├── notification-store.js
│   └── notification-toast-stack.html
└── settings/
    └── ...
```

Naming conventions:
- Components: `feature-name.html`
- Stores: `feature-store.js` or `feature-name-store.js`
- Modals: placed in `modals/` or feature folder

---

## Key Exports Summary

### `/js/components.js`
```javascript
export async function importComponent(path, targetElement)
export async function loadComponents(roots)
export function getParentAttributes(el)
// Global: globalThis.xAttrs
```

### `/js/AlpineStore.js`
```javascript
export function createStore(name, initialState)
export function getStore(name)
export function saveState(store, include, exclude)
export function loadState(store, state, include, exclude)
```

### `/js/modals.js`
```javascript
export function openModal(modalPath)
export function closeModal(modalPath?)
export function scrollModal(id)
// Globals: globalThis.openModal, closeModal, scrollModal
```

### `/js/api.js`
```javascript
export async function callJsonApi(endpoint, data)
export async function fetchApi(url, request)
```

---

## Addendum: Additional Patterns

### Alpine Transitions

Use `x-transition` for enter/leave animations:

```html
<div x-show="visible"
     x-transition:enter="fade-enter"
     x-transition:leave="fade-leave">
```

### Two-Click Confirmation (`$confirmClick`)

Magic helper for destructive actions:

```html
<button @click="$confirmClick($event, () => $store.myStore.delete(item.id))">
  <span class="material-symbols-outlined">delete</span>
</button>
```

First click arms (icon changes to checkmark), second click confirms. Auto-resets after 2s.

### Device Detection

Body receives `device-touch` or `device-mouse` class via `/js/initializer.js`. Use for input-type-specific styling:

```css
.device-touch .hover-only { display: none; }
```

### CSS Variables Reference

Defined in `/webui/index.css`:

| Variable | Purpose |
|----------|---------|
| `--color-background` | Page background |
| `--color-text` | Primary text |
| `--color-primary` | Headings, emphasis |
| `--color-panel` | Card/sidebar backgrounds |
| `--color-border` | Borders, dividers |
| `--color-accent` | Highlights, actions |
| `--color-input` | Form field backgrounds |
| `--spacing-xs/sm/md/lg` | Consistent spacing scale |
| `--font-size-small/normal/large` | Typography scale |
| `--transition-speed` | Animation duration (0.3s) |

Theme switching via `.light-mode` class on root element.

---

*End of Component System Documentation*
