"""Configuration for the training data extraction pipeline."""

from pathlib import Path

# Source and output paths
SILVER_SURFER_ROOT = Path("/mnt/wdblack/dev/projects/webemo-aaron/SilverSurferPlatform")
OUTPUT_DIR = Path(__file__).parent / "output"
CHUNKS_DIR = OUTPUT_DIR / "chunks"
SEED_PAIRS_DIR = OUTPUT_DIR / "seeds"
VALIDATED_DIR = OUTPUT_DIR / "validated"

# Claude API settings for seed pair generation
CLAUDE_MODEL_BULK = "claude-haiku-4-5-20251001"
CLAUDE_MODEL_COMPLEX = "claude-sonnet-4-6"
CLAUDE_MAX_TOKENS = 4096
CLAUDE_BATCH_SIZE = 100

# Token limits
MAX_CHUNK_TOKENS = 4000
MIN_RESPONSE_CHARS = 200
MAX_RESPONSE_TOKENS = 16000

# Taxonomy — skills and knowledge categories for classification
TAXONOMY = {
    "skills": {
        "architecture_design": [
            "microservices_decomposition",
            "event_driven_patterns",
            "api_gateway_design",
            "data_model_design",
            "multi_tenant_isolation",
        ],
        "code_generation": [
            "react_component_patterns",
            "fastapi_service_scaffolding",
            "database_schema_design",
            "test_generation",
            "docker_kubernetes_config",
        ],
        "solution_composition": [
            "kit_selection_and_customization",
            "business_outcome_mapping",
            "integration_planning",
            "deployment_strategy",
        ],
        "quality_engineering": [
            "code_review_feedback",
            "test_coverage_analysis",
            "security_audit",
            "performance_optimization",
        ],
    },
    "knowledge": {
        "technology_preferences": [
            "framework_selection_criteria",
            "database_choice_patterns",
            "cloud_service_preferences",
        ],
        "industry_patterns": [
            "healthcare_compliance",
            "fintech_security",
            "ecommerce_scalability",
            "saas_multi_tenancy",
        ],
        "operational_standards": [
            "85_percent_coverage_gate",
            "rbac_from_day_one",
            "event_sourcing_pattern",
            "base_model_inheritance",
        ],
    },
}

