import { createStore } from "/js/AlpineStore.js";

// Chats sidebar store: contexts list and selected chat id
const model = {
  contexts: [],
  selected: "",

  init() {
    // No-op: data is driven by poll() in index.js; this store provides a stable target
  },
};

export const store = createStore("chats", model);


