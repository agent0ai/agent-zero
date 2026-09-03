/**
 * Custom handler for text_editor tool messages
 * Uses drawProcessStep with code='TXT' (cyan)
 * Hides _tool_name from display to keep the step clean.
 */
import {
  buildDetailPayload,
  cleanStepTitle,
  drawProcessStep,
} from "/js/messages.js";
import { store as stepDetailStore } from "/components/modals/process-step-detail/step-detail-store.js";
import { ttsService } from "/js/tts-service.js";
import {
  copyToClipboard,
  createActionButton,
} from "/components/messages/action-buttons/simple-action-buttons.js";

export default function (extData) {
  if (extData.type !== "text_editor") return;

  extData.handler = function ({ id, content, kvps, heading, timestamp, agentno = 0, ...rest }) {
    const title = cleanStepTitle(heading);
    const displayKvps = { ...kvps };
    // Hide internal tool name from display
    delete displayKvps._tool_name;

    const contentText = String(content ?? "");
    const actionButtons = contentText.trim()
      ? [
          createActionButton("detail", "", () =>
            stepDetailStore.showStepDetail(
              buildDetailPayload(arguments[0], { headerLabels: [] })
            )
          ),
          createActionButton("copy", "", () => copyToClipboard(contentText)),
          createActionButton("speak", "", () => ttsService.speak(contentText)),
        ]
      : [
          createActionButton("detail", "", () =>
            stepDetailStore.showStepDetail(
              buildDetailPayload(arguments[0], { headerLabels: [] })
            )
          ),
        ];

    return drawProcessStep({
      id,
      title,
      code: "TXT",
      classes: ["TXT"],
      kvps: displayKvps,
      content,
      actionButtons,
      log: arguments[0],
    });
  };
}
