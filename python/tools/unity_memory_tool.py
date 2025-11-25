"""
Unity Memory Tool for Agent Zero.

Provides intelligent memory operations for Unity game development,
integrating with the enhanced Qdrant backend for powerful searches
and context retrieval.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from python.helpers.tool import Tool, Response
from python.helpers import files
from python.helpers.unity_qdrant_enhanced import (
    UnityQdrantEnhanced, UnityCollectionType, UnityQueryContext
)
from python.helpers.unity_context_engine import UnityContextEngine, QueryIntent
from python.helpers.unity_knowledge_extractor import UnityKnowledgeExtractor
from python.helpers.unity_project_tracker import UnityProjectTracker


class UnityMemory(Tool):
    """
    Unity-specific memory tool with intelligent context retrieval.

    Supports operations:
    - search: Semantic search across Unity knowledge base
    - store: Store new Unity entities (scripts, solutions, errors, tasks)
    - context: Get comprehensive context for a query
    - extract: Extract knowledge from Unity project
    - relationships: Query entity relationships
    - health: Get project health report
    """

    async def execute(self, **kwargs) -> Response:
        operation = kwargs.get("operation", "search")

        # Initialize Unity systems if needed
        await self._ensure_initialized()

        if operation == "search":
            return await self._search(**kwargs)
        elif operation == "store":
            return await self._store(**kwargs)
        elif operation == "context":
            return await self._get_context(**kwargs)
        elif operation == "extract":
            return await self._extract_project(**kwargs)
        elif operation == "relationships":
            return await self._get_relationships(**kwargs)
        elif operation == "health":
            return await self._get_health(**kwargs)
        elif operation == "scene_info":
            return await self._get_scene_info(**kwargs)
        elif operation == "find_usages":
            return await self._find_usages(**kwargs)
        elif operation == "debug_error":
            return await self._debug_error(**kwargs)
        elif operation == "task":
            return await self._manage_task(**kwargs)
        else:
            return Response(
                message=f"Unknown operation: {operation}",
                break_loop=False
            )

    async def _ensure_initialized(self):
        """Ensure Unity systems are initialized."""
        if not hasattr(self.agent.context, "unity_qdrant"):
            from python.helpers.memory import Memory

            # Get base memory
            memory = await Memory.get(self.agent)

            # Check if it's Qdrant backend
            if hasattr(memory.db, "is_qdrant") and memory.db.is_qdrant:
                # Create enhanced Unity client from existing connection
                self.agent.context.unity_qdrant = UnityQdrantEnhanced(
                    embedder=memory.db.embedder,
                    base_collection="agent-zero-unity",
                    url=memory.db.client._url,
                )
            else:
                # Create new Unity client
                from python.helpers.memory_config import get_memory_config
                cfg = get_memory_config()
                qcfg = cfg.get("qdrant", {}) or {}

                from models import get_embedding_model
                embedder = get_embedding_model(
                    self.agent.config.embeddings_model.provider,
                    self.agent.config.embeddings_model.name,
                )

                self.agent.context.unity_qdrant = UnityQdrantEnhanced(
                    embedder=embedder,
                    base_collection="agent-zero-unity",
                    url=qcfg.get("url", "http://localhost:6333"),
                    api_key=qcfg.get("api_key", ""),
                )

            # Initialize context engine
            project_id = self.agent.context.config.memory_subdir or "default"
            self.agent.context.unity_context = UnityContextEngine(
                self.agent.context.unity_qdrant,
                project_id,
            )

    async def _search(self, **kwargs) -> Response:
        """Perform semantic search across Unity knowledge base."""
        query = kwargs.get("query", "")
        entity_types = kwargs.get("entity_types", None)
        scene_filter = kwargs.get("scene_filter", None)
        limit = kwargs.get("limit", 20)
        include_relationships = kwargs.get("include_relationships", False)

        if not query:
            return Response(message="Query is required for search", break_loop=False)

        # Convert entity type strings to enum
        collection_types = None
        if entity_types:
            type_map = {
                "script": UnityCollectionType.SCRIPTS,
                "scene": UnityCollectionType.SCENES,
                "prefab": UnityCollectionType.PREFABS,
                "gameobject": UnityCollectionType.GAMEOBJECTS,
                "asset": UnityCollectionType.ASSETS,
                "error": UnityCollectionType.ERRORS,
                "solution": UnityCollectionType.SOLUTIONS,
                "task": UnityCollectionType.TASKS,
                "documentation": UnityCollectionType.DOCUMENTATION,
            }
            collection_types = [
                type_map.get(t.lower())
                for t in entity_types
                if t.lower() in type_map
            ]

        # Build filters
        filters = {}
        if scene_filter:
            filters["scene_name"] = scene_filter

        project_id = self.agent.context.config.memory_subdir or "default"

        results = await self.agent.context.unity_qdrant.search_unity(
            query=query,
            collection_types=collection_types,
            project_id=project_id,
            limit=limit,
            filters=filters if filters else None,
            include_relationships=include_relationships,
        )

        # Format results
        output = f"Found {len(results)} results for: {query}\n\n"

        for i, result in enumerate(results[:limit], 1):
            metadata = result.document.metadata
            output += f"## {i}. {metadata.get('entity_name', 'Unknown')} "
            output += f"({result.collection}, score: {result.score:.2f})\n"

            if metadata.get("file_path"):
                output += f"   Path: {metadata['file_path']}\n"
            if metadata.get("scene_name"):
                output += f"   Scene: {metadata['scene_name']}\n"

            # Show preview of content
            content = result.document.page_content[:300]
            output += f"   Preview: {content}...\n\n"

            # Show relationships
            if result.relationships:
                output += f"   Relationships: {len(result.relationships)}\n"
                for rel in result.relationships[:3]:
                    output += f"     - {rel.get('relationship_type')}: {rel.get('target_entity', '')[:30]}\n"
                output += "\n"

        return Response(message=output, break_loop=False)

    async def _store(self, **kwargs) -> Response:
        """Store new Unity entity in knowledge base."""
        entity_type = kwargs.get("entity_type", "documentation")
        name = kwargs.get("name", "")
        content = kwargs.get("content", "")
        file_path = kwargs.get("file_path", None)
        metadata = kwargs.get("metadata", {})

        if not name or not content:
            return Response(
                message="Name and content are required for storing",
                break_loop=False
            )

        project_id = self.agent.context.config.memory_subdir or "default"
        qdrant = self.agent.context.unity_qdrant

        try:
            if entity_type == "solution":
                doc_id = await qdrant.store_error(
                    error_message=metadata.get("error_message", name),
                    error_type=metadata.get("error_type", "General"),
                    stack_trace=metadata.get("stack_trace", ""),
                    project_id=project_id,
                    solution=content,
                    metadata=metadata,
                )
            elif entity_type == "error":
                doc_id = await qdrant.store_error(
                    error_message=name,
                    error_type=metadata.get("error_type", "Unknown"),
                    stack_trace=content,
                    project_id=project_id,
                    metadata=metadata,
                )
            elif entity_type == "task":
                doc_id = await qdrant.store_task(
                    task_id=metadata.get("task_id", name.replace(" ", "_")),
                    title=name,
                    description=content,
                    status=metadata.get("status", "pending"),
                    priority=metadata.get("priority", 3),
                    project_id=project_id,
                    tags=metadata.get("tags", []),
                    metadata=metadata,
                )
            else:
                # Generic documentation/asset
                doc_id = await qdrant.store_asset(
                    asset_path=file_path or f"knowledge/{name}",
                    asset_type=entity_type,
                    guid=name,
                    project_id=project_id,
                    metadata={
                        "entity_name": name,
                        "content": content,
                        **metadata,
                    }
                )

            return Response(
                message=f"Successfully stored {entity_type}: {name}\nID: {doc_id}",
                break_loop=False
            )

        except Exception as e:
            return Response(
                message=f"Failed to store {entity_type}: {str(e)}",
                break_loop=False
            )

    async def _get_context(self, **kwargs) -> Response:
        """Get comprehensive context for a query."""
        query = kwargs.get("query", "")
        include_code = kwargs.get("include_code", True)
        include_errors = kwargs.get("include_errors", True)
        include_tasks = kwargs.get("include_tasks", True)

        if not query:
            return Response(message="Query is required", break_loop=False)

        context_engine = self.agent.context.unity_context
        context = await context_engine.get_context(
            query=query,
            include_code=include_code,
            include_errors=include_errors,
            include_tasks=include_tasks,
        )

        # Format output
        output = f"# Context for: {query}\n\n"
        output += f"## Query Analysis\n"
        output += f"- Intent: {context.query_analysis.intent.value}\n"

        if context.query_analysis.unity_concepts:
            output += f"- Unity Concepts: {', '.join(context.query_analysis.unity_concepts)}\n"
        if context.query_analysis.entities_mentioned:
            output += f"- Entities: {', '.join(context.query_analysis.entities_mentioned)}\n"

        output += f"\n## Summary\n{context.summary}\n"

        # Primary results
        if context.context_chain.primary_results:
            output += f"\n## Relevant Code/Entities ({len(context.context_chain.primary_results)})\n"
            for result in context.context_chain.primary_results[:5]:
                meta = result.document.metadata
                output += f"\n### {meta.get('entity_name', 'Unknown')}\n"
                output += f"Type: {result.collection}, Score: {result.score:.2f}\n"
                if meta.get("file_path"):
                    output += f"Path: {meta['file_path']}\n"
                output += f"```\n{result.document.page_content[:500]}\n```\n"

        # Related errors
        if context.related_errors:
            output += f"\n## Related Errors ({len(context.related_errors)})\n"
            for error in context.related_errors[:3]:
                output += f"- {error.get('error_type')}: {error.get('message', '')[:100]}\n"
                if error.get("has_solution"):
                    output += f"  ✓ Solution available\n"

        # Related solutions
        if context.related_solutions:
            output += f"\n## Potential Solutions ({len(context.related_solutions)})\n"
            for sol in context.related_solutions[:3]:
                output += f"- {sol.get('problem', '')[:100]}\n"
                output += f"  → {sol.get('solution', '')[:150]}\n"

        # Recommendations
        if context.recommended_actions:
            output += f"\n## Recommendations\n"
            for rec in context.recommended_actions:
                output += f"- {rec}\n"

        return Response(message=output, break_loop=False)

    async def _extract_project(self, **kwargs) -> Response:
        """Extract knowledge from Unity project."""
        project_path = kwargs.get("project_path", "")
        incremental = kwargs.get("incremental", True)

        if not project_path:
            return Response(
                message="Project path is required for extraction",
                break_loop=False
            )

        if not files.exists(project_path):
            return Response(
                message=f"Project path not found: {project_path}",
                break_loop=False
            )

        project_id = self.agent.context.config.memory_subdir or "default"
        qdrant = self.agent.context.unity_qdrant

        extractor = UnityKnowledgeExtractor(
            qdrant_client=qdrant,
            project_id=project_id,
        )

        # Extract with progress updates
        def progress_callback(progress):
            percent = (
                progress.processed_files / progress.total_files * 100
                if progress.total_files > 0 else 0
            )
            self.agent.context.log.log(
                type="progress",
                heading=f"Extracting Unity project: {percent:.0f}%",
            )

        progress = await extractor.extract_project(
            project_path=project_path,
            incremental=incremental,
            progress_callback=progress_callback,
        )

        output = f"# Unity Project Extraction Complete\n\n"
        output += f"- Scripts extracted: {progress.scripts_extracted}\n"
        output += f"- Scenes extracted: {progress.scenes_extracted}\n"
        output += f"- Prefabs extracted: {progress.prefabs_extracted}\n"
        output += f"- Assets extracted: {progress.assets_extracted}\n"
        output += f"- Total files processed: {progress.processed_files}\n"

        if progress.errors:
            output += f"\n## Errors ({len(progress.errors)})\n"
            for error in progress.errors[:10]:
                output += f"- {error}\n"

        return Response(message=output, break_loop=False)

    async def _get_relationships(self, **kwargs) -> Response:
        """Query entity relationships."""
        entity_id = kwargs.get("entity_id", "")
        depth = kwargs.get("depth", 2)

        if not entity_id:
            return Response(
                message="Entity ID is required",
                break_loop=False
            )

        qdrant = self.agent.context.unity_qdrant
        dependencies = await qdrant.get_entity_dependencies(entity_id, depth)

        output = f"# Relationships for: {entity_id}\n\n"
        output += f"Found {len(dependencies)} relationships (depth: {depth})\n\n"

        for dep in dependencies[:20]:
            output += f"- {dep.get('relationship_type')}: "
            output += f"{dep.get('target_entity', 'Unknown')}\n"

        return Response(message=output, break_loop=False)

    async def _get_health(self, **kwargs) -> Response:
        """Get project health report."""
        project_path = kwargs.get("project_path", "")

        if not project_path:
            return Response(
                message="Project path is required for health check",
                break_loop=False
            )

        project_id = self.agent.context.config.memory_subdir or "default"
        qdrant = self.agent.context.unity_qdrant

        tracker = UnityProjectTracker(
            qdrant=qdrant,
            project_id=project_id,
            project_path=project_path,
        )

        report = await tracker.get_health_report()

        output = f"# Unity Project Health Report\n\n"
        output += f"**Health Score: {report['health_score']}/100**\n"
        output += f"State: {report['state']}\n\n"

        if report.get("issues"):
            output += f"## Issues\n"
            for issue in report["issues"]:
                output += f"- ⚠️ {issue}\n"
            output += "\n"

        output += f"## Statistics\n"
        stats = report.get("statistics", {})
        output += f"- Scripts: {stats.get('scripts', 0)}\n"
        output += f"- Scenes: {stats.get('scenes', 0)}\n"
        output += f"- Prefabs: {stats.get('prefabs', 0)}\n"
        output += f"- Lines of Code: {stats.get('lines_of_code', 0)}\n\n"

        output += f"## Build Info\n"
        build = report.get("build_info", {})
        output += f"- Last Build: {build.get('last_status', 'None')}\n"
        output += f"- Builds Today: {build.get('builds_today', 0)}\n"
        output += f"- Success Rate: {build.get('success_rate', 0):.0%}\n\n"

        if report.get("recommendations"):
            output += f"## Recommendations\n"
            for rec in report["recommendations"]:
                output += f"- 💡 {rec}\n"

        return Response(message=output, break_loop=False)

    async def _get_scene_info(self, **kwargs) -> Response:
        """Get comprehensive scene information."""
        scene_name = kwargs.get("scene_name", "")

        if not scene_name:
            return Response(
                message="Scene name is required",
                break_loop=False
            )

        project_id = self.agent.context.config.memory_subdir or "default"
        qdrant = self.agent.context.unity_qdrant

        # Search for scene
        results = await qdrant.search_unity(
            query=scene_name,
            collection_types=[UnityCollectionType.SCENES],
            project_id=project_id,
            filters={"scene_name": scene_name},
            limit=1,
        )

        if not results:
            return Response(
                message=f"Scene not found: {scene_name}",
                break_loop=False
            )

        scene = results[0]
        meta = scene.document.metadata

        output = f"# Scene: {scene_name}\n\n"
        output += f"Path: {meta.get('file_path', 'Unknown')}\n"
        output += f"GameObjects: {meta.get('game_object_count', 0)}\n"

        if meta.get("root_objects"):
            output += f"\n## Root Objects\n"
            for obj in meta.get("root_objects", [])[:20]:
                output += f"- {obj}\n"

        # Get GameObjects in scene
        go_results = await qdrant.search_unity(
            query=f"gameobjects in {scene_name}",
            collection_types=[UnityCollectionType.GAMEOBJECTS],
            project_id=project_id,
            filters={"scene_name": scene_name},
            limit=50,
        )

        if go_results:
            output += f"\n## Key GameObjects ({len(go_results)})\n"
            for go in go_results[:15]:
                go_meta = go.document.metadata
                output += f"- {go_meta.get('entity_name', 'Unknown')}"
                if go_meta.get("tag") and go_meta["tag"] != "Untagged":
                    output += f" [Tag: {go_meta['tag']}]"
                if go_meta.get("components"):
                    output += f" ({', '.join(go_meta['components'][:3])})"
                output += "\n"

        return Response(message=output, break_loop=False)

    async def _find_usages(self, **kwargs) -> Response:
        """Find usages of a class, method, or asset."""
        name = kwargs.get("name", "")
        usage_type = kwargs.get("type", "class")

        if not name:
            return Response(
                message="Name is required for usage search",
                break_loop=False
            )

        project_id = self.agent.context.config.memory_subdir or "default"
        qdrant = self.agent.context.unity_qdrant

        output = f"# Usages of: {name}\n\n"

        if usage_type == "class":
            # Find scripts containing this class
            script_results = await qdrant.find_scripts_by_class(name, project_id)
            if script_results:
                output += f"## In Scripts ({len(script_results)})\n"
                for r in script_results[:10]:
                    output += f"- {r.document.metadata.get('file_path', 'Unknown')}\n"

            # Find GameObjects using this as component
            go_results = await qdrant.find_gameobjects_by_component(
                name, project_id=project_id
            )
            if go_results:
                output += f"\n## As Component ({len(go_results)})\n"
                for r in go_results[:10]:
                    meta = r.document.metadata
                    output += f"- {meta.get('entity_name')} in {meta.get('scene_name', 'Unknown')}\n"

        elif usage_type == "method":
            # Search for method calls
            results = await qdrant.search_unity(
                query=f"calls {name} method",
                collection_types=[UnityCollectionType.SCRIPTS],
                project_id=project_id,
                limit=20,
            )
            if results:
                output += f"## Method References ({len(results)})\n"
                for r in results:
                    output += f"- {r.document.metadata.get('file_path', 'Unknown')}\n"

        elif usage_type == "asset":
            # Search for asset references
            results = await qdrant.search_unity(
                query=f"uses {name} asset",
                collection_types=[
                    UnityCollectionType.SCENES,
                    UnityCollectionType.PREFABS,
                ],
                project_id=project_id,
                limit=20,
            )
            if results:
                output += f"## Asset References ({len(results)})\n"
                for r in results:
                    meta = r.document.metadata
                    output += f"- {meta.get('entity_name')} ({r.collection})\n"

        if "##" not in output:
            output += "No usages found."

        return Response(message=output, break_loop=False)

    async def _debug_error(self, **kwargs) -> Response:
        """Debug an error with context and solutions."""
        error_message = kwargs.get("error_message", "")
        stack_trace = kwargs.get("stack_trace", "")

        if not error_message:
            return Response(
                message="Error message is required",
                break_loop=False
            )

        from python.helpers.unity_context_engine import ContextAwarePromptBuilder

        context_engine = self.agent.context.unity_context
        prompt_builder = ContextAwarePromptBuilder(context_engine)

        debug_context = await prompt_builder.build_debug_prompt(
            error_message, stack_trace
        )

        return Response(message=debug_context, break_loop=False)

    async def _manage_task(self, **kwargs) -> Response:
        """Create or update a task."""
        action = kwargs.get("action", "create")
        title = kwargs.get("title", "")
        description = kwargs.get("description", "")
        status = kwargs.get("status", "pending")
        priority = kwargs.get("priority", 3)
        task_id = kwargs.get("task_id", "")

        project_id = self.agent.context.config.memory_subdir or "default"
        qdrant = self.agent.context.unity_qdrant

        if action == "create":
            if not title:
                return Response(message="Title required for task", break_loop=False)

            doc_id = await qdrant.store_task(
                task_id=title.replace(" ", "_").lower(),
                title=title,
                description=description,
                status=status,
                priority=priority,
                project_id=project_id,
            )

            return Response(
                message=f"Task created: {title}\nID: {doc_id}",
                break_loop=False
            )

        elif action == "update":
            if not task_id:
                return Response(
                    message="Task ID required for update",
                    break_loop=False
                )

            # Search and update
            results = await qdrant.search_unity(
                query=task_id,
                collection_types=[UnityCollectionType.TASKS],
                project_id=project_id,
                limit=1,
            )

            if results:
                # Re-store with updated status
                task = results[0].document.metadata
                await qdrant.store_task(
                    task_id=task_id,
                    title=task.get("title", ""),
                    description=task.get("description", ""),
                    status=status,
                    priority=task.get("priority", 3),
                    project_id=project_id,
                )
                return Response(
                    message=f"Task updated: {task_id} -> {status}",
                    break_loop=False
                )
            else:
                return Response(message=f"Task not found: {task_id}", break_loop=False)

        elif action == "list":
            results = await qdrant.search_unity(
                query="all tasks",
                collection_types=[UnityCollectionType.TASKS],
                project_id=project_id,
                limit=20,
            )

            output = "# Tasks\n\n"
            for result in results:
                meta = result.document.metadata
                status_icon = {
                    "pending": "⏳",
                    "in_progress": "🔄",
                    "completed": "✅",
                    "blocked": "🚫",
                }.get(meta.get("status", ""), "❓")

                output += f"{status_icon} [{meta.get('priority', '?')}] {meta.get('title', 'Unknown')}\n"

            return Response(message=output, break_loop=False)

        return Response(message=f"Unknown task action: {action}", break_loop=False)
