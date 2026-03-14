# Agent Jumbo Clone: AI Software Architect Training & Deployment Plan

## Vision

Build an autonomous AI software architect that embodies Aaron's decision-making patterns,
architectural preferences, and solution-building processes. Deploy it on GCP as the primary
intelligence powering Agent Jumbo, capable of designing and building complete software
solutions without human intervention.

---

## 1. Model Selection

### Primary: Qwen3-235B-A22B (MoE, 22B active)

| Attribute | Detail |
|-----------|--------|
| Architecture | Mixture-of-Experts, 235B total / 22B active per token |
| Context window | 128K tokens |
| License | Apache 2.0 — unrestricted commercial + derivative works |
| Tool calling | Native (OpenAI format) + Hermes format |
| Thinking mode | Built-in `/think` and `/no_think` toggle |
| Fine-tuning | LoRA, QLoRA (8-bit recommended for MoE), full SFT |
| Agent Jumbo integration | Already in MODEL_CATALOG, Hermes parser in tool_adapter.py |
| SWE-bench | ~62% (Qwen3-235B), Qwen3-Coder variants 70%+ |

**Why not GLM-4.7?** GLM-4.7 has better agentic benchmarks (73.8% SWE-bench) but a
younger fine-tuning ecosystem. Qwen3 has mature tooling (MS-SWIFT, Unsloth, LLaMA-Factory,
Axolotl), extensive documentation, and Agent Jumbo already has deep Qwen integration.

### Utility/Fast Clone: Qwen3-30B-A3B (MoE, 3B active)

Fine-tuned with the same training data for fast inference on routine tasks.
Runs on a single L4 GPU (~$480/month). Handles heartbeat triggers, simple tool calls,
background processing.

### Embedding: sentence-transformers/all-MiniLM-L6-v2

Already integrated in Agent Jumbo's memory system. Zero cost (CPU inference).
Upgrade path: `nomic-embed-text-v1.5` for 8K context embeddings.

---

## 2. Phased Training Strategy

Research consensus (2026): Start with RAG for immediate value, then fine-tune for
behavioral consistency, then RLHF/DPO from your feedback for alignment.

### Phase A: RAG Foundation (Week 1-2)

**Goal**: Architect clone that retrieves your patterns from a knowledge base.

No fine-tuning required. Ingest Silver Surfer Platform + best practices into
Agent Jumbo's knowledge graph + FAISS memory.

```text
Data Sources:
├── Silver Surfer Platform
│   ├── 20+ service implementations (architecture patterns)
│   ├── 500+ documentation files (written reasoning)
│   ├── 25+ kit templates (solution composition patterns)
│   ├── Agent orchestration code (workflow patterns)
│   └── Test suites + quality gates (standards)
├── Public Best Practices
│   ├── Clean Architecture, DDD, 12-Factor App
│   ├── GCP Cloud Architecture Framework
│   ├── OWASP Security Guidelines
│   └── Microservices patterns (Sam Newman, Martin Fowler)
└── Personal Decision Records
    ├── Architecture Decision Records (ADRs)
    ├── Code review patterns and preferences
    └── Technology selection criteria
```

**Implementation**:

1. Create a chunking pipeline that processes Silver Surfer files:
   - Code files: chunk by class/function with surrounding context
   - Documentation: chunk by section (H2 headers)
   - Kit templates: chunk by component (kit.yaml + associated files)
2. Generate embeddings and store in FAISS + KnowledgeGraph
3. Create a system prompt that instructs the base model to:
   - Always check retrieved context before making architecture decisions
   - Prefer patterns found in the knowledge base over generic approaches
   - Cite which kit/service/pattern influenced the decision

**Validation**: Present 10 architecture scenarios, compare responses with and
without RAG. Measure how often the model uses your established patterns.

### Phase B: Supervised Fine-Tuning (Week 3-6)

**Goal**: Model that *thinks* like you without needing retrieval for core patterns.

This is where we transform the base Qwen3-235B into your clone. Fine-tuning
teaches the model HOW to reason about architecture, not just WHAT to retrieve.

#### Training Data Generation Pipeline

The key insight from research: you need **instruction-response pairs** that
capture your decision-making process, not just your code.

##### Stage 1: Extract Decision Traces from Silver Surfer (Automated)

Use a frontier model (Claude) to analyze Silver Surfer code and generate
training pairs in ChatML format:

