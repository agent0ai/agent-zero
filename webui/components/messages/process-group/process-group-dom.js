/**
 * Process group DOM utilities (no store/state)
 */
import { store as preferencesStore } from "/components/sidebar/bottom/preferences/preferences-store.js";

export function applyModeSteps(detailMode, showUtils) {
  const mode =
    detailMode ||
    preferencesStore.detailMode ||
    "current";
  const showUtilsFlag =
    typeof showUtils === "boolean"
      ? showUtils
      : preferencesStore.showUtils || false;

  const chatHistory = document.getElementById("chat-history");
  if (!chatHistory) return;

  const shouldExpandGroup = mode !== "collapsed";
  const shouldExpandError = mode === "current" || mode === "expanded";

  // Walk DOM once (reverse to match message traversal patterns)
  const groups = chatHistory.children;
  for (let gi = groups.length - 1; gi >= 0; gi -= 1) {
    const messageGroup = groups[gi];
    const containers = messageGroup.children;
    for (let ci = containers.length - 1; ci >= 0; ci -= 1) {
      const container = containers[ci];

      if (container.classList.contains("has-process-group")) {
        const processGroup = container.querySelector(".process-group");
        if (processGroup) {
          applyModeToProcessGroup(processGroup, mode, showUtilsFlag, shouldExpandGroup);
        }
      }

      const errorGroups = container.getElementsByClassName("error-group");
      if (errorGroups.length) {
        for (let ei = 0; ei < errorGroups.length; ei += 1) {
          errorGroups[ei].classList.toggle("expanded", shouldExpandError);
        }
      }
    }
  }
}

function applyModeToProcessGroup(group, mode, showUtilsFlag, shouldExpandGroup) {
  group.classList.toggle("expanded", shouldExpandGroup);

  const isActiveGroup = group.classList.contains("active");
  const isGroupCompleted = group.classList.contains("process-group-completed");
  const steps = group.getElementsByClassName("process-step");
  if (!steps.length) return;

  let lastVisibleStep = null;
  const shouldFindLastVisible = mode === "current" && isActiveGroup && !isGroupCompleted;

  for (let i = steps.length - 1; i >= 0; i -= 1) {
    const step = steps[i];

    if (shouldFindLastVisible && !lastVisibleStep) {
      if (showUtilsFlag || !step.classList.contains("message-util")) {
        lastVisibleStep = step;
      }
    }

    let shouldExpand = false;
    if (mode === "expanded") {
      shouldExpand = true;
    } else if (mode === "current" && isActiveGroup) {
      shouldExpand = step === lastVisibleStep;
    }

    if (shouldExpand) {
      step.classList.add("step-expanded");
    } else {
      const shouldDefer =
        mode === "current" &&
        isActiveGroup &&
        lastVisibleStep &&
        step !== lastVisibleStep;
      if (!shouldDefer) {
        step.classList.remove("step-expanded");
        step.removeAttribute("data-user-pinned");
      }
    }
  }
}
