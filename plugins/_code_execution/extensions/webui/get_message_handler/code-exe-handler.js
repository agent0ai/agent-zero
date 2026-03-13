import {
  createActionButton,
  copyToClipboard,
} from "/components/messages/action-buttons/simple-action-buttons.js";
import { store as stepDetailStore } from "/components/modals/process-step-detail/step-detail-store.js";
import {
  buildDetailPayload,
  cleanStepTitle,
  drawProcessStep,
} from "/js/messages.js";

export default async function registerCodeExeHandler(extData) {
  if (extData?.type === "code_exe") {
    extData.handler = drawMessageCodeExe;
  }
}

function drawMessageCodeExe({
  id,
  type,
  heading,
  test,
  content,
  kvps,
  timestamp,
  agentno = 0,
  ...additional
}) {
  let title = "Code Execution";
  // show command at the start and end
  if (kvps?.code && /done_all|code_execution_tool/.test(heading || "")) {
    const s = kvps.session;
    title = `${s != null ? `[${s}] ` : ""}${kvps.runtime || "bash"}> ${kvps.code.trim()}`;
  } else {
    // during execution show the original heading (current step)
    title = cleanStepTitle(heading);
  }

  const displayKvps = {};

  const headerLabels = [
    kvps?.runtime && { label: kvps.runtime, class: "tool-name-badge" },
    kvps?.session != null && {
      label: `Session ${kvps.session}`,
      class: "header-label",
    },
  ].filter(Boolean);

  const commandText = String(kvps?.code ?? "");
  const outputText = String(content ?? "");

  const actionButtons = [];
  actionButtons.push(
    createActionButton("detail", "", () =>
      stepDetailStore.showStepDetail(
        buildDetailPayload(arguments[0], { headerLabels }),
      ),
    ),
  );
  if (commandText.trim()) {
    actionButtons.push(
      createActionButton("copy", "Command", () => copyToClipboard(commandText)),
    );
  }
  if (outputText.trim()) {
    actionButtons.push(
      createActionButton("copy", "Output", () => copyToClipboard(outputText)),
    );
  }
  const stepData = drawProcessStep({
    id,
    title,
    code: "EXE",
    classes: undefined,
    kvps: displayKvps,
    content,
    contentClasses: ["terminal-output"],
    actionButtons,
    log: arguments[0],
  });

  return stepData;
}
