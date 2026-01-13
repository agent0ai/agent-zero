## Research idea generation tool:

### generate_idea
Generate novel research ideas for a given topic with novelty validation and reflection rounds.
Returns list of research ideas with titles, hypotheses, experiments, and novelty scores.

usage:
~~~json
{
    "thoughts": [
        "The user wants research ideas about neural architecture search",
        "I'll use generate_idea to create several novel research proposals",
    ],
    "headline": "Generating research ideas about neural architecture search",
    "tool_name": "generate_idea",
    "tool_args": {
        "topic": "Neural architecture search for efficient transformers",
        "num_ideas": 5,
        "num_reflections": 3
    }
}
~~~

Parameters:
- topic (required): Research topic description in markdown format
- num_ideas (optional): Number of ideas to generate (default: 5)
- num_reflections (optional): Reflection rounds per idea for refinement (default: 3)

The tool will:
1. Generate creative research ideas based on the topic
2. Search related literature for each idea
3. Refine ideas through multiple reflection rounds
4. Validate novelty by checking for similar existing work
5. Store ideas in context data for later experiment execution
