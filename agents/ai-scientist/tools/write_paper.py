"""
Write Paper Tool - Generate publication-ready LaTeX manuscripts.

Follows AI-Scientist-v2 patterns:
1. Load experiment summaries
2. Gather citations via Semantic Scholar
3. Generate LaTeX with reflection rounds
4. Compile PDF
"""

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage
from python.helpers.tool import Response, Tool


# LaTeX template for workshop-style papers (4-page ICBINB format)
LATEX_TEMPLATE = r"""
\documentclass{article}

\usepackage[utf8]{inputenc}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{amsmath}
\usepackage{hyperref}

\title{<<TITLE>>}
\author{AI Scientist}
\date{}

\begin{document}
\maketitle

\begin{abstract}
<<ABSTRACT>>
\end{abstract}

\section{Introduction}
<<INTRODUCTION>>

\section{Related Work}
<<RELATED_WORK>>

\section{Method}
<<METHOD>>

\section{Experiments}
<<EXPERIMENTS>>

\section{Results}
<<RESULTS>>

\section{Conclusion}
<<CONCLUSION>>

\bibliographystyle{plain}
\bibliography{references}

\end{document}
"""

WRITEUP_PROMPT = """Your goal is to write up the following research idea as a scientific paper.

## Research Idea
```markdown
{idea_text}
```

## Experiment Summaries
```json
{summaries}
```

## Available Plots
{plot_list}

## Current LaTeX Template
```latex
{latex_template}
```

## Instructions
1. Write a complete scientific paper based on the idea and experiment results
2. Include all sections: Abstract, Introduction, Related Work, Method, Experiments, Results, Conclusion
3. Report experimental results accurately - do not fabricate data
4. Reference the available plots using \\includegraphics
5. Keep the paper concise (4 pages for workshop, 8 pages for full paper)
6. Use proper LaTeX formatting

Return the complete LaTeX document wrapped in ```latex ... ``` blocks.
"""

REFLECTION_PROMPT = """Review and improve the following LaTeX paper.

Current LaTeX:
```latex
{current_latex}
```

Issues to check:
1. LaTeX syntax errors
2. Scientific rigor and clarity
3. Accuracy of reported results
4. Proper use of figures and tables
5. Citation completeness
6. Grammar and style

Provide the improved LaTeX wrapped in ```latex ... ``` blocks.
"""


