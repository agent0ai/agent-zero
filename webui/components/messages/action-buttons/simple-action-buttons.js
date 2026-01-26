// Message Action Buttons - Copy and Speak functionality
import { store as speechStore } from "/components/chat/speech/speech-store.js";
import { store as stepDetailStore } from "/components/modals/process-step-detail/step-detail-store.js";

/**
 * Copy text to clipboard with fallback for non-secure contexts
 */
async function copyToClipboard(text) {
  if (navigator.clipboard && window.isSecureContext) {
    await navigator.clipboard.writeText(text);
  } else {
    // Fallback for local dev / non-secure contexts
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.style.cssText = "position:fixed;left:-9999px";
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand("copy");
    document.body.removeChild(textarea);
  }
}

/**
 * Show visual feedback on a button (success/error state)
 */
function showButtonFeedback(button, success, originalIcon) {
  const icon = button.querySelector(".material-symbols-outlined");
  if (!icon) return;
  
  icon.textContent = success ? "check" : "error";
  button.classList.add(success ? "success" : "error");
  
  setTimeout(() => {
    icon.textContent = originalIcon;
    button.classList.remove("success", "error");
  }, 2000);
}

/**
 * Create action button element
 */
function createButton(iconName, label, className) {
  const btn = document.createElement("button");
  btn.className = `action-button ${className}`;
  btn.setAttribute("aria-label", label);
  btn.setAttribute("title", label);
  btn.innerHTML = `<span class="material-symbols-outlined">${iconName}</span>`;
  return btn;
}

/**
 * Add action buttons (copy, speak, optionally view details) to an element.
 * Data is attached to buttons as data attributes for DOM-first behavior.
 *
 * @param {HTMLElement} container - Element to append buttons to
 * @param {Object} options - Configuration
 * @param {string|Function|HTMLElement} [options.contentRef] - Text content source
 * @param {Object} [options.detailPayload] - Detail payload for modal
 * @param {Function} [options.onViewDetails] - Optional detail handler
 * @param {string} [options.copyContent] - Text for copy action
 * @param {string} [options.speakContent] - Text for speak action
 */
export function addActionButtonsToElement(container, options = {}) {
  const {
    contentRef,
    detailPayload,
    onViewDetails,
    copyContent,
    speakContent
  } = options;

  const resolveContent = (explicit) => {
    if (typeof explicit === "string") return explicit;
    if (typeof explicit === "function") return explicit();
    if (explicit instanceof HTMLElement) return explicit.innerText || "";
    return "";
  };

  const resolvedCopyContent =
    resolveContent(copyContent ?? contentRef) || container.innerText || "";
  const resolvedSpeakContent =
    resolveContent(speakContent ?? contentRef) || container.innerText || "";

  let buttonsDiv = container.querySelector(".step-action-buttons");
  if (!buttonsDiv) {
    buttonsDiv = document.createElement("div");
    buttonsDiv.className = "step-action-buttons";
    container.appendChild(buttonsDiv);
  }

  const setDetailPayload = (btn) => {
    if (detailPayload) {
      btn.dataset.detailPayload = JSON.stringify(detailPayload);
    } else {
      delete btn.dataset.detailPayload;
    }
    if (onViewDetails) {
      btn._detailHandler = onViewDetails;
    } else {
      delete btn._detailHandler;
    }
  };

  // View Details button (optional)
  let viewBtn = buttonsDiv.querySelector(".view-details-action");
  if (detailPayload || onViewDetails) {
    if (!viewBtn) {
      viewBtn = createButton("open_in_full", "View details", "view-details-action");
      viewBtn.onclick = (e) => {
        e.stopPropagation();
        const handler = viewBtn._detailHandler;
        if (typeof handler === "function") {
          handler();
          return;
        }
        const payload = viewBtn.dataset.detailPayload;
        if (payload) {
          try {
            stepDetailStore.showStepDetail(JSON.parse(payload));
          } catch (err) {
            console.error("Failed to parse detail payload:", err);
          }
        }
      };
      buttonsDiv.appendChild(viewBtn);
    }
    setDetailPayload(viewBtn);
  } else if (viewBtn) {
    viewBtn.remove();
  }

  // Copy button
  let copyBtn = buttonsDiv.querySelector(".copy-action");
  if (!copyBtn) {
    copyBtn = createButton("content_copy", "Copy text", "copy-action");
    copyBtn.onclick = async (e) => {
      e.stopPropagation();
      const text = copyBtn.dataset.copyContent || "";
      if (!text) return;

      try {
        await copyToClipboard(text);
        showButtonFeedback(copyBtn, true, "content_copy");
      } catch (err) {
        console.error("Copy failed:", err);
        showButtonFeedback(copyBtn, false, "content_copy");
      }
    };
    buttonsDiv.appendChild(copyBtn);
  }
  copyBtn.dataset.copyContent = resolvedCopyContent;

  // Speak button
  let speakBtn = buttonsDiv.querySelector(".speak-action");
  if (!speakBtn) {
    speakBtn = createButton("volume_up", "Speak text", "speak-action");
    speakBtn.onclick = async (e) => {
      e.stopPropagation();
      const text = speakBtn.dataset.speakContent || "";
      if (!text.trim()) return;

      try {
        showButtonFeedback(speakBtn, true, "volume_up");
        await speechStore.speak(text);
      } catch (err) {
        console.error("Speech failed:", err);
        showButtonFeedback(speakBtn, false, "volume_up");
      }
    };
    buttonsDiv.appendChild(speakBtn);
  }
  speakBtn.dataset.speakContent = resolvedSpeakContent;
}
