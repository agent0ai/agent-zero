import { createStore } from "/js/AlpineStore.js";

const model = {
  context: null,

  init() {
    this.initialize();
  },

  initialize() {
    // Nothing special needed for initialization yet
  },

  setContext(contextId) {
    this.context = contextId;
  },

  getContext() {
    return this.context;
  }
};

// Create and export the store
const store = createStore("context", model);
export { store };