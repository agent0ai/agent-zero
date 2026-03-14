import { createStore } from "/js/AlpineStore.js";

// Complete list of Agent Jumbo skills/tools with metadata
const ALL_SKILLS = [
    // Business & Sales
    {
        id: "customer_lifecycle",
        name: "Customer Lifecycle",
        description: "Track customers through sales pipeline stages",
        icon: "👥",
        category: "Business",
        keywords: ["customer", "client", "lead", "prospect", "sales", "crm", "pipeline"],
        example: "Track a new customer named Acme Corp"
    },
    {
        id: "portfolio_manager_tool",
        name: "Portfolio Manager",
        description: "Manage projects, milestones, and deliverables",
        icon: "📁",
        category: "Business",
        keywords: ["project", "portfolio", "milestone", "deliverable", "status"],
        example: "Create a new project for the web redesign"
    },
    {
        id: "business_xray_tool",
        name: "Business X-Ray",
        description: "Analyze ROI, cost-benefit, and business cases",
        icon: "📊",
        category: "Business",
        keywords: ["analyze", "roi", "business case", "cost benefit", "analysis"],
        example: "Calculate ROI for the automation project"
    },
    {
        id: "sales_generator",
        name: "Sales Generator",
        description: "Generate proposals, demos, and case studies",
        icon: "💼",
        category: "Business",
        keywords: ["proposal", "demo", "case study", "pitch", "presentation"],
        example: "Generate a proposal for Acme Corp"
    },
    {
        id: "property_manager_tool",
        name: "Property Manager",
        description: "Manage real estate portfolios and properties",
        icon: "🏠",
        category: "Business",
        keywords: ["property", "real estate", "tenant", "lease", "rental"],
        example: "List all properties in the downtown portfolio"
    },

    // Development
    {
        id: "code_execution_tool",
        name: "Code Execution",
        description: "Execute code in Python, Node.js, or shell",
        icon: "💻",
        category: "Development",
        keywords: ["code", "execute", "run", "python", "script", "shell", "bash"],
        example: "Run this Python script to process the data"
    },
    {
        id: "project_scaffold",
        name: "Project Scaffold",
        description: "Generate project structures from templates",
        icon: "🏗️",
        category: "Development",
        keywords: ["scaffold", "template", "boilerplate", "create project", "setup"],
        example: "Scaffold a new FastAPI project"
    },
    {
        id: "deployment_orchestrator",
        name: "Deployment Orchestrator",
        description: "CI/CD, Docker, and Kubernetes automation",
        icon: "🚀",
        category: "Development",
        keywords: ["deploy", "deployment", "ci/cd", "docker", "kubernetes", "k8s"],
        example: "Create a GitHub Actions workflow for this project"
    },
    {
        id: "diagram_tool",
        name: "Diagram Generator",
        description: "Create Mermaid diagrams and flowcharts",
        icon: "📐",
        category: "Development",
        keywords: ["diagram", "flowchart", "mermaid", "chart", "visualization"],
        example: "Create a sequence diagram for the auth flow"
    },
    {
        id: "diagram_architect",
        name: "Diagram Architect",
        description: "Auto-generate architecture diagrams from code",
        icon: "🏛️",
        category: "Development",
        keywords: ["architecture", "system", "components", "design", "structure"],
        example: "Generate an architecture diagram from the codebase"
    },

    // Automation & Workflows
    {
        id: "workflow_engine",
        name: "Workflow Engine",
        description: "Design and execute multi-stage workflows",
        icon: "🔄",
        category: "Automation",
        keywords: ["workflow", "stage", "process", "pipeline", "automation"],
        example: "Start the product development workflow"
    },
    {
        id: "workflow_training",
        name: "Workflow Training",
        description: "Track skill progression and learning paths",
        icon: "📚",
        category: "Automation",
        keywords: ["training", "skill", "learning", "course", "certification"],
        example: "Show my progress on the Python skill"
    },
    {
        id: "ralph_loop",
        name: "Ralph Loop",
        description: "Autonomous iterative task execution",
        icon: "🔁",
        category: "Automation",
        keywords: ["ralph", "loop", "autonomous", "iterate", "repeat"],
        example: "Start a Ralph loop to fix all test failures"
    },
    {
        id: "scheduler",
        name: "Task Scheduler",
        description: "Schedule tasks to run at specific times",
        icon: "⏰",
        category: "Automation",
        keywords: ["schedule", "cron", "timer", "recurring", "later"],
        example: "Schedule a daily report at 9am"
    },
    {
        id: "virtual_team",
        name: "Virtual Team",
        description: "Orchestrate AI team members for tasks",
        icon: "👨‍👩‍👧‍👦",
        category: "Automation",
        keywords: ["team", "delegate", "assign", "collaborate", "parallel"],
        example: "Assign this task to the frontend specialist"
    },

    // Communication
    {
        id: "email",
        name: "Email",
        description: "Send and manage emails",
        icon: "📧",
        category: "Communication",
        keywords: ["email", "mail", "send", "message", "notification"],
        example: "Send an email to the team about the update"
    },
    {
        id: "notify_user",
        name: "Notify User",
        description: "Send notifications to the user",
        icon: "🔔",
        category: "Communication",
        keywords: ["notify", "alert", "notification", "remind"],
        example: "Notify me when the task is complete"
    },
    {
        id: "a2a_chat",
        name: "Agent-to-Agent Chat",
        description: "Communicate with other AI agents",
        icon: "🤝",
        category: "Communication",
        keywords: ["a2a", "agent", "chat", "communicate", "connect"],
        example: "Ask the research agent for market data"
    },

    // Research & Knowledge
    {
        id: "search_engine",
        name: "Web Search",
        description: "Search the web for information",
        icon: "🔍",
        category: "Research",
        keywords: ["search", "google", "find", "lookup", "research"],
        example: "Search for the latest React best practices"
    },
    {
        id: "browser_agent",
        name: "Browser Agent",
        description: "Automated web browsing and interaction",
        icon: "🌐",
        category: "Research",
        keywords: ["browse", "website", "scrape", "web", "page"],
        example: "Go to GitHub and check the repository stats"
    },
    {
        id: "document_query",
        name: "Document Query",
        description: "Query and analyze documents",
        icon: "📄",
        category: "Research",
        keywords: ["document", "pdf", "query", "read", "analyze"],
        example: "Summarize the key points from this PDF"
    },
    {
        id: "memory_load",
        name: "Memory Load",
        description: "Load memories and context from storage",
        icon: "🧠",
        category: "Research",
        keywords: ["memory", "recall", "remember", "context", "history"],
        example: "Load what we discussed about the project"
    },

    // AI & Integration
    {
        id: "ai_migration",
        name: "AI Migration",
        description: "Analyze and plan AI transformation",
        icon: "🔮",
        category: "AI & Integration",
        keywords: ["ai", "migration", "transform", "automate", "optimize"],
        example: "Analyze this process for AI automation potential"
    },
    {
        id: "skill_importer",
        name: "Skill Importer",
        description: "Import Claude Code plugin skills",
        icon: "📥",
        category: "AI & Integration",
        keywords: ["import", "skill", "plugin", "claude", "command"],
        example: "Import the code review skill from Claude Code"
    },
    {
        id: "plugin_marketplace",
        name: "Plugin Marketplace",
        description: "Browse and install plugins",
        icon: "🛒",
        category: "AI & Integration",
        keywords: ["plugin", "marketplace", "install", "extension", "addon"],
        example: "Search the marketplace for code analysis plugins"
    },
    {
        id: "claude_sdk_bridge",
        name: "Claude SDK Bridge",
        description: "Bridge to Claude Agent SDK",
        icon: "🌉",
        category: "AI & Integration",
        keywords: ["sdk", "claude", "bridge", "api", "integration"],
        example: "Initialize a Claude SDK session"
    }
];

