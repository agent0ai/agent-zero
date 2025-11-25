"""
Intelligent Context Retrieval Engine for Unity Projects.

This module provides advanced context-aware retrieval with:
- Multi-hop reasoning through entity relationships
- Semantic expansion and query understanding
- Context ranking and relevance scoring
- Automatic context chain building
- LLM-assisted query refinement
"""

import asyncio
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import logging

from langchain_core.documents import Document

from python.helpers.unity_qdrant_enhanced import (
    UnityQdrantEnhanced, UnityCollectionType, UnitySearchResult, UnityQueryContext
)
from python.unity_memory.unity_schema import (
    EntityType, RelationshipType, UnityQueryBuilder
)

logger = logging.getLogger(__name__)


class QueryIntent(Enum):
    """Detected intent of user queries."""
    FIND_CODE = "find_code"
    UNDERSTAND_SYSTEM = "understand_system"
    DEBUG_ERROR = "debug_error"
    IMPLEMENT_FEATURE = "implement_feature"
    OPTIMIZE_PERFORMANCE = "optimize_performance"
    FIND_USAGE = "find_usage"
    NAVIGATE_PROJECT = "navigate_project"
    REVIEW_ARCHITECTURE = "review_architecture"
    GET_DOCUMENTATION = "get_documentation"
    GENERAL = "general"


@dataclass
class QueryAnalysis:
    """Analysis of a user query."""
    original_query: str
    intent: QueryIntent
    entities_mentioned: List[str]
    unity_concepts: List[str]
    code_patterns: List[str]
    file_references: List[str]
    expanded_query: str
    confidence: float


@dataclass
class ContextChain:
    """A chain of related context for multi-hop reasoning."""
    primary_results: List[UnitySearchResult]
    hop_1_results: List[UnitySearchResult]
    hop_2_results: List[UnitySearchResult]
    relationships_found: List[Dict[str, Any]]
    total_score: float

    def all_results(self) -> List[UnitySearchResult]:
        """Get all results in order of relevance."""
        return self.primary_results + self.hop_1_results + self.hop_2_results


@dataclass
class RetrievalContext:
    """Full context for a query including all relevant information."""
    query_analysis: QueryAnalysis
    context_chain: ContextChain
    summary: str
    recommended_actions: List[str]
    related_errors: List[Dict[str, Any]]
    related_solutions: List[Dict[str, Any]]
    related_tasks: List[Dict[str, Any]]


