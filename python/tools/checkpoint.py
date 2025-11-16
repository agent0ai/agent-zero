from agent import Agent
from python.helpers.tool import Tool, Response


class Checkpoint(Tool):
    """
    Tool for manual checkpoint management.

    Allows agents to create, list, restore, and manage checkpoints.
    """

    async def execute(self, action: str = "create", checkpoint_id: str = "", **kwargs):
        """
        Execute checkpoint operations.

        Args:
            action: The action to perform (create, list, restore, delete, cleanup, validate)
            checkpoint_id: The checkpoint ID (for restore, delete, validate)

        Returns:
            Response with operation result
        """
        from python.helpers.checkpoint_manager import CheckpointManager

        manager = CheckpointManager.get()

        if action == "create":
            return await self._create_checkpoint(manager)
        elif action == "list":
            return await self._list_checkpoints(manager)
        elif action == "restore":
            return await self._restore_checkpoint(manager, checkpoint_id)
        elif action == "delete":
            return await self._delete_checkpoint(manager, checkpoint_id)
        elif action == "cleanup":
            return await self._cleanup_checkpoints(manager)
        elif action == "validate":
            return await self._validate_checkpoint(manager, checkpoint_id)
        else:
            return Response(
                message=f"Unknown action: {action}. Valid actions: create, list, restore, delete, cleanup, validate",
                break_loop=False
            )

    async def _create_checkpoint(self, manager):
        """Create a manual checkpoint"""
        checkpoint = await manager.create_checkpoint(self.agent.context, "manual")
        await manager.save_checkpoint(checkpoint)

        metadata = checkpoint.metadata
        message = (
            f"Checkpoint created successfully!\n"
            f"ID: {checkpoint.checkpoint_id}\n"
            f"Type: {checkpoint.checkpoint_type}\n"
            f"Messages: {metadata.get('message_count', 0)}\n"
            f"Tool executions: {metadata.get('tool_execution_count', 0)}"
        )

        return Response(message=message, break_loop=False)

    async def _list_checkpoints(self, manager):
        """List checkpoints for current context"""
        checkpoints = await manager.list_checkpoints(self.agent.context.id)

        if not checkpoints:
            return Response(message="No checkpoints found for this context.", break_loop=False)

        message = f"Found {len(checkpoints)} checkpoint(s):\n\n"
        for cp in checkpoints:
            message += (
                f"ID: {cp.checkpoint_id}\n"
                f"Type: {cp.checkpoint_type}\n"
                f"Created: {cp.created_at}\n"
                f"Messages: {cp.message_count}\n\n"
            )

        return Response(message=message, break_loop=False)

    async def _restore_checkpoint(self, manager, checkpoint_id: str):
        """Restore from a checkpoint"""
        if not checkpoint_id:
            return Response(message="Error: checkpoint_id is required for restore action", break_loop=False)

        checkpoint = await manager.load_checkpoint(checkpoint_id)
        if not checkpoint:
            return Response(message=f"Error: Checkpoint {checkpoint_id} not found", break_loop=False)

        # Validate before restoring
        validation = await manager.validate_checkpoint(checkpoint)
        if not validation.is_valid:
            return Response(
                message=f"Error: Checkpoint validation failed:\n{chr(10).join(validation.errors)}",
                break_loop=False
            )

        # Restore context
        context = await manager.restore_context(checkpoint)

        message = f"Checkpoint {checkpoint_id} restored successfully!"
        if validation.warnings:
            message += f"\n\nWarnings:\n{chr(10).join(validation.warnings)}"

        return Response(message=message, break_loop=False)

    async def _delete_checkpoint(self, manager, checkpoint_id: str):
        """Delete a checkpoint"""
        if not checkpoint_id:
            return Response(message="Error: checkpoint_id is required for delete action", break_loop=False)

        deleted = await manager.store.delete(checkpoint_id)

        if deleted:
            return Response(message=f"Checkpoint {checkpoint_id} deleted successfully", break_loop=False)
        else:
            return Response(message=f"Error: Checkpoint {checkpoint_id} not found", break_loop=False)

    async def _cleanup_checkpoints(self, manager):
        """Cleanup old checkpoints"""
        deleted_count = await manager.cleanup_checkpoints(self.agent.context.id)

        return Response(
            message=f"Cleanup complete. Deleted {deleted_count} old checkpoint(s).",
            break_loop=False
        )

    async def _validate_checkpoint(self, manager, checkpoint_id: str):
        """Validate a checkpoint"""
        if not checkpoint_id:
            return Response(message="Error: checkpoint_id is required for validate action", break_loop=False)

        checkpoint = await manager.load_checkpoint(checkpoint_id)
        if not checkpoint:
            return Response(message=f"Error: Checkpoint {checkpoint_id} not found", break_loop=False)

        validation = await manager.validate_checkpoint(checkpoint)

        message = f"Validation result for {checkpoint_id}:\n"
        message += f"Valid: {validation.is_valid}\n"

        if validation.errors:
            message += f"\nErrors:\n{chr(10).join(validation.errors)}\n"

        if validation.warnings:
            message += f"\nWarnings:\n{chr(10).join(validation.warnings)}\n"

        return Response(message=message, break_loop=False)