const model = {
    // State
    visible: false,
    searchQuery: "",
    contextSuggestions: [],
    currentInputText: "",

    // All available skills
    allSkills: ALL_SKILLS,

    // Initialize
    init() {
        // Listen for input changes from the chat input
        this.setupInputListener();
    },

    // Setup listener for chat input changes
    setupInputListener() {
        // This will be called by the chat input component
        document.addEventListener('skillsSuggest:analyze', (e) => {
            this.analyzeInput(e.detail?.text || '');
        });
    },

    // Analyze input text and update suggestions without opening the UI.
    // The skills panel should only appear after explicit user interaction
    // (for example clicking the skills button).
    analyzeInput(text) {
        this.currentInputText = text;

        if (!text || text.length < 3) {
            this.contextSuggestions = [];
            return;
        }

        const textLower = text.toLowerCase();
        const suggestions = [];

        for (const skill of this.allSkills) {
            for (const keyword of skill.keywords) {
                if (textLower.includes(keyword)) {
                    suggestions.push({
                        ...skill,
                        matchedKeyword: keyword
                    });
                    break; // Only add once per skill
                }
            }
        }

        this.contextSuggestions = suggestions;

        // Do not auto-open on typing.
    },

    // Show the dropdown
    show() {
        this.visible = true;
    },

    // Hide the dropdown
    hide() {
        this.visible = false;
    },

    // Toggle visibility
    toggle() {
        this.visible = !this.visible;
    },

    // Get skills grouped by category
    getGroupedSkills() {
        const query = this.searchQuery.toLowerCase();
        const filtered = query
            ? this.allSkills.filter(s =>
                s.name.toLowerCase().includes(query) ||
                s.description.toLowerCase().includes(query) ||
                s.keywords.some(k => k.includes(query))
            )
            : this.allSkills;

        // Group by category
        const groups = {};
        for (const skill of filtered) {
            if (!groups[skill.category]) {
                groups[skill.category] = [];
            }
            groups[skill.category].push(skill);
        }

        return Object.entries(groups).map(([name, skills]) => ({ name, skills }));
    },

    // Select a skill and insert example into chat
    selectSkill(skill) {
        // Dispatch event to insert skill example into chat
        document.dispatchEvent(new CustomEvent('skillsSuggest:insert', {
            detail: {
                skillId: skill.id,
                text: skill.example,
                skillName: skill.name
            }
        }));

        this.hide();
    },

    // Show all tools in a modal or help page
    showAllTools() {
        // Dispatch event to show tools documentation
        document.dispatchEvent(new CustomEvent('skillsSuggest:showDocs', {
            detail: { view: 'all-tools' }
        }));
    },

    // Open help
    openHelp() {
        document.dispatchEvent(new CustomEvent('skillsSuggest:showDocs', {
            detail: { view: 'help' }
        }));
    }
};

export const store = createStore("skillsSuggest", model);
