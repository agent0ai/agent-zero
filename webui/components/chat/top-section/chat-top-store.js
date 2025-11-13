import { createStore } from "/js/AlpineStore.js";

// define the model object holding data and functions
const model = {
  connected: false, // Shows whether agent is actively processing (green when true)
  backendAlive: true, // Tracks backend connection health
};

// convert it to alpine store
const store = createStore("chatTop", model);

// export for use in other files
export { store };
