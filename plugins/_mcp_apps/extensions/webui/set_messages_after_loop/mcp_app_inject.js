/**
 * set_messages_after_loop extension — injects MCP App iframes into
 * the .process-group-response container, above the response .message div.
 *
 * Runs after ALL messages are rendered, so the DOM is stable and
 * .process-group-response is guaranteed to exist (if a response was sent).
 */

export default async function(context) {
  // Find all MCP App steps that have stored kvps
  const appSteps = document.querySelectorAll(".mcp-app-step[data-mcp-app-kvps-json]");

  for (const step of appSteps) {
    const stepId = step.getAttribute("data-step-id");
    const frameId = `mcp-app-frame-${stepId}`;

    // Already injected
    if (document.getElementById(frameId)) continue;

    // Find the process group this step belongs to
    const processGroup = step.closest(".process-group");
    if (!processGroup) continue;

    // Find the response container in this process group
    const responseContainer = processGroup.querySelector(".process-group-response");
    if (!responseContainer) continue;

    // Parse the stored kvps
    let kvps;
    try {
      kvps = JSON.parse(step.getAttribute("data-mcp-app-kvps-json"));
    } catch (e) {
      continue;
    }

    // Find the .message.message-agent-response div inside the response container
    const messageDiv = responseContainer.querySelector(".message.message-agent-response");
    if (!messageDiv) continue;

    // Create the iframe container and prepend it inside the message div (before .message-body)
    const frameContainer = document.createElement("div");
    frameContainer.id = frameId;
    frameContainer.className = "mcp-app-frame-container";
    frameContainer.style.cssText = "margin-bottom: 12px;";
    frameContainer.setAttribute("data-mcp-app-kvps", "");
    frameContainer.__mcp_app_kvps = kvps;

    messageDiv.prepend(frameContainer);

    // Load the renderer component
    await loadRendererComponent(frameContainer, kvps);
  }
}

async function loadRendererComponent(mountEl, kvps) {
  try {
    const resp = await fetch("/usr/plugins/mcp_apps/webui/mcp-app-renderer.html");
    if (!resp.ok) {
      mountEl.innerHTML = `<div style="color: var(--color-error, #c00); padding: 8px;">Failed to load MCP App renderer</div>`;
      return;
    }
    const html = await resp.text();
    mountEl.innerHTML = html;

    if (window.Alpine) {
      window.Alpine.initTree(mountEl);
    }
  } catch (e) {
    console.error("[mcp-apps] Failed to load renderer:", e);
    mountEl.innerHTML = `<div style="color: var(--color-error, #c00); padding: 8px;">Error: ${e.message}</div>`;
  }
}
