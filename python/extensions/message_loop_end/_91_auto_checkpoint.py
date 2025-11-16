from python.helpers.extension import Extension
from agent import LoopData, AgentContextType


class AutoCheckpoint(Extension):
    """
    Automatically create checkpoints at configured message intervals.

    Runs after each message loop iteration and creates a checkpoint
    if the message count threshold is reached.
    """

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        # Skip if checkpointing is not enabled
        config = self.agent.config
        if not getattr(config, 'checkpoint_enabled', False):
            return

        if not getattr(config, 'checkpoint_auto_save', False):
            return

        # Skip BACKGROUND contexts
        if self.agent.context.type == AgentContextType.BACKGROUND:
            return

        # Check if we should create a checkpoint based on message interval
        history = self.agent.history
        # Count messages from current topic
        message_count = len(history.current.messages)

        interval = getattr(config, 'checkpoint_interval_messages', 10)

        # Track last checkpoint message count to prevent duplicates
        last_checkpoint_count = getattr(self.agent.context, '_last_checkpoint_message_count', -1)

        # Create checkpoint if:
        # 1. We've reached an interval milestone
        # 2. We haven't already checkpointed at this count (prevents duplicates)
        if message_count > 0 and message_count % interval == 0 and message_count != last_checkpoint_count:
            from python.helpers.checkpoint_manager import CheckpointManager

            manager = CheckpointManager.get()
            checkpoint = await manager.create_checkpoint(self.agent.context, "auto")
            await manager.save_checkpoint(checkpoint)

            # Store the message count to prevent duplicate checkpoints
            self.agent.context._last_checkpoint_message_count = message_count

            # Cleanup old checkpoints
            keep_last_n = getattr(config, 'checkpoint_keep_last_n', 5)
            await manager.cleanup_checkpoints(self.agent.context.id, keep_last_n)
