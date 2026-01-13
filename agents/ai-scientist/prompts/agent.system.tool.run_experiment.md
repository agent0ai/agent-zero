## Experiment execution tool:

### run_experiment
Execute 4-stage ML experiment pipeline for a research idea using subordinate agents.
Implements best-first tree search through experiment space with automatic code generation.

usage:
~~~json
{
    "thoughts": [
        "The user wants to run experiments for the 'sparse_attention' idea",
        "I'll execute the full 4-stage experiment pipeline",
    ],
    "headline": "Running experiments for sparse_attention research idea",
    "tool_name": "run_experiment",
    "tool_args": {
        "idea_name": "sparse_attention",
        "resume": false,
        "max_iterations_per_stage": 10
    }
}
~~~

Parameters:
- idea_name (required): Name of the research idea (from generate_idea output)
- resume (optional): Resume from checkpoint if available (default: false)
- max_iterations_per_stage (optional): Max experiment nodes per stage (default: 10)

The tool executes 4 stages:
1. Initial Implementation - Get basic working code
2. Baseline Tuning - Optimize hyperparameters
3. Creative Research - Explore novel improvements
4. Ablation Studies - Analyze component contributions

Each stage:
- Spawns subordinate agents to write experiment code
- Executes code and tracks metrics
- Uses best-first search to explore variations
- Saves checkpoints for resumption
- Stores results for paper generation
