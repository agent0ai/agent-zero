# AI Scientist

Agent specialized in autonomous scientific research - generates research ideas, runs experiments via tree search, and writes publication-ready papers.

## Capabilities

1. **Research Ideation** - Generate novel research ideas with novelty validation via Semantic Scholar
2. **Experiment Execution** - Run experiments through a 4-stage pipeline using subordinate agents
3. **Paper Writing** - Generate publication-ready LaTeX manuscripts with citations

## Usage

### Generate Ideas
```
Generate 5 research ideas about: improving transformer efficiency through sparse attention mechanisms
```

### Run Experiments
```
Run experiment for idea: sparse_attention_routing
```

### Write Paper
```
Write a paper for experiment: sparse_attention_routing --format workshop
```

## 4-Stage Experiment Pipeline

- **Stage 1 (Initial)**: Basic working implementation on a simple dataset
- **Stage 2 (Tuning)**: Hyperparameter optimization, add 2 more datasets
- **Stage 3 (Research)**: Novel improvements and insights, 3 datasets total
- **Stage 4 (Ablation)**: Systematic component analysis

## Example Topics

- Sparse attention mechanisms for long-context transformers
- Adaptive learning rate scheduling for vision transformers
- Memory-efficient fine-tuning techniques
- Neural architecture search for edge deployment
- Self-supervised learning for low-resource domains
