import { createStore } from "/js/AlpineStore.js";

const INTENTS = [
  { value: "research", label: "Research" },
  { value: "draft", label: "Draft" },
  { value: "review", label: "Review" },
  { value: "docs", label: "Docs" },
];

const STAGES = [
  { value: "intake", label: "Intake" },
  { value: "draft", label: "Draft" },
  { value: "review", label: "Review" },
  { value: "export", label: "Export" },
];

// define the model object holding data and functions
const model = {
  connected: false,
  progressActive: false,  // true when progress bar is active

  intents: INTENTS,
  stages: STAGES,

  intent: null,
  stage: "intake",

  inputs: {
    intake: {
      parties: "",
      jurisdiction: "",
      facts: "",
      reliefSought: "",
    },
    draft: {
      docType: "pleading",
      notes: "",
    },
    review: {
      checks: {
        completeness: false,
        citations: false,
        formatting: false,
        consistency: false,
      },
      notes: "",
    },
    export: {
      format: "docx",
      name: "",
      requireReviewComplete: true,
    },
  },

  setIntent(value) {
    this.intent = value;
  },

  clearIntent() {
    this.intent = null;
  },

  setStage(value) {
    this.stage = value;
  },

  clearWorkflow() {
    this.intent = null;
    this.stage = "intake";
    this.inputs.intake = {
      parties: "",
      jurisdiction: "",
      facts: "",
      reliefSought: "",
    };
    this.inputs.draft = { docType: "pleading", notes: "" };
    this.inputs.review = {
      checks: {
        completeness: false,
        citations: false,
        formatting: false,
        consistency: false,
      },
      notes: "",
    };
    this.inputs.export = {
      format: "docx",
      name: "",
      requireReviewComplete: true,
    };
  },

  get intentLabel() {
    return (
      this.intents.find((i) => i.value === this.intent)?.label || "—"
    );
  },

  get stageLabel() {
    return this.stages.find((s) => s.value === this.stage)?.label || "—";
  },

  get isReviewComplete() {
    const checks = this.inputs?.review?.checks || {};
    const values = Object.values(checks);
    return values.length > 0 && values.every(Boolean);
  },

  /**
   * For outbound message payloads.
   * Keep keys stable so backend routing can hook in later.
   */
  getWorkflowPayload() {
    if (!this.intent) return null;
    return {
      version: 1,
      intent: this.intent,
      stage: this.stage,
      inputs: this.inputs,
    };
  },
};

// convert it to alpine store
const store = createStore("chatTop", model);

// export for use in other files
export { store };
