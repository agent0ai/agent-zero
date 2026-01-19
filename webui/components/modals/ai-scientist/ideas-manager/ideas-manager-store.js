import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";
import { getContext } from "/index.js";

const model = {
    // State
    ideas: [],
    selectedIdea: null,
    loading: false,
    generatingIdeas: false,
    topic: "",
    numIdeas: 5,
    _initialized: false,

    init() {
        if (this._initialized) return;
        this._initialized = true;
    },

    // Open Ideas Manager modal (preferred entry point)
    async open() {
        await window.openModal("modals/ai-scientist/ideas-manager/ideas-manager.html");
    },

    async onOpen() {
        await this.loadIdeas();
    },

    async loadIdeas() {
        this.loading = true;
        try {
            const response = await callJsonApi("scientist_get_ideas", {
                context: getContext(),
            });
            this.ideas = response.ideas || [];
        } catch (e) {
            console.error("Failed to load ideas:", e);
            this.ideas = [];
        }
        this.loading = false;
    },

    async generateIdeas() {
        if (!this.topic.trim()) return;

        this.generatingIdeas = true;
        const startingCount = this.ideas.length;

        try {
            await callJsonApi("scientist_generate_ideas", {
                topic: this.topic,
                num_ideas: this.numIdeas,
                context: getContext(),
            });

            // Poll for new ideas (agent runs asynchronously)
            const maxAttempts = 60; // 60 seconds max wait
            let attempts = 0;

            while (attempts < maxAttempts) {
                await new Promise(resolve => setTimeout(resolve, 1000)); // Wait 1s
                await this.loadIdeas();

                // Check if new ideas appeared
                if (this.ideas.length > startingCount) {
                    break;
                }
                attempts++;
            }
        } catch (e) {
            console.error("Failed to generate ideas:", e);
        }
        this.generatingIdeas = false;
    },

    selectIdea(ideaName) {
        this.selectedIdea = this.ideas.find((i) => i.Name === ideaName) || null;
    },

    async startExperiment() {
        if (!this.selectedIdea) return;

        try {
            await callJsonApi("scientist_start_experiment", {
                idea_name: this.selectedIdea.Name,
                context: getContext(),
            });
            window.closeModal();
        } catch (e) {
            console.error("Failed to start experiment:", e);
        }
    },

    getNoveltyClass(score) {
        if (score >= 8) return "high";
        if (score >= 5) return "medium";
        return "low";
    },

    cleanup() {
        this.selectedIdea = null;
    },
};

export const store = createStore("ideasManagerStore", model);