class UnityContextEngine:
    """
    Intelligent context retrieval engine for Unity projects.

    Features:
    - Query intent detection and semantic expansion
    - Multi-hop reasoning through entity relationships
    - Context ranking with relevance scoring
    - Automatic context chain building
    - Error-solution matching
    """

    # Unity-specific concepts for query expansion
    UNITY_CONCEPTS = {
        # Core
        "gameobject", "component", "transform", "prefab", "scene",
        "hierarchy", "inspector", "project", "assets",
        # Physics
        "rigidbody", "collider", "trigger", "collision", "physics",
        "raycast", "joint", "force", "velocity",
        # Rendering
        "renderer", "material", "shader", "mesh", "texture",
        "lighting", "camera", "culling", "LOD",
        # Animation
        "animator", "animation", "state machine", "blend tree",
        "animation controller", "mecanim",
        # UI
        "canvas", "button", "text", "image", "panel",
        "layout", "event system", "ui toolkit",
        # Audio
        "audio source", "audio listener", "audio mixer",
        # Networking
        "netcode", "network", "rpc", "sync", "spawn",
        "network behaviour", "network variable",
        # AI
        "navmesh", "agent", "pathfinding", "behavior tree",
        # Scripting
        "monobehaviour", "scriptable object", "coroutine",
        "async", "update", "start", "awake",
    }

    # Error pattern recognition
    ERROR_PATTERNS = {
        r"NullReferenceException": "null_reference",
        r"MissingReferenceException": "missing_reference",
        r"MissingComponentException": "missing_component",
        r"IndexOutOfRangeException": "index_out_of_range",
        r"InvalidOperationException": "invalid_operation",
        r"SerializationException": "serialization",
        r"cannot be used in this context": "context_error",
        r"not found": "not_found",
        r"compile error": "compile_error",
        r"shader error": "shader_error",
    }

    def __init__(
        self,
        qdrant: UnityQdrantEnhanced,
        project_id: str,
        llm_callback: Optional[callable] = None,
        max_context_items: int = 50,
        multi_hop_depth: int = 2,
    ):
        self.qdrant = qdrant
        self.project_id = project_id
        self.llm_callback = llm_callback
        self.max_context_items = max_context_items
        self.multi_hop_depth = multi_hop_depth

        # Cache for recent queries
        self._query_cache: Dict[str, RetrievalContext] = {}
        self._entity_cache: Dict[str, UnitySearchResult] = {}

    async def get_context(
        self,
        query: str,
        unity_context: Optional[UnityQueryContext] = None,
        include_code: bool = True,
        include_errors: bool = True,
        include_tasks: bool = True,
        max_results: int = 30,
    ) -> RetrievalContext:
        """
        Get comprehensive context for a query.

        This is the main entry point for intelligent retrieval.
        """
        # Check cache
        cache_key = f"{query}:{self.project_id}"
        if cache_key in self._query_cache:
            return self._query_cache[cache_key]

        # Analyze query
        analysis = await self._analyze_query(query)

        # Build context chain with multi-hop reasoning
        context_chain = await self._build_context_chain(
            analysis, unity_context, max_results
        )

        # Get related errors and solutions if debugging
        related_errors = []
        related_solutions = []
        if include_errors and analysis.intent in [QueryIntent.DEBUG_ERROR, QueryIntent.GENERAL]:
            related_errors = await self._find_related_errors(query, analysis)
            related_solutions = await self._find_related_solutions(query, analysis)

        # Get related tasks
        related_tasks = []
        if include_tasks:
            related_tasks = await self._find_related_tasks(query, analysis)

        # Generate summary and recommendations
        summary = self._generate_context_summary(
            analysis, context_chain, related_errors, related_solutions
        )
        recommendations = self._generate_recommendations(
            analysis, context_chain, related_errors
        )

        result = RetrievalContext(
            query_analysis=analysis,
            context_chain=context_chain,
            summary=summary,
            recommended_actions=recommendations,
            related_errors=related_errors,
            related_solutions=related_solutions,
            related_tasks=related_tasks,
        )

        # Cache result
        self._query_cache[cache_key] = result

        return result

    async def _analyze_query(self, query: str) -> QueryAnalysis:
        """Analyze query to understand intent and extract entities."""
        query_lower = query.lower()

        # Detect intent
        intent = self._detect_intent(query_lower)

        # Extract mentioned entities
        entities = self._extract_entities(query)

        # Find Unity concepts
        concepts = [c for c in self.UNITY_CONCEPTS if c in query_lower]

        # Find code patterns
        code_patterns = self._extract_code_patterns(query)

        # Find file references
        file_refs = re.findall(r'[\w/]+\.(cs|unity|prefab|mat|asset)', query)

        # Expand query with related terms
        expanded = self._expand_query(query, intent, concepts, entities)

        return QueryAnalysis(
            original_query=query,
            intent=intent,
            entities_mentioned=entities,
            unity_concepts=concepts,
            code_patterns=code_patterns,
            file_references=file_refs,
            expanded_query=expanded,
            confidence=0.8 if concepts or entities else 0.5,
        )

    def _detect_intent(self, query: str) -> QueryIntent:
        """Detect the intent of a query."""
        # Error debugging
        if any(word in query for word in ["error", "exception", "bug", "crash", "fix", "debug", "issue"]):
            return QueryIntent.DEBUG_ERROR

        # Finding code
        if any(word in query for word in ["find", "where", "locate", "search for", "show me"]):
            return QueryIntent.FIND_CODE

        # Understanding
        if any(word in query for word in ["how does", "explain", "what is", "understand", "describe"]):
            return QueryIntent.UNDERSTAND_SYSTEM

        # Implementation
        if any(word in query for word in ["implement", "create", "add", "make", "build", "develop"]):
            return QueryIntent.IMPLEMENT_FEATURE

        # Performance
        if any(word in query for word in ["performance", "optimize", "slow", "fps", "memory", "profile"]):
            return QueryIntent.OPTIMIZE_PERFORMANCE

        # Usage
        if any(word in query for word in ["usage", "used by", "references", "depends on", "using"]):
            return QueryIntent.FIND_USAGE

        # Documentation
        if any(word in query for word in ["document", "docs", "api", "reference", "guide"]):
            return QueryIntent.GET_DOCUMENTATION

        # Architecture
        if any(word in query for word in ["architecture", "structure", "design", "pattern", "overview"]):
            return QueryIntent.REVIEW_ARCHITECTURE

        return QueryIntent.GENERAL

    def _extract_entities(self, query: str) -> List[str]:
        """Extract entity names from query."""
        entities = []

        # PascalCase names (likely class/component names)
        entities.extend(re.findall(r'\b([A-Z][a-zA-Z0-9]+(?:[A-Z][a-zA-Z0-9]+)+)\b', query))

        # camelCase names (likely variable/method names)
        entities.extend(re.findall(r'\b([a-z][a-zA-Z0-9]+(?:[A-Z][a-zA-Z0-9]+)+)\b', query))

        # Quoted strings
        entities.extend(re.findall(r'["\']([^"\']+)["\']', query))

        return list(set(entities))

    def _extract_code_patterns(self, query: str) -> List[str]:
        """Extract code-like patterns from query."""
        patterns = []

        # Method signatures
        patterns.extend(re.findall(r'\b\w+\s*\([^)]*\)', query))

        # Type annotations
        patterns.extend(re.findall(r'\b(?:int|float|string|bool|Vector[23]|Quaternion|Transform)\b', query))

        # Unity attributes
        patterns.extend(re.findall(r'\[\w+(?:\([^)]*\))?\]', query))

        return patterns

    def _expand_query(
        self,
        query: str,
        intent: QueryIntent,
        concepts: List[str],
        entities: List[str]
    ) -> str:
        """Expand query with related terms for better retrieval."""
        expansions = [query]

        # Add synonyms based on intent
        if intent == QueryIntent.DEBUG_ERROR:
            expansions.append("exception solution fix")
        elif intent == QueryIntent.FIND_CODE:
            expansions.append("class method function script")
        elif intent == QueryIntent.IMPLEMENT_FEATURE:
            expansions.append("example implementation pattern")
        elif intent == QueryIntent.OPTIMIZE_PERFORMANCE:
            expansions.append("optimization profiler memory CPU")

        # Add concept-related terms
        concept_expansions = {
            "collision": "oncollisionenter collider trigger physics",
            "animation": "animator state mecanim blend clip",
            "networking": "netcode rpc sync spawn network",
            "ui": "canvas button text panel layout",
        }

        for concept in concepts:
            if concept in concept_expansions:
                expansions.append(concept_expansions[concept])

        return " ".join(expansions)

    async def _build_context_chain(
        self,
        analysis: QueryAnalysis,
        unity_context: Optional[UnityQueryContext],
        max_results: int,
    ) -> ContextChain:
        """Build context chain with multi-hop reasoning."""
        # Primary search
        primary_results = await self._primary_search(analysis, unity_context, max_results)

        # First hop - find related entities
        hop_1_results = await self._hop_search(primary_results, depth=1)

        # Second hop - expand further
        hop_2_results = []
        if self.multi_hop_depth >= 2 and len(hop_1_results) < max_results:
            hop_2_results = await self._hop_search(hop_1_results, depth=2)

        # Find relationships
        relationships = await self._find_relationships(
            primary_results + hop_1_results
        )

        # Calculate total score
        total_score = sum(r.score for r in primary_results)

        return ContextChain(
            primary_results=primary_results,
            hop_1_results=hop_1_results[:15],
            hop_2_results=hop_2_results[:10],
            relationships_found=relationships,
            total_score=total_score,
        )

    async def _primary_search(
        self,
        analysis: QueryAnalysis,
        unity_context: Optional[UnityQueryContext],
        max_results: int,
    ) -> List[UnitySearchResult]:
        """Perform primary search based on query analysis."""
        # Select collection types based on intent
        collection_types = self._select_collections(analysis.intent)

        # Build filters
        filters = {}
        if analysis.file_references:
            filters["file_path"] = analysis.file_references[0]

        results = await self.qdrant.search_unity(
            query=analysis.expanded_query,
            collection_types=collection_types,
            project_id=self.project_id,
            context=unity_context,
            limit=max_results,
            filters=filters if filters else None,
        )

        # Boost scores for exact entity matches
        for result in results:
            for entity in analysis.entities_mentioned:
                if entity.lower() in result.document.page_content.lower():
                    result.score *= 1.2

        return sorted(results, key=lambda x: x.score, reverse=True)

    def _select_collections(self, intent: QueryIntent) -> List[UnityCollectionType]:
        """Select relevant collections based on query intent."""
        if intent == QueryIntent.FIND_CODE:
            return [
                UnityCollectionType.SCRIPTS,
                UnityCollectionType.COMPONENTS,
                UnityCollectionType.PREFABS,
            ]
        elif intent == QueryIntent.DEBUG_ERROR:
            return [
                UnityCollectionType.ERRORS,
                UnityCollectionType.SOLUTIONS,
                UnityCollectionType.SCRIPTS,
            ]
        elif intent == QueryIntent.IMPLEMENT_FEATURE:
            return [
                UnityCollectionType.SCRIPTS,
                UnityCollectionType.SOLUTIONS,
                UnityCollectionType.DOCUMENTATION,
            ]
        elif intent == QueryIntent.UNDERSTAND_SYSTEM:
            return [
                UnityCollectionType.SCRIPTS,
                UnityCollectionType.SCENES,
                UnityCollectionType.DOCUMENTATION,
            ]
        elif intent == QueryIntent.FIND_USAGE:
            return [
                UnityCollectionType.SCRIPTS,
                UnityCollectionType.SCENES,
                UnityCollectionType.PREFABS,
                UnityCollectionType.GAMEOBJECTS,
            ]
        elif intent == QueryIntent.REVIEW_ARCHITECTURE:
            return [
                UnityCollectionType.SCENES,
                UnityCollectionType.SCRIPTS,
                UnityCollectionType.PREFABS,
            ]
        else:
            return list(UnityCollectionType)[:8]  # Top 8 most relevant

    async def _hop_search(
        self,
        source_results: List[UnitySearchResult],
        depth: int,
    ) -> List[UnitySearchResult]:
        """Search for entities related to source results."""
        related_results = []
        seen_ids = {r.document.metadata.get("id") for r in source_results}

        for result in source_results[:10]:  # Limit expansion sources
            metadata = result.document.metadata

            # Get related entities based on relationships
            relationships = result.relationships
            for rel in relationships:
                target_id = rel.get("target_entity")
                source_id = rel.get("source_entity")

                for related_id in [target_id, source_id]:
                    if related_id and related_id not in seen_ids:
                        try:
                            docs = await self.qdrant.aget_by_ids([related_id])
                            for doc in docs:
                                related_results.append(UnitySearchResult(
                                    document=doc,
                                    score=result.score * 0.7,  # Reduce score for hops
                                    collection=result.collection,
                                ))
                                seen_ids.add(related_id)
                        except Exception:
                            pass

            # Expand based on entity type
            entity_type = metadata.get("entity_type")
            if entity_type == "script":
                # Find GameObjects using this script
                class_names = metadata.get("class_names", [])
                for class_name in class_names[:3]:
                    try:
                        usage_results = await self.qdrant.find_gameobjects_by_component(
                            class_name, project_id=self.project_id
                        )
                        for ur in usage_results:
                            if ur.document.metadata.get("id") not in seen_ids:
                                ur.score *= 0.6
                                related_results.append(ur)
                                seen_ids.add(ur.document.metadata.get("id"))
                    except Exception:
                        pass

            elif entity_type == "scene":
                # Find key GameObjects in scene
                scene_name = metadata.get("scene_name")
                if scene_name:
                    try:
                        go_results = await self.qdrant.search_unity(
                            query=f"important gameobjects in {scene_name}",
                            collection_types=[UnityCollectionType.GAMEOBJECTS],
                            project_id=self.project_id,
                            filters={"scene_name": scene_name},
                            limit=5,
                        )
                        for gr in go_results:
                            if gr.document.metadata.get("id") not in seen_ids:
                                gr.score *= 0.5
                                related_results.append(gr)
                                seen_ids.add(gr.document.metadata.get("id"))
                    except Exception:
                        pass

        return related_results

    async def _find_relationships(
        self,
        results: List[UnitySearchResult],
    ) -> List[Dict[str, Any]]:
        """Find relationships between result entities."""
        relationships = []

        for result in results:
            relationships.extend(result.relationships)

        # Deduplicate
        seen = set()
        unique_rels = []
        for rel in relationships:
            key = f"{rel.get('source_entity')}:{rel.get('target_entity')}"
            if key not in seen:
                seen.add(key)
                unique_rels.append(rel)

        return unique_rels

    async def _find_related_errors(
        self,
        query: str,
        analysis: QueryAnalysis,
    ) -> List[Dict[str, Any]]:
        """Find errors related to the query."""
        # Check if query contains error message
        error_type = None
        for pattern, etype in self.ERROR_PATTERNS.items():
            if re.search(pattern, query, re.IGNORECASE):
                error_type = etype
                break

        results = await self.qdrant.search_unity(
            query=query,
            collection_types=[UnityCollectionType.ERRORS],
            project_id=self.project_id,
            limit=5,
            filters={"error_type": error_type} if error_type else None,
        )

        return [
            {
                "error_type": r.document.metadata.get("error_type"),
                "message": r.document.metadata.get("error_message"),
                "has_solution": r.document.metadata.get("has_solution", False),
                "score": r.score,
            }
            for r in results
        ]

    async def _find_related_solutions(
        self,
        query: str,
        analysis: QueryAnalysis,
    ) -> List[Dict[str, Any]]:
        """Find solutions related to the query."""
        results = await self.qdrant.search_unity(
            query=query,
            collection_types=[UnityCollectionType.SOLUTIONS],
            project_id=self.project_id,
            limit=5,
        )

        return [
            {
                "problem": r.document.metadata.get("problem_description", ""),
                "solution": r.document.metadata.get("solution_description", ""),
                "effectiveness": r.document.metadata.get("effectiveness_score", 0),
                "score": r.score,
            }
            for r in results
        ]

    async def _find_related_tasks(
        self,
        query: str,
        analysis: QueryAnalysis,
    ) -> List[Dict[str, Any]]:
        """Find tasks related to the query."""
        results = await self.qdrant.search_unity(
            query=query,
            collection_types=[UnityCollectionType.TASKS],
            project_id=self.project_id,
            limit=5,
        )

        return [
            {
                "title": r.document.metadata.get("title"),
                "status": r.document.metadata.get("status"),
                "priority": r.document.metadata.get("priority"),
                "score": r.score,
            }
            for r in results
        ]

    def _generate_context_summary(
        self,
        analysis: QueryAnalysis,
        context_chain: ContextChain,
        errors: List[Dict[str, Any]],
        solutions: List[Dict[str, Any]],
    ) -> str:
        """Generate a summary of retrieved context."""
        parts = []

        # Query understanding
        parts.append(f"Query Intent: {analysis.intent.value}")
        if analysis.unity_concepts:
            parts.append(f"Unity Concepts: {', '.join(analysis.unity_concepts)}")
        if analysis.entities_mentioned:
            parts.append(f"Entities: {', '.join(analysis.entities_mentioned)}")

        # Results summary
        total_results = len(context_chain.all_results())
        parts.append(f"\nFound {total_results} relevant items")

        # Top results by type
        type_counts = {}
        for result in context_chain.primary_results:
            t = result.collection
            type_counts[t] = type_counts.get(t, 0) + 1

        if type_counts:
            parts.append("Results by type: " + ", ".join(
                f"{t}: {c}" for t, c in sorted(type_counts.items(), key=lambda x: -x[1])
            ))

        # Errors
        if errors:
            parts.append(f"\nFound {len(errors)} related error(s)")

        # Solutions
        if solutions:
            parts.append(f"Found {len(solutions)} potential solution(s)")

        return "\n".join(parts)

    def _generate_recommendations(
        self,
        analysis: QueryAnalysis,
        context_chain: ContextChain,
        errors: List[Dict[str, Any]],
    ) -> List[str]:
        """Generate recommended actions based on context."""
        recommendations = []

        if analysis.intent == QueryIntent.DEBUG_ERROR:
            if errors and any(e.get("has_solution") for e in errors):
                recommendations.append("Review existing solutions for similar errors")
            recommendations.append("Check null references in related scripts")
            recommendations.append("Verify component dependencies are met")

        elif analysis.intent == QueryIntent.IMPLEMENT_FEATURE:
            recommendations.append("Review existing similar implementations")
            recommendations.append("Check for reusable patterns in the codebase")

        elif analysis.intent == QueryIntent.OPTIMIZE_PERFORMANCE:
            recommendations.append("Profile the specific methods identified")
            recommendations.append("Check for unnecessary Update() calls")
            recommendations.append("Review object pooling opportunities")

        elif analysis.intent == QueryIntent.FIND_USAGE:
            recommendations.append("Check scene references")
            recommendations.append("Review prefab dependencies")
            recommendations.append("Search for script references")

        # Always add these for code queries
        if analysis.intent in [QueryIntent.FIND_CODE, QueryIntent.UNDERSTAND_SYSTEM]:
            if context_chain.primary_results:
                top_result = context_chain.primary_results[0]
                file_path = top_result.document.metadata.get("file_path")
                if file_path:
                    recommendations.append(f"Open: {file_path}")

        return recommendations

    async def get_entity_context(
        self,
        entity_id: str,
        include_relationships: bool = True,
        include_usages: bool = True,
        max_related: int = 20,
    ) -> Dict[str, Any]:
        """Get comprehensive context for a specific entity."""
        # Retrieve entity
        docs = await self.qdrant.aget_by_ids([entity_id])
        if not docs:
            return {"error": "Entity not found"}

        entity = docs[0]
        metadata = entity.metadata
        entity_type = metadata.get("entity_type")

        result = {
            "entity": {
                "id": entity_id,
                "type": entity_type,
                "name": metadata.get("entity_name"),
                "content": entity.page_content,
                "metadata": metadata,
            },
            "relationships": [],
            "usages": [],
            "dependencies": [],
        }

        if include_relationships:
            result["dependencies"] = await self.qdrant.get_entity_dependencies(
                entity_id, depth=2
            )

        if include_usages:
            # Find where this entity is used
            if entity_type == "script":
                # Find GameObjects using this script
                class_names = metadata.get("class_names", [])
                for class_name in class_names:
                    usages = await self.qdrant.find_gameobjects_by_component(
                        class_name, project_id=self.project_id
                    )
                    result["usages"].extend([
                        {
                            "entity_id": u.document.metadata.get("id"),
                            "name": u.document.metadata.get("entity_name"),
                            "type": "gameobject",
                            "scene": u.document.metadata.get("scene_name"),
                        }
                        for u in usages
                    ])

            elif entity_type == "prefab":
                # Find scenes containing this prefab
                prefab_name = metadata.get("entity_name")
                results = await self.qdrant.search_unity(
                    query=prefab_name,
                    collection_types=[UnityCollectionType.SCENES],
                    project_id=self.project_id,
                    limit=10,
                )
                result["usages"] = [
                    {
                        "entity_id": r.document.metadata.get("id"),
                        "name": r.document.metadata.get("entity_name"),
                        "type": "scene",
                    }
                    for r in results
                ]

        return result

    async def find_code_pattern(
        self,
        pattern_description: str,
        max_examples: int = 5,
    ) -> List[Dict[str, Any]]:
        """Find code examples matching a pattern description."""
        results = await self.qdrant.search_unity(
            query=f"code example {pattern_description}",
            collection_types=[
                UnityCollectionType.SCRIPTS,
                UnityCollectionType.SOLUTIONS,
            ],
            project_id=self.project_id,
            limit=max_examples * 2,
        )

        examples = []
        for result in results:
            content = result.document.page_content
            metadata = result.document.metadata

            # Extract code-like sections
            code_match = re.search(
                r'```[csharp]*\n(.*?)\n```',
                content,
                re.DOTALL
            )

            examples.append({
                "file": metadata.get("file_path"),
                "class": metadata.get("class_names", [None])[0],
                "content": code_match.group(1) if code_match else content[:500],
                "score": result.score,
            })

        return examples[:max_examples]

    def clear_cache(self):
        """Clear all caches."""
        self._query_cache.clear()
        self._entity_cache.clear()


