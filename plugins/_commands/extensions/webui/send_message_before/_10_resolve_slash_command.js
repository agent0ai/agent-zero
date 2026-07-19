import { store } from "/plugins/_commands/webui/commands-slash-store.js";

export default async function resolveSlashCommand(sendCtx) {
  await store.resolveBeforeSend(sendCtx);
}
