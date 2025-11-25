"""
Unity Project State Tracker with Real-Time Monitoring.

This module provides comprehensive project state tracking:
- Real-time file change detection
- Build status monitoring
- Error aggregation and trending
- Performance metrics collection
- Development velocity tracking
"""

import asyncio
import os
import json
import hashlib
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import logging
import re
from collections import defaultdict

from python.helpers.unity_qdrant_enhanced import (
    UnityQdrantEnhanced, UnityCollectionType
)
from python.helpers.unity_knowledge_extractor import UnityKnowledgeExtractor

logger = logging.getLogger(__name__)


class ProjectState(Enum):
    """Overall project state."""
    HEALTHY = "healthy"
    WARNINGS = "warnings"
    ERRORS = "errors"
    BUILDING = "building"
    UNKNOWN = "unknown"


class BuildStatus(Enum):
    """Build status."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ChangeType(Enum):
    """Type of file change."""
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"


@dataclass
class FileChange:
    """Represents a file change event."""
    path: str
    change_type: ChangeType
    timestamp: datetime
    old_path: Optional[str] = None  # For renames


@dataclass
class BuildInfo:
    """Information about a build."""
    build_id: str
    status: BuildStatus
    target: str  # StandaloneWindows64, Android, etc.
    started_at: datetime
    finished_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    output_path: Optional[str] = None
    size_bytes: Optional[int] = None


@dataclass
class ErrorTrend:
    """Error trending data."""
    error_type: str
    count_today: int
    count_week: int
    count_total: int
    first_seen: datetime
    last_seen: datetime
    is_resolved: bool
    resolution_rate: float


@dataclass
class PerformanceMetric:
    """Performance metric data point."""
    name: str
    value: float
    unit: str
    timestamp: datetime
    scene: Optional[str] = None
    context: Optional[str] = None


@dataclass
class DevelopmentVelocity:
    """Development velocity metrics."""
    commits_today: int
    commits_week: int
    files_changed_today: int
    files_changed_week: int
    lines_added_today: int
    lines_removed_today: int
    tasks_completed_today: int
    tasks_completed_week: int
    avg_task_completion_hours: float


@dataclass
class ProjectSnapshot:
    """Complete snapshot of project state."""
    timestamp: datetime
    state: ProjectState
    project_id: str
    project_path: str

    # File statistics
    total_scripts: int = 0
    total_scenes: int = 0
    total_prefabs: int = 0
    total_assets: int = 0
    total_lines_of_code: int = 0

    # Recent changes
    recent_changes: List[FileChange] = field(default_factory=list)

    # Build info
    last_build: Optional[BuildInfo] = None
    builds_today: int = 0
    build_success_rate: float = 0.0

    # Errors
    active_errors: int = 0
    warnings: int = 0
    error_trends: List[ErrorTrend] = field(default_factory=list)

    # Performance
    performance_metrics: List[PerformanceMetric] = field(default_factory=list)

    # Velocity
    velocity: Optional[DevelopmentVelocity] = None

    # Unity specific
    unity_version: str = ""
    active_scene: str = ""
    play_mode_active: bool = False


class UnityProjectTracker:
    """
    Tracks Unity project state in real-time.

    Features:
    - File change monitoring with debouncing
    - Build status tracking
    - Error aggregation and trending
    - Performance metric collection
    - Development velocity calculation
    - Integration with Qdrant for persistence
    """

    def __init__(
        self,
        qdrant: UnityQdrantEnhanced,
        project_id: str,
        project_path: str,
        extractor: Optional[UnityKnowledgeExtractor] = None,
        snapshot_interval_seconds: int = 300,  # 5 minutes
        change_debounce_seconds: float = 2.0,
    ):
        self.qdrant = qdrant
        self.project_id = project_id
        self.project_path = Path(project_path)
        self.extractor = extractor or UnityKnowledgeExtractor(
            qdrant, project_id
        )
        self.snapshot_interval = snapshot_interval_seconds
        self.change_debounce = change_debounce_seconds

        # State tracking
        self._current_snapshot: Optional[ProjectSnapshot] = None
        self._pending_changes: List[FileChange] = []
        self._change_task: Optional[asyncio.Task] = None
        self._running = False

        # Build tracking
        self._builds: List[BuildInfo] = []
        self._current_build: Optional[BuildInfo] = None

        # Error tracking
        self._errors: Dict[str, List[datetime]] = defaultdict(list)

        # Performance tracking
        self._metrics: List[PerformanceMetric] = []

        # Callbacks
        self._on_state_change: List[Callable[[ProjectSnapshot], None]] = []
        self._on_error: List[Callable[[str, str], None]] = []
        self._on_build_complete: List[Callable[[BuildInfo], None]] = []

    async def start(self):
        """Start project tracking."""
        self._running = True

        # Initial snapshot
        self._current_snapshot = await self._create_snapshot()

        # Start background tasks
        asyncio.create_task(self._snapshot_loop())
        asyncio.create_task(self._file_watcher())

        logger.info(f"Project tracker started for {self.project_path}")

    async def stop(self):
        """Stop project tracking."""
        self._running = False
        logger.info("Project tracker stopped")

    def on_state_change(self, callback: Callable[[ProjectSnapshot], None]):
        """Register callback for state changes."""
        self._on_state_change.append(callback)

    def on_error(self, callback: Callable[[str, str], None]):
        """Register callback for new errors."""
        self._on_error.append(callback)

    def on_build_complete(self, callback: Callable[[BuildInfo], None]):
        """Register callback for build completion."""
        self._on_build_complete.append(callback)

    async def get_current_state(self) -> ProjectSnapshot:
        """Get current project state."""
        if not self._current_snapshot:
            self._current_snapshot = await self._create_snapshot()
        return self._current_snapshot

    async def record_error(
        self,
        error_type: str,
        error_message: str,
        stack_trace: str = "",
        script_path: Optional[str] = None,
        line_number: Optional[int] = None,
    ):
        """Record a new error occurrence."""
        now = datetime.now()

        # Track locally
        error_key = f"{error_type}:{hashlib.md5(error_message.encode()).hexdigest()[:8]}"
        self._errors[error_key].append(now)

        # Store in Qdrant
        await self.qdrant.store_error(
            error_message=error_message,
            error_type=error_type,
            stack_trace=stack_trace,
            project_id=self.project_id,
            related_script=script_path,
            metadata={
                "line_number": line_number,
                "session_time": now.isoformat(),
            }
        )

        # Notify callbacks
        for callback in self._on_error:
            try:
                callback(error_type, error_message)
            except Exception as e:
                logger.error(f"Error callback failed: {e}")

    async def start_build(
        self,
        target: str,
        build_options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Start tracking a new build."""
        build_id = f"build_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        self._current_build = BuildInfo(
            build_id=build_id,
            status=BuildStatus.IN_PROGRESS,
            target=target,
            started_at=datetime.now(),
        )

        self._builds.append(self._current_build)

        # Update state
        if self._current_snapshot:
            self._current_snapshot.state = ProjectState.BUILDING
            self._current_snapshot.last_build = self._current_build
            await self._notify_state_change()

        logger.info(f"Build started: {build_id} for {target}")
        return build_id

    async def finish_build(
        self,
        success: bool,
        errors: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
        output_path: Optional[str] = None,
    ):
        """Finish the current build."""
        if not self._current_build:
            return

        self._current_build.status = BuildStatus.SUCCESS if success else BuildStatus.FAILED
        self._current_build.finished_at = datetime.now()
        self._current_build.duration_seconds = (
            self._current_build.finished_at - self._current_build.started_at
        ).total_seconds()
        self._current_build.errors = errors or []
        self._current_build.warnings = warnings or []
        self._current_build.output_path = output_path

        if output_path and os.path.exists(output_path):
            self._current_build.size_bytes = os.path.getsize(output_path)

        # Store in Qdrant
        await self._store_build_info(self._current_build)

        # Notify callbacks
        for callback in self._on_build_complete:
            try:
                callback(self._current_build)
            except Exception as e:
                logger.error(f"Build callback failed: {e}")

        # Update state
        if self._current_snapshot:
            self._current_snapshot.state = (
                ProjectState.HEALTHY if success else ProjectState.ERRORS
            )
            self._current_snapshot.builds_today += 1
            await self._notify_state_change()

        logger.info(f"Build finished: {self._current_build.build_id} - {self._current_build.status.value}")
        self._current_build = None

    async def record_metric(
        self,
        name: str,
        value: float,
        unit: str,
        scene: Optional[str] = None,
        context: Optional[str] = None,
    ):
        """Record a performance metric."""
        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            timestamp=datetime.now(),
            scene=scene,
            context=context,
        )

        self._metrics.append(metric)

        # Keep only last 1000 metrics in memory
        if len(self._metrics) > 1000:
            self._metrics = self._metrics[-1000:]

        # Store in Qdrant periodically (batch)
        if len(self._metrics) % 100 == 0:
            await self._store_metrics_batch()

    async def get_error_trends(self, days: int = 7) -> List[ErrorTrend]:
        """Get error trending data."""
        trends = []
        now = datetime.now()
        day_ago = now - timedelta(days=1)
        week_ago = now - timedelta(days=days)

        for error_key, timestamps in self._errors.items():
            if not timestamps:
                continue

            parts = error_key.split(":", 1)
            error_type = parts[0] if parts else error_key

            count_today = sum(1 for t in timestamps if t > day_ago)
            count_week = sum(1 for t in timestamps if t > week_ago)

            trends.append(ErrorTrend(
                error_type=error_type,
                count_today=count_today,
                count_week=count_week,
                count_total=len(timestamps),
                first_seen=min(timestamps),
                last_seen=max(timestamps),
                is_resolved=False,  # Would need to check solutions
                resolution_rate=0.0,
            ))

        return sorted(trends, key=lambda t: t.count_today, reverse=True)

    async def get_velocity(self, days: int = 7) -> DevelopmentVelocity:
        """Calculate development velocity metrics."""
        now = datetime.now()
        day_ago = now - timedelta(days=1)
        week_ago = now - timedelta(days=days)

        # Count recent changes
        today_changes = [c for c in self._pending_changes if c.timestamp > day_ago]
        week_changes = [c for c in self._pending_changes if c.timestamp > week_ago]

        # Estimate lines changed (would need git integration for accurate numbers)
        lines_added = len([c for c in today_changes if c.change_type == ChangeType.CREATED]) * 50
        lines_removed = len([c for c in today_changes if c.change_type == ChangeType.DELETED]) * 30

        # Task completion from Qdrant
        tasks_results = await self.qdrant.search_unity(
            query="status completed",
            collection_types=[UnityCollectionType.TASKS],
            project_id=self.project_id,
            filters={"status": "completed"},
            limit=100,
        )

        return DevelopmentVelocity(
            commits_today=len(today_changes) // 5,  # Estimate
            commits_week=len(week_changes) // 5,
            files_changed_today=len(today_changes),
            files_changed_week=len(week_changes),
            lines_added_today=lines_added,
            lines_removed_today=lines_removed,
            tasks_completed_today=sum(
                1 for r in tasks_results
                if (now - datetime.fromisoformat(
                    r.document.metadata.get("completed_at", now.isoformat())
                )).days < 1
            ),
            tasks_completed_week=len(tasks_results),
            avg_task_completion_hours=24.0,  # Would need task timing data
        )

    async def get_health_report(self) -> Dict[str, Any]:
        """Generate a comprehensive health report."""
        snapshot = await self.get_current_state()
        trends = await self.get_error_trends()
        velocity = await self.get_velocity()

        # Determine health score
        health_score = 100
        issues = []

        # Deduct for errors
        if snapshot.active_errors > 0:
            health_score -= min(30, snapshot.active_errors * 5)
            issues.append(f"{snapshot.active_errors} active errors")

        # Deduct for warnings
        if snapshot.warnings > 10:
            health_score -= min(10, snapshot.warnings)
            issues.append(f"{snapshot.warnings} warnings")

        # Deduct for failing builds
        if snapshot.build_success_rate < 0.8:
            health_score -= 20
            issues.append(f"Build success rate: {snapshot.build_success_rate:.0%}")

        # Deduct for error trends
        critical_errors = [t for t in trends if t.count_today > 5]
        if critical_errors:
            health_score -= len(critical_errors) * 5
            issues.append(f"{len(critical_errors)} critical error patterns")

        return {
            "timestamp": datetime.now().isoformat(),
            "project_id": self.project_id,
            "health_score": max(0, health_score),
            "state": snapshot.state.value,
            "issues": issues,
            "statistics": {
                "scripts": snapshot.total_scripts,
                "scenes": snapshot.total_scenes,
                "prefabs": snapshot.total_prefabs,
                "lines_of_code": snapshot.total_lines_of_code,
            },
            "build_info": {
                "last_status": snapshot.last_build.status.value if snapshot.last_build else "none",
                "builds_today": snapshot.builds_today,
                "success_rate": snapshot.build_success_rate,
            },
            "errors": {
                "active": snapshot.active_errors,
                "warnings": snapshot.warnings,
                "trending": [asdict(t) for t in trends[:5]],
            },
            "velocity": asdict(velocity) if velocity else None,
            "recommendations": self._generate_recommendations(snapshot, trends),
        }

    def _generate_recommendations(
        self,
        snapshot: ProjectSnapshot,
        trends: List[ErrorTrend],
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        if snapshot.active_errors > 0:
            recommendations.append("Fix active compilation errors before continuing")

        if trends:
            top_error = trends[0]
            if top_error.count_today > 3:
                recommendations.append(
                    f"Investigate recurring {top_error.error_type} "
                    f"({top_error.count_today} occurrences today)"
                )

        if snapshot.build_success_rate < 0.8 and snapshot.builds_today > 2:
            recommendations.append("Review build configuration - high failure rate")

        if snapshot.warnings > 20:
            recommendations.append(f"Address {snapshot.warnings} compiler warnings")

        if snapshot.total_lines_of_code > 50000:
            recommendations.append("Consider code organization review for large codebase")

        return recommendations

    async def _create_snapshot(self) -> ProjectSnapshot:
        """Create a new project snapshot."""
        # Count files
        scripts = list(self.project_path.glob("Assets/**/*.cs"))
        scenes = list(self.project_path.glob("Assets/**/*.unity"))
        prefabs = list(self.project_path.glob("Assets/**/*.prefab"))

        # Count lines of code
        total_lines = 0
        for script in scripts[:100]:  # Limit for performance
            try:
                total_lines += sum(1 for _ in open(script, 'r', encoding='utf-8-sig'))
            except Exception:
                pass

        # Extrapolate if limited
        if len(scripts) > 100:
            total_lines = int(total_lines * len(scripts) / 100)

        # Get Unity version from ProjectSettings
        unity_version = await self._get_unity_version()

        # Calculate build success rate
        recent_builds = self._builds[-10:] if self._builds else []
        success_rate = (
            sum(1 for b in recent_builds if b.status == BuildStatus.SUCCESS) / len(recent_builds)
            if recent_builds else 1.0
        )

        # Determine state
        state = ProjectState.HEALTHY
        active_errors = len([k for k, v in self._errors.items() if v])
        warnings = 0  # Would need to track separately

        if self._current_build:
            state = ProjectState.BUILDING
        elif active_errors > 0:
            state = ProjectState.ERRORS
        elif warnings > 10:
            state = ProjectState.WARNINGS

        return ProjectSnapshot(
            timestamp=datetime.now(),
            state=state,
            project_id=self.project_id,
            project_path=str(self.project_path),
            total_scripts=len(scripts),
            total_scenes=len(scenes),
            total_prefabs=len(prefabs),
            total_assets=len(list(self.project_path.glob("Assets/**/*.*"))),
            total_lines_of_code=total_lines,
            recent_changes=self._pending_changes[-50:],
            last_build=self._builds[-1] if self._builds else None,
            builds_today=sum(
                1 for b in self._builds
                if b.started_at.date() == datetime.now().date()
            ),
            build_success_rate=success_rate,
            active_errors=active_errors,
            warnings=warnings,
            error_trends=await self.get_error_trends(days=7),
            performance_metrics=self._metrics[-20:],
            velocity=await self.get_velocity(),
            unity_version=unity_version,
        )

    async def _get_unity_version(self) -> str:
        """Get Unity version from project settings."""
        settings_path = self.project_path / "ProjectSettings" / "ProjectSettings.asset"
        if settings_path.exists():
            try:
                content = settings_path.read_text()
                match = re.search(r"m_EditorVersion:\s*(.+)", content)
                if match:
                    return match.group(1).strip()
            except Exception:
                pass
        return "Unknown"

    async def _snapshot_loop(self):
        """Background task to create periodic snapshots."""
        while self._running:
            await asyncio.sleep(self.snapshot_interval)
            try:
                self._current_snapshot = await self._create_snapshot()
                await self._store_snapshot(self._current_snapshot)
                await self._notify_state_change()
            except Exception as e:
                logger.error(f"Snapshot loop error: {e}")

    async def _file_watcher(self):
        """Background task to watch for file changes."""
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
        except ImportError:
            logger.warning("watchdog not installed, file watching disabled")
            return

        class ChangeHandler(FileSystemEventHandler):
            def __init__(handler_self, tracker):
                handler_self.tracker = tracker

            def _handle(handler_self, event, change_type):
                if not event.is_directory:
                    path = Path(event.src_path)
                    if path.suffix in {".cs", ".unity", ".prefab", ".mat", ".asset"}:
                        change = FileChange(
                            path=str(path),
                            change_type=change_type,
                            timestamp=datetime.now(),
                        )
                        handler_self.tracker._pending_changes.append(change)
                        asyncio.create_task(
                            handler_self.tracker._process_change(change)
                        )

            def on_created(handler_self, event):
                handler_self._handle(event, ChangeType.CREATED)

            def on_modified(handler_self, event):
                handler_self._handle(event, ChangeType.MODIFIED)

            def on_deleted(handler_self, event):
                handler_self._handle(event, ChangeType.DELETED)

        handler = ChangeHandler(self)
        observer = Observer()
        observer.schedule(
            handler,
            str(self.project_path / "Assets"),
            recursive=True
        )
        observer.start()

        while self._running:
            await asyncio.sleep(1)

        observer.stop()
        observer.join()

    async def _process_change(self, change: FileChange):
        """Process a file change with debouncing."""
        # Cancel existing debounce task
        if self._change_task:
            self._change_task.cancel()

        # Create new debounce task
        self._change_task = asyncio.create_task(
            self._debounced_extract(change.path)
        )

    async def _debounced_extract(self, path: str):
        """Extract knowledge after debounce period."""
        await asyncio.sleep(self.change_debounce)

        if self.extractor and os.path.exists(path):
            try:
                file_path = Path(path)
                if file_path.suffix == ".cs":
                    await self.extractor._extract_script(
                        file_path, self.project_path
                    )
                elif file_path.suffix == ".unity":
                    await self.extractor._extract_scene(
                        file_path, self.project_path
                    )
                elif file_path.suffix == ".prefab":
                    await self.extractor._extract_prefab(
                        file_path, self.project_path
                    )

                logger.debug(f"Extracted: {path}")
            except Exception as e:
                logger.error(f"Extraction failed for {path}: {e}")

    async def _notify_state_change(self):
        """Notify callbacks of state change."""
        if not self._current_snapshot:
            return

        for callback in self._on_state_change:
            try:
                callback(self._current_snapshot)
            except Exception as e:
                logger.error(f"State change callback failed: {e}")

    async def _store_snapshot(self, snapshot: ProjectSnapshot):
        """Store snapshot in Qdrant."""
        content = f"""
Project Snapshot: {snapshot.timestamp.isoformat()}
State: {snapshot.state.value}
Scripts: {snapshot.total_scripts}
Scenes: {snapshot.total_scenes}
Prefabs: {snapshot.total_prefabs}
Lines of Code: {snapshot.total_lines_of_code}
Active Errors: {snapshot.active_errors}
Build Success Rate: {snapshot.build_success_rate:.0%}
"""

        await self.qdrant.aadd_documents(
            documents=[{
                "page_content": content,
                "metadata": {
                    "entity_type": "project_snapshot",
                    "timestamp": snapshot.timestamp.isoformat(),
                    "state": snapshot.state.value,
                    **asdict(snapshot),
                }
            }],
            ids=[f"snapshot:{snapshot.project_id}:{snapshot.timestamp.isoformat()}"]
        )

    async def _store_build_info(self, build: BuildInfo):
        """Store build information in Qdrant."""
        content = f"""
Build: {build.build_id}
Target: {build.target}
Status: {build.status.value}
Duration: {build.duration_seconds:.1f}s
Errors: {len(build.errors)}
Warnings: {len(build.warnings)}
"""

        await self.qdrant.aadd_documents(
            documents=[{
                "page_content": content,
                "metadata": {
                    "entity_type": "build_log",
                    "build_id": build.build_id,
                    "status": build.status.value,
                    "target": build.target,
                    "duration": build.duration_seconds,
                    "error_count": len(build.errors),
                    "warning_count": len(build.warnings),
                }
            }],
            ids=[f"build:{self.project_id}:{build.build_id}"]
        )

    async def _store_metrics_batch(self):
        """Store accumulated metrics in Qdrant."""
        if not self._metrics:
            return

        # Group by metric name
        by_name = defaultdict(list)
        for metric in self._metrics[-100:]:
            by_name[metric.name].append(metric)

        for name, metrics in by_name.items():
            values = [m.value for m in metrics]
            content = f"""
Performance Metric: {name}
Average: {sum(values) / len(values):.2f} {metrics[0].unit}
Min: {min(values):.2f}
Max: {max(values):.2f}
Samples: {len(values)}
"""

            await self.qdrant.aadd_documents(
                documents=[{
                    "page_content": content,
                    "metadata": {
                        "entity_type": "performance_metric",
                        "metric_name": name,
                        "avg_value": sum(values) / len(values),
                        "min_value": min(values),
                        "max_value": max(values),
                        "unit": metrics[0].unit,
                        "sample_count": len(values),
                    }
                }],
                ids=[f"metric:{self.project_id}:{name}:{datetime.now().isoformat()}"]
            )
