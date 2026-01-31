// Inline button two-click confirmation for destructive actions.
// First click arms, second click confirms, timeout resets.

const CONFIRM_TIMEOUT = 2000;
const CONFIRM_CLASS = 'confirming';
const CONFIRM_ICON = 'check';
const CONFIRM_TEXT = 'Confirm';

const buttonStates = new WeakMap();

// Handles inline two-click confirmation for a button.
export function confirmClick(event, action) {
  const button = event.currentTarget;
  if (!button) return;

  const state = buttonStates.get(button);

  if (state?.confirming) {
    clearTimeout(state.timeoutId);
    resetButton(button, state);
    buttonStates.delete(button);
    action();
  } else {
    const iconEl = button.querySelector('.material-symbols-outlined, .material-icons-outlined');
    // Check if only icon is visible (no visible text children)
    const textSpans = button.querySelectorAll('span:not(.material-symbols-outlined):not(.material-icons-outlined)');
    const hasVisibleText = Array.from(textSpans).some(span => {
      const style = window.getComputedStyle(span);
      return style.display !== 'none' && span.textContent.trim() !== '';
    });
    const isIconButton = iconEl && !hasVisibleText;
    
    const newState = {
      confirming: true,
      isIconButton,
      originalIcon: iconEl?.textContent?.trim(),
      originalHTML: isIconButton ? null : button.innerHTML,
      timeoutId: setTimeout(() => {
        resetButton(button, newState);
        buttonStates.delete(button);
      }, CONFIRM_TIMEOUT)
    };
    
    buttonStates.set(button, newState);
    button.classList.add(CONFIRM_CLASS);
    
    if (isIconButton && iconEl) {
      // Icon-only button: just swap icon
      iconEl.textContent = CONFIRM_ICON;
    } else {
      // Text button: show icon + optional "Confirm" text
      const originalText = button.textContent.trim();
      const confirmContent = originalText.length >= 4
        ? `<span class="material-symbols-outlined">${CONFIRM_ICON}</span>${CONFIRM_TEXT}`
        : `<span class="material-symbols-outlined">${CONFIRM_ICON}</span>`;
      button.innerHTML = confirmContent;
    }
  }
}

// Reset button to original state
function resetButton(button, state) {
  button.classList.remove(CONFIRM_CLASS);
  if (state.isIconButton) {
    const iconEl = button.querySelector('.material-symbols-outlined, .material-icons-outlined');
    if (iconEl && state.originalIcon) {
      iconEl.textContent = state.originalIcon;
    }
  } else if (state.originalHTML) {
    button.innerHTML = state.originalHTML;
  }
}

// Register Alpine magic helper
export function registerAlpineMagic() {
  if (globalThis.Alpine) {
    Alpine.magic('confirmClick', () => confirmClick);
  }
}

