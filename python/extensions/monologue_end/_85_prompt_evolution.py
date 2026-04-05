"""
Auto-trigger extension for the Prompt Evolution meta-learning tool

This extension:
1. Hooks into the monologue_end extension point
2. Checks if ENABLE_PROMPT_EVOLUTION is enabled
3. Auto-triggers prompt_evolution tool every N monologues (configurable)
4. Tracks execution count using agent.data for persistence
5. Skips execution if insufficient history
6. Logs when meta-analysis is triggered

Author: Agent Zero Meta-Learning System
Created: January 5, 2026
"""

import os
import asyncio
from python.helpers.extension import Extension
from python.helpers.log import LogItem
from agent import LoopData


class AutoPromptEvolution(Extension):
    """
    Extension that periodically triggers the prompt evolution meta-learning tool
    """

    # Key for storing state in agent.data
    DATA_KEY_MONOLOGUE_COUNT = "_meta_learning_monologue_count"
    DATA_KEY_LAST_EXECUTION = "_meta_learning_last_execution"

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        """
        Execute auto-trigger check for prompt evolution

        Args:
            loop_data: Current monologue loop data
            **kwargs: Additional arguments
        """

        # Check if meta-learning is enabled
        if not self._is_enabled():
            return

        # Initialize tracking data if not present
        if self.DATA_KEY_MONOLOGUE_COUNT not in self.agent.data:
            self.agent.data[self.DATA_KEY_MONOLOGUE_COUNT] = 0
            self.agent.data[self.DATA_KEY_LAST_EXECUTION] = 0

        # Increment monologue counter
        self.agent.data[self.DATA_KEY_MONOLOGUE_COUNT] += 1
        current_count = self.agent.data[self.DATA_KEY_MONOLOGUE_COUNT]

        # Get configuration
        trigger_interval = int(os.getenv("PROMPT_EVOLUTION_TRIGGER_INTERVAL", "10"))
        min_interactions = int(os.getenv("PROMPT_EVOLUTION_MIN_INTERACTIONS", "20"))

        # Get last execution count
        last_execution = self.agent.data[self.DATA_KEY_LAST_EXECUTION]

        # Calculate monologues since last execution
        monologues_since_last = current_count - last_execution

        # Check if we should trigger
        should_trigger = monologues_since_last >= trigger_interval

        if not should_trigger:
            return

        # Check if we have enough history
        history_size = len(self.agent.history)
        if history_size < min_interactions:
            self.agent.context.log.log(
                type="info",
                heading="Meta-Learning Auto-Trigger",
                content=f"Skipped: Insufficient history ({history_size}/{min_interactions} messages). Monologue #{current_count}",
            )
            return

        # Log that we're triggering meta-analysis
        log_item = self.agent.context.log.log(
            type="util",
            heading=f"Meta-Learning Auto-Triggered (Monologue #{current_count})",
            content=f"Analyzing last {history_size} interactions. This happens every {trigger_interval} monologues.",
        )

        # Update last execution counter
        self.agent.data[self.DATA_KEY_LAST_EXECUTION] = current_count

        # Run meta-analysis in background to avoid blocking
        task = asyncio.create_task(self._run_meta_analysis(log_item, current_count))
        return task

    async def _run_meta_analysis(self, log_item: LogItem, monologue_count: int):
        """
        Execute the prompt evolution tool

        Args:
            log_item: Log item to update with results
            monologue_count: Current monologue count for tracking
        """
        try:
            # Dynamically import the prompt evolution tool
            from python.tools.prompt_evolution import PromptEvolution

            # Create tool instance
            tool = PromptEvolution(
                agent=self.agent,
                name="prompt_evolution",
                method=None,
                args={},
                message="Auto-triggered meta-analysis",
                loop_data=None
            )

            # Execute the tool
            response = await tool.execute()

            # Update log with results
            if response and response.message:
                log_item.update(
                    heading=f"Meta-Learning Complete (Monologue #{monologue_count})",
                    content=response.message,
                )
            else:
                log_item.update(
                    heading=f"Meta-Learning Complete (Monologue #{monologue_count})",
                    content="Analysis completed but no significant findings.",
                )

        except Exception as e:
            # Log error but don't crash the extension
            log_item.update(
                heading=f"Meta-Learning Error (Monologue #{monologue_count})",
                content=f"Auto-trigger failed: {str(e)}",
            )
            self.agent.context.log.log(
                type="error",
                heading="Meta-Learning Auto-Trigger Error",
                content=str(e),
            )

    def _is_enabled(self) -> bool:
        """
        Check if prompt evolution is enabled in environment settings

        Returns:
            True if enabled, False otherwise
        """
        return os.getenv("ENABLE_PROMPT_EVOLUTION", "false").lower() == "true"
