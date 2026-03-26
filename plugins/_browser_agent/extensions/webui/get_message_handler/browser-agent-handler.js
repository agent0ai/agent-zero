import {
  createActionButton,
  copyToClipboard,
} from "/components/messages/action-buttons/simple-action-buttons.js";
import { store as stepDetailStore } from "/components/modals/process-step-detail/step-detail-store.js";
import { store as speechStore } from "/components/chat/speech/speech-store.js";
import {
  buildDetailPayload,
  cleanStepTitle,
  drawProcessStep,
} from "/js/messages.js";

export default async function registerBrowserAgentHandler(extData) {
  if (extData?.type === "browser") {
    extData.handler = drawMessageBrowserAgent;
  }
}

function drawMessageBrowserAgent({
  id,
  type,
  heading,
  content,
  kvps,
  timestamp,
  agentno = 0,
  ...additional
}) {
  const title = cleanStepTitle(heading);
  const displayKvps = { ...kvps };
  const answerText = String(kvps?.answer ?? "");
  const actionButtons = answerText.trim()
    ? [
        createActionButton("detail", "", () =>
          stepDetailStore.showStepDetail(
            buildDetailPayload(arguments[0], { headerLabels: [] }),
          ),
        ),
        createActionButton("speak", "", () => speechStore.speak(answerText)),
        createActionButton("copy", "", () => copyToClipboard(answerText)),
      ].filter(Boolean)
    : [];

  return drawProcessStep({
    id,
    title,
    code: "WWW",
    classes: undefined,
    kvps: displayKvps,
    content,
    actionButtons,
    log: arguments[0],
  });
}
