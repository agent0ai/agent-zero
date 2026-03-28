"""
Tool Suggestions Module

Analyzes conversation patterns to identify tool gaps and generate structured suggestions
for new tools that would improve agent capabilities.

This module integrates with the meta-analysis system to detect:
- Repeated manual operations that could be automated
- Failed tool attempts or missing capabilities
- User requests that couldn't be fulfilled
- Patterns indicating need for new integrations
"""

from dataclasses import dataclass, field
from typing import Literal, Optional
from datetime import datetime
import json
import re
from agent import Agent
from python.helpers import call_llm, history
from python.helpers.log import LogItem
from python.helpers.print_style import PrintStyle


Priority = Literal["high", "medium", "low"]


@dataclass
class ToolSuggestion:
    """Structured suggestion for a new tool."""

    name: str  # Tool name in snake_case (e.g., "pdf_generator_tool")
    purpose: str  # Clear description of what the tool does
    use_cases: list[str]  # List of specific use cases
    priority: Priority  # Urgency/importance of this tool
    required_integrations: list[str] = field(default_factory=list)  # External dependencies needed
    evidence: list[str] = field(default_factory=list)  # Conversation excerpts showing need
    estimated_complexity: Literal["simple", "moderate", "complex"] = "moderate"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "purpose": self.purpose,
            "use_cases": self.use_cases,
            "priority": self.priority,
            "required_integrations": self.required_integrations,
            "evidence": self.evidence,
            "estimated_complexity": self.estimated_complexity,
            "timestamp": self.timestamp,
        }

    @staticmethod
    def from_dict(data: dict) -> "ToolSuggestion":
        """Create from dictionary."""
        return ToolSuggestion(
            name=data["name"],
            purpose=data["purpose"],
            use_cases=data["use_cases"],
            priority=data["priority"],
            required_integrations=data.get("required_integrations", []),
            evidence=data.get("evidence", []),
            estimated_complexity=data.get("estimated_complexity", "moderate"),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
        )


@dataclass
class ConversationPattern:
    """Detected pattern indicating a potential tool need."""

    pattern_type: Literal[
        "repeated_manual_operation",
        "failed_tool_attempt",
        "missing_capability",
        "user_request_unfulfilled",
        "workaround_detected",
        "integration_gap",
    ]
    description: str
    frequency: int  # How many times detected
    examples: list[str]  # Specific conversation excerpts
    severity: Literal["critical", "important", "nice_to_have"]


