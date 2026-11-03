import { drawMessageToolSimple } from "/js/messages.js";

export default async function registerMemoryHandler(extData) {
  const memoryTools = ["memory", "memory_load", "memory_save", "memory_delete", "memory_forget"];
  if (extData?.type === "memory" || memoryTools.includes(extData?.tool_name)) {
    extData.handler = (log) =>
      drawMessageToolSimple({ ...log, code: "MEM" });
  }
}
