import asyncio

from agent import AgentContext, LoopData
from python.helpers import message_queue as mq
from python.helpers.extension import Extension


class ProcessQueue(Extension):
    """Process queued messages after monologue ends."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        # Only process for agent0 (main agent)
        if self.agent.number != 0:
            return

        context = self.agent.context

        # Check if there are queued messages
        if mq.has_queue(context):
            # Schedule delayed task to send next queued message
            # This allows current monologue to fully complete first
            asyncio.create_task(self._delayed_send(context))

    async def _delayed_send(self, context: AgentContext):
        """Wait for task to complete, then send next queued message."""

        # Wait for current task to finish, but no more than 1 minute to prevent hanging tasks
        total_wait = 0
        while context.is_running() and total_wait < 60:
            await asyncio.sleep(0.1)
            total_wait += 0.1

        # Send next queued message if task is not running
        if not context.is_running():
            mq.send_next(context)