```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are Aaron's AI architect clone. You design solutions using
      his established patterns: microservices with event-driven communication,
      FastAPI/Express backends, React frontends, PostgreSQL, comprehensive testing
      with 85%+ coverage gates, multi-tenant isolation, and RBAC from day one."
    },
    {
      "role": "user",
      "content": "Design a customer management system for a SaaS company."
    },
    {
      "role": "assistant",
      "content": "<think>\nLet me apply Aaron's solution composition approach:\n
      1. Start from the CRM kit template — it has the Customer 360 Intelligence
         Engine component with proven business outcomes.\n
      2. Architecture: Microservices pattern from Silver Surfer — gateway,
         dedicated service per domain, event bus for async communication.\n
      3. Data model: BaseModel pattern with UUID, timestamps, change tracking.\n
      4. Auth: RBAC middleware with permission matrix from day one.\n
      5. Quality: 85%+ test coverage gate, TDD-driven generation.\n
      </think>\n\n## Architecture\n\n### Service Decomposition\n..."
    }
  ]
}
```

##### Stage 2: Generate Synthetic Training Data (InstructLab Methodology)

From research: InstructLab can generate large amounts of training data from
minimal seed examples using the LAB (Large-scale Alignment for chatBots) method.

```text
Seed Examples Needed:        ~200-500 curated pairs
Synthetic Data Generated:    ~10,000-50,000 pairs
Training Data Composition:   75% reasoning / 25% non-reasoning
```

**Extraction scripts to build**:

```text
scripts/training/
├── extract_architecture_decisions.py
│   # Analyzes Silver Surfer code + docs → architecture Q&A pairs
│   # Input: service code, kit.yaml, documentation
│   # Output: "Given X requirement, design Y" → architectural response
│
├── extract_code_patterns.py
│   # Extracts code generation patterns from advanced-code-generator.js
│   # Input: template definitions, framework adapters
│   # Output: "Generate a React component for X" → code following your patterns
│
├── extract_solution_compositions.py
│   # Extracts solution composition logic from solution_composer.js
│   # Input: component library, business outcomes
│   # Output: "Build a solution for X industry" → composed blueprint
│
├── extract_quality_standards.py
│   # Extracts testing and quality patterns
│   # Input: test suites, quality gates, TDD generator
│   # Output: "Review this code" → quality feedback in your style
│
├── generate_synthetic_pairs.py
│   # Uses Claude API to expand seed examples into diverse training data
│   # Applies InstructLab taxonomy: skills (how-to) + knowledge (facts)
│
└── validate_training_data.py
    # Quality checks: deduplication, format validation, diversity scoring
```

**Data Categories (Taxonomy)**:

```yaml
taxonomy:
  skills:
    architecture_design:
      - microservices_decomposition
      - event_driven_patterns
      - api_gateway_design
      - data_model_design
      - multi_tenant_isolation
    code_generation:
      - react_component_patterns
      - fastapi_service_scaffolding
      - database_schema_design
      - test_generation
      - docker_kubernetes_config
    solution_composition:
      - kit_selection_and_customization
      - business_outcome_mapping
      - integration_planning
      - deployment_strategy
    quality_engineering:
      - code_review_feedback
      - test_coverage_analysis
      - security_audit
      - performance_optimization
  knowledge:
    technology_preferences:
      - framework_selection_criteria
      - database_choice_patterns
      - cloud_service_preferences
    industry_patterns:
      - healthcare_compliance
      - fintech_security
      - ecommerce_scalability
      - saas_multi_tenancy
    operational_standards:
      - 85_percent_coverage_gate
      - rbac_from_day_one
      - event_sourcing_pattern
      - base_model_inheritance
```

#### Fine-Tuning Configuration

Based on current best practices (Unsloth + MS-SWIFT for Qwen3 MoE):