class ToolSuggestionAnalyzer:
    """
    Analyzes conversation history to identify tool gaps and generate suggestions.

    Uses the utility LLM to:
    1. Detect patterns in conversation that indicate missing tools
    2. Analyze tool usage failures and workarounds
    3. Generate structured suggestions for new tools
    """

    def __init__(self, agent: Agent):
        self.agent = agent

    async def analyze_conversation_for_gaps(
        self,
        log_item: Optional[LogItem] = None,
        min_messages: int = 10,
    ) -> list[ConversationPattern]:
        """
        Analyze recent conversation history to detect patterns indicating tool gaps.

        Args:
            log_item: Optional log item for progress updates
            min_messages: Minimum number of messages to analyze

        Returns:
            List of detected conversation patterns
        """
        try:
            # Get conversation history
            conversation_text = self._extract_conversation_history(min_messages)

            if not conversation_text:
                PrintStyle.standard("Not enough conversation history to analyze")
                return []

            if log_item:
                log_item.stream(progress="\nAnalyzing conversation patterns...")

            # Use utility LLM to detect patterns
            analysis_prompt = self.agent.read_prompt(
                "fw.tool_gap_analysis.sys.md",
                fallback=self._get_default_analysis_system_prompt()
            )

            message_prompt = self.agent.read_prompt(
                "fw.tool_gap_analysis.msg.md",
                fallback=self._get_default_analysis_message_prompt(conversation_text)
            )

            response = await self.agent.call_utility_model(
                system=analysis_prompt,
                message=message_prompt,
            )

            # Parse response into structured patterns
            patterns = self._parse_pattern_analysis(response)

            if log_item:
                log_item.stream(progress=f"\nFound {len(patterns)} potential gaps")

            return patterns

        except Exception as e:
            PrintStyle.error(f"Error analyzing conversation for gaps: {str(e)}")
            return []

    async def generate_tool_suggestions(
        self,
        patterns: list[ConversationPattern],
        log_item: Optional[LogItem] = None,
    ) -> list[ToolSuggestion]:
        """
        Generate structured tool suggestions based on detected patterns.

        Args:
            patterns: List of conversation patterns detected
            log_item: Optional log item for progress updates

        Returns:
            List of tool suggestions
        """
        if not patterns:
            return []

        try:
            if log_item:
                log_item.stream(progress="\nGenerating tool suggestions...")

            # Convert patterns to text for analysis
            patterns_text = self._patterns_to_text(patterns)

            # Use utility LLM to generate suggestions
            system_prompt = self.agent.read_prompt(
                "fw.tool_suggestion_generation.sys.md",
                fallback=self._get_default_suggestion_system_prompt()
            )

            message_prompt = self.agent.read_prompt(
                "fw.tool_suggestion_generation.msg.md",
                fallback=self._get_default_suggestion_message_prompt(patterns_text)
            )

            response = await self.agent.call_utility_model(
                system=system_prompt,
                message=message_prompt,
            )

            # Parse response into structured suggestions
            suggestions = self._parse_suggestions(response, patterns)

            if log_item:
                log_item.stream(progress=f"\nGenerated {len(suggestions)} suggestions")

            return suggestions

        except Exception as e:
            PrintStyle.error(f"Error generating tool suggestions: {str(e)}")
            return []

    async def analyze_and_suggest(
        self,
        log_item: Optional[LogItem] = None,
        min_messages: int = 10,
    ) -> list[ToolSuggestion]:
        """
        Complete workflow: analyze conversation and generate suggestions.

        Args:
            log_item: Optional log item for progress updates
            min_messages: Minimum number of messages to analyze

        Returns:
            List of tool suggestions
        """
        patterns = await self.analyze_conversation_for_gaps(log_item, min_messages)

        if not patterns:
            return []

        suggestions = await self.generate_tool_suggestions(patterns, log_item)
        return suggestions

    def _extract_conversation_history(self, min_messages: int = 10) -> str:
        """
        Extract recent conversation history as text.

        Args:
            min_messages: Minimum number of messages to extract

        Returns:
            Formatted conversation text
        """
        try:
            # Get history from agent
            hist = self.agent.history

            if hist.counter < min_messages:
                return ""

            # Get recent messages (last 30 or min_messages, whichever is larger)
            output_messages = hist.output()

            # Take recent messages
            recent_count = max(min_messages, min(30, len(output_messages)))
            recent_messages = output_messages[-recent_count:] if recent_count > 0 else []

            # Format as text
            conversation_lines = []
            for msg in recent_messages:
                role = "AI" if msg["ai"] else "User"
                content = history._stringify_content(msg["content"])
                conversation_lines.append(f"{role}: {content}")

            return "\n\n".join(conversation_lines)

        except Exception as e:
            PrintStyle.error(f"Error extracting conversation history: {str(e)}")
            return ""

    def _parse_pattern_analysis(self, response: str) -> list[ConversationPattern]:
        """
        Parse LLM response into structured conversation patterns.

        Expected JSON format:
        {
            "patterns": [
                {
                    "pattern_type": "repeated_manual_operation",
                    "description": "...",
                    "frequency": 3,
                    "examples": ["...", "..."],
                    "severity": "important"
                },
                ...
            ]
        }
        """
        patterns = []

        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group(0))

                for pattern_data in data.get("patterns", []):
                    pattern = ConversationPattern(
                        pattern_type=pattern_data.get("pattern_type", "missing_capability"),
                        description=pattern_data.get("description", ""),
                        frequency=pattern_data.get("frequency", 1),
                        examples=pattern_data.get("examples", []),
                        severity=pattern_data.get("severity", "nice_to_have"),
                    )
                    patterns.append(pattern)

        except json.JSONDecodeError as e:
            PrintStyle.error(f"Failed to parse pattern analysis JSON: {str(e)}")
            # Fallback: try to extract patterns from text
            patterns = self._parse_patterns_from_text(response)

        return patterns

    def _parse_patterns_from_text(self, text: str) -> list[ConversationPattern]:
        """Fallback parser for non-JSON responses."""
        patterns = []

        # Simple pattern detection from text
        lines = text.strip().split('\n')
        current_pattern = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Look for pattern indicators
            if any(keyword in line.lower() for keyword in [
                "repeated", "manual operation", "workaround", "failed attempt",
                "missing capability", "unfulfilled request", "integration gap"
            ]):
                if current_pattern:
                    patterns.append(current_pattern)

                # Determine pattern type
                pattern_type = "missing_capability"
                if "repeated" in line.lower() or "manual" in line.lower():
                    pattern_type = "repeated_manual_operation"
                elif "failed" in line.lower():
                    pattern_type = "failed_tool_attempt"
                elif "workaround" in line.lower():
                    pattern_type = "workaround_detected"
                elif "unfulfilled" in line.lower():
                    pattern_type = "user_request_unfulfilled"
                elif "integration" in line.lower():
                    pattern_type = "integration_gap"

                current_pattern = ConversationPattern(
                    pattern_type=pattern_type,
                    description=line,
                    frequency=1,
                    examples=[],
                    severity="nice_to_have",
                )
            elif current_pattern and line.startswith("-"):
                current_pattern.examples.append(line[1:].strip())

        if current_pattern:
            patterns.append(current_pattern)

        return patterns

    def _parse_suggestions(
        self,
        response: str,
        patterns: list[ConversationPattern]
    ) -> list[ToolSuggestion]:
        """
        Parse LLM response into structured tool suggestions.

        Expected JSON format:
        {
            "suggestions": [
                {
                    "name": "pdf_generator_tool",
                    "purpose": "...",
                    "use_cases": ["...", "..."],
                    "priority": "high",
                    "required_integrations": ["pdfkit", "weasyprint"],
                    "estimated_complexity": "moderate"
                },
                ...
            ]
        }
        """
        suggestions = []

        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group(0))

                for sugg_data in data.get("suggestions", []):
                    # Extract evidence from patterns
                    evidence = []
                    for pattern in patterns[:3]:  # Limit to top 3 patterns
                        evidence.extend(pattern.examples[:2])  # 2 examples per pattern

                    suggestion = ToolSuggestion(
                        name=sugg_data.get("name", "unnamed_tool"),
                        purpose=sugg_data.get("purpose", ""),
                        use_cases=sugg_data.get("use_cases", []),
                        priority=sugg_data.get("priority", "medium"),
                        required_integrations=sugg_data.get("required_integrations", []),
                        evidence=evidence[:5],  # Max 5 evidence items
                        estimated_complexity=sugg_data.get("estimated_complexity", "moderate"),
                    )
                    suggestions.append(suggestion)

        except json.JSONDecodeError as e:
            PrintStyle.error(f"Failed to parse suggestions JSON: {str(e)}")
            # Fallback: try to extract from text
            suggestions = self._parse_suggestions_from_text(response, patterns)

        return suggestions

    def _parse_suggestions_from_text(
        self,
        text: str,
        patterns: list[ConversationPattern]
    ) -> list[ToolSuggestion]:
        """Fallback parser for non-JSON suggestion responses."""
        suggestions = []

        lines = text.strip().split('\n')
        current_suggestion = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Look for tool name indicators
            if "tool" in line.lower() and ("name:" in line.lower() or line.endswith("_tool")):
                if current_suggestion:
                    suggestions.append(current_suggestion)

                # Extract tool name
                name_match = re.search(r'(\w+_tool)', line)
                tool_name = name_match.group(1) if name_match else "unnamed_tool"

                current_suggestion = ToolSuggestion(
                    name=tool_name,
                    purpose="",
                    use_cases=[],
                    priority="medium",
                )
            elif current_suggestion:
                if "purpose:" in line.lower():
                    current_suggestion.purpose = line.split(":", 1)[1].strip()
                elif "use case" in line.lower() or line.startswith("-"):
                    use_case = line.lstrip("- ").strip()
                    if use_case:
                        current_suggestion.use_cases.append(use_case)
                elif "priority:" in line.lower():
                    priority_text = line.split(":", 1)[1].strip().lower()
                    if priority_text in ["high", "medium", "low"]:
                        current_suggestion.priority = priority_text

        if current_suggestion:
            suggestions.append(current_suggestion)

        return suggestions

    def _patterns_to_text(self, patterns: list[ConversationPattern]) -> str:
        """Convert patterns to formatted text for LLM analysis."""
        lines = ["# Detected Patterns\n"]

        for i, pattern in enumerate(patterns, 1):
            lines.append(f"\n## Pattern {i}: {pattern.pattern_type}")
            lines.append(f"**Severity:** {pattern.severity}")
            lines.append(f"**Frequency:** {pattern.frequency}")
            lines.append(f"**Description:** {pattern.description}")

            if pattern.examples:
                lines.append("\n**Examples:**")
                for example in pattern.examples[:3]:  # Limit to 3 examples
                    lines.append(f"- {example}")

        return "\n".join(lines)

    # Default prompts (fallbacks if prompt files don't exist)

    def _get_default_analysis_system_prompt(self) -> str:
        """Default system prompt for gap analysis."""
        return """You are an expert at analyzing conversation patterns to identify missing capabilities and tool gaps.

Your task is to analyze conversation history and detect patterns that indicate:
1. Repeated manual operations that could be automated
2. Failed tool attempts or errors
3. Missing capabilities the agent doesn't have
4. User requests that couldn't be fulfilled
5. Workarounds the agent had to use
6. Integration gaps with external services

For each pattern you detect, provide:
- Pattern type (one of: repeated_manual_operation, failed_tool_attempt, missing_capability, user_request_unfulfilled, workaround_detected, integration_gap)
- Clear description of what you observed
- How many times you saw this pattern (frequency)
- Specific examples from the conversation
- Severity (critical, important, nice_to_have)

Respond in JSON format with a "patterns" array."""

    def _get_default_analysis_message_prompt(self, conversation: str) -> str:
        """Default message prompt for gap analysis."""
        return f"""Analyze the following conversation history and identify patterns indicating tool gaps or missing capabilities:

{conversation}

Provide your analysis as a JSON object with this structure:
{{
    "patterns": [
        {{
            "pattern_type": "repeated_manual_operation",
            "description": "User repeatedly asks for X which requires manual steps",
            "frequency": 3,
            "examples": ["Example 1", "Example 2"],
            "severity": "important"
        }}
    ]
}}"""

    def _get_default_suggestion_system_prompt(self) -> str:
        """Default system prompt for suggestion generation."""
        return """You are an expert at designing tools and automation solutions for AI agents.

Based on detected patterns and gaps, your task is to suggest new tools that would:
1. Automate repeated manual operations
2. Fill missing capabilities
3. Improve success rates for failed operations
4. Better serve user needs

For each tool suggestion, provide:
- Tool name (in snake_case, ending with _tool)
- Clear purpose statement
- Specific use cases
- Priority (high, medium, low)
- Required integrations or dependencies
- Estimated complexity (simple, moderate, complex)

Respond in JSON format with a "suggestions" array."""

    def _get_default_suggestion_message_prompt(self, patterns: str) -> str:
        """Default message prompt for suggestion generation."""
        return f"""Based on the following detected patterns, suggest new tools that would address these gaps:

{patterns}

Provide your suggestions as a JSON object with this structure:
{{
    "suggestions": [
        {{
            "name": "example_tool",
            "purpose": "Clear description of what this tool does",
            "use_cases": ["Use case 1", "Use case 2"],
            "priority": "high",
            "required_integrations": ["dependency1", "dependency2"],
            "estimated_complexity": "moderate"
        }}
    ]
}}"""


