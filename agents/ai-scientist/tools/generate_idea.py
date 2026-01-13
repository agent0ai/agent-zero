import json
import re
from typing import Any

from python.helpers.tool import Tool, Response
from langchain_core.messages import HumanMessage, SystemMessage


# Idea JSON schema for validation
IDEA_SCHEMA = {
    "required_fields": [
        "Name",
        "Title",
        "Short Hypothesis",
        "Abstract",
        "Experiments",
        "Risk Factors and Limitations",
    ],
    "optional_fields": ["Related Work", "Code"],
}


class GenerateIdea(Tool):
    """Generate research ideas with novelty validation."""

    async def execute(
        self,
        topic: str = "",
        num_ideas: int = 5,
        num_reflections: int = 3,
        **kwargs,
    ) -> Response:
        """
        Generate research ideas for a given topic.

        Args:
            topic: Research topic description (markdown)
            num_ideas: Number of ideas to generate (default 5)
            num_reflections: Reflection rounds per idea (default 3)
        """
        # Get topic from args if not passed directly
        if not topic:
            topic = kwargs.get("topic", "")

        if not topic:
            return Response(
                message="Error: no topic provided. Please provide a research topic.",
                break_loop=False,
            )

        # Initialize ideas storage
        if "research_ideas" not in self.agent.data:
            self.agent.data["research_ideas"] = {}

        ideas = []
        for i in range(num_ideas):
            # Log progress
            self.agent.context.log.log(
                type="progress",
                heading=f"Generating idea {i + 1}/{num_ideas}",
                content="",
            )

            try:
                idea = await self._generate_single_idea(topic, num_reflections, i)
                if idea:
                    # Validate novelty
                    novelty_score = await self._check_novelty(idea)
                    idea["novelty_score"] = novelty_score

                    # Store idea
                    self.agent.data["research_ideas"][idea["Name"]] = idea
                    ideas.append(idea)

                    self.agent.context.log.log(
                        type="info",
                        heading=f"Idea {i + 1} generated",
                        content=idea["Title"],
                        kvps={"novelty_score": novelty_score},
                    )
            except Exception as e:
                self.agent.context.log.log(
                    type="warning",
                    heading=f"Idea {i + 1} failed",
                    content=str(e),
                )

        if not ideas:
            return Response(
                message="Failed to generate any valid research ideas.",
                break_loop=False,
            )

        # Format summary
        summary = self._format_ideas_summary(ideas)

        return Response(
            message=f"Generated {len(ideas)} research ideas:\n\n{summary}\n\nUse `run_experiment` to start experiments on an idea.",
            break_loop=False,
        )

    async def _generate_single_idea(
        self, topic: str, num_reflections: int, idea_num: int
    ) -> dict | None:
        """Generate a single research idea with reflection rounds."""

        # Initial generation prompt
        prompt = self._build_generation_prompt(topic, idea_num)

        # Get initial idea from agent's chat model
        response = await self._query_model(prompt)
        idea = self._parse_idea_json(response)

        if not idea:
            return None

        # Reflection rounds
        for r in range(num_reflections):
            self.agent.context.log.log(
                type="progress",
                heading=f"Reflection {r + 1}/{num_reflections}",
                content=f"Refining idea: {idea.get('Title', 'Unknown')}",
            )

            # Search related work
            search_query = f"{idea.get('Title', '')} {idea.get('Short Hypothesis', '')}"
            related_work = await self._search_related_work(search_query[:200])

            # Refine idea based on literature
            idea = await self._refine_idea(idea, related_work, r, num_reflections)

        return idea

    def _build_generation_prompt(self, topic: str, idea_num: int) -> dict:
        """Build the prompt for idea generation."""
        return {
            "Role": "You are a creative AI researcher generating novel research ideas.",
            "Task": f"Generate research idea #{idea_num + 1} for the following topic.",
            "Topic": topic,
            "Instructions": [
                "Generate a research idea with the following JSON structure:",
                "- Name: short identifier (snake_case, e.g., 'sparse_attention_routing')",
                "- Title: paper title",
                "- Short Hypothesis: 1-2 sentences describing the core hypothesis",
                "- Abstract: 3-4 sentence abstract",
                "- Experiments: list of 3-5 proposed experiments",
                "- Risk Factors and Limitations: list of potential issues",
                "",
                "Respond with ONLY valid JSON, no additional text.",
            ],
            "Example Output": json.dumps(
                {
                    "Name": "example_idea",
                    "Title": "Example Research Title",
                    "Short Hypothesis": "We hypothesize that X improves Y.",
                    "Abstract": "This paper proposes...",
                    "Experiments": ["Experiment 1", "Experiment 2"],
                    "Risk Factors and Limitations": ["Risk 1", "Risk 2"],
                },
                indent=2,
            ),
        }

    async def _query_model(self, prompt: dict) -> str:
        """Query the agent's chat model."""
        # Create messages for the query
        system_msg = SystemMessage(
            content="You are a research idea generator. Respond only with valid JSON."
        )
        user_msg = HumanMessage(content=json.dumps(prompt, indent=2))

        # Get response via agent's chat model
        response, _reasoning = await self.agent.call_chat_model(
            messages=[system_msg, user_msg],
        )

        return response if isinstance(response, str) else str(response)

    def _parse_idea_json(self, response: str) -> dict | None:
        """Parse JSON from model response."""
        # Try to extract JSON from response
        try:
            # Look for JSON block
            json_match = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))

            # Try direct parse
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to find JSON object in response
            try:
                start = response.find("{")
                end = response.rfind("}") + 1
                if start >= 0 and end > start:
                    return json.loads(response[start:end])
            except Exception:
                pass
        return None

    async def _search_related_work(self, query: str) -> list[dict]:
        """Search for related papers using Semantic Scholar tool."""
        try:
            # Get the semantic_scholar tool via agent's get_tool method
            # Note: get_tool() is synchronous, not async
            ss_tool = self.agent.get_tool(
                name="semantic_scholar",
                method=None,
                args={"query": query, "limit": 5},
                message="",
                loop_data=self.loop_data,
            )

            if not ss_tool:
                return []

            response = await ss_tool.execute(query=query, limit=5)

            # Extract papers from response message
            # The response contains formatted text like "1. **Title**\n   Authors: ..."
            if hasattr(response, "message") and response.message:
                papers = []
                paper_matches = re.findall(r"\*\*(.+?)\*\*", response.message)
                for title in paper_matches:
                    papers.append({"title": title})
                return papers
            return []
        except Exception:
            return []

    async def _refine_idea(
        self, idea: dict, related_work: list, round_num: int, total_rounds: int
    ) -> dict:
        """Refine idea based on related work."""
        prompt = {
            "Role": "You are refining a research idea based on literature review.",
            "Round": f"{round_num + 1}/{total_rounds}",
            "Current Idea": idea,
            "Related Work Found": related_work[:5] if related_work else "No related work found",
            "Instructions": [
                "Review the current idea and related work.",
                "Refine the idea to:",
                "1. Differentiate from existing work",
                "2. Address potential gaps",
                "3. Strengthen the hypothesis",
                "Return the refined idea as JSON with the same structure.",
            ],
        }

        response = await self._query_model(prompt)
        refined = self._parse_idea_json(response)

        return refined if refined else idea

    async def _check_novelty(self, idea: dict) -> int:
        """Check novelty score (1-10) by searching for similar work."""
        title = idea.get("Title", "")
        hypothesis = idea.get("Short Hypothesis", "")

        # Search for similar papers
        query = f"{title} {hypothesis}"[:200]

        try:
            # Get the semantic_scholar tool
            # Note: get_tool() is synchronous, not async
            ss_tool = self.agent.get_tool(
                name="semantic_scholar",
                method=None,
                args={"query": query, "limit": 10},
                message="",
                loop_data=self.loop_data,
            )

            if not ss_tool:
                return 5  # Default score if tool not available

            response = await ss_tool.execute(query=query, limit=10)

            # Parse the response to count similar papers
            message = response.message if hasattr(response, 'message') else str(response)

            # Count how many papers were found (look for "Found X papers" pattern)
            match = re.search(r"Found (\d+) papers", message)
            if match:
                num_papers = int(match.group(1))
                # Higher score = more novel (fewer similar papers found)
                if num_papers == 0:
                    return 10
                elif num_papers <= 2:
                    return 9
                elif num_papers <= 5:
                    return 7
                elif num_papers <= 10:
                    return 5
                else:
                    return 3

            return 7  # Default score if we can't parse
        except Exception:
            return 5  # Default score on error

    def _format_ideas_summary(self, ideas: list[dict]) -> str:
        """Format ideas for display."""
        summary = []
        for i, idea in enumerate(ideas, 1):
            summary.append(
                f"**{i}. {idea.get('Title', 'Unknown')}**\n"
                f"   Name: `{idea.get('Name', 'unknown')}`\n"
                f"   Hypothesis: {idea.get('Short Hypothesis', 'N/A')}\n"
                f"   Novelty Score: {idea.get('novelty_score', 'N/A')}/10\n"
            )
        return "\n".join(summary)
