# python/helpers/checkpoint_store.py
from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from python.helpers.checkpoint import AgentCheckpoint, CheckpointMetadata
import json
from python.helpers import files


class CheckpointStore(ABC):
    """Abstract base class for checkpoint storage backends"""

    @abstractmethod
    async def save(self, checkpoint: AgentCheckpoint) -> None:
        """Save a checkpoint to storage"""
        pass

    @abstractmethod
    async def load(self, checkpoint_id: str) -> Optional[AgentCheckpoint]:
        """Load a checkpoint by ID"""
        pass

    @abstractmethod
    async def load_latest(self, context_id: str) -> Optional[AgentCheckpoint]:
        """Load the most recent checkpoint for a context"""
        pass

    @abstractmethod
    async def delete(self, checkpoint_id: str) -> bool:
        """Delete a checkpoint by ID"""
        pass

    @abstractmethod
    async def list_metadata(self, context_id: Optional[str] = None, limit: int = 100) -> List[CheckpointMetadata]:
        """List checkpoint metadata, optionally filtered by context"""
        pass

    @abstractmethod
    async def cleanup_old(self, context_id: str, keep_last_n: int) -> int:
        """Remove old checkpoints, keeping only the last N"""
        pass


class FileCheckpointStore(CheckpointStore):
    """File-based checkpoint storage using Agent Zero's file helpers"""

    def __init__(self, base_path: str = "tmp/checkpoints"):
        self.base_path = base_path

    def _get_checkpoint_path(self, context_id: str, checkpoint_id: str) -> str:
        """Get the file path for a checkpoint"""
        return files.get_abs_path(self.base_path, context_id, f"{checkpoint_id}.json")

    def _get_context_folder(self, context_id: str) -> str:
        """Get the folder path for a context's checkpoints"""
        return files.get_abs_path(self.base_path, context_id)

    async def save(self, checkpoint: AgentCheckpoint) -> None:
        """Save checkpoint to file"""
        path = self._get_checkpoint_path(checkpoint.context_id, checkpoint.checkpoint_id)
        files.make_dirs(path)

        # Serialize checkpoint to JSON
        data = checkpoint.model_dump()
        json_data = json.dumps(data, default=str, ensure_ascii=False)
        files.write_file(path, json_data)

    async def load(self, checkpoint_id: str) -> Optional[AgentCheckpoint]:
        """Load checkpoint by ID - requires scanning all contexts"""
        # This is a simplified implementation; could be optimized with an index
        return None

    async def load_latest(self, context_id: str) -> Optional[AgentCheckpoint]:
        """Load most recent checkpoint for context"""
        from datetime import datetime

        context_folder = self._get_context_folder(context_id)

        if not files.exists(context_folder):
            return None

        # List all checkpoint files
        checkpoint_files = files.list_files(context_folder, "*.json")
        if not checkpoint_files:
            return None

        # Load all checkpoints and find the most recent
        latest_checkpoint = None
        latest_time = None

        for filename in checkpoint_files:
            path = files.get_abs_path(context_folder, filename)
            json_data = files.read_file(path)
            data = json.loads(json_data)

            # Convert ISO datetime string back to datetime
            data['created_at'] = datetime.fromisoformat(data['created_at'])
            checkpoint = AgentCheckpoint(**data)

            if latest_time is None or checkpoint.created_at > latest_time:
                latest_checkpoint = checkpoint
                latest_time = checkpoint.created_at

        return latest_checkpoint

    async def delete(self, checkpoint_id: str) -> bool:
        """Delete checkpoint by ID"""
        return False

    async def list_metadata(self, context_id: Optional[str] = None, limit: int = 100) -> List[CheckpointMetadata]:
        """List checkpoint metadata, optionally filtered by context"""
        from datetime import datetime

        metadata_list = []

        if context_id:
            # List for specific context
            context_folder = self._get_context_folder(context_id)
            if files.exists(context_folder):
                checkpoint_files = files.list_files(context_folder, "*.json")
                for filename in checkpoint_files[:limit]:
                    path = files.get_abs_path(context_folder, filename)
                    json_data = files.read_file(path)
                    data = json.loads(json_data)

                    metadata = CheckpointMetadata(
                        checkpoint_id=data["checkpoint_id"],
                        context_id=data["context_id"],
                        created_at=datetime.fromisoformat(data["created_at"]),
                        checkpoint_type=data["checkpoint_type"],
                        message_count=data.get("metadata", {}).get("message_count", 0),
                        tool_execution_count=data.get("metadata", {}).get("tool_execution_count", 0)
                    )
                    metadata_list.append(metadata)
        else:
            # List across all contexts - scan filesystem for ALL checkpoint directories
            import os
            base_folder = files.get_abs_path(self.base_path)

            if files.exists(base_folder):
                # List all entries in the base checkpoints folder
                entries = os.listdir(base_folder)

                # Filter to only directories (each directory is a context_id)
                for entry in entries:
                    entry_path = os.path.join(base_folder, entry)
                    if os.path.isdir(entry_path):
                        # This is a context folder, list its checkpoints
                        ctx_metadata = await self.list_metadata(context_id=entry, limit=limit)
                        metadata_list.extend(ctx_metadata)
                        if len(metadata_list) >= limit:
                            break

        # Sort by created_at descending (newest first) before returning
        metadata_list.sort(key=lambda m: m.created_at, reverse=True)
        return metadata_list[:limit]

    async def cleanup_old(self, context_id: str, keep_last_n: int) -> int:
        """Remove old checkpoints, keeping only the last N"""
        from datetime import datetime

        context_folder = self._get_context_folder(context_id)

        if not files.exists(context_folder):
            return 0

        # Load all checkpoints and sort by created_at
        checkpoint_files = files.list_files(context_folder, "*.json")
        checkpoints = []

        for filename in checkpoint_files:
            path = files.get_abs_path(context_folder, filename)
            json_data = files.read_file(path)
            data = json.loads(json_data)
            data['created_at'] = datetime.fromisoformat(data['created_at'])
            checkpoints.append((data['checkpoint_id'], data['created_at'], path))

        # Sort by created_at descending (newest first)
        checkpoints.sort(key=lambda x: x[1], reverse=True)

        # Delete checkpoints beyond keep_last_n
        deleted_count = 0
        for checkpoint_id, _, path in checkpoints[keep_last_n:]:
            if files.exists(path):
                files.delete_file(path)
                deleted_count += 1

        return deleted_count