# Convenience functions

async def analyze_for_tool_gaps(
    agent: Agent,
    log_item: Optional[LogItem] = None,
    min_messages: int = 10,
) -> list[ToolSuggestion]:
    """
    Convenience function to analyze conversation and generate tool suggestions.

    Args:
        agent: Agent instance
        log_item: Optional log item for progress updates
        min_messages: Minimum number of messages to analyze

    Returns:
        List of tool suggestions
    """
    analyzer = ToolSuggestionAnalyzer(agent)
    return await analyzer.analyze_and_suggest(log_item, min_messages)


async def get_conversation_patterns(
    agent: Agent,
    log_item: Optional[LogItem] = None,
    min_messages: int = 10,
) -> list[ConversationPattern]:
    """
    Convenience function to just get conversation patterns without suggestions.

    Args:
        agent: Agent instance
        log_item: Optional log item for progress updates
        min_messages: Minimum number of messages to analyze

    Returns:
        List of conversation patterns
    """
    analyzer = ToolSuggestionAnalyzer(agent)
    return await analyzer.analyze_conversation_for_gaps(log_item, min_messages)


def format_suggestions_report(suggestions: list[ToolSuggestion]) -> str:
    """
    Format tool suggestions as a readable report.

    Args:
        suggestions: List of tool suggestions

    Returns:
        Formatted report string
    """
    if not suggestions:
        return "No tool suggestions generated."

    lines = ["# Tool Suggestions Report\n"]
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    lines.append(f"Total suggestions: {len(suggestions)}\n")

    # Group by priority
    high_priority = [s for s in suggestions if s.priority == "high"]
    medium_priority = [s for s in suggestions if s.priority == "medium"]
    low_priority = [s for s in suggestions if s.priority == "low"]

    for priority_name, priority_list in [
        ("High Priority", high_priority),
        ("Medium Priority", medium_priority),
        ("Low Priority", low_priority),
    ]:
        if not priority_list:
            continue

        lines.append(f"\n## {priority_name} ({len(priority_list)} suggestions)\n")

        for suggestion in priority_list:
            lines.append(f"\n### {suggestion.name}")
            lines.append(f"**Purpose:** {suggestion.purpose}")
            lines.append(f"**Complexity:** {suggestion.estimated_complexity}")

            if suggestion.use_cases:
                lines.append("\n**Use Cases:**")
                for use_case in suggestion.use_cases:
                    lines.append(f"- {use_case}")

            if suggestion.required_integrations:
                lines.append(f"\n**Required:** {', '.join(suggestion.required_integrations)}")

            if suggestion.evidence:
                lines.append("\n**Evidence:**")
                for evidence in suggestion.evidence[:3]:  # Max 3 evidence items
                    lines.append(f"- {evidence[:100]}...")  # Truncate long evidence

    return "\n".join(lines)


