// Chat Branching Plugin — injects a "branch" button into every message's action bar.
// Uses the unified handler output: context.results[] = { args: { no, … }, result: { element, … } }

import { createActionButton } from "/components/messages/action-buttons/simple-action-buttons.js";
import { callJsonApi } from "/js/api.js";
import { store as chatsStore } from "/components/sidebar/chats/chats-store.js";

export default async function injectBranchButtons(context) {
  if (!context?.results?.length) return;

  for (const { args, result } of context.results) {
    if (!result?.element || args.no == null || !args.id) continue;

    const logNo = args.no;
    for (const bar of result.element.querySelectorAll(".step-action-buttons")) {
      if (bar.querySelector(".action-fork_right")) continue;
      bar.appendChild(
        createActionButton("fork_right", "Branch chat", async () => {
          const ctxid = globalThis.getContext?.();
          if (!ctxid) throw new Error("No active chat");

          const res = await callJsonApi("/plugins/_chat_branching/branch_chat", {
            context: ctxid,
            log_no: logNo,
          });
          if (!res?.ok) throw new Error(res?.message || "Branch failed");
          chatsStore.selectChat(res.ctxid);
        }),
      );
    }
  }
}