```yaml
# Qwen3-235B-A22B Fine-Tuning Config
model:
  name: Qwen/Qwen3-235B-A22B
  quantization: 8bit        # NOT 4bit for MoE (quality loss too high)
  max_seq_length: 8192      # Increase to 32768 for production

lora:
  rank: 64                  # Higher rank for complex architectural reasoning
  alpha: 128                # 2x rank is standard
  dropout: 0.05
  target_modules:           # All attention + MLP layers
    - q_proj
    - k_proj
    - v_proj
    - o_proj
    - gate_proj
    - up_proj
    - down_proj
  # NOTE: Do NOT fine-tune the MoE router layer (disabled by default)

training:
  framework: ms-swift       # Best Qwen3 MoE support
  stages:
    - name: sft
      epochs: 3
      learning_rate: 2e-5
      warmup_ratio: 0.1
      batch_size: 4
      gradient_accumulation: 8
      optimizer: adamw_torch
      kl_penalty: 0.01      # KL-anchored SFT to prevent drift
      dataset_ratio:
        reasoning: 0.75
        conversational: 0.25

    - name: dpo              # Direct Preference Optimization
      epochs: 1
      learning_rate: 1e-6   # Much lower than SFT
      beta: 0.1             # Sweep [0.05, 0.1, 0.2] to find best
      dataset: preference_pairs.jsonl

hardware:
  training: 4x A100 80GB    # ~$12/hr on GCP
  estimated_training_time: 48-72 hours for SFT
  estimated_cost: $600-900 per training run
```

#### Utility Model (Qwen3-30B-A3B)

Same training data, smaller model, cheaper hardware:

```yaml
model:
  name: Qwen/Qwen3-30B-A3B
  quantization: 8bit

lora:
  rank: 32
  alpha: 64

training:
  hardware: 1x A100 80GB    # ~$3/hr
  estimated_training_time: 12-24 hours
  estimated_cost: $36-72 per training run
```

### Phase C: DPO/RLHF from Your Feedback (Week 7-10)

**Goal**: Align the model to your preferences through iterative feedback.

After deploying Phase B, you use the clone for real tasks and provide feedback:

1. **Preference pairs**: For each task, the model generates 2-3 responses.
   You pick the one that best matches what you would have done.
2. **Rejection sampling**: Model generates multiple solutions, you flag
   which ones are "not how I'd do it" with brief reasons.
3. **Iterative DPO**: Train on collected preference pairs every 1-2 weeks.

```text
Feedback Collection Flow:
User request → Clone generates 2 responses → Aaron picks preferred
                                            → Pair saved to preference_pairs.jsonl
                                            → Every 100 pairs: retrain DPO stage
```

---

## 3. GCP Deployment Architecture

### Training Infrastructure

```text
GCP Project: agent-jumbo-training
Region: us-central1

Training Cluster (ephemeral — spin up for training runs only):
├── Node: a3-highgpu-4g (4x A100 80GB)
│   ├── MS-SWIFT or Axolotl training framework
│   ├── Training data mounted from GCS bucket
│   └── Checkpoints saved to GCS every 1000 steps
│
├── GCS Bucket: gs://agent-jumbo-training/
│   ├── datasets/           # Training JSONL files
│   ├── checkpoints/        # Model checkpoints during training
│   ├── adapters/           # Final LoRA adapters
│   └── evaluations/        # Benchmark results per training run
│
└── Artifact Registry: LoRA adapter versioning
```

### Inference Infrastructure

```text
GCP Project: agent-jumbo-production
Region: us-central1

GKE Cluster: agent-jumbo-inference
├── Node Pool: "primary" (scale 0-2)
│   ├── Machine: a3-highgpu-4g (4x H100 80GB)
│   ├── vLLM serving Qwen3-235B-A22B + LoRA adapter
│   ├── Expert Parallelism enabled
│   ├── KV-Cache: 70% GPU memory allocation
│   └── OpenAI-compatible API on port 8000
│
├── Node Pool: "utility" (always-on)
│   ├── Machine: g2-standard-8 (1x L4 24GB)
│   ├── vLLM serving Qwen3-30B-A3B + LoRA adapter
│   └── Handles all traffic during primary scale-to-zero
│
├── Node Pool: "app" (always-on)
│   ├── Machine: e2-standard-8
│   ├── Agent Jumbo Flask backend + Next.js frontend
│   ├── Ollama sidecar (qwen2.5-coder:3b baseline fallback)
│   └── LLM Router → primary → utility → DeepSeek API → Ollama
│
└── GKE Inference Gateway
    ├── Intelligent routing by KV-Cache utilization
    ├── HPA based on inference_pool_average_kv_cache_utilization
    └── Request queuing during scale-up
```

### vLLM Serving Configuration

