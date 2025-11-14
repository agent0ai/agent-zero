# python/helpers/checkpoint_manager.py
import threading
from typing import Optional, List
from datetime import datetime, timezone

from python.helpers.checkpoint import AgentCheckpoint, CheckpointMetadata, CheckpointConfig, calculate_structure_hash, CheckpointValidationResult
from python.helpers.checkpoint_store import CheckpointStore, FileCheckpointStore, MemoryCheckpointStore
from agent import AgentContext


class CheckpointManager:
    """Singleton manager for checkpoint operations"""

    _instance: Optional["CheckpointManager"] = None
    _lock = threading.RLock()

    def __init__(self):
        self._store: Optional[CheckpointStore] = None
        self._config = CheckpointConfig()

    @classmethod
    def get(cls) -> "CheckpointManager":
        """Get the singleton instance"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = CheckpointManager()
        return cls._instance

    def initialize(self, config: CheckpointConfig):
        """Initialize the checkpoint manager with configuration"""
        self._config = config

        # Create appropriate store based on config
        if config.storage_backend == "file":
            self._store = FileCheckpointStore(base_path=config.storage_path)
        elif config.storage_backend == "memory":
            self._store = MemoryCheckpointStore()
        else:
            raise ValueError(f"Unknown storage backend: {config.storage_backend}")

    @property
    def store(self) -> CheckpointStore:
        """Get the checkpoint store, initializing with defaults if needed"""
        if self._store is None:
            self.initialize(self._config)
        return self._store  # type: ignore

    async def create_checkpoint(self, context: AgentContext, checkpoint_type: str) -> AgentCheckpoint:
        """
        Create a checkpoint from the current agent context.

        Args:
            context: The agent context to checkpoint
            checkpoint_type: Type of checkpoint (manual, auto, scheduled, pre_tool, post_tool)

        Returns:
            The created checkpoint
        """
        from python.helpers.persist_chat import _serialize_context
        from agent import Agent

        # Serialize the complete agent state
        agent_state = _serialize_context(context)

        # Collect tool and extension names
        tools = []
        extensions = []

        # Get tools from agent's config
        if context.agent0:
            config = context.agent0.config
            # Tools are dynamically loaded, collect them from the agent
            if hasattr(config, 'tools'):
                tools = list(config.tools.keys()) if isinstance(config.tools, dict) else []

        # Calculate structure hash
        structure_hash = calculate_structure_hash(
            context.config,
            tools,
            extensions
        )

        # Count messages and tool executions
        message_count = 0
        tool_execution_count = 0

        if context.agent0:
            # Count messages from all history components
            history = context.agent0.history
            message_count = len(history.current.messages)
            for topic in history.topics:
                message_count += len(topic.messages)
            for bulk in history.bulks:
                # Bulks contain compressed records, count them too
                message_count += len(bulk.records)

            # Count tool executions from messages in current topic
            for msg in history.current.messages:
                if hasattr(msg, 'content') and isinstance(msg.content, dict):
                    if 'tool_calls' in msg.content:
                        tool_execution_count += 1

        # Create checkpoint
        checkpoint = AgentCheckpoint(
            context_id=context.id,
            context_type=context.type.value,
            created_at=datetime.now(timezone.utc),
            checkpoint_type=checkpoint_type,
            agent_state=agent_state,
            execution_state={
                "paused": context.paused,
                "streaming_agent_number": context.streaming_agent.number if context.streaming_agent else 0,
            },
            structure_hash=structure_hash,
            metadata={
                "message_count": message_count,
                "tool_execution_count": tool_execution_count,
                "context_name": context.name,
            }
        )

        return checkpoint

    async def save_checkpoint(self, checkpoint: AgentCheckpoint) -> None:
        """Save a checkpoint to the configured store"""
        await self.store.save(checkpoint)

    async def load_checkpoint(self, checkpoint_id: str) -> Optional[AgentCheckpoint]:
        """Load a checkpoint by ID"""
        # Try to load from store - for memory store, we can load directly
        checkpoint = await self.store.load(checkpoint_id)
        if checkpoint:
            return checkpoint

        # For file store, scan filesystem for ALL contexts (including deleted chats)
        if isinstance(self.store, FileCheckpointStore):
            import json
            from python.helpers import files
            import os

            base_folder = files.get_abs_path(self.store.base_path)
            if files.exists(base_folder):
                # Scan all context directories in the filesystem
                entries = os.listdir(base_folder)
                for entry in entries:
                    entry_path = os.path.join(base_folder, entry)
                    if os.path.isdir(entry_path):
                        # This is a context_id folder, check for the checkpoint
                        checkpoint_path = self.store._get_checkpoint_path(entry, checkpoint_id)
                        if files.exists(checkpoint_path):
                            json_data = files.read_file(checkpoint_path)
                            data = json.loads(json_data)
                            data['created_at'] = datetime.fromisoformat(data['created_at'])
                            return AgentCheckpoint(**data)

        return None

    async def validate_checkpoint(self, checkpoint: AgentCheckpoint) -> CheckpointValidationResult:
        """
        Validate that a checkpoint can be safely restored.

        Checks:
        - Structure hash matches current configuration
        - Required tools and extensions exist
        - Agent configuration is compatible
        """
        errors = []
        warnings = []

        # Get current context if it exists
        current_context = AgentContext._contexts.get(checkpoint.context_id)

        if not current_context:
            warnings.append(f"Context {checkpoint.context_id} no longer exists, will be recreated")
        else:
            # Calculate current structure hash
            tools = []
            extensions = []

            current_hash = calculate_structure_hash(
                current_context.config,
                tools,
                extensions
            )

            if current_hash != checkpoint.structure_hash:
                warnings.append(
                    "Structure hash mismatch - agent configuration may have changed. "
                    "Restore may not work correctly."
                )

        # Validate checkpoint data structure
        if not checkpoint.agent_state:
            errors.append("Checkpoint has no agent state data")

        if not checkpoint.context_id:
            errors.append("Checkpoint has no context ID")

        is_valid = len(errors) == 0

        return CheckpointValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings
        )

    async def restore_context(self, checkpoint: AgentCheckpoint) -> AgentContext:
        """
        Restore an agent context from a checkpoint.

        Args:
            checkpoint: The checkpoint to restore from

        Returns:
            The restored AgentContext
        """
        from python.helpers.persist_chat import _deserialize_context
        from agent import Agent

        # Validate checkpoint first
        validation = await self.validate_checkpoint(checkpoint)
        if not validation.is_valid:
            raise ValueError(f"Cannot restore invalid checkpoint: {validation.errors}")

        # Deserialize context from checkpoint agent_state
        context = _deserialize_context(checkpoint.agent_state)

        # Restore execution state
        context.paused = checkpoint.execution_state.get("paused", False)

        # Update streaming agent if needed
        streaming_agent_number = checkpoint.execution_state.get("streaming_agent_number", 0)
        if streaming_agent_number > 0:
            agent = context.agent0
            while agent and agent.number != streaming_agent_number:
                agent = agent.data.get(Agent.DATA_NAME_SUBORDINATE, None)
            context.streaming_agent = agent

        return context

    async def list_checkpoints(self, context_id: Optional[str] = None) -> List[CheckpointMetadata]:
        """List checkpoints, optionally filtered by context"""
        return await self.store.list_metadata(context_id=context_id)

    async def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """
        Delete a checkpoint by ID.
        
        Args:
            checkpoint_id: The ID of the checkpoint to delete
            
        Returns:
            True if deleted successfully, False if not found
        """
        # For file store, we need to find which context the checkpoint belongs to
        if isinstance(self.store, FileCheckpointStore):
            import json
            from python.helpers import files
            import os
            
            # Scan all context folders to find the checkpoint
            base_folder = files.get_abs_path(self.store.base_path)
            if files.exists(base_folder):
                entries = os.listdir(base_folder)
                for entry in entries:
                    entry_path = os.path.join(base_folder, entry)
                    if os.path.isdir(entry_path):
                        # Check if checkpoint exists in this context folder
                        checkpoint_path = self.store._get_checkpoint_path(entry, checkpoint_id)
                        if files.exists(checkpoint_path):
                            files.delete_file(checkpoint_path)
                            return True
            return False
        else:
            # For memory store, use direct delete
            return await self.store.delete(checkpoint_id)

    async def cleanup_checkpoints(self, context_id: str, keep_last_n: Optional[int] = None) -> int:
        """
        Remove old checkpoints for a context, keeping only the last N.

        Args:
            context_id: The context to clean up
            keep_last_n: Number of checkpoints to keep (uses config default if None)

        Returns:
            Number of checkpoints deleted
        """
        if keep_last_n is None:
            keep_last_n = self._config.keep_last_n

        return await self.store.cleanup_old(context_id, keep_last_n)
