import { drawMessageToolSimple } from "/js/messages.js";

/**
 * Registers the browser_agent tool message handler to set the custom badge.
 * @param {object} extData 
 */
export default async function registerBrowserToolHandler(extData) {
  if (extData?.tool_name === "browser_agent") {
    extData.handler = drawBrowserTool;
  }
}

function drawBrowserTool(args) {
  return drawMessageToolSimple({ ...args, code: "WWW" });
}
