"""Run one backup at a time independently of HTTP request lifetimes."""

import asyncio
import logging
import tempfile
import threading
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import BinaryIO

logger = logging.getLogger(__name__)


@dataclass
class BackupJob:
    name: str
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    directory: tempfile.TemporaryDirectory = field(
        default_factory=lambda: tempfile.TemporaryDirectory(prefix="a0-backup-")
    )
    status: str = "running"
    downloads: set[BinaryIO] = field(default_factory=set)
    expired: bool = False
    timer: threading.Timer | None = None

    @property
    def path(self) -> Path:
        return Path(self.directory.name) / "backup.zip"


class BackupJobs:
    """Keep a completed archive for one hour, or until the next backup starts."""

    def __init__(self, retention_seconds: float = 3600):
        self.retention_seconds = retention_seconds
        self._lock = threading.Lock()
        self._job: BackupJob | None = None

    def start(self, name: str, create: Callable[[str], Awaitable[None]]) -> dict:
        with self._lock:
            if self._job:
                if self._job.status == "running" or self._job.downloads:
                    raise RuntimeError(
                        "A backup is already being created or downloaded"
                    )
                self._discard(self._job)
            job = BackupJob(name=name)
            self._job = job
            try:
                threading.Thread(
                    target=self._run, args=(job, create), name="Backup", daemon=True
                ).start()
            except Exception:
                self._discard(job)
                raise
            return self._status(job)

    def status(self, job_id: str) -> dict:
        with self._lock:
            return self._status(self._get(job_id))

    def acquire_download(self, job_id: str) -> tuple[BinaryIO, str]:
        with self._lock:
            job = self._get(job_id)
            if job.status != "completed":
                raise RuntimeError("Backup is not ready for download")
            stream = job.path.open("rb")
            job.downloads.add(stream)
            return stream, f"{job.name}.zip"

    def release_download(self, job_id: str, stream: BinaryIO) -> None:
        with self._lock:
            stream.close()
            job = self._job
            if job and job.id == job_id:
                job.downloads.discard(stream)
                if job.expired and not job.downloads:
                    self._discard(job)

    def _get(self, job_id: str) -> BackupJob:
        if not self._job or self._job.id != job_id or self._job.expired:
            raise KeyError("Backup expired or was not found. Create a new backup.")
        return self._job

    @staticmethod
    def _status(job: BackupJob) -> dict:
        result = {"success": True, "job_id": job.id, "status": job.status}
        if job.status == "failed":
            result["error"] = "Backup creation failed. See the server log for details."
        return result

    def _run(self, job: BackupJob, create: Callable[[str], Awaitable[None]]) -> None:
        try:
            with asyncio.Runner() as runner:
                runner.run(create(str(job.path)))
            status = "completed"
        except Exception:
            logger.exception("Backup creation failed")
            job.directory.cleanup()
            status = "failed"
        with self._lock:
            job.status = status
            job.timer = threading.Timer(self.retention_seconds, self._expire, (job,))
            job.timer.daemon = True
            job.timer.start()

    def _expire(self, job: BackupJob) -> None:
        with self._lock:
            if self._job is job:
                job.expired = True
                if not job.downloads:
                    self._discard(job)

    def _discard(self, job: BackupJob) -> None:
        if job.timer:
            job.timer.cancel()
        job.directory.cleanup()
        self._job = None


backup_jobs = BackupJobs()
