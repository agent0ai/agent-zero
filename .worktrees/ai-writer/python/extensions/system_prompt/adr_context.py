import os

from python.helpers import files
from python.helpers.extension import Extension


class adr_context(Extension):
    """
    Injects recent Architecture Decision Records (ADRs) into the system prompt.
    Ensures the agent is aware of historical decisions for consistency.
    """

    async def execute(self, system_prompt: list[str], **kwargs) -> None:
        if not self.agent: return

        # Only inject if we are in a solutioning context
        profile = getattr(self.agent.config, "profile", "default")
        if profile not in ["architect", "developer", "solutioning"]: # Logic could be more broad
            pass

        try:
            adr_dir = files.get_abs_path("knowledge/custom/architectural_patterns/adrs")
            if not os.path.exists(adr_dir): return

            # Get latest 3 ADRs
            files_list = [f for f in os.listdir(adr_dir) if f.endswith(".md")]
            files_list.sort(reverse=True)
            latest_adrs = files_list[:3]

            if not latest_adrs: return

            ctx_text = "## 📜 Historical Architectural Decisions (ADRs)\n"
            ctx_text += "You must maintain consistency with following recent decisions:\n\n"

            for adr_file in latest_adrs:
                with open(os.path.join(adr_dir, adr_file), encoding='utf-8') as f:
                    # Just take the first few lines / summary
                    content = f.read()
                    # Extract decision section if possible, otherwise first 200 chars
                    decision_marker = "## Decision"
                    if decision_marker in content:
                        summary = content.split(decision_marker)[1].split("##")[0].strip()
                    else:
                        summary = content[:200] + "..."

                    ctx_text += f"### {adr_file}\n{summary}\n\n"

            system_prompt.append(ctx_text)

        except Exception:
            pass  # Non-critical failure
