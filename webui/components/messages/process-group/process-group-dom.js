/**
 * Process group DOM utilities (no store/state)
 */
import { store as preferencesStore } from "/components/sidebar/bottom/preferences/preferences-store.js";

export function isAtLiveTail(
  chatHistory = document.getElementById("chat-history"),
) {
  if (!chatHistory) return false;
  const windowEnd = Number(chatHistory.dataset.messageWindowEnd);
  const windowTotal = Number(chatHistory.dataset.messageWindowTotal);
  return (
    Number.isFinite(windowEnd) &&
    Number.isFinite(windowTotal) &&
    windowEnd >= windowTotal
  );
}

export function isGroupComplete(group) {
  return (
    group.hasAttribute("data-group-complete") ||
    Boolean(group.querySelector(".process-group-response"))
  );
}

export function getCurrentStep(
  chatHistory = document.getElementById("chat-history"),
  showUtils = preferencesStore.showUtils,
) {
  if (!isAtLiveTail(chatHistory)) return null;
  const groups = Array.from(chatHistory.querySelectorAll(".process-group"));
  const group = groups[groups.length - 1];
  if (!group || isGroupComplete(group)) return null;
  const steps = Array.from(group.querySelectorAll(".process-step"));
  for (let si = steps.length - 1; si >= 0; si -= 1) {
    const step = steps[si];
    if (showUtils || !step.classList.contains("message-util")) return step;
  }
  return null;
}

export async function applyModeSteps(
  detailMode,
  showUtils,
  chatHistory = document.getElementById("chat-history"),
) {
  const mode =
    detailMode ||
    preferencesStore.detailMode ||
    "current";

  if (!chatHistory) return;

  chatHistory.dataset.detailMode = mode;

  const shouldExpand = mode !== "collapsed";
  const allMode = mode === "expanded";
  const showUtilsFlag =
    typeof showUtils === "boolean"
      ? showUtils
      : preferencesStore.showUtils || false;
  const pending = [];
  const messages = Array.from(chatHistory.querySelectorAll(".process-group"));
  const currentStep =
    mode === "current" ? getCurrentStep(chatHistory, showUtilsFlag) : null;
  for (let i = 0; i < messages.length; i += 1) {
    const group = messages[i];
    if (typeof group.__setExpanded === "function") {
      pending.push(Promise.resolve(group.__setExpanded(shouldExpand)));
    } else {
      group.classList.toggle("expanded", shouldExpand);
    }

    const steps = Array.from(group.querySelectorAll(".process-step"));

    for (let si = 0; si < steps.length; si += 1) {
      const step = steps[si];
      const shouldExpandStep = allMode || step === currentStep;
      if (typeof step.__setExpanded === "function") {
        pending.push(Promise.resolve(step.__setExpanded(shouldExpandStep)));
      } else {
        step.classList.toggle("expanded", shouldExpandStep);
      }
    }
  }

  await Promise.allSettled(pending);
}
