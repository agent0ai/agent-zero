# WebUI CSS DOX

## Purpose

- Own shared stylesheet modules for the WebUI.
- Keep shared visual primitives stable across components and pages.

## Ownership

- Each CSS file owns a named surface or primitive family such as buttons, messages, modals, notifications, scheduler, settings, surfaces, tables, or toast.
- Component-specific styles should usually stay inside the component HTML unless they are intentionally shared.
- `modals.css` owns the shared stacked modal shell, backdrop, scroll area, footer slot, modal button classes, floating/no-backdrop modal behavior, and shared modal section primitives.
- `surfaces.css` owns surface modal switchers, action rails, draggable header affordances, focus-button state, and right-canvas surface primitives.
- `index.css` defines global theme variables such as `--color-*`, `--spacing-*`, `--font-size-*`, and `--transition-speed`.

## Local Contracts

- Use existing CSS variables and naming patterns before introducing new global tokens.
- Avoid broad selectors that unexpectedly restyle plugin UI or unrelated components.
- Keep layout rules responsive and verify text does not overflow fixed controls.
- Shared modal buttons use `btn btn-ok` for positive actions and `btn btn-cancel` for dismissive or negative actions.
- Shared compact text actions use `.text-button`; component-local styles may adjust layout or sizing but must not be the only definition of the primitive.
- Modal footer action order is positive action first, dismissive or negative action second.
- Modal footers use `.modal-footer` plus `data-modal-footer`; do not redefine `.btn`, `.modal-footer`, `.modal-inner`, or `.modal-scroll` inside components.
- Shared modal sizing keeps `.modal-inner` centered with `width: 90%`, `max-width: 960px`, and `max-height: 90vh`.
- Tall modal bodies must scroll inside `.modal-scroll`; pinned footer content must stay outside that scroll area.
- `.modal-floating` must keep the full-screen shell pointer-transparent while `.modal-inner` remains pointer-active.
- Use `.modal-no-backdrop` only for backdrop suppression without click-through floating behavior.
- Shared modal layers must stay above the mobile right-canvas rail while confirmation dialogs remain above normal modals.
- Do not add decorative one-note palette changes that conflict with existing WebUI design.

## Work Guidance

- Keep shared CSS small and scoped to clear class families.
- Coordinate class renames with all component and plugin references.
- Prefer improving an existing primitive over creating a near-duplicate style family.
- Use component-local styles for unique layouts and shared CSS for repeated primitives such as modal sections, toolbars, buttons, tables, notifications, and surfaces.
- Preserve modal sizing and scrolling expectations: centered `.modal-inner`, constrained viewport height, body scroll inside `.modal-scroll`, and footer outside the scroll area.

## Verification

- Manually inspect affected WebUI screens at desktop and mobile widths for shared CSS changes.
- Run visual or frontend tests if the touched style has coverage.
- For modal CSS, test a tall modal, a footer modal, a stacked modal, and a floating modal.

## Child DOX Index

No child DOX files.
