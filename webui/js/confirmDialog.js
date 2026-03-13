// Custom confirmation dialog. CSS in /css/modals.css

import { callJsExtensions } from "/js/extensions.js";

const DIALOG_TYPES = {
  warning: { icon: 'warning', color: 'var(--color-warning, #f59e0b)' },
  danger: { icon: 'error', color: 'var(--color-error, #ef4444)' },
  info: { icon: 'info', color: 'var(--color-primary, #3b82f6)' }
};

export function showConfirmDialog(options) {
  const {
    title = 'Confirm',
    message = '',
    confirmText = 'Confirm',
    cancelText = 'Cancel',
    type = 'warning',
    extensionContext = null,
  } = options;

  const typeConfig = DIALOG_TYPES[type] || DIALOG_TYPES.warning;

  return new Promise((resolve) => {
    // Create backdrop
    const backdrop = document.createElement('div');
    backdrop.className = 'confirm-dialog-backdrop';
    
    // Create dialog
    const dialog = document.createElement('div');
    dialog.className = 'confirm-dialog';
    dialog.innerHTML = `
      <div class="confirm-dialog-header">
        <span class="confirm-dialog-icon material-symbols-outlined" style="color: ${typeConfig.color}">${typeConfig.icon}</span>
        <span class="confirm-dialog-title">${title}</span>
      </div>
      <div class="confirm-dialog-body">${message}</div>
      <div class="confirm-dialog-footer">
        <button class="button cancel confirm-dialog-cancel">${cancelText}</button>
        <button class="button confirm confirm-dialog-confirm">${confirmText}</button>
      </div>
    `;

    backdrop.appendChild(dialog);
    document.body.appendChild(backdrop);

    const titleElement = dialog.querySelector('.confirm-dialog-title');
    const bodyElement = dialog.querySelector('.confirm-dialog-body');
    const footerElement = dialog.querySelector('.confirm-dialog-footer');
    const cancelButton = dialog.querySelector('.confirm-dialog-cancel');
    const confirmButton = dialog.querySelector('.confirm-dialog-confirm');
    let isClosed = false;

    // Show with animation
    const showDialog = () => {
      requestAnimationFrame(() => {
        backdrop.classList.add('visible');
        cancelButton?.focus();
      });
    };

    // Close handler
    const close = (result) => {
      if (isClosed) return;
      isClosed = true;
      backdrop.classList.remove('visible');
      document.removeEventListener('keydown', handleKeydown);
      setTimeout(() => {
        backdrop.remove();
        resolve(result);
      }, 200);
    };

    // Event listeners
    cancelButton.addEventListener('click', () => close(false));
    confirmButton.addEventListener('click', () => close(true));
    backdrop.addEventListener('click', (e) => e.target === backdrop && close(false));

    // Keyboard handling
    const handleKeydown = (e) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        close(false);
        return;
      }

      if (e.key !== 'Enter') return;

      const activeElement = document.activeElement;
      if (
        activeElement
        && dialog.contains(activeElement)
        && (
          activeElement.tagName === 'BUTTON'
          || activeElement.tagName === 'A'
          || activeElement.tagName === 'INPUT'
          || activeElement.tagName === 'TEXTAREA'
          || activeElement.tagName === 'SELECT'
          || activeElement.isContentEditable
        )
      ) {
        return;
      }

      e.preventDefault();
      close(true);
    };
    document.addEventListener('keydown', handleKeydown);

    const extensionData = {
      options,
      dialog,
      backdrop,
      titleElement,
      bodyElement,
      footerElement,
      confirmButton,
      cancelButton,
      close,
      title,
      message,
      type,
      confirmText,
      cancelText,
      extensionContext,
    };

    callJsExtensions('confirm_dialog_after_render', extensionData)
      .finally(showDialog);
  });
}