```yaml
# vllm-primary.yaml (Qwen3-235B-A22B)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vllm-primary
spec:
  replicas: 1
  template:
    spec:
      containers:
        - name: vllm
          image: vllm/vllm-openai:latest
          args:
            - --model=Qwen/Qwen3-235B-A22B
            - --enable-lora
            - --lora-modules=architect-clone=/models/architect-lora
            - --tensor-parallel-size=4
            - --max-model-len=32768
            - --gpu-memory-utilization=0.85
            - --enable-chunked-prefill
            - --max-num-seqs=32
          resources:
            limits:
              nvidia.com/gpu: 4
          volumeMounts:
            - name: model-cache
              mountPath: /models
      volumes:
        - name: model-cache
          persistentVolumeClaim:
            claimName: model-storage
```

### Auto-Scaling Strategy

```text
Primary (Qwen3-235B-A22B):
  Scale-to-zero:    Nights + weekends (16hr/day active)
  Scale-up trigger:  First request (cold start ~3 min)
  Scale-out:         KV-Cache > 80% → add replica
  Fallback:          Utility model handles all during scale-to-zero

Utility (Qwen3-30B-A3B):
  Always-on:         $480/month is cheap enough to keep warm
  Scale-out:         Queue > 50 pending → add replica

Cost Profiles:
  Full 24/7:         ~$9,500/month
  Smart scaling:     ~$3,500/month (recommended)
  Budget mode:       ~$900/month (utility model + DeepSeek API only)
```

---

## 4. Agent Jumbo Integration

### LLM Router Configuration

Add to `conf/model_providers.yaml`:

```yaml
architect_clone_primary:
  provider: openai
  api_base: http://vllm-primary:8000/v1
  api_key: not-needed
  models:
    - architect-clone-235b:
        capabilities: [chat, code, reasoning, function_calling, agent]
        context_window: 32768
        cost_per_1k_input: 0.0   # Self-hosted
        cost_per_1k_output: 0.0

architect_clone_utility:
  provider: openai
  api_base: http://vllm-utility:8000/v1
  api_key: not-needed
  models:
    - architect-clone-30b:
        capabilities: [chat, code, function_calling, agent]
        context_window: 32768
        cost_per_1k_input: 0.0
        cost_per_1k_output: 0.0
```

### Tool Adapter Strategy

Qwen3 supports native OpenAI-style function calling. Agent Jumbo's `ToolAdapter`
at `python/helpers/tool_adapter.py` already handles this:

```python
# No changes needed — set strategy.format = "native"
# Qwen3's built-in tool calling maps directly to OpenAI function calling format
```

### Fallback Chain

```text
Request → architect-clone-235b (primary, self-hosted)
       → architect-clone-30b (utility, self-hosted)
       → deepseek-v3.1 (API, $0.27/M input)
       → qwen2.5-coder:3b (Ollama baseline, local)
```

---

## 5. Training Data from Silver Surfer Platform

### High-Value Extraction Targets

| Source File | Size | Training Data Type | Est. Pairs |
|-------------|------|-------------------|------------|
| `universal_solution_orchestrator.py` | Core | Orchestration decision traces | 200+ |
| `tdd-project-generator.js` | 75KB | Quality gate patterns, swarm agent design | 300+ |
| `advanced-code-generator.js` | 65KB | Code template patterns per framework | 500+ |
| `solution_composer.js` | Core | Solution composition blueprints | 200+ |
| `design-engine.js` | 45KB | Industry-specific UI patterns | 200+ |
| `BaseModel.js` + middleware | Core | Data model + auth patterns | 100+ |
| 25+ kit templates | Varies | Domain-specific solution patterns | 500+ |
| 500+ .md documentation | Varies | Written architectural reasoning | 1000+ |
| Test suites | Varies | Quality standards and review patterns | 200+ |

**Estimated seed pairs**: ~3,200+
**After synthetic expansion**: ~50,000-100,000 training examples

### Extraction Pipeline Architecture

```text
Silver Surfer Codebase
        │
        ▼
┌─────────────────────┐
│  Extract & Classify  │ ← Python scripts parse code + docs
│  (extract_*.py)      │   into structured chunks
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Generate Seed Pairs │ ← Claude API converts chunks into
│  (generate_seeds.py) │   instruction-response pairs
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Synthetic Expansion │ ← InstructLab taxonomy + LAB method
│  (expand_data.py)    │   generates 10-50x more pairs
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Quality Validation  │ ← Dedup, format check, diversity
│  (validate.py)       │   scoring, human spot-check
└─────────┬───────────┘
          │
          ▼
    training_data.jsonl
    (50K-100K pairs)
```

---

## 6. Evaluation Framework

### How to Measure "Thinks Like Aaron"

