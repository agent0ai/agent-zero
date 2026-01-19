import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";
import { getContext } from "/index.js";

const model = {
    // State
    experiments: [],
    selectedExperiment: null,
    progress: null,
    polling: null,
    loading: false,
    closePromise: null,
    _initialized: false,

    init() {
        if (this._initialized) return;
        this._initialized = true;
    },

    // Open Experiment Dashboard modal (preferred entry point)
    async open() {
        // Prevent double-open
        if (this.closePromise) return;

        // Open modal and capture promise for cleanup
        this.closePromise = window.openModal(
            "modals/ai-scientist/experiment-dashboard/experiment-dashboard.html"
        );

        // Setup cleanup on modal close (defensive - regardless of close method)
        if (this.closePromise && typeof this.closePromise.then === "function") {
            this.closePromise.then(() => {
                this.cleanup();
            });
        }

        // Load data and start polling
        await this.loadExperiments();
        this.startPolling();
    },

    // Called via x-create as fallback when modal opened externally
    async onOpen() {
        // Skip if opened via store.open() (closePromise already set)
        if (this.closePromise) return;

        await this.loadExperiments();
        this.startPolling();
    },

    startPolling() {
        // Clear any existing polling first
        if (this.polling) {
            clearInterval(this.polling);
        }
        this.polling = setInterval(() => {
            if (this.selectedExperiment) {
                this.refreshProgress();
            }
        }, 3000);
    },

    async loadExperiments() {
        this.loading = true;
        try {
            const response = await callJsonApi("scientist_get_experiments", {
                context: getContext(),
            });
            this.experiments = response.experiments || [];
        } catch (e) {
            console.error("Failed to load experiments:", e);
            this.experiments = [];
        }
        this.loading = false;
    },

    async refreshProgress() {
        if (!this.selectedExperiment) return;
        try {
            const response = await callJsonApi("scientist_get_experiment_progress", {
                idea_name: this.selectedExperiment.idea_name,
                context: getContext(),
            });
            this.progress = response;
        } catch (e) {
            console.error("Failed to refresh progress:", e);
        }
    },

    selectExperiment(ideaName) {
        this.selectedExperiment = this.experiments.find(
            (e) => e.idea_name === ideaName
        );
        if (this.selectedExperiment) {
            this.refreshProgress();
        } else {
            this.progress = null;
        }
    },

    getStageStatus(stageNum) {
        if (!this.progress) return "pending";
        const stage = this.progress.stages?.[`stage_${stageNum}`];
        if (!stage) return "pending";
        if (stage.best_node_id) return "completed";
        if (stage.nodes?.length > 0) return "in_progress";
        return "pending";
    },

    getStageName(stageNum) {
        const names = ["Initial", "Tuning", "Research", "Ablation"];
        return names[stageNum - 1] || `Stage ${stageNum}`;
    },

    getStageNodes(stageNum) {
        if (!this.progress) return [];
        return this.progress.stages?.[`stage_${stageNum}`]?.nodes || [];
    },

    getAllNodes() {
        if (!this.progress) return [];
        return this.progress.tree_nodes || [];
    },

    cleanup() {
        if (this.polling) {
            clearInterval(this.polling);
            this.polling = null;
        }
        this.selectedExperiment = null;
        this.progress = null;
        this.closePromise = null;
    },
};

export const store = createStore("experimentDashboardStore", model);
