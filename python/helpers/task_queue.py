"""
Task Queue Manager for Parallel Agent Delegation

Manages parallel task execution, dependencies, and resource coordination.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from collections import defaultdict
import uuid


class TaskStatus(Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """Represents a single task in the queue."""
    id: str
    message: str
    profile: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    agent: Optional[Any] = None  # Agent instance assigned to this task


@dataclass
class TaskGroup:
    """Represents a group of related tasks."""
    id: str
    tasks: List[Task] = field(default_factory=list)
    wait_for_all: bool = True
    timeout: Optional[float] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None


class TaskQueue:
    """
    Manages a queue of tasks with dependency resolution and parallel execution.
    """

    def __init__(self, max_concurrent: int = 5):
        """
        Initialize the task queue.

        Args:
            max_concurrent: Maximum number of tasks to run concurrently
        """
        self.max_concurrent = max_concurrent
        self.tasks: Dict[str, Task] = {}
        self.task_groups: Dict[str, TaskGroup] = {}
        self.running_tasks: Set[str] = set()
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self._lock = asyncio.Lock()

    def add_task(
        self,
        task_id: str,
        message: str,
        profile: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Task:
        """
        Add a task to the queue.

        Args:
            task_id: Unique identifier for the task
            message: Task message/description
            profile: Agent profile to use (optional)
            dependencies: List of task IDs this task depends on
            metadata: Additional metadata for the task

        Returns:
            Created Task object
        """
        if task_id in self.tasks:
            raise ValueError(f"Task {task_id} already exists")

        task = Task(
            id=task_id,
            message=message,
            profile=profile,
            dependencies=dependencies or [],
            metadata=metadata or {},
        )

        self.tasks[task_id] = task

        # Build dependency graph
        for dep_id in task.dependencies:
            if dep_id not in self.tasks:
                raise ValueError(f"Dependency {dep_id} does not exist")
            self.dependency_graph[task_id].add(dep_id)
            self.reverse_dependency_graph[dep_id].add(task_id)

        return task

    def add_task_group(
        self,
        tasks: List[Dict[str, Any]],
        wait_for_all: bool = True,
        timeout: Optional[float] = None,
    ) -> TaskGroup:
        """
        Add a group of tasks to the queue.

        Args:
            tasks: List of task dictionaries with id, message, profile, dependencies
            wait_for_all: Whether to wait for all tasks to complete
            timeout: Maximum time to wait for completion (seconds)

        Returns:
            Created TaskGroup object
        """
        group_id = str(uuid.uuid4())
        group = TaskGroup(id=group_id, wait_for_all=wait_for_all, timeout=timeout)

        # Add all tasks to the group
        for task_data in tasks:
            task_id = task_data.get("id", str(uuid.uuid4()))
            task = self.add_task(
                task_id=task_id,
                message=task_data["message"],
                profile=task_data.get("profile"),
                dependencies=task_data.get("dependencies", []),
                metadata=task_data.get("metadata", {}),
            )
            group.tasks.append(task)

        self.task_groups[group_id] = group
        return group

    def _get_ready_tasks(self) -> List[Task]:
        """Get tasks that are ready to run (dependencies satisfied)."""
        ready = []
        for task in self.tasks.values():
            if task.status == TaskStatus.PENDING:
                # Check if all dependencies are completed
                deps_satisfied = all(
                    self.tasks[dep_id].status == TaskStatus.COMPLETED
                    for dep_id in task.dependencies
                )
                if deps_satisfied:
                    ready.append(task)
        return ready

    def _update_task_status(
        self, task_id: str, status: TaskStatus, result: Optional[str] = None, error: Optional[str] = None
    ):
        """Update task status and handle dependent tasks."""
        task = self.tasks.get(task_id)
        if not task:
            return

        task.status = status
        if status == TaskStatus.RUNNING:
            task.started_at = datetime.now(timezone.utc)
            self.running_tasks.add(task_id)
        elif status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
            task.completed_at = datetime.now(timezone.utc)
            self.running_tasks.discard(task_id)
            if result:
                task.result = result
            if error:
                task.error = error

    async def execute_task(
        self,
        task: Task,
        agent_factory: Callable[[str, Optional[str]], Any],
        execute_func: Callable[[Any, str], Any],
    ) -> str:
        """
        Execute a single task.

        Args:
            task: Task to execute
            agent_factory: Function to create an agent (config, profile) -> agent
            execute_func: Function to execute task on agent (agent, message) -> result

        Returns:
            Task result
        """
        self._update_task_status(task.id, TaskStatus.RUNNING)

        try:
            # Create agent for this task
            agent = agent_factory(task.profile)
            task.agent = agent

            # Execute task
            result = await execute_func(agent, task.message)

            self._update_task_status(task.id, TaskStatus.COMPLETED, result=result)
            return result

        except Exception as e:
            error_msg = str(e)
            self._update_task_status(task.id, TaskStatus.FAILED, error=error_msg)
            raise

    async def execute_group(
        self,
        group_id: str,
        agent_factory: Callable[[str, Optional[str]], Any],
        execute_func: Callable[[Any, str], Any],
    ) -> Dict[str, Any]:
        """
        Execute all tasks in a group with dependency resolution.

        Args:
            group_id: Task group ID
            agent_factory: Function to create agents
            execute_func: Function to execute tasks

        Returns:
            Dictionary mapping task IDs to results
        """
        group = self.task_groups.get(group_id)
        if not group:
            raise ValueError(f"Task group {group_id} not found")

        results: Dict[str, Any] = {}
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def execute_with_limit(task: Task):
            async with semaphore:
                try:
                    result = await self.execute_task(task, agent_factory, execute_func)
                    results[task.id] = {"status": "completed", "result": result}
                except Exception as e:
                    results[task.id] = {"status": "failed", "error": str(e)}

        # Execute tasks respecting dependencies
        while True:
            ready_tasks = self._get_ready_tasks()
            ready_in_group = [t for t in ready_tasks if t in group.tasks]

            if not ready_in_group:
                # Check if all tasks are done
                if all(t.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED) for t in group.tasks):
                    break
                # Wait for some tasks to complete
                await asyncio.sleep(0.1)
                continue

            # Execute ready tasks in parallel
            await asyncio.gather(*[execute_with_limit(task) for task in ready_in_group])

            if not group.wait_for_all:
                # Check if we have enough results
                completed = sum(1 for t in group.tasks if t.status == TaskStatus.COMPLETED)
                if completed > 0:
                    break

        group.completed_at = datetime.now(timezone.utc)
        return results

    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get the status of a task."""
        task = self.tasks.get(task_id)
        return task.status if task else None

    def get_group_status(self, group_id: str) -> Dict[str, Any]:
        """Get the status of a task group."""
        group = self.task_groups.get(group_id)
        if not group:
            return {}

        return {
            "id": group_id,
            "total_tasks": len(group.tasks),
            "completed": sum(1 for t in group.tasks if t.status == TaskStatus.COMPLETED),
            "failed": sum(1 for t in group.tasks if t.status == TaskStatus.FAILED),
            "running": sum(1 for t in group.tasks if t.status == TaskStatus.RUNNING),
            "pending": sum(1 for t in group.tasks if t.status == TaskStatus.PENDING),
            "tasks": {t.id: {"status": t.status.value, "result": t.result, "error": t.error} for t in group.tasks},
        }

    def cancel_task(self, task_id: str):
        """Cancel a task."""
        task = self.tasks.get(task_id)
        if task and task.status == TaskStatus.PENDING:
            self._update_task_status(task_id, TaskStatus.CANCELLED)

    def cancel_group(self, group_id: str):
        """Cancel all pending tasks in a group."""
        group = self.task_groups.get(group_id)
        if group:
            for task in group.tasks:
                if task.status == TaskStatus.PENDING:
                    self.cancel_task(task.id)

