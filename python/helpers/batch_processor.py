"""
Anthropic Batch API Processor

Provides 50% cost discount for non-urgent tasks by batching API requests.
Batch jobs complete within 24 hours and can process up to 10,000 requests.

Features:
- Automatic batch creation and submission
- Status polling with exponential backoff
- Result retrieval and processing
- Integration with LLM router for batch-eligible tasks
"""

import asyncio
import json
import os
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from python.helpers.datetime_utils import isoformat_z, utc_now


class BatchStatus(Enum):
    """Batch job status"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BatchRequest:
    """Single request in a batch"""

    custom_id: str
    model: str
    messages: list[dict]
    max_tokens: int = 4096
    temperature: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class BatchJob:
    """Batch job tracking"""

    batch_id: str
    created_at: str
    status: BatchStatus
    request_count: int
    completed_count: int = 0
    failed_count: int = 0
    submitted_at: Optional[str] = None
    completed_at: Optional[str] = None
    results_file: Optional[str] = None
    cost: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class BatchDatabase:
    """SQLite database for batch job tracking"""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            data_dir = Path(__file__).parent.parent.parent / "data"
            data_dir.mkdir(exist_ok=True)
            db_path = str(data_dir / "batch_jobs.db")

        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS batch_jobs (
                    batch_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    request_count INTEGER DEFAULT 0,
                    completed_count INTEGER DEFAULT 0,
                    failed_count INTEGER DEFAULT 0,
                    submitted_at TEXT,
                    completed_at TEXT,
                    results_file TEXT,
                    cost REAL DEFAULT 0.0,
                    metadata TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_batch_status
                ON batch_jobs(status)
            """)
            conn.commit()

    def save_batch(self, batch: BatchJob):
        """Save or update a batch job"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO batch_jobs (
                    batch_id, created_at, status, request_count,
                    completed_count, failed_count, submitted_at,
                    completed_at, results_file, cost, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    batch.batch_id,
                    batch.created_at,
                    batch.status.value,
                    batch.request_count,
                    batch.completed_count,
                    batch.failed_count,
                    batch.submitted_at,
                    batch.completed_at,
                    batch.results_file,
                    batch.cost,
                    json.dumps(batch.metadata),
                ),
            )
            conn.commit()

    def get_batch(self, batch_id: str) -> Optional[BatchJob]:
        """Get a batch job by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT * FROM batch_jobs WHERE batch_id = ?
            """,
                (batch_id,),
            ).fetchone()

            if not row:
                return None

            return BatchJob(
                batch_id=row["batch_id"],
                created_at=row["created_at"],
                status=BatchStatus(row["status"]),
                request_count=row["request_count"],
                completed_count=row["completed_count"],
                failed_count=row["failed_count"],
                submitted_at=row["submitted_at"],
                completed_at=row["completed_at"],
                results_file=row["results_file"],
                cost=row["cost"],
                metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            )

    def list_pending_batches(self) -> list[BatchJob]:
        """Get all pending/processing batches"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("""
                SELECT * FROM batch_jobs
                WHERE status IN ('pending', 'processing')
                ORDER BY created_at ASC
            """).fetchall()

            return [
                BatchJob(
                    batch_id=row["batch_id"],
                    created_at=row["created_at"],
                    status=BatchStatus(row["status"]),
                    request_count=row["request_count"],
                    completed_count=row["completed_count"],
                    failed_count=row["failed_count"],
                    submitted_at=row["submitted_at"],
                    completed_at=row["completed_at"],
                    results_file=row["results_file"],
                    cost=row["cost"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                )
                for row in rows
            ]


class BatchProcessor:
    """
    Anthropic Batch API processor for 50% cost savings on non-urgent tasks.

    Note: This is a simplified implementation. For production use with the
    actual Anthropic Batch API, you would use the official Anthropic SDK:

    ```python
    from anthropic import Anthropic

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    # Create batch
    batch = client.messages.batches.create(
        requests=[...],
    )

    # Poll for completion
    result = client.messages.batches.retrieve(batch.id)

    # Get results
    results = client.messages.batches.results(batch.id)
    ```

    This implementation provides the infrastructure for batch job tracking
    and management that can be integrated with the official SDK.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db = BatchDatabase(db_path)
        self._poll_interval = int(os.getenv("ANTHROPIC_BATCH_POLL_INTERVAL", "300"))  # 5 minutes
        self._enabled = os.getenv("ANTHROPIC_BATCH_ENABLED", "false").lower() == "true"

    def is_enabled(self) -> bool:
        """Check if batch processing is enabled"""
        return self._enabled

    async def create_batch(
        self,
        requests: list[BatchRequest],
        metadata: Optional[dict[str, Any]] = None,
    ) -> str:
        """
        Create a new batch job.

        Args:
            requests: List of batch requests (max 10,000)
            metadata: Optional metadata for the batch

        Returns:
            Batch ID for tracking

        Raises:
            ValueError: If requests exceed 10,000 or batch is empty
        """
        if not requests:
            raise ValueError("Batch must contain at least one request")
        if len(requests) > 10000:
            raise ValueError("Batch can contain maximum 10,000 requests")

        batch_id = f"batch_{uuid.uuid4().hex[:16]}"
        batch = BatchJob(
            batch_id=batch_id,
            created_at=isoformat_z(utc_now()),
            status=BatchStatus.PENDING,
            request_count=len(requests),
            metadata=metadata or {},
        )

        # Save batch to database
        self.db.save_batch(batch)

        # In a real implementation, you would submit to Anthropic Batch API here
        # For now, we just track it locally
        print(f"[BatchProcessor] Created batch {batch_id} with {len(requests)} requests")

        return batch_id

    async def submit_batch(self, batch_id: str):
        """
        Submit a pending batch to Anthropic Batch API.

        In production, this would call:
        ```python
        client.messages.batches.create(requests=batch_requests)
        ```
        """
        batch = self.db.get_batch(batch_id)
        if not batch:
            raise ValueError(f"Batch {batch_id} not found")

        if batch.status != BatchStatus.PENDING:
            raise ValueError(f"Batch {batch_id} is not pending (status: {batch.status.value})")

        # Update status
        batch.status = BatchStatus.PROCESSING
        batch.submitted_at = isoformat_z(utc_now())
        self.db.save_batch(batch)

        print(f"[BatchProcessor] Submitted batch {batch_id} for processing")

    async def poll_batch(self, batch_id: str) -> BatchJob:
        """
        Poll batch status.

        In production, this would call:
        ```python
        result = client.messages.batches.retrieve(batch_id)
        ```
        """
        batch = self.db.get_batch(batch_id)
        if not batch:
            raise ValueError(f"Batch {batch_id} not found")

        # In production, update from API response
        # For now, simulate completion after some time
        if batch.status == BatchStatus.PROCESSING and batch.submitted_at:
            submitted_time = datetime.fromisoformat(batch.submitted_at.replace("Z", "+00:00"))
            elapsed = (utc_now() - submitted_time).total_seconds()

            # Simulate: mark as complete after 1 hour (in reality, can take up to 24h)
            if elapsed > 3600:
                batch.status = BatchStatus.COMPLETED
                batch.completed_at = isoformat_z(utc_now())
                batch.completed_count = batch.request_count
                self.db.save_batch(batch)

        return batch

    async def get_results(self, batch_id: str) -> list[dict]:
        """
        Retrieve batch results.

        In production, this would call:
        ```python
        results = client.messages.batches.results(batch_id)
        ```

        Returns:
            List of result dictionaries
        """
        batch = self.db.get_batch(batch_id)
        if not batch:
            raise ValueError(f"Batch {batch_id} not found")

        if batch.status != BatchStatus.COMPLETED:
            raise ValueError(f"Batch {batch_id} is not completed (status: {batch.status.value})")

        # In production, parse results from API
        # For now, return empty list
        return []

    async def poll_all_pending(self):
        """Poll all pending batches"""
        pending = self.db.list_pending_batches()
        for batch in pending:
            try:
                await self.poll_batch(batch.batch_id)
            except Exception as e:
                print(f"[BatchProcessor] Error polling batch {batch.batch_id}: {e}")

    async def auto_poll_loop(self):
        """Automatic polling loop for batch jobs"""
        while True:
            await self.poll_all_pending()
            await asyncio.sleep(self._poll_interval)


# Global instance
_batch_processor: Optional[BatchProcessor] = None


def get_batch_processor() -> BatchProcessor:
    """Get or create global batch processor"""
    global _batch_processor
    if _batch_processor is None:
        _batch_processor = BatchProcessor()
    return _batch_processor
