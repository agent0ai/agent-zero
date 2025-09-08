import { createStore } from "/js/AlpineStore.js";

const model = {
  versionNo: "",
  commitTime: "",
  get versionLabel() {
    return this.versionNo && this.commitTime
      ? `Version ${this.versionNo} ${this.commitTime}`
      : "";
  },
  init() {
    const gi = (globalThis && globalThis.gitinfo) ? globalThis.gitinfo : null;
    if (gi && gi.version && gi.commit_time) {
      this.versionNo = gi.version;
      this.commitTime = gi.commit_time;
      return;
    }
  },
};

export const store = createStore("app", model);


