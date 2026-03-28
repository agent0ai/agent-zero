"""
Meta-Learning Dashboard API

Provides endpoints for monitoring and managing Agent Zero's meta-learning system,
including meta-analyses, prompt suggestions, and version control.

Author: Agent Zero Meta-Learning System
Created: January 5, 2026
"""

from python.helpers.api import ApiHandler, Request, Response
from python.helpers.memory import Memory
from python.helpers.prompt_versioning import PromptVersionManager
from python.helpers.dirty_json import DirtyJson
from agent import AgentContext
from datetime import datetime
from typing import Dict, List, Optional, Any
import os
import json


class MetaLearning(ApiHandler):
    """
    Handler for meta-learning dashboard operations

    Supports multiple actions:
    - list_analyses: Get recent meta-analyses from SOLUTIONS memory
    - get_analysis: Get specific analysis details by ID
    - list_suggestions: Get pending prompt refinement suggestions
    - apply_suggestion: Apply a specific suggestion with approval
    - trigger_analysis: Manually trigger meta-analysis
    - list_versions: List prompt versions
    - rollback_version: Rollback to previous prompt version
    """

    async def process(self, input: dict, request: Request) -> dict | Response:
        """
        Route request to appropriate handler based on action

        Args:
            input: Request data with 'action' field
            request: Flask request object

        Returns:
            Response dictionary or Response object
        """
        try:
            action = input.get("action", "list_analyses")

            if action == "list_analyses":
                return await self._list_analyses(input)
            elif action == "get_analysis":
                return await self._get_analysis(input)
            elif action == "list_suggestions":
                return await self._list_suggestions(input)
            elif action == "apply_suggestion":
                return await self._apply_suggestion(input)
            elif action == "trigger_analysis":
                return await self._trigger_analysis(input)
            elif action == "list_versions":
                return await self._list_versions(input)
            elif action == "rollback_version":
                return await self._rollback_version(input)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    async def _list_analyses(self, input: dict) -> dict:
        """
        List recent meta-analyses from SOLUTIONS memory

        Args:
            input: Request data containing:
                - memory_subdir: Memory subdirectory (default: "default")
                - limit: Maximum number of analyses to return (default: 20)
                - search: Optional search query

        Returns:
            Dictionary with analyses list and metadata
        """
        try:
            memory_subdir = input.get("memory_subdir", "default")
            limit = input.get("limit", 20)
            search_query = input.get("search", "")

            # Get memory instance
            memory = await Memory.get_by_subdir(memory_subdir, preload_knowledge=False)

            # Search for meta-analysis entries in SOLUTIONS area
            # Meta-analyses are stored with special tags/metadata
            analyses = []

            if search_query:
                # Semantic search for analyses
                docs = await memory.search_similarity_threshold(
                    query=search_query,
                    limit=limit * 2,  # Get more to filter
                    threshold=0.5,
                    filter=f"area == '{Memory.Area.SOLUTIONS.value}'",
                )
            else:
                # Get all from SOLUTIONS area
                all_docs = memory.db.get_all_docs()
                docs = [
                    doc for doc_id, doc in all_docs.items()
                    if doc.metadata.get("area", "") == Memory.Area.SOLUTIONS.value
                ]

            # Filter for meta-analysis documents (those with meta-learning metadata)
            for doc in docs:
                metadata = doc.metadata

                # Check if this is a meta-analysis result
                # Meta-analyses contain specific structure from prompt_evolution.py
                if self._is_meta_analysis(doc):
                    analysis = {
                        "id": metadata.get("id", "unknown"),
                        "timestamp": metadata.get("timestamp", "unknown"),
                        "content": doc.page_content,
                        "metadata": metadata,
                        "preview": doc.page_content[:200] + ("..." if len(doc.page_content) > 200 else ""),
                    }

                    # Try to parse structured data from content
                    try:
                        parsed = self._parse_analysis_content(doc.page_content)
                        if parsed:
                            analysis["structured"] = parsed
                    except Exception:
                        pass

                    analyses.append(analysis)

            # Sort by timestamp (newest first)
            analyses.sort(key=lambda a: a.get("timestamp", ""), reverse=True)

            # Apply limit
            if limit and len(analyses) > limit:
                analyses = analyses[:limit]

            return {
                "success": True,
                "analyses": analyses,
                "total_count": len(analyses),
                "memory_subdir": memory_subdir,
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to list analyses: {str(e)}",
                "analyses": [],
                "total_count": 0,
            }

    async def _get_analysis(self, input: dict) -> dict:
        """
        Get specific analysis details by ID

        Args:
            input: Request data containing:
                - analysis_id: ID of the analysis
                - memory_subdir: Memory subdirectory (default: "default")

        Returns:
            Dictionary with analysis details
        """
        try:
            analysis_id = input.get("analysis_id")
            memory_subdir = input.get("memory_subdir", "default")

            if not analysis_id:
                return {
                    "success": False,
                    "error": "Analysis ID is required",
                }

            # Get memory instance
            memory = await Memory.get_by_subdir(memory_subdir, preload_knowledge=False)

            # Get document by ID
            doc = memory.get_document_by_id(analysis_id)

            if not doc:
                return {
                    "success": False,
                    "error": f"Analysis with ID '{analysis_id}' not found",
                }

            # Format analysis
            analysis = {
                "id": doc.metadata.get("id", analysis_id),
                "timestamp": doc.metadata.get("timestamp", "unknown"),
                "content": doc.page_content,
                "metadata": doc.metadata,
            }

            # Parse structured data
            try:
                parsed = self._parse_analysis_content(doc.page_content)
                if parsed:
                    analysis["structured"] = parsed
            except Exception as e:
                analysis["parse_error"] = str(e)

            return {
                "success": True,
                "analysis": analysis,
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get analysis: {str(e)}",
            }

    async def _list_suggestions(self, input: dict) -> dict:
        """
        List pending prompt refinement suggestions

        Extracts suggestions from recent meta-analyses that haven't been applied yet.

        Args:
            input: Request data containing:
                - memory_subdir: Memory subdirectory (default: "default")
                - status: Filter by status (pending/applied/rejected, default: all)
                - limit: Maximum number to return (default: 50)

        Returns:
            Dictionary with suggestions list
        """
        try:
            memory_subdir = input.get("memory_subdir", "default")
            status_filter = input.get("status", "")  # "", "pending", "applied", "rejected"
            limit = input.get("limit", 50)

            # Get recent analyses
            analyses_result = await self._list_analyses({
                "memory_subdir": memory_subdir,
                "limit": 20,  # Check last 20 analyses
            })

            if not analyses_result.get("success"):
                return analyses_result

            # Extract suggestions from analyses
            suggestions = []

            for analysis in analyses_result.get("analyses", []):
                structured = analysis.get("structured", {})

                # Extract prompt refinements
                refinements = structured.get("prompt_refinements", [])
                for ref in refinements:
                    suggestion = {
                        "id": f"{analysis['id']}_ref_{len(suggestions)}",
                        "analysis_id": analysis["id"],
                        "timestamp": analysis.get("timestamp", ""),
                        "type": "prompt_refinement",
                        "target_file": ref.get("target_file", ""),
                        "description": ref.get("description", ""),
                        "rationale": ref.get("rationale", ""),
                        "suggested_change": ref.get("suggested_change", ""),
                        "confidence": ref.get("confidence", 0.5),
                        "status": ref.get("status", "pending"),
                        "priority": ref.get("priority", "medium"),
                    }
                    suggestions.append(suggestion)

                # Extract tool suggestions
                tool_suggestions = structured.get("tool_suggestions", [])
                for tool_sug in tool_suggestions:
                    suggestion = {
                        "id": f"{analysis['id']}_tool_{len(suggestions)}",
                        "analysis_id": analysis["id"],
                        "timestamp": analysis.get("timestamp", ""),
                        "type": "new_tool",
                        "tool_name": tool_sug.get("tool_name", ""),
                        "description": tool_sug.get("description", ""),
                        "rationale": tool_sug.get("rationale", ""),
                        "confidence": tool_sug.get("confidence", 0.5),
                        "status": tool_sug.get("status", "pending"),
                        "priority": tool_sug.get("priority", "low"),
                    }
                    suggestions.append(suggestion)

            # Filter by status if specified
            if status_filter:
                suggestions = [s for s in suggestions if s.get("status") == status_filter]

            # Sort by confidence (high to low) then timestamp (newest first)
            suggestions.sort(
                key=lambda s: (s.get("confidence", 0), s.get("timestamp", "")),
                reverse=True
            )

            # Apply limit
            if limit and len(suggestions) > limit:
                suggestions = suggestions[:limit]

            return {
                "success": True,
                "suggestions": suggestions,
                "total_count": len(suggestions),
                "memory_subdir": memory_subdir,
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to list suggestions: {str(e)}",
                "suggestions": [],
                "total_count": 0,
            }

    async def _apply_suggestion(self, input: dict) -> dict:
        """
        Apply a specific prompt refinement suggestion with approval

        Args:
            input: Request data containing:
                - suggestion_id: ID of the suggestion to apply
                - analysis_id: ID of the analysis containing the suggestion
                - memory_subdir: Memory subdirectory (default: "default")
                - approved: Explicit approval flag (must be True)

        Returns:
            Dictionary with application result
        """
        try:
            suggestion_id = input.get("suggestion_id")
            analysis_id = input.get("analysis_id")
            memory_subdir = input.get("memory_subdir", "default")
            approved = input.get("approved", False)

            if not suggestion_id or not analysis_id:
                return {
                    "success": False,
                    "error": "suggestion_id and analysis_id are required",
                }

            if not approved:
                return {
                    "success": False,
                    "error": "Explicit approval required to apply suggestion (approved=True)",
                }

            # Get the analysis
            analysis_result = await self._get_analysis({
                "analysis_id": analysis_id,
                "memory_subdir": memory_subdir,
            })

            if not analysis_result.get("success"):
                return analysis_result

            analysis = analysis_result.get("analysis", {})
            structured = analysis.get("structured", {})

            # Find the specific suggestion
            suggestion = None
            suggestion_type = None

            # Check prompt refinements
            for ref in structured.get("prompt_refinements", []):
                if suggestion_id == f"{analysis_id}_ref_{structured.get('prompt_refinements', []).index(ref)}":
                    suggestion = ref
                    suggestion_type = "prompt_refinement"
                    break

            if not suggestion:
                return {
                    "success": False,
                    "error": f"Suggestion with ID '{suggestion_id}' not found in analysis",
                }

            # Apply the suggestion based on type
            if suggestion_type == "prompt_refinement":
                result = await self._apply_prompt_refinement(suggestion, memory_subdir)
                return result
            else:
                return {
                    "success": False,
                    "error": f"Unsupported suggestion type: {suggestion_type}",
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to apply suggestion: {str(e)}",
            }

    async def _apply_prompt_refinement(self, suggestion: dict, memory_subdir: str) -> dict:
        """
        Apply a prompt refinement suggestion

        Args:
            suggestion: Suggestion dictionary with refinement details
            memory_subdir: Memory subdirectory

        Returns:
            Dictionary with application result
        """
        try:
            target_file = suggestion.get("target_file", "")
            suggested_change = suggestion.get("suggested_change", "")
            description = suggestion.get("description", "")

            if not target_file or not suggested_change:
                return {
                    "success": False,
                    "error": "target_file and suggested_change are required",
                }

            # Initialize version manager
            version_manager = PromptVersionManager()

            # Apply the change (this creates a backup automatically)
            version_id = version_manager.apply_change(
                file_name=target_file,
                content=suggested_change,
                change_description=description
            )

            # Update the suggestion status in memory
            # (In a full implementation, we'd update the original document)
            # For now, just return success with version info

            return {
                "success": True,
                "message": f"Applied refinement to {target_file}",
                "version_id": version_id,
                "target_file": target_file,
                "description": description,
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to apply prompt refinement: {str(e)}",
            }

    async def _trigger_analysis(self, input: dict) -> dict:
        """
        Manually trigger meta-analysis

        Creates a context and calls the prompt_evolution tool to analyze recent history.

        Args:
            input: Request data containing:
                - context_id: Optional context ID (creates new if not provided)
                - background: Run in background (default: False)

        Returns:
            Dictionary with trigger result
        """
        try:
            context_id = input.get("context_id", "")
            background = input.get("background", False)

            # Get or create context
            context = self.use_context(context_id, create_if_not_exists=True)

            # Import the prompt evolution tool
            from python.tools.prompt_evolution import PromptEvolution

            # Create tool instance
            tool = PromptEvolution(agent=context.agent0, args={}, message="")

            # Execute meta-analysis
            if background:
                # Run in background (return immediately)
                import asyncio
                asyncio.create_task(tool.execute())

                return {
                    "success": True,
                    "message": "Meta-analysis started in background",
                    "context_id": context.id,
                }
            else:
                # Run synchronously
                response = await tool.execute()

                return {
                    "success": True,
                    "message": response.message if response else "Meta-analysis completed",
                    "context_id": context.id,
                    "analysis_complete": True,
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to trigger analysis: {str(e)}",
            }

    async def _list_versions(self, input: dict) -> dict:
        """
        List prompt versions

        Proxy to the versioning system to get version history.

        Args:
            input: Request data containing:
                - limit: Maximum versions to return (default: 20)

        Returns:
            Dictionary with versions list
        """
        try:
            limit = input.get("limit", 20)

            # Initialize version manager
            version_manager = PromptVersionManager()

            # Get versions
            versions = version_manager.list_versions(limit=limit)

            return {
                "success": True,
                "versions": versions,
                "total_count": len(versions),
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to list versions: {str(e)}",
                "versions": [],
                "total_count": 0,
            }

    async def _rollback_version(self, input: dict) -> dict:
        """
        Rollback to a previous prompt version

        Args:
            input: Request data containing:
                - version_id: Version to rollback to (required)
                - create_backup: Create backup before rollback (default: True)

        Returns:
            Dictionary with rollback result
        """
        try:
            version_id = input.get("version_id")
            create_backup = input.get("create_backup", True)

            if not version_id:
                return {
                    "success": False,
                    "error": "version_id is required",
                }

            # Initialize version manager
            version_manager = PromptVersionManager()

            # Perform rollback
            success = version_manager.rollback(
                version_id=version_id,
                create_backup=create_backup
            )

            if success:
                return {
                    "success": True,
                    "message": f"Successfully rolled back to version {version_id}",
                    "version_id": version_id,
                    "backup_created": create_backup,
                }
            else:
                return {
                    "success": False,
                    "error": "Rollback failed",
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to rollback: {str(e)}",
            }

    # Helper methods

    def _is_meta_analysis(self, doc) -> bool:
        """
        Check if a document is a meta-analysis result

        Args:
            doc: Document to check

        Returns:
            True if document contains meta-analysis data
        """
        # Meta-analyses have specific markers
        content = doc.page_content.lower()
        metadata = doc.metadata

        # Check for meta-analysis keywords
        has_keywords = any(kw in content for kw in [
            "meta-analysis",
            "prompt refinement",
            "tool suggestion",
            "performance pattern",
            "failure analysis"
        ])

        # Check metadata tags
        has_meta_tags = metadata.get("meta_learning", False) or \
                       metadata.get("analysis_type") == "meta" or \
                       "meta" in str(metadata.get("tags", []))

        return has_keywords or has_meta_tags

    def _parse_analysis_content(self, content: str) -> Optional[Dict]:
        """
        Parse structured data from analysis content

        Args:
            content: Analysis content (may contain JSON)

        Returns:
            Parsed dictionary or None
        """
        try:
            # Try to parse as JSON directly
            if content.strip().startswith("{"):
                return DirtyJson.parse_string(content)

            # Try to extract JSON from markdown code blocks
            import re
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
            if json_match:
                return DirtyJson.parse_string(json_match.group(1))

            # Try to find JSON object in content
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
            if json_match:
                return DirtyJson.parse_string(json_match.group(0))

            return None

        except Exception:
            return None

    @classmethod
    def get_methods(cls) -> list[str]:
        """
        Supported HTTP methods

        Returns:
            List of method names
        """
        return ["GET", "POST"]