def save_suggestions_to_memory(
    agent: Agent,
    suggestions: list[ToolSuggestion],
) -> None:
    """
    Save tool suggestions to agent memory for future reference.

    Args:
        agent: Agent instance
        suggestions: List of tool suggestions to save
    """
    try:
        import asyncio
        from python.helpers.memory import Memory

        async def _save():
            memory = await Memory.get(agent)

            for suggestion in suggestions:
                # Format as memory text
                memory_text = f"""Tool Suggestion: {suggestion.name}
Purpose: {suggestion.purpose}
Priority: {suggestion.priority}
Complexity: {suggestion.estimated_complexity}
Use Cases: {', '.join(suggestion.use_cases)}
Required Integrations: {', '.join(suggestion.required_integrations)}
"""

                # Save to SOLUTIONS area
                await memory.insert_text(
                    memory_text,
                    metadata={
                        "area": Memory.Area.SOLUTIONS.value,
                        "type": "tool_suggestion",
                        "tool_name": suggestion.name,
                        "priority": suggestion.priority,
                    }
                )

            PrintStyle.standard(f"Saved {len(suggestions)} tool suggestions to memory")

        asyncio.run(_save())

    except Exception as e:
        PrintStyle.error(f"Failed to save suggestions to memory: {str(e)}")