| Metric | Method | Target |
|--------|--------|--------|
| Architecture alignment | Present 50 design scenarios, compare to Silver Surfer patterns | >80% pattern match |
| Technology selection | Ask "which database/framework for X" across 30 scenarios | >90% match to your preferences |
| Quality standards | Review 20 generated solutions for 85% coverage, RBAC, etc. | All solutions include your standards |
| Solution composition | Given 10 requirements, measure kit selection accuracy | >75% match to your kit choices |
| Code style | Generate 50 code samples, compare to Silver Surfer patterns | Consistent naming, structure, patterns |
| Tool use | Run 20 multi-step tasks, measure tool chain quality | >85% successful autonomous completion |
| Reasoning quality | Compare thinking traces to your actual decision process | Qualitative assessment by you |

### Benchmark Suite

Create `tests/benchmarks/architect_clone/`:

```text
benchmarks/
├── architecture_scenarios.jsonl      # 50 design problems with expected approaches
├── technology_selection.jsonl        # 30 "which tool for this job" questions
├── quality_review.jsonl              # 20 code samples to review (test quality instincts)
├── solution_composition.jsonl        # 10 business requirements → expected blueprints
├── tool_chain_tasks.jsonl            # 20 multi-step agent tasks
└── evaluate.py                       # Automated scoring + report generation
```

---

## 7. Implementation Timeline

| Week | Phase | Deliverable | Cost |
|------|-------|-------------|------|
| 1 | RAG Foundation | Knowledge base ingested, system prompt tuned | ~$50 (embeddings) |
| 2 | RAG Validation | 10 architecture scenarios validated | $0 |
| 3 | Data Extraction | Training pipeline scripts, seed pairs generated | ~$100 (Claude API) |
| 4 | Synthetic Expansion | 50K+ training pairs from InstructLab/Claude | ~$200 (API costs) |
| 5-6 | SFT Training | 2-3 training runs with evaluation | ~$1,800-2,700 |
| 7 | Deployment | vLLM serving on GKE, LLM Router integration | ~$500 (infrastructure) |
| 8 | Validation | Full benchmark suite, A/B testing vs base model | ~$500 |
| 9-10 | DPO Alignment | Preference collection + DPO training | ~$500 |

**Total estimated cost**: ~$3,650-4,550 for initial training
**Ongoing inference**: ~$3,500/month (smart scaling) or ~$900/month (budget)

---

## 8. Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Catastrophic forgetting | Model loses general coding ability | KL-anchored SFT (0.01 penalty), 75/25 reasoning split |
| Overfitting to Silver Surfer patterns | Model can't adapt to new problems | Diverse synthetic data, temperature > 0 during generation |
| MoE router degradation | Experts stop specializing correctly | Do NOT fine-tune router layer (disabled by default) |
| Training data quality | Bad pairs teach wrong patterns | Human validation of 5% random sample, automated dedup |
| Context window regression | Fine-tuned model loses long-context ability | Include long-context examples in training data |
| Tool calling degradation | Model stops using tools correctly | Include tool-use examples in 25% of training data |

---

## 9. Files to Create

### Training Infrastructure

```text
scripts/training/
├── extract_architecture_decisions.py    # Silver Surfer → architecture Q&A
├── extract_code_patterns.py             # Code generator → code completion pairs
├── extract_solution_compositions.py     # Solution composer → blueprint pairs
├── extract_quality_standards.py         # Test suites → review feedback pairs
├── generate_synthetic_pairs.py          # Claude API seed expansion
├── validate_training_data.py            # Quality checks
├── prepare_dataset.py                   # Final JSONL formatting
├── train_sft.sh                         # MS-SWIFT SFT training script
├── train_dpo.sh                         # DPO alignment training script
├── evaluate_clone.py                    # Benchmark evaluation
└── config/
    ├── sft_235b.yaml                    # SFT config for primary model
    ├── sft_30b.yaml                     # SFT config for utility model
    ├── dpo_235b.yaml                    # DPO config for primary model
    └── taxonomy.yaml                    # InstructLab-style skill/knowledge taxonomy
```

### GCP Infrastructure

