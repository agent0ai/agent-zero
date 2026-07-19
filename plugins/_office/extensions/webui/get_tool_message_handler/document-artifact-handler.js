import {
  cleanStepTitle,
  drawProcessStep,
} from "/js/messages.js";

export default async function registerDocumentArtifactHandler(extData) {
  if (extData?.tool_name === "document_artifact") {
    extData.handler = drawDocumentArtifactTool;
  }
}

function drawDocumentArtifactTool({
  id,
  type,
  heading,
  content,
  kvps,
  timestamp,
  agentno = 0,
  ...additional
}) {
  const args = arguments[0];
  const title = cleanStepTitle(heading);
  const displayKvps = { ...kvps };

  return drawProcessStep({
    id,
    title,
    code: "DOC",
    classes: undefined,
    kvps: displayKvps,
    content,
    actionButtons: [],
    log: args,
  });
}
