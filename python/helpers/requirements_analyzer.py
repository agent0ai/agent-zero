"""
Requirements Analyzer for Parallel Agent Delegation

Analyzes user prompts to extract requirements, identify parallelizable tasks,
and suggest appropriate agent profiles.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import re


@dataclass
class Requirement:
    """Represents a single requirement extracted from a prompt."""
    id: str
    description: str
    agent_profile: Optional[str] = None
    priority: int = 0
    dependencies: List[str] = field(default_factory=list)
    estimated_complexity: str = "medium"  # low, medium, high
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RequirementsAnalysis:
    """Result of analyzing a prompt for requirements."""
    original_prompt: str
    requirements: List[Requirement] = field(default_factory=list)
    can_parallelize: bool = False
    suggested_profiles: List[str] = field(default_factory=list)
    estimated_time: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class RequirementsAnalyzer:
    """
    Analyzes user prompts to extract requirements and identify parallelizable tasks.
    """

    # Common patterns that indicate parallelizable tasks
    PARALLEL_INDICATORS = [
        r"and\s+also",
        r"meanwhile",
        r"in\s+parallel",
        r"simultaneously",
        r"at\s+the\s+same\s+time",
        r"while\s+.*\s+also",
        r"both\s+.*\s+and",
        r"multiple",
        r"several",
        r"various",
    ]

    # Profile keywords mapping
    PROFILE_KEYWORDS = {
        "developer": ["code", "program", "implement", "debug", "test", "function", "class", "api", "script"],
        "researcher": ["research", "find", "analyze", "study", "investigate", "explore", "compare"],
        "hacker": ["security", "vulnerability", "penetration", "exploit", "audit", "secure"],
        "agent0": ["orchestrate", "coordinate", "manage", "delegate"],
    }

    def __init__(self, agent: Any):
        """
        Initialize the requirements analyzer.

        Args:
            agent: Agent instance for LLM calls
        """
        self.agent = agent

    async def analyze(self, prompt: str) -> RequirementsAnalysis:
        """
        Analyze a prompt to extract requirements and identify parallelizable tasks.

        Args:
            prompt: User prompt to analyze

        Returns:
            RequirementsAnalysis object
        """
        # Quick heuristic check for parallelizability
        can_parallelize = self._check_parallelizable(prompt)

        # Use LLM for detailed analysis if prompt seems complex
        if len(prompt.split()) > 20 or can_parallelize:
            return await self._analyze_with_llm(prompt)
        else:
            return self._analyze_simple(prompt)

    def _check_parallelizable(self, prompt: str) -> bool:
        """Quick check if prompt might contain parallelizable tasks."""
        prompt_lower = prompt.lower()
        return any(re.search(pattern, prompt_lower, re.IGNORECASE) for pattern in self.PARALLEL_INDICATORS)

    def _analyze_simple(self, prompt: str) -> RequirementsAnalysis:
        """Simple heuristic-based analysis for straightforward prompts."""
        requirements = [Requirement(
            id="req_1",
            description=prompt,
            agent_profile=self._suggest_profile(prompt),
        )]

        return RequirementsAnalysis(
            original_prompt=prompt,
            requirements=requirements,
            can_parallelize=False,
            suggested_profiles=[req.agent_profile for req in requirements if req.agent_profile],
        )

    async def _analyze_with_llm(self, prompt: str) -> RequirementsAnalysis:
        """
        Use LLM to analyze prompt and extract requirements.

        Args:
            prompt: User prompt to analyze

        Returns:
            RequirementsAnalysis object
        """
        system_prompt = """You are a requirements analyzer. Analyze the user's prompt and extract distinct requirements that could potentially be executed in parallel.

For each requirement, identify:
1. A clear description
2. Suggested agent profile (developer, researcher, hacker, agent0, or empty for default)
3. Dependencies on other requirements (if any)
4. Estimated complexity (low, medium, high)

Format your response as a structured analysis that identifies:
- Individual requirements that can be worked on independently
- Dependencies between requirements
- Suggested agent profiles for each requirement
- Whether tasks can be parallelized

Be specific and actionable."""

        try:
            response = await self.agent.call_utility_model(
                system=system_prompt,
                message=f"Analyze this prompt and extract requirements:\n\n{prompt}",
            )

            return self._parse_llm_response(prompt, response)
        except Exception:
            # Fallback to simple analysis on error
            return self._analyze_simple(prompt)

    def _parse_llm_response(self, original_prompt: str, llm_response: str) -> RequirementsAnalysis:
        """
        Parse LLM response into RequirementsAnalysis.

        This is a simplified parser - in production, you might want more robust parsing.
        """
        requirements = []
        can_parallelize = False
        suggested_profiles = []

        # Try to extract requirements from response
        # Look for numbered lists or bullet points
        lines = llm_response.split('\n')
        req_id = 1

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for requirement indicators
            if any(indicator in line.lower() for indicator in ['requirement', 'task', 'need', 'should', 'must']):
                # Extract profile if mentioned
                profile = self._extract_profile_from_text(line)
                
                # Extract dependencies
                dependencies = self._extract_dependencies(line, requirements)

                req = Requirement(
                    id=f"req_{req_id}",
                    description=line,
                    agent_profile=profile,
                    dependencies=dependencies,
                )
                requirements.append(req)
                if profile:
                    suggested_profiles.append(profile)
                req_id += 1

                if len(requirements) > 1:
                    can_parallelize = True

        # If no requirements extracted, create a single requirement
        if not requirements:
            requirements = [Requirement(
                id="req_1",
                description=original_prompt,
                agent_profile=self._suggest_profile(original_prompt),
            )]

        return RequirementsAnalysis(
            original_prompt=original_prompt,
            requirements=requirements,
            can_parallelize=can_parallelize or len(requirements) > 1,
            suggested_profiles=list(set(suggested_profiles)) if suggested_profiles else [self._suggest_profile(original_prompt)],
        )

    def _suggest_profile(self, text: str) -> Optional[str]:
        """Suggest agent profile based on keywords in text."""
        text_lower = text.lower()
        scores = {}

        for profile, keywords in self.PROFILE_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                scores[profile] = score

        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        return None

    def _extract_profile_from_text(self, text: str) -> Optional[str]:
        """Extract mentioned profile from text."""
        text_lower = text.lower()
        for profile in self.PROFILE_KEYWORDS.keys():
            if profile in text_lower:
                return profile
        return None

    def _extract_dependencies(self, text: str, existing_requirements: List[Requirement]) -> List[str]:
        """Extract dependency references from text."""
        dependencies = []
        text_lower = text.lower()

        # Look for references to other requirements
        for req in existing_requirements:
            # Simple heuristic: check if requirement ID or key words are mentioned
            if req.id.lower() in text_lower or any(word in text_lower for word in ['after', 'following', 'depends']):
                dependencies.append(req.id)

        return dependencies

    def requirements_to_tasks(self, analysis: RequirementsAnalysis) -> List[Dict[str, Any]]:
        """
        Convert requirements analysis to task list format.

        Args:
            analysis: RequirementsAnalysis object

        Returns:
            List of task dictionaries ready for TaskQueue
        """
        tasks = []
        for req in analysis.requirements:
            task = {
                "id": req.id,
                "message": req.description,
                "profile": req.agent_profile,
                "dependencies": req.dependencies,
                "metadata": {
                    "complexity": req.estimated_complexity,
                    "priority": req.priority,
                    **req.metadata,
                },
            }
            tasks.append(task)

        return tasks

