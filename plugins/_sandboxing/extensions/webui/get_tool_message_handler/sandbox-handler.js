import { cleanStepTitle, drawProcessStep } from "/js/messages.js";

export default function registerSandboxHandler(extData) {
  if (extData.tool_name === "sandbox") extData.handler = drawSandboxStep;
}

function drawSandboxStep(log) {
  const { action, name } = log.kvps;
  return drawProcessStep({
    id: log.id,
    title: cleanStepTitle(log.heading),
    code: "SBX",
    kvps: { action: action || "list", ...(name && { name }) },
    log,
  });
}