class ContextAwarePromptBuilder:
    """Build context-aware prompts for Unity development."""

    def __init__(self, context_engine: UnityContextEngine):
        self.context_engine = context_engine

    async def build_debug_prompt(
        self,
        error_message: str,
        stack_trace: str = "",
    ) -> str:
        """Build a prompt for debugging an error."""
        context = await self.context_engine.get_context(
            f"{error_message} {stack_trace}",
            include_code=True,
            include_errors=True,
        )

        prompt_parts = [
            "# Unity Error Debug Context\n",
            f"## Error\n{error_message}\n",
        ]

        if stack_trace:
            prompt_parts.append(f"## Stack Trace\n```\n{stack_trace}\n```\n")

        # Add related code
        if context.context_chain.primary_results:
            prompt_parts.append("## Related Code\n")
            for result in context.context_chain.primary_results[:3]:
                path = result.document.metadata.get("file_path", "Unknown")
                content = result.document.page_content[:500]
                prompt_parts.append(f"### {path}\n```csharp\n{content}\n```\n")

        # Add known solutions
        if context.related_solutions:
            prompt_parts.append("## Known Solutions\n")
            for sol in context.related_solutions[:2]:
                prompt_parts.append(f"- {sol.get('solution', '')}\n")

        prompt_parts.append("## Recommendations\n")
        for rec in context.recommended_actions:
            prompt_parts.append(f"- {rec}\n")

        return "".join(prompt_parts)

    async def build_implementation_prompt(
        self,
        feature_description: str,
    ) -> str:
        """Build a prompt for implementing a feature."""
        context = await self.context_engine.get_context(
            f"implement {feature_description}",
            include_code=True,
            include_tasks=True,
        )

        prompt_parts = [
            "# Unity Implementation Context\n",
            f"## Feature: {feature_description}\n",
        ]

        # Add similar implementations
        if context.context_chain.primary_results:
            prompt_parts.append("## Similar Implementations\n")
            for result in context.context_chain.primary_results[:5]:
                name = result.document.metadata.get("entity_name", "Unknown")
                path = result.document.metadata.get("file_path", "")
                prompt_parts.append(f"### {name}\n")
                prompt_parts.append(f"Path: {path}\n")
                prompt_parts.append(f"```csharp\n{result.document.page_content[:800]}\n```\n")

        # Add related tasks
        if context.related_tasks:
            prompt_parts.append("## Related Tasks\n")
            for task in context.related_tasks:
                status = task.get("status", "unknown")
                title = task.get("title", "")
                prompt_parts.append(f"- [{status}] {title}\n")

        return "".join(prompt_parts)

    async def build_architecture_prompt(
        self,
        system_query: str,
    ) -> str:
        """Build a prompt for understanding system architecture."""
        context = await self.context_engine.get_context(
            f"architecture {system_query}",
            include_code=True,
        )

        prompt_parts = [
            "# Unity Architecture Context\n",
            f"## System: {system_query}\n",
        ]

        # Group by entity type
        by_type = {}
        for result in context.context_chain.all_results():
            t = result.document.metadata.get("entity_type", "other")
            if t not in by_type:
                by_type[t] = []
            by_type[t].append(result)

        for entity_type, results in by_type.items():
            prompt_parts.append(f"\n## {entity_type.title()}s\n")
            for result in results[:5]:
                name = result.document.metadata.get("entity_name", "Unknown")
                prompt_parts.append(f"- {name}\n")

        # Add relationships
        if context.context_chain.relationships_found:
            prompt_parts.append("\n## Relationships\n")
            for rel in context.context_chain.relationships_found[:10]:
                src = rel.get("source_entity", "")[:20]
                tgt = rel.get("target_entity", "")[:20]
                rtype = rel.get("relationship_type", "")
                prompt_parts.append(f"- {src} --{rtype}--> {tgt}\n")

        return "".join(prompt_parts)