class MemoryCheckpointStore(CheckpointStore):
    """In-memory checkpoint storage for testing and ephemeral contexts"""

    def __init__(self):
        self._checkpoints: Dict[str, AgentCheckpoint] = {}
        self._context_index: Dict[str, List[str]] = {}

    async def save(self, checkpoint: AgentCheckpoint) -> None:
        """Save checkpoint to memory"""
        self._checkpoints[checkpoint.checkpoint_id] = checkpoint

        # Update context index
        if checkpoint.context_id not in self._context_index:
            self._context_index[checkpoint.context_id] = []
        if checkpoint.checkpoint_id not in self._context_index[checkpoint.context_id]:
            self._context_index[checkpoint.context_id].append(checkpoint.checkpoint_id)

    async def load(self, checkpoint_id: str) -> Optional[AgentCheckpoint]:
        """Load checkpoint by ID"""
        return self._checkpoints.get(checkpoint_id)

    async def load_latest(self, context_id: str) -> Optional[AgentCheckpoint]:
        """Load most recent checkpoint for context"""
        checkpoint_ids = self._context_index.get(context_id, [])
        if not checkpoint_ids:
            return None

        # Find the most recent checkpoint
        latest_checkpoint = None
        latest_time = None

        for checkpoint_id in checkpoint_ids:
            checkpoint = self._checkpoints.get(checkpoint_id)
            if checkpoint and (latest_time is None or checkpoint.created_at > latest_time):
                latest_checkpoint = checkpoint
                latest_time = checkpoint.created_at

        return latest_checkpoint

    async def delete(self, checkpoint_id: str) -> bool:
        """Delete checkpoint by ID"""
        if checkpoint_id not in self._checkpoints:
            return False

        checkpoint = self._checkpoints[checkpoint_id]
        del self._checkpoints[checkpoint_id]

        # Update context index
        if checkpoint.context_id in self._context_index:
            self._context_index[checkpoint.context_id].remove(checkpoint_id)

        return True

    async def list_metadata(self, context_id: Optional[str] = None, limit: int = 100) -> List[CheckpointMetadata]:
        """List checkpoint metadata"""
        metadata_list = []

        if context_id:
            checkpoint_ids = self._context_index.get(context_id, [])
        else:
            checkpoint_ids = list(self._checkpoints.keys())

        for checkpoint_id in checkpoint_ids[:limit]:
            checkpoint = self._checkpoints.get(checkpoint_id)
            if checkpoint:
                metadata = CheckpointMetadata(
                    checkpoint_id=checkpoint.checkpoint_id,
                    context_id=checkpoint.context_id,
                    created_at=checkpoint.created_at,
                    checkpoint_type=checkpoint.checkpoint_type,
                    message_count=checkpoint.metadata.get("message_count", 0),
                    tool_execution_count=checkpoint.metadata.get("tool_execution_count", 0)
                )
                metadata_list.append(metadata)

        return metadata_list

    async def cleanup_old(self, context_id: str, keep_last_n: int) -> int:
        """Remove old checkpoints, keeping only the last N"""
        checkpoint_ids = self._context_index.get(context_id, [])
        if len(checkpoint_ids) <= keep_last_n:
            return 0

        # Sort checkpoints by created_at
        checkpoints = [(cid, self._checkpoints[cid].created_at) for cid in checkpoint_ids if cid in self._checkpoints]
        checkpoints.sort(key=lambda x: x[1], reverse=True)

        # Delete old checkpoints
        deleted_count = 0
        for checkpoint_id, _ in checkpoints[keep_last_n:]:
            await self.delete(checkpoint_id)
            deleted_count += 1

        return deleted_count
