// Message Action Buttons - DOM helpers for message action buttons

const ACTION_ICON_MAP = {
  detail: "open_in_full",
  speak: "volume_up",
  copy: "content_copy",
};

const ACTION_LABELS = {
  detail: "View details",
  speak: "Speak",
  copy: "Copy",
};

function resolveActionIcon(icon) {
  if (!icon) return "";
  return ACTION_ICON_MAP[icon] || icon;
}

function buildActionLabel(icon, text) {
  const baseLabel = ACTION_LABELS[icon] || text || icon;
  if (text && ACTION_LABELS[icon]) return `${ACTION_LABELS[icon]} ${text}`;
  return baseLabel;
}

/**
 * Copy text to clipboard with fallback for non-secure contexts
 */
export async function copyToClipboard(text) {
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
export function showButtonFeedback(button, success, originalIcon) {
  const icon = button.querySelector(".material-symbols-outlined");
  if (!icon) return;
  
  icon.textContent = success ? "check" : "error";
  button.classList.add(success ? "success" : "error");
  
  setTimeout(() => {
    icon.textContent = originalIcon;
    button.classList.remove("success", "error");
  }, 1000);
}

/**
 * Create action button element
 */
export function createActionButton(icon, text = "", handler = null) {
  const iconName = resolveActionIcon(icon);
  if (!iconName) return null;

  const button = document.createElement("button");
  button.type = "button";
  button.className = `action-button action-${icon}`;
  const label = buildActionLabel(icon, text);
  if (label) {
    button.setAttribute("aria-label", label);
    button.setAttribute("title", label);
  }
  button.innerHTML = `<span class="material-symbols-outlined">${iconName}</span>`;

  if (typeof handler === "function") {
    button.addEventListener("click", async (event) => {
      event.stopPropagation();
      const shouldShowFeedback = true; // icon === "copy" || icon === "speak";
      try {
        await handler();
        if (shouldShowFeedback) {
          showButtonFeedback(button, true, iconName);
        }
      } catch (err) {
        console.error("Action button failed:", err);
        if (shouldShowFeedback) {
          showButtonFeedback(button, false, iconName);
        }
      }
    });
  }

  return button;
}