```text
infra/gcp/
├── terraform/
│   ├── main.tf                          # GKE cluster, node pools, storage
│   ├── variables.tf                     # Instance types, regions, scaling
│   ├── outputs.tf                       # Endpoints, bucket paths
│   └── modules/
│       ├── gke_inference/               # Inference cluster with GPU pools
│       └── training_node/               # Ephemeral training instances
├── kubernetes/
│   ├── vllm-primary.yaml               # Primary model deployment
│   ├── vllm-utility.yaml               # Utility model deployment
│   ├── inference-gateway.yaml           # GKE Inference Gateway config
│   ├── hpa-primary.yaml                # Autoscaler for primary
│   └── model-storage-pvc.yaml          # Persistent volume for model cache
└── scripts/
    ├── deploy_model.sh                  # Upload LoRA + restart vLLM
    ├── scale_to_zero.sh                 # Off-peak scaling
    └── run_training.sh                  # Spin up training node, run, tear down
```

### Agent Jumbo Integration

```text
conf/
├── model_providers.yaml                 # Add architect-clone entries
└── architect_clone_system_prompt.md     # System prompt for the clone

python/helpers/
└── clone_feedback.py                    # Preference pair collection for DPO
```

---

## 10. Research Sources

- [Ultimate Guide — Best Fine-Tuning Platforms of Open Source LLM 2026](https://www.siliconflow.com/articles/en/the-best-fine-tuning-platforms-of-open-source-llm)
- [10 Best Open Source LLMs You Can Fine-Tune in 2026](https://azumo.com/artificial-intelligence/ai-insights/top-open-source-llms)
- [Fine-Tuning Open Source Models — Stanford](https://rcpedia.stanford.edu/blog/2025/11/07/fine-tuning-open-source-models/)
- [Best Open Source LLM for Agent Workflow 2026](https://www.siliconflow.com/articles/en/best-open-source-LLM-for-Agent-Workflow)
- [Qwen3 Fine-Tuning Guide — Unsloth](https://unsloth.ai/docs/models/qwen3-how-to-run-and-fine-tune)
- [Qwen3.5 Fine-Tuning Guide — Unsloth](https://unsloth.ai/docs/models/qwen3.5/fine-tune)
- [Practical Guide: Fine-Tuning Qwen3 with LoRA (KL-anchored SFT + DPO)](https://blog.ivan.digital/finetuning-qwen3-with-lora-done-right-94d6343e1814)
- [Fine-Tune Qwen3 8B with LoRA — Hugging Face](https://huggingface.co/docs/optimum-neuron/en/training_tutorials/finetune_qwen3)
- [MS-SWIFT Training — Qwen Official](https://qwen.readthedocs.io/en/latest/training/ms_swift.html)
- [RAG vs Fine-Tuning 2026: Complete Guide](https://calmops.com/ai/rag-vs-fine-tuning-2026-complete-guide/)
- [LLM Fine-Tuning vs RAG vs Agents: Practical Comparison](https://mitrix.io/blog/llm-fine%E2%80%91tuning-vs-rag-vs-agents-a-practical-comparison/)
- [InstructLab Synthetic Data Generation](https://www.redhat.com/en/blog/how-instructlabs-synthetic-data-generation-enhances-llms)
- [InstructLab — IBM Research](https://research.ibm.com/blog/instruct-lab)
- [Fine-Tuning Renaissance: LLaMA-Factory vs Unsloth vs Axolotl](https://hiya31.medium.com/the-fine-tuning-renaissance-comparing-llama-factory-unsloth-deepspeed-and-axolotl-d67d26b26be4)
- [Axolotl vs LLaMA-Factory vs Unsloth for AI Fine-Tuning 2026](https://www.index.dev/skill-vs-skill/ai-axolotl-vs-llama-factory-vs-unsloth)
- [Definitive Guide to Fine-Tuning with Axolotl and LLaMA-Factory](https://www.superteams.ai/blog/a-definitive-guide-to-fine-tuning-llms-using-axolotl-and-llama-factory)
- [vLLM Production Stack on GCP GKE](https://docs.vllm.ai/projects/production-stack/en/vllm-stack-0.1.2/deployment/cloud-deployment/gcp.html)
- [Serve Llama on GKE with vLLM — Google Cloud](https://docs.cloud.google.com/kubernetes-engine/docs/tutorials/serve-llama-gpus-vllm)
- [GKE Inference Gateway — Google Cloud Blog](https://cloud.google.com/blog/topics/developers-practitioners/implementing-high-performance-llm-serving-on-gke-an-inference-gateway-walkthrough)
- [Synthetic Data for LLM Training — Survey](https://arxiv.org/html/2503.14023v1)