# Keyword mappings for taxonomy classification
TAXONOMY_KEYWORDS: dict[str, list[str]] = {
    # Skills - Architecture Design
    "skills.architecture_design.microservices_decomposition": [
        "microservice",
        "service mesh",
        "decompos",
        "bounded context",
        "domain driven",
        "service registry",
        "api gateway",
    ],
    "skills.architecture_design.event_driven_patterns": [
        "event bus",
        "event driven",
        "publish",
        "subscribe",
        "message queue",
        "kafka",
        "rabbitmq",
        "event sourcing",
        "cqrs",
        "async",
    ],
    "skills.architecture_design.api_gateway_design": [
        "gateway",
        "api route",
        "proxy",
        "rate limit",
        "load balanc",
        "reverse proxy",
        "nginx",
        "kong",
    ],
    "skills.architecture_design.data_model_design": [
        "data model",
        "schema",
        "entity",
        "relationship",
        "migration",
        "orm",
        "sequelize",
        "sqlalchemy",
        "base model",
        "uuid",
    ],
    "skills.architecture_design.multi_tenant_isolation": [
        "multi-tenant",
        "tenant",
        "isolation",
        "tenant_id",
        "row-level",
        "organization",
        "workspace",
    ],
    # Skills - Code Generation
    "skills.code_generation.react_component_patterns": [
        "react",
        "component",
        "jsx",
        "tsx",
        "hook",
        "useState",
        "useEffect",
        "redux",
        "next.js",
        "frontend",
    ],
    "skills.code_generation.fastapi_service_scaffolding": [
        "fastapi",
        "flask",
        "express",
        "endpoint",
        "router",
        "middleware",
        "rest api",
        "backend",
        "python service",
    ],
    "skills.code_generation.database_schema_design": [
        "create table",
        "alter table",
        "index",
        "foreign key",
        "migration",
        "postgresql",
        "mysql",
        "database schema",
    ],
    "skills.code_generation.test_generation": [
        "test",
        "jest",
        "pytest",
        "describe(",
        "it(",
        "expect(",
        "assert",
        "mock",
        "stub",
        "fixture",
        "coverage",
    ],
    "skills.code_generation.docker_kubernetes_config": [
        "docker",
        "dockerfile",
        "kubernetes",
        "k8s",
        "helm",
        "pod",
        "deployment",
        "container",
        "docker-compose",
    ],
    # Skills - Solution Composition
    "skills.solution_composition.kit_selection_and_customization": [
        "kit",
        "template",
        "scaffold",
        "starter",
        "blueprint",
        "boilerplate",
        "generator",
    ],
    "skills.solution_composition.business_outcome_mapping": [
        "business outcome",
        "roi",
        "kpi",
        "metric",
        "conversion",
        "revenue",
        "retention",
        "churn",
        "growth",
    ],
    "skills.solution_composition.integration_planning": [
        "integration",
        "webhook",
        "api connect",
        "third-party",
        "oauth",
        "sso",
        "external service",
    ],
    "skills.solution_composition.deployment_strategy": [
        "deploy",
        "ci/cd",
        "pipeline",
        "staging",
        "production",
        "rollback",
        "blue-green",
        "canary",
    ],
    # Skills - Quality Engineering
    "skills.quality_engineering.code_review_feedback": [
        "code review",
        "pull request",
        "review comment",
        "refactor",
        "clean code",
        "best practice",
        "code smell",
    ],
    "skills.quality_engineering.test_coverage_analysis": [
        "coverage",
        "85%",
        "test coverage",
        "untested",
        "branch coverage",
        "line coverage",
        "quality gate",
    ],
    "skills.quality_engineering.security_audit": [
        "security",
        "vulnerability",
        "owasp",
        "xss",
        "csrf",
        "injection",
        "authentication",
        "authorization",
        "rbac",
        "permission",
    ],
    "skills.quality_engineering.performance_optimization": [
        "performance",
        "latency",
        "throughput",
        "cache",
        "optimize",
        "bottleneck",
        "profil",
        "benchmark",
    ],
    # Knowledge - Technology Preferences
    "knowledge.technology_preferences.framework_selection_criteria": [
        "framework",
        "library",
        "tool selection",
        "technology choice",
        "stack",
        "comparison",
        "evaluate",
    ],
    "knowledge.technology_preferences.database_choice_patterns": [
        "postgresql",
        "mongodb",
        "redis",
        "database choice",
        "sql vs nosql",
        "data store",
        "persistence",
    ],
    "knowledge.technology_preferences.cloud_service_preferences": [
        "gcp",
        "aws",
        "azure",
        "cloud run",
        "cloud function",
        "gke",
        "cloud deploy",
        "serverless",
    ],
    # Knowledge - Industry Patterns
    "knowledge.industry_patterns.healthcare_compliance": [
        "healthcare",
        "hipaa",
        "ehr",
        "medical",
        "patient",
        "clinical",
        "health data",
        "phi",
    ],
    "knowledge.industry_patterns.fintech_security": [
        "fintech",
        "payment",
        "stripe",
        "pci",
        "financial",
        "banking",
        "transaction",
        "ledger",
    ],
    "knowledge.industry_patterns.ecommerce_scalability": [
        "ecommerce",
        "e-commerce",
        "shop",
        "cart",
        "checkout",
        "inventory",
        "product catalog",
        "order",
    ],
    "knowledge.industry_patterns.saas_multi_tenancy": [
        "saas",
        "subscription",
        "multi-tenant",
        "billing",
        "plan",
        "tier",
        "usage-based",
        "metering",
    ],
    # Knowledge - Operational Standards
    "knowledge.operational_standards.85_percent_coverage_gate": [
        "85%",
        "coverage gate",
        "quality gate",
        "minimum coverage",
        "test threshold",
    ],
    "knowledge.operational_standards.rbac_from_day_one": [
        "rbac",
        "role-based",
        "permission",
        "access control",
        "admin",
        "role",
        "authorization",
    ],
    "knowledge.operational_standards.event_sourcing_pattern": [
        "event sourcing",
        "event store",
        "event log",
        "audit trail",
        "immutable log",
        "replay",
    ],
    "knowledge.operational_standards.base_model_inheritance": [
        "base model",
        "basemodel",
        "uuid",
        "timestamps",
        "created_at",
        "updated_at",
        "change tracking",
        "soft delete",
    ],
}

# System prompt for the architect clone
SYSTEM_PROMPT = (
    "You are Aaron's AI architect clone. You design solutions using his "
    "established patterns: microservices with event-driven communication, "
    "FastAPI/Express backends, React frontends, PostgreSQL, comprehensive "
    "testing with 85%+ coverage gates, multi-tenant isolation, and RBAC "
    "from day one. You compose solutions from kit templates, prioritize "
    "developer experience, and always include quality gates, monitoring, "
    "and deployment automation in your designs."
)


def chatml_messages(
    user_content: str,
    assistant_content: str,
    system_content: str | None = None,
) -> list[dict[str, str]]:
    """Format messages into ChatML message list."""
    messages = []
    if system_content:
        messages.append({"role": "system", "content": system_content})
    messages.append({"role": "user", "content": user_content})
    messages.append({"role": "assistant", "content": assistant_content})
    return messages


def chatml_record(
    user_content: str,
    assistant_content: str,
    source_file: str,
    taxonomy_category: str,
    chunk_hash: str,
) -> dict:
    """Create a complete ChatML training record with metadata."""
    return {
        "messages": chatml_messages(user_content, assistant_content, SYSTEM_PROMPT),
        "metadata": {
            "source_file": source_file,
            "taxonomy_category": taxonomy_category,
            "chunk_hash": chunk_hash,
        },
    }