class WritePaper(Tool):
    """Generate publication-ready LaTeX manuscripts from experiment results."""

    async def execute(
        self,
        idea_name: str,
        format: str = "workshop",
        num_reflections: int = 3,
        skip_citations: bool = False,
        **kwargs,
    ) -> Response:
        """
        Generate a scientific paper from completed experiments.

        Args:
            idea_name: Name of the idea with completed experiments
            format: Paper format ('workshop' for 4-page, 'full' for 8-page)
            num_reflections: Number of reflection rounds for improvement
            skip_citations: Skip citation gathering (faster but less complete)
        """
        # Load experiment data
        experiments = self.agent.context.data.get("experiments", {})
        exp_data = experiments.get(idea_name)

        if not exp_data:
            return Response(
                message=f"No experiment data found for '{idea_name}'. Run experiments first.",
                break_loop=False,
            )

        # Check if experiment is complete
        if exp_data.get("current_stage", 0) <= 4:
            return Response(
                message=f"Experiment '{idea_name}' is not complete. Current stage: {exp_data.get('current_stage', 0)}",
                break_loop=False,
            )

        # Load idea
        idea = exp_data.get("idea", {})
        if not idea:
            ideas = self.agent.context.data.get("research_ideas", {})
            idea = ideas.get(idea_name, {})

        self.agent.context.log.log(
            type="info",
            heading=f"Writing paper: {idea.get('Title', idea_name)}",
            content=f"Format: {format}, Reflections: {num_reflections}",
        )

        # Setup output directory
        output_dir = Path(f"work_dir/ai-scientist/{idea_name}/paper")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: Prepare experiment summaries
        self.agent.context.log.log(
            type="progress",
            heading="Preparing summaries",
            content="Loading experiment results...",
        )
        summaries = self._prepare_summaries(exp_data)

        # Step 2: Gather citations (optional)
        citations = ""
        if not skip_citations:
            self.agent.context.log.log(
                type="progress",
                heading="Gathering citations",
                content="Searching literature...",
            )
            citations = await self._gather_citations(idea, summaries)

        # Step 3: Collect available plots
        figures_dir = Path(f"work_dir/ai-scientist/{idea_name}/figures")
        plot_list = self._get_available_plots(figures_dir)

        # Step 4: Generate initial LaTeX
        self.agent.context.log.log(
            type="progress",
            heading="Generating LaTeX",
            content="Writing initial draft...",
        )

        latex_content = await self._generate_latex(
            idea, summaries, plot_list, format
        )

        if not latex_content:
            return Response(
                message="Failed to generate LaTeX content.",
                break_loop=False,
            )

        # Step 5: Reflection rounds
        for i in range(num_reflections):
            self.agent.context.log.log(
                type="progress",
                heading=f"Reflection {i + 1}/{num_reflections}",
                content="Improving paper...",
            )
            latex_content = await self._reflect_and_improve(latex_content)

        # Step 6: Save LaTeX and compile PDF
        latex_file = output_dir / "paper.tex"
        with open(latex_file, "w") as f:
            f.write(latex_content)

        # Save citations if gathered
        if citations:
            bib_file = output_dir / "references.bib"
            with open(bib_file, "w") as f:
                f.write(citations)

        # Copy figures
        if figures_dir.exists():
            dest_figures = output_dir / "figures"
            if dest_figures.exists():
                shutil.rmtree(dest_figures)
            shutil.copytree(figures_dir, dest_figures)

        # Try to compile PDF
        pdf_success = self._compile_latex(output_dir)

        # Store paper in agent data
        if "papers" not in self.agent.context.data:
            self.agent.context.data["papers"] = {}

        self.agent.context.data["papers"][idea_name] = {
            "idea_name": idea_name,
            "format": format,
            "latex_path": str(latex_file),
            "pdf_path": str(output_dir / "paper.pdf") if pdf_success else None,
            "citations_count": len(citations.split("@")) - 1 if citations else 0,
        }

        result_msg = f"Paper generated for '{idea.get('Title', idea_name)}'\n\n"
        result_msg += f"LaTeX saved to: {latex_file}\n"
        if pdf_success:
            result_msg += f"PDF compiled: {output_dir / 'paper.pdf'}\n"
        else:
            result_msg += "PDF compilation failed (LaTeX may need manual fixes)\n"

        self.agent.context.log.log(
            type="info",
            heading="Paper complete",
            content=result_msg,
        )

        return Response(message=result_msg, break_loop=False)

    def _prepare_summaries(self, exp_data: dict) -> dict:
        """Prepare experiment summaries for the writeup prompt."""
        summaries = {
            "baseline": {},
            "research": {},
            "ablation": {},
        }

        journals = exp_data.get("journals", {})

        # Stage 2 = baseline tuning
        stage_2 = journals.get("stage_2", {})
        if hasattr(stage_2, "get_best_node"):
            best = stage_2.get_best_node()
            if best:
                summaries["baseline"] = {
                    "plan": best.plan,
                    "metric": best.metric,
                    "analysis": best.analysis,
                }
        elif isinstance(stage_2, dict):
            nodes = stage_2.get("nodes", [])
            best_id = stage_2.get("best_node_id")
            for node in nodes:
                if isinstance(node, dict) and node.get("id") == best_id:
                    summaries["baseline"] = {
                        "plan": node.get("plan", ""),
                        "metric": node.get("metric"),
                        "analysis": node.get("analysis", ""),
                    }
                    break

        # Stage 3 = creative research
        stage_3 = journals.get("stage_3", {})
        if hasattr(stage_3, "get_best_node"):
            best = stage_3.get_best_node()
            if best:
                summaries["research"] = {
                    "plan": best.plan,
                    "metric": best.metric,
                    "analysis": best.analysis,
                }
        elif isinstance(stage_3, dict):
            nodes = stage_3.get("nodes", [])
            best_id = stage_3.get("best_node_id")
            for node in nodes:
                if isinstance(node, dict) and node.get("id") == best_id:
                    summaries["research"] = {
                        "plan": node.get("plan", ""),
                        "metric": node.get("metric"),
                        "analysis": node.get("analysis", ""),
                    }
                    break

        # Stage 4 = ablation studies
        stage_4 = journals.get("stage_4", {})
        if hasattr(stage_4, "nodes"):
            summaries["ablation"] = [
                {"plan": n.plan, "metric": n.metric, "analysis": n.analysis}
                for n in stage_4.nodes
                if not n.is_buggy
            ]
        elif isinstance(stage_4, dict):
            nodes = stage_4.get("nodes", [])
            summaries["ablation"] = [
                {
                    "plan": n.get("plan", ""),
                    "metric": n.get("metric"),
                    "analysis": n.get("analysis", ""),
                }
                for n in nodes
                if isinstance(n, dict) and not n.get("is_buggy", False)
            ]

        return summaries

    def _get_available_plots(self, figures_dir: Path) -> str:
        """Get list of available plot files."""
        if not figures_dir.exists():
            return "No plots available"

        plots = []
        for f in figures_dir.iterdir():
            if f.suffix.lower() in [".png", ".pdf", ".jpg", ".jpeg"]:
                plots.append(f.name)

        if not plots:
            return "No plots available"

        return "Available plots:\n" + "\n".join(f"- {p}" for p in sorted(plots))

    async def _gather_citations(self, idea: dict, summaries: dict) -> str:
        """Gather citations using Semantic Scholar."""
        bibtex_entries = []
        seen_titles = set()

        # Build search queries from idea
        title = idea.get("Title", "")
        hypothesis = idea.get("Short Hypothesis", "")
        abstract = idea.get("Abstract", "")

        queries = [
            title[:100],
            hypothesis[:100],
            abstract[:100] if abstract else "",
        ]

        for query in queries:
            if not query.strip():
                continue

            try:
                # Get the semantic_scholar tool via agent's get_tool method
                ss_tool = self.agent.get_tool(
                    name="semantic_scholar",
                    method=None,
                    args={"query": query, "limit": 5},
                    message="",
                    loop_data=self.loop_data,
                )

                if not ss_tool:
                    continue

                response = await ss_tool.execute(query=query, limit=5)

                # Parse response to extract paper metadata
                # Response format: "1. **Title**\n   Authors: X, Y\n   Year: 2024 | Citations: N"
                if hasattr(response, "message") and response.message:
                    paper_blocks = re.split(r"\n\d+\.\s+\*\*", response.message)
                    for block in paper_blocks[1:]:  # Skip first empty split
                        # Extract title
                        title_match = re.match(r"(.+?)\*\*", block)
                        if not title_match:
                            continue
                        paper_title = title_match.group(1).strip()

                        # Skip if already seen
                        title_lower = paper_title.lower()
                        if title_lower in seen_titles:
                            continue
                        seen_titles.add(title_lower)

                        # Extract authors
                        author_match = re.search(r"Authors?:\s*(.+?)(?:\n|$)", block)
                        authors = author_match.group(1).strip() if author_match else "Unknown"

                        # Extract year
                        year_match = re.search(r"Year:\s*(\d{4})", block)
                        year = year_match.group(1) if year_match else "2024"

                        # Generate citation key
                        first_author = authors.split(",")[0].split()[-1] if authors else "unknown"
                        cite_key = f"{first_author.lower()}{year}"

                        # Build BibTeX entry
                        bibtex = f"""@article{{{cite_key},
  title = {{{paper_title}}},
  author = {{{authors}}},
  year = {{{year}}},
}}"""
                        bibtex_entries.append(bibtex)

            except Exception as e:
                self.agent.context.log.log(
                    type="warning",
                    heading="Citation search failed",
                    content=str(e),
                )

        return "\n\n".join(bibtex_entries)

    async def _generate_latex(
        self,
        idea: dict,
        summaries: dict,
        plot_list: str,
        format: str,
    ) -> Optional[str]:
        """Generate initial LaTeX using the agent's chat model."""
        # Prepare the writeup prompt
        idea_text = f"""
# {idea.get('Title', 'Research Paper')}

## Hypothesis
{idea.get('Short Hypothesis', '')}

## Abstract
{idea.get('Abstract', '')}

## Experiments
{json.dumps(idea.get('Experiments', []), indent=2)}
"""

        prompt = WRITEUP_PROMPT.format(
            idea_text=idea_text,
            summaries=json.dumps(summaries, indent=2),
            plot_list=plot_list,
            latex_template=LATEX_TEMPLATE,
        )

        page_limit = 4 if format == "workshop" else 8
        system_msg = SystemMessage(
            content=f"""You are an AI researcher writing a scientific paper.
Write a complete {page_limit}-page paper in LaTeX format.
Be accurate - only report results that are in the experiment summaries.
Do not fabricate or hallucinate data."""
        )
        user_msg = HumanMessage(content=prompt)

        try:
            response, _reasoning = await self.agent.call_chat_model(
                messages=[system_msg, user_msg],
            )

            # Extract LaTeX from response
            latex_match = re.search(r"```latex\s*(.*?)\s*```", response, re.DOTALL)
            if latex_match:
                return latex_match.group(1).strip()

            # Try without language specifier
            latex_match = re.search(r"```\s*(\\document.*?)\s*```", response, re.DOTALL)
            if latex_match:
                return latex_match.group(1).strip()

            return None

        except Exception as e:
            self.agent.context.log.log(
                type="warning",
                heading="LaTeX generation failed",
                content=str(e),
            )
            return None

    async def _reflect_and_improve(self, latex_content: str) -> str:
        """Run a reflection round to improve the LaTeX."""
        prompt = REFLECTION_PROMPT.format(current_latex=latex_content)

        system_msg = SystemMessage(
            content="You are improving a scientific paper. Fix issues and return improved LaTeX."
        )
        user_msg = HumanMessage(content=prompt)

        try:
            response, _reasoning = await self.agent.call_chat_model(
                messages=[system_msg, user_msg],
            )

            # Extract improved LaTeX
            latex_match = re.search(r"```latex\s*(.*?)\s*```", response, re.DOTALL)
            if latex_match:
                return latex_match.group(1).strip()

            return latex_content  # Return original if parsing fails

        except Exception:
            return latex_content

    def _compile_latex(self, output_dir: Path) -> bool:
        """Compile LaTeX to PDF using pdflatex and bibtex."""
        latex_file = output_dir / "paper.tex"
        if not latex_file.exists():
            return False

        try:
            # Standard LaTeX compilation sequence:
            # pdflatex -> bibtex -> pdflatex -> pdflatex
            # This ensures all references and citations are resolved

            # First pdflatex pass (generates .aux file)
            subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "paper.tex"],
                cwd=output_dir,
                capture_output=True,
                timeout=60,
            )

            # Run bibtex (processes .aux and .bib files)
            bib_file = output_dir / "references.bib"
            if bib_file.exists():
                subprocess.run(
                    ["bibtex", "paper"],
                    cwd=output_dir,
                    capture_output=True,
                    timeout=30,
                )

            # Two more pdflatex passes (resolves all references)
            for _ in range(2):
                subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", "paper.tex"],
                    cwd=output_dir,
                    capture_output=True,
                    timeout=60,
                )

            pdf_file = output_dir / "paper.pdf"
            return pdf_file.exists()

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.agent.context.log.log(
                type="warning",
                heading="PDF compilation failed",
                content=f"pdflatex/bibtex error: {str(e)}",
            )
            return False
