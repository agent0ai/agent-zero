import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";
import { getContext } from "/index.js";

/**
 * Paper Generator Store
 *
 * Manages state for the Paper Generator modal, which allows users to:
 * - Select a completed experiment
 * - Configure paper generation options (format, reflections, citations)
 * - Trigger paper generation via agent message
 * - View generation progress and results
 */
const model = {
    // State
    experiments: [],
    selectedExperiment: null,
    format: "workshop", // "workshop" (4-page) or "full" (8-page)
    numReflections: 3,
    skipCitations: false,
    generating: false,
    progress: "",
    result: null,
    error: null, // Error message for UI display
    loading: false,
    closePromise: null,
    _initialized: false,

    init() {
        if (this._initialized) return;
        this._initialized = true;
    },

    /**
     * Open Paper Generator modal (preferred entry point)
     * Uses closePromise pattern for cleanup on modal close
     */
    async open() {
        // Prevent double-open
        if (this.closePromise) return;

        // Open modal and capture promise for cleanup
        this.closePromise = window.openModal(
            "modals/ai-scientist/paper-generator/paper-generator.html"
        );

        // Setup cleanup on modal close (defensive - regardless of close method)
        if (this.closePromise && typeof this.closePromise.then === "function") {
            this.closePromise.then(() => {
                this.cleanup();
            });
        }

        // Load completed experiments
        await this.loadExperiments();
    },

    /**
     * Called via x-create as fallback when modal opened externally
     */
    async onOpen() {
        // Skip if opened via store.open() (closePromise already set)
        if (this.closePromise) return;

        await this.loadExperiments();
    },

    /**
     * Fetch completed experiments from API
     */
    async loadExperiments() {
        this.loading = true;
        this.error = null;
        try {
            const response = await callJsonApi("scientist_get_experiments", {
                context: getContext(),
            });
            // Filter to only show completed experiments
            this.experiments = (response.experiments || []).filter(
                (exp) => exp.status === "completed"
            );
        } catch (e) {
            console.error("Failed to load experiments:", e);
            this.experiments = [];
            this.error = "Failed to load experiments. Please try again.";
        }
        this.loading = false;
    },

    /**
     * Select an experiment by idea name
     */
    selectExperiment(ideaName) {
        this.selectedExperiment =
            this.experiments.find((e) => e.idea_name === ideaName) || null;
        // Clear previous result when selecting new experiment
        this.result = null;
    },

    /**
     * Check if an experiment is currently selected
     */
    isSelected(ideaName) {
        return this.selectedExperiment?.idea_name === ideaName;
    },

    /**
     * Trigger paper generation via agent message
     */
    async generatePaper() {
        if (!this.selectedExperiment || this.generating) return;

        this.generating = true;
        this.progress = "Starting paper generation...";
        this.result = null;

        try {
            // Build the command message for the agent
            const parts = [
                `Generate paper for experiment: ${this.selectedExperiment.idea_name}`,
                `--format ${this.format}`,
                `--reflections ${this.numReflections}`,
            ];

            if (this.skipCitations) {
                parts.push("--skip-citations");
            }

            const message = parts.join(" ");

            // Send message to agent
            await callJsonApi("msg", {
                message: message,
                context: getContext(),
            });

            this.progress =
                "Paper generation started. Check the chat for progress.";

            // Note: The actual result will come through the agent's response
            // We could poll for completion or use WebSocket updates in the future
        } catch (e) {
            console.error("Failed to generate paper:", e);
            this.progress = `Error: ${e.message || "Failed to start generation"}`;
        }

        this.generating = false;
    },

    /**
     * Reset state and closePromise on modal close
     */
    cleanup() {
        this.selectedExperiment = null;
        this.progress = "";
        this.result = null;
        this.error = null;
        this.generating = false;
        this.closePromise = null;
        // Preserve user preferences: format, numReflections, skipCitations
    },
};

export const store = createStore("paperGeneratorStore", model);
