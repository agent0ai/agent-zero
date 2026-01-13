## Paper generation tool:

### write_paper
Generate publication-ready LaTeX manuscripts from completed experiment results.
Includes literature search, citation gathering, and multi-round reflection for quality.

usage:
~~~json
{
    "thoughts": [
        "The experiments for 'sparse_attention' are complete",
        "I'll generate a workshop paper with the results",
    ],
    "headline": "Writing paper for sparse_attention experiments",
    "tool_name": "write_paper",
    "tool_args": {
        "idea_name": "sparse_attention",
        "format": "workshop",
        "num_reflections": 3,
        "skip_citations": false
    }
}
~~~

Parameters:
- idea_name (required): Name of idea with completed experiments
- format (optional): Paper format - "workshop" for 4-page or "full" for 8-page (default: "workshop")
- num_reflections (optional): Reflection rounds for improvement (default: 3)
- skip_citations (optional): Skip citation gathering for faster generation (default: false)

The tool will:
1. Load experiment summaries from all 4 stages
2. Search and gather relevant citations via Semantic Scholar
3. Generate initial LaTeX draft with all sections
4. Improve through multiple reflection rounds
5. Compile to PDF (requires pdflatex and bibtex)
6. Store paper metadata for retrieval

Output saved to: work_dir/ai-scientist/{idea_name}/paper/
