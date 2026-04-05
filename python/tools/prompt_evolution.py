"""
Prompt Evolution Tool

Meta-analysis engine that analyzes Agent Zero's performance and suggests
prompt improvements, new tools, and refinements based on conversation patterns.

This is the core of Agent Zero's self-evolving capability.

Author: Agent Zero Meta-Learning System
Created: January 5, 2026
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional
from python.helpers.tool import Tool, Response
from python.helpers.dirty_json import DirtyJson
from python.helpers.memory import Memory
from python.helpers.prompt_versioning import PromptVersionManager
from agent import Agent


class PromptEvolution(Tool):
    """
    Meta-learning tool that analyzes agent performance and evolves prompts

    This tool:
    1. Analyzes recent conversation history for patterns
    2. Detects failures, successes, and gaps
    3. Generates specific prompt refinement suggestions
    4. Suggests new tools to build
    5. Stores analysis results in memory for review
    6. Optionally applies high-confidence suggestions
    """

    async def execute(self, **kwargs):
        """
        Execute meta-analysis on recent agent interactions

        Returns:
            Response with analysis summary and suggestions
        """

        # Check if meta-learning is enabled
        if not self._is_enabled():
            return Response(
                message="Meta-learning is disabled. Enable with ENABLE_PROMPT_EVOLUTION=true",
                break_loop=False
            )

        # Get configuration
        min_interactions = int(os.getenv("PROMPT_EVOLUTION_MIN_INTERACTIONS", "20"))
        max_history = int(os.getenv("PROMPT_EVOLUTION_MAX_HISTORY", "100"))
        confidence_threshold = float(os.getenv("PROMPT_EVOLUTION_CONFIDENCE_THRESHOLD", "0.7"))
        auto_apply = os.getenv("AUTO_APPLY_PROMPT_EVOLUTION", "false").lower() == "true"

        # Check if we have enough history
        history_size = len(self.agent.history)
        if history_size < min_interactions:
            return Response(
                message=f"Not enough interaction history ({history_size}/{min_interactions}). Skipping meta-analysis.",
                break_loop=False
            )

        # Analyze recent history
        self.agent.context.log.log(
            type="util",
            heading=f"Meta-Learning: Analyzing last {min(history_size, max_history)} interactions...",
        )

        analysis_result = await self._analyze_history(
            history_limit=max_history,
            confidence_threshold=confidence_threshold
        )

        if not analysis_result:
            return Response(
                message="Meta-analysis completed but found no significant patterns.",
                break_loop=False
            )

        # Store analysis in memory
        await self._store_analysis(analysis_result)

        # Apply suggestions if auto-apply is enabled
        applied_count = 0
        if auto_apply:
            applied_count = await self._apply_suggestions(
                analysis_result,
                confidence_threshold
            )

        # Generate response summary
        summary = self._generate_summary(analysis_result, applied_count, auto_apply)

        return Response(
            message=summary,
            break_loop=False
        )

    async def _analyze_history(self, history_limit: int, confidence_threshold: float) -> Optional[Dict]:
        """
        Analyze conversation history for patterns and generate suggestions

        Args:
            history_limit: Maximum number of messages to analyze
            confidence_threshold: Minimum confidence for suggestions

        Returns:
            Analysis result dictionary or None if analysis failed
        """

        # Get recent history
        recent_history = self.agent.history[-history_limit:]

        # Format history for analysis
        history_text = self._format_history_for_analysis(recent_history)

        # Load meta-analysis system prompt
        system_prompt = self.agent.read_prompt("meta_learning.analyze.sys.md", "")

        # If prompt doesn't exist, use built-in default
        if not system_prompt or system_prompt == "":
            system_prompt = self._get_default_analysis_prompt()

        # Call utility LLM for meta-analysis
        try:
            analysis_json = await self.agent.call_utility_model(
                system=system_prompt,
                message=f"Analyze this conversation history:\n\n{history_text}\n\nProvide detailed meta-analysis in JSON format.",
            )

            # Parse JSON response
            analysis = DirtyJson.parse_string(analysis_json)

            if not analysis:
                return None

            # Add metadata
            analysis["meta"] = {
                "timestamp": datetime.now().isoformat(),
                "monologue_count": getattr(self.agent, 'mono_count', 0),
                "history_size": len(recent_history),
                "confidence_threshold": confidence_threshold
            }

            # Filter by confidence
            if "prompt_refinements" in analysis:
                analysis["prompt_refinements"] = [
                    r for r in analysis["prompt_refinements"]
                    if r.get("confidence", 0) >= confidence_threshold
                ]

            return analysis

        except Exception as e:
            self.agent.context.log.log(
                type="error",
                heading="Meta-analysis failed",
                content=str(e)
            )
            return None

    def _format_history_for_analysis(self, history: List[Dict]) -> str:
        """
        Format conversation history for LLM analysis

        Args:
            history: List of message dictionaries

        Returns:
            Formatted history string
        """
        formatted = []

        for idx, msg in enumerate(history):
            role = msg.get("role", "unknown")
            content = str(msg.get("content", ""))

            # Truncate very long messages
            if len(content) > 1000:
                content = content[:1000] + "... [truncated]"

            # Format with role and index
            formatted.append(f"[{idx}] {role.upper()}: {content}")

        return "\n\n".join(formatted)

    async def _store_analysis(self, analysis: Dict) -> None:
        """
        Store meta-analysis results in memory for future reference

        Args:
            analysis: Analysis result dictionary
        """
        # Get memory database
        db = await Memory.get(self.agent)

        # Format analysis as text
        analysis_text = self._format_analysis_for_storage(analysis)

        # Store in SOLUTIONS memory area with meta_learning tag
        await db.insert_text(
            text=analysis_text,
            metadata={
                "area": Memory.Area.SOLUTIONS.value,
                "type": "meta_learning",
                "timestamp": analysis["meta"]["timestamp"],
                "monologue_count": analysis["meta"]["monologue_count"]
            }
        )

        self.agent.context.log.log(
            type="info",
            heading="Meta-Learning",
            content="Analysis results stored in memory (SOLUTIONS area)"
        )

    def _format_analysis_for_storage(self, analysis: Dict) -> str:
        """
        Format analysis results for memory storage

        Args:
            analysis: Analysis dictionary

        Returns:
            Formatted text string
        """
        lines = []
        lines.append(f"# Meta-Learning Analysis")
        lines.append(f"**Date:** {analysis['meta']['timestamp']}")
        lines.append(f"**Monologue:** #{analysis['meta']['monologue_count']}")
        lines.append(f"**History Analyzed:** {analysis['meta']['history_size']} messages")
        lines.append("")

        # Failure patterns
        if analysis.get("failure_patterns"):
            lines.append("## Failure Patterns Detected")
            for pattern in analysis["failure_patterns"]:
                lines.append(f"- **{pattern.get('pattern', 'Unknown')}**")
                lines.append(f"  - Frequency: {pattern.get('frequency', 0)}")
                lines.append(f"  - Severity: {pattern.get('severity', 'unknown')}")
                lines.append(f"  - Affected: {', '.join(pattern.get('affected_prompts', []))}")
            lines.append("")

        # Success patterns
        if analysis.get("success_patterns"):
            lines.append("## Success Patterns Identified")
            for pattern in analysis["success_patterns"]:
                lines.append(f"- **{pattern.get('pattern', 'Unknown')}**")
                lines.append(f"  - Frequency: {pattern.get('frequency', 0)}")
                lines.append(f"  - Confidence: {pattern.get('confidence', 0)}")
            lines.append("")

        # Missing instructions
        if analysis.get("missing_instructions"):
            lines.append("## Missing Instructions")
            for gap in analysis["missing_instructions"]:
                lines.append(f"- **{gap.get('gap', 'Unknown')}**")
                lines.append(f"  - Impact: {gap.get('impact', 'unknown')}")
                lines.append(f"  - Location: {gap.get('suggested_location', 'N/A')}")
            lines.append("")

        # Tool suggestions
        if analysis.get("tool_suggestions"):
            lines.append("## Tool Suggestions")
            for tool in analysis["tool_suggestions"]:
                lines.append(f"- **{tool.get('tool_name', 'unknown')}**")
                lines.append(f"  - Purpose: {tool.get('purpose', 'N/A')}")
                lines.append(f"  - Priority: {tool.get('priority', 'unknown')}")
            lines.append("")

        # Prompt refinements
        if analysis.get("prompt_refinements"):
            lines.append("## Prompt Refinement Suggestions")
            for ref in analysis["prompt_refinements"]:
                lines.append(f"- **{ref.get('file', 'unknown')}**")
                lines.append(f"  - Section: {ref.get('section', 'N/A')}")
                lines.append(f"  - Reason: {ref.get('reason', 'N/A')}")
                lines.append(f"  - Confidence: {ref.get('confidence', 0):.2f}")
            lines.append("")

        return "\n".join(lines)

    async def _apply_suggestions(self, analysis: Dict, confidence_threshold: float) -> int:
        """
        Apply high-confidence prompt refinements automatically

        Args:
            analysis: Analysis result dictionary
            confidence_threshold: Minimum confidence for auto-apply

        Returns:
            Number of suggestions applied
        """
        if not analysis.get("prompt_refinements"):
            return 0

        version_manager = PromptVersionManager()
        applied_count = 0

        for refinement in analysis["prompt_refinements"]:
            confidence = refinement.get("confidence", 0)

            # Only apply high-confidence suggestions
            if confidence < confidence_threshold:
                continue

            try:
                file_name = refinement.get("file", "")
                proposed_content = refinement.get("proposed", "")
                reason = refinement.get("reason", "Meta-learning suggestion")

                if not file_name or not proposed_content:
                    continue

                # Apply change with automatic versioning
                version_manager.apply_change(
                    file_name=file_name,
                    content=proposed_content,
                    change_description=reason
                )

                applied_count += 1

                self.agent.context.log.log(
                    type="info",
                    heading="Meta-Learning",
                    content=f"Applied refinement to {file_name} (confidence: {confidence:.2f})"
                )

            except Exception as e:
                self.agent.context.log.log(
                    type="warning",
                    heading="Meta-Learning",
                    content=f"Failed to apply refinement to {refinement.get('file', 'unknown')}: {str(e)}"
                )

        return applied_count

    def _generate_summary(self, analysis: Dict, applied_count: int, auto_apply: bool) -> str:
        """
        Generate human-readable summary of meta-analysis results

        Args:
            analysis: Analysis dictionary
            applied_count: Number of suggestions applied
            auto_apply: Whether auto-apply is enabled

        Returns:
            Formatted summary string
        """
        lines = []
        lines.append("📊 **Meta-Learning Analysis Complete**")
        lines.append("")
        lines.append(f"**Analyzed:** {analysis['meta']['history_size']} messages")
        lines.append(f"**Monologue:** #{analysis['meta']['monologue_count']}")
        lines.append("")

        # Patterns detected
        failure_count = len(analysis.get("failure_patterns", []))
        success_count = len(analysis.get("success_patterns", []))
        gap_count = len(analysis.get("missing_instructions", []))
        tool_count = len(analysis.get("tool_suggestions", []))
        refinement_count = len(analysis.get("prompt_refinements", []))

        lines.append("**Findings:**")
        lines.append(f"- {failure_count} failure patterns identified")
        lines.append(f"- {success_count} success patterns recognized")
        lines.append(f"- {gap_count} missing instructions detected")
        lines.append(f"- {tool_count} new tools suggested")
        lines.append(f"- {refinement_count} prompt refinements proposed")
        lines.append("")

        # Application status
        if auto_apply:
            lines.append(f"**Auto-Applied:** {applied_count} high-confidence refinements")
        else:
            lines.append(f"**Action Required:** Review {refinement_count} suggestions in memory")
            lines.append("_(Auto-apply disabled, suggestions saved for manual review)_")

        lines.append("")
        lines.append("💾 Full analysis stored in memory (SOLUTIONS area)")
        lines.append("🔍 Use memory_query to retrieve detailed suggestions")

        return "\n".join(lines)

    def _is_enabled(self) -> bool:
        """Check if meta-learning is enabled in settings"""
        return os.getenv("ENABLE_PROMPT_EVOLUTION", "false").lower() == "true"

    def _get_default_analysis_prompt(self) -> str:
        """
        Get default meta-analysis system prompt (fallback if file doesn't exist)

        Returns:
            Default system prompt for meta-analysis
        """
        return """# Assistant's Role
You are a meta-learning AI that analyzes conversation histories to improve Agent Zero's performance.

# Your Job
1. Receive conversation HISTORY between USER and AGENT
2. Analyze patterns of success and failure
3. Identify gaps in current prompts/instructions
4. Suggest specific prompt improvements
5. Recommend new tools to build

# Output Format

Return JSON with this structure:

{
  "failure_patterns": [
    {
      "pattern": "Description of what went wrong",
      "frequency": 3,
      "severity": "high|medium|low",
      "affected_prompts": ["file1.md", "file2.md"],
      "example_messages": [42, 58]
    }
  ],
  "success_patterns": [
    {
      "pattern": "Description of what worked well",
      "frequency": 8,
      "confidence": 0.9,
      "related_prompts": ["file1.md"]
    }
  ],
  "missing_instructions": [
    {
      "gap": "Description of missing guidance",
      "impact": "high|medium|low",
      "suggested_location": "file.md",
      "proposed_addition": "Specific text to add"
    }
  ],
  "tool_suggestions": [
    {
      "tool_name": "snake_case_name",
      "purpose": "One sentence description",
      "use_case": "When to use this tool",
      "priority": "high|medium|low",
      "required_integrations": ["library1"]
    }
  ],
  "prompt_refinements": [
    {
      "file": "agent.system.tool.code_exe.md",
      "section": "Section to modify",
      "current": "Current text (if modifying)",
      "proposed": "Proposed new text",
      "reason": "Why this change will help",
      "confidence": 0.85
    }
  ]
}

# Rules
- Only suggest changes based on observed patterns (minimum 2 occurrences)
- Be specific - vague suggestions are not useful
- Include concrete examples from the history
- Prioritize high-impact, high-confidence suggestions
- Never suggest changes based on speculation
- Focus on systemic improvements, not one-off issues
- If no patterns found, return empty arrays"""
