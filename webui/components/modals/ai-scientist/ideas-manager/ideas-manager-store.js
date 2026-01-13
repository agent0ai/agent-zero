import { createStore } from "/js/AlpineStore.js";
import { callJsonApi } from "/js/api.js";

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

    async onOpen() {
        await this.loadIdeas();
    },

    async loadIdeas() {
        this.loading = true;
        try {
            const response = await callJsonApi("scientist_get_ideas", {});
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
        try {
            await callJsonApi("scientist_generate_ideas", {
                topic: this.topic,
                num_ideas: this.numIdeas,
            });
            // Refresh ideas list
            await this.loadIdeas();
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
