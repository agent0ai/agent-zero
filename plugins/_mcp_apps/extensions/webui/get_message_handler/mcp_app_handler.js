/**
 * JS extension for get_message_handler — registers the mcp_app message type handler.
 * Renders a compact APP process step. The iframe is injected separately
 * by the set_messages_after_loop extension once all messages are in the DOM.
 */
import { drawProcessStep } from "/js/messages.js";

export default async function(extData) {
  if (extData.type !== "mcp_app") return;

  extData.handler = drawMessageMcpApp;
}

function drawMessageMcpApp({ id, type, heading, content, kvps, timestamp, agentno = 0, ...additional }) {
  const toolName = kvps?.tool_name || "MCP App";
  const serverName = kvps?.server_name || "";
  const resourceUri = kvps?.resource_uri || "";

  const cleanTitle = heading
    ? heading.replace(/^icon:\/\/\S+\s*/, "")
    : `MCP App: ${toolName}`;

  const result = drawProcessStep({
    id,
    title: cleanTitle,
    code: "APP",
    classes: ["mcp-app-step"],
    kvps: { server: serverName, tool: toolName },
    content: resourceUri,
    actionButtons: [],
    log: { id, type, heading, content, kvps, timestamp, agentno, ...additional },
    allowCompletedGroup: true,
  });

  // Store kvps on the step element so the after-loop extension can find it
  if (result.step) {
    result.step.setAttribute("data-mcp-app-kvps-json", JSON.stringify(kvps || {}));
  }

  return result;
}
