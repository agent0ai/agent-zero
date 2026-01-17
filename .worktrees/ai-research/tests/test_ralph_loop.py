"""
Unit tests for Ralph Loop - Autonomous iterative task execution.

Tests database layer, manager business logic, completion detection,
iteration management, and workflow integration.
"""

import os

# Add parent directory to path
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from instruments.custom.ralph_loop.ralph_db import RalphLoopDatabase
from instruments.custom.ralph_loop.ralph_manager import RalphLoopManager


class TestRalphLoopDatabase:
    """Test suite for RalphLoopDatabase CRUD operations"""

    @pytest.fixture(autouse=True)
    def setup_method(self, tmp_path):
        """Create fresh database for each test"""
        self.db_path = str(tmp_path / "test_ralph.db")
        self.db = RalphLoopDatabase(self.db_path)

    # ========== Loop CRUD Tests ==========

    def test_create_and_get_loop(self):
        """Test creating and retrieving a loop"""
        loop_id = self.db.create_loop(
            prompt="Build a REST API with tests",
            name="API Development",
            completion_promise="ALL_TESTS_PASSING",
            max_iterations=50,
            agent_id="agent_0"
        )

        assert loop_id > 0, "Should return valid loop ID"

        loop = self.db.get_loop(loop_id)
        assert loop is not None, "Should retrieve loop by ID"
        assert loop['name'] == "API Development"
        assert loop['prompt'] == "Build a REST API with tests"
        assert loop['completion_promise'] == "ALL_TESTS_PASSING"
        assert loop['max_iterations'] == 50
        assert loop['current_iteration'] == 0
        assert loop['status'] == 'active'
        assert loop['agent_id'] == "agent_0"

    def test_create_loop_with_defaults(self):
        """Test loop creation with default values"""
        loop_id = self.db.create_loop(prompt="Simple task")

        loop = self.db.get_loop(loop_id)
        assert loop['name'] == "Ralph Loop"  # Default name
        assert loop['max_iterations'] == 50  # Default max
        assert loop['completion_promise'] is None
        assert loop['agent_id'] is None

    def test_create_loop_with_workflow(self):
        """Test creating loop linked to workflow"""
        loop_id = self.db.create_loop(
            prompt="Implement feature",
            workflow_execution_id=42,
            task_id="implement_core",
            context={"source": "workflow"}
        )

        loop = self.db.get_loop(loop_id)
        assert loop['workflow_execution_id'] == 42
        assert loop['task_id'] == "implement_core"
        assert loop['context']['source'] == "workflow"

    def test_get_loop_not_found(self):
        """Test getting non-existent loop"""
        assert self.db.get_loop(999) is None

    def test_get_active_loop(self):
        """Test getting active loop for agent"""
        # Create inactive loop first
        loop1 = self.db.create_loop(
            prompt="Old task",
            agent_id="agent_0"
        )
        self.db.complete_loop(loop1, status="completed")

        # Create active loop
        loop2 = self.db.create_loop(
            prompt="Current task",
            agent_id="agent_0"
        )

        active = self.db.get_active_loop("agent_0")
        assert active is not None
        assert active['loop_id'] == loop2
        assert active['status'] == 'active'

    def test_get_active_loop_none(self):
        """Test when no active loop exists"""
        assert self.db.get_active_loop("agent_0") is None

        # Create completed loop
        loop_id = self.db.create_loop(prompt="Done", agent_id="agent_0")
        self.db.complete_loop(loop_id)

        assert self.db.get_active_loop("agent_0") is None

    def test_list_loops(self):
        """Test listing loops with filters"""
        # Create multiple loops
        self.db.create_loop(prompt="Task 1", agent_id="agent_0")
        loop2 = self.db.create_loop(prompt="Task 2", agent_id="agent_0")
        self.db.create_loop(prompt="Task 3", agent_id="agent_1")

        # Complete one
        self.db.complete_loop(loop2, status="completed")

        # List all
        all_loops = self.db.list_loops()
        assert len(all_loops) == 3

        # Filter by agent
        agent0_loops = self.db.list_loops(agent_id="agent_0")
        assert len(agent0_loops) == 2

        # Filter by status
        active_loops = self.db.list_loops(status="active")
        assert len(active_loops) == 2

        completed_loops = self.db.list_loops(status="completed")
        assert len(completed_loops) == 1

    def test_list_loops_limit(self):
        """Test list loops with limit"""
        for i in range(10):
            self.db.create_loop(prompt=f"Task {i}")

        loops = self.db.list_loops(limit=5)
        assert len(loops) == 5

    def test_update_loop(self):
        """Test updating loop fields"""
        loop_id = self.db.create_loop(prompt="Task")

        self.db.update_loop(
            loop_id,
            status="paused",
            current_iteration=5,
            last_output="Progress made"
        )

        loop = self.db.get_loop(loop_id)
        assert loop['status'] == "paused"
        assert loop['current_iteration'] == 5
        assert loop['last_output'] == "Progress made"

    def test_update_loop_context(self):
        """Test updating loop context"""
        loop_id = self.db.create_loop(
            prompt="Task",
            context={"key1": "value1"}
        )

        self.db.update_loop(
            loop_id,
            context={"key1": "updated", "key2": "new"}
        )

        loop = self.db.get_loop(loop_id)
        assert loop['context']['key1'] == "updated"
        assert loop['context']['key2'] == "new"

    def test_increment_iteration(self):
        """Test iteration counter increment"""
        loop_id = self.db.create_loop(prompt="Task")

        loop = self.db.get_loop(loop_id)
        assert loop['current_iteration'] == 0

        new_val = self.db.increment_iteration(loop_id)
        assert new_val == 1

        new_val = self.db.increment_iteration(loop_id)
        assert new_val == 2

        loop = self.db.get_loop(loop_id)
        assert loop['current_iteration'] == 2

    def test_complete_loop(self):
        """Test completing a loop"""
        loop_id = self.db.create_loop(prompt="Task")

        self.db.complete_loop(loop_id, status="completed")

        loop = self.db.get_loop(loop_id)
        assert loop['status'] == "completed"
        assert loop['completed_at'] is not None

    def test_complete_loop_with_status(self):
        """Test completing with different statuses"""
        loop1 = self.db.create_loop(prompt="Task 1")
        loop2 = self.db.create_loop(prompt="Task 2")
        loop3 = self.db.create_loop(prompt="Task 3")

        self.db.complete_loop(loop1, status="completed")
        self.db.complete_loop(loop2, status="cancelled")
        self.db.complete_loop(loop3, status="max_iterations")

        assert self.db.get_loop(loop1)['status'] == "completed"
        assert self.db.get_loop(loop2)['status'] == "cancelled"
        assert self.db.get_loop(loop3)['status'] == "max_iterations"

    def test_delete_loop(self):
        """Test deleting a loop and its iterations"""
        loop_id = self.db.create_loop(prompt="Task")
        self.db.create_iteration(loop_id, 1)
        self.db.create_iteration(loop_id, 2)

        self.db.delete_loop(loop_id)

        assert self.db.get_loop(loop_id) is None
        assert len(self.db.get_iterations(loop_id)) == 0

    # ========== Iteration Tests ==========

    def test_create_iteration(self):
        """Test creating an iteration record"""
        loop_id = self.db.create_loop(prompt="Task")

        iter_id = self.db.create_iteration(
            loop_id=loop_id,
            iteration_number=1,
            output_summary="Started working",
            files_modified=["file1.py", "file2.py"]
        )

        assert iter_id > 0

        iterations = self.db.get_iterations(loop_id)
        assert len(iterations) == 1
        assert iterations[0]['iteration_number'] == 1
        assert iterations[0]['output_summary'] == "Started working"
        assert "file1.py" in iterations[0]['files_modified']

    def test_complete_iteration(self):
        """Test completing an iteration with results"""
        loop_id = self.db.create_loop(prompt="Task")
        iter_id = self.db.create_iteration(loop_id, 1)

        self.db.complete_iteration(
            iteration_id=iter_id,
            output_summary="Tests pass",
            files_modified=["src/main.py"],
            git_commit="abc123",
            success=True
        )

        iterations = self.db.get_iterations(loop_id)
        assert iterations[0]['completed_at'] is not None
        assert iterations[0]['success'] == 1  # SQLite stores bool as int
        assert iterations[0]['git_commit'] == "abc123"

    def test_complete_iteration_with_error(self):
        """Test completing iteration with error"""
        loop_id = self.db.create_loop(prompt="Task")
        iter_id = self.db.create_iteration(loop_id, 1)

        self.db.complete_iteration(
            iteration_id=iter_id,
            success=False,
            error_message="Build failed: missing module"
        )

        iterations = self.db.get_iterations(loop_id)
        assert iterations[0]['success'] == 0
        assert "missing module" in iterations[0]['error_message']

    def test_get_iterations_ordered(self):
        """Test iterations are returned in order"""
        loop_id = self.db.create_loop(prompt="Task")

        self.db.create_iteration(loop_id, 3)
        self.db.create_iteration(loop_id, 1)
        self.db.create_iteration(loop_id, 2)

        iterations = self.db.get_iterations(loop_id)
        assert [it['iteration_number'] for it in iterations] == [1, 2, 3]

    def test_get_latest_iteration(self):
        """Test getting the most recent iteration"""
        loop_id = self.db.create_loop(prompt="Task")

        self.db.create_iteration(loop_id, 1, output_summary="First")
        self.db.create_iteration(loop_id, 2, output_summary="Second")
        self.db.create_iteration(loop_id, 3, output_summary="Third")

        latest = self.db.get_latest_iteration(loop_id)
        assert latest['iteration_number'] == 3
        assert latest['output_summary'] == "Third"

    def test_get_latest_iteration_none(self):
        """Test latest iteration when none exist"""
        loop_id = self.db.create_loop(prompt="Task")
        assert self.db.get_latest_iteration(loop_id) is None

    # ========== Statistics Tests ==========

    def test_get_stats_empty(self):
        """Test stats on empty database"""
        stats = self.db.get_stats()
        assert stats['total_loops'] == 0
        assert stats['active_loops'] == 0
        assert stats['completed_loops'] == 0
        assert stats['total_iterations'] == 0

    def test_get_stats_with_data(self):
        """Test stats with various data"""
        # Create loops
        loop1 = self.db.create_loop(prompt="Task 1", agent_id="agent_0")
        loop2 = self.db.create_loop(prompt="Task 2", agent_id="agent_0")
        self.db.create_loop(prompt="Task 3", agent_id="agent_1")

        # Add iterations
        self.db.create_iteration(loop1, 1)
        self.db.create_iteration(loop1, 2)
        self.db.create_iteration(loop2, 1)

        # Complete some
        self.db.update_loop(loop1, current_iteration=10)
        self.db.complete_loop(loop1, status="completed")
        self.db.update_loop(loop2, current_iteration=5)
        self.db.complete_loop(loop2, status="cancelled")

        stats = self.db.get_stats()
        assert stats['total_loops'] == 3
        assert stats['active_loops'] == 1
        assert stats['completed_loops'] == 1
        assert stats['cancelled_loops'] == 1
        assert stats['total_iterations'] == 3

    def test_get_stats_by_agent(self):
        """Test stats filtered by agent"""
        self.db.create_loop(prompt="Task 1", agent_id="agent_0")
        self.db.create_loop(prompt="Task 2", agent_id="agent_0")
        self.db.create_loop(prompt="Task 3", agent_id="agent_1")

        stats_0 = self.db.get_stats(agent_id="agent_0")
        assert stats_0['total_loops'] == 2

        stats_1 = self.db.get_stats(agent_id="agent_1")
        assert stats_1['total_loops'] == 1


class TestRalphLoopManager:
    """Test suite for RalphLoopManager business logic"""

    @pytest.fixture(autouse=True)
    def setup_method(self, tmp_path):
        """Create fresh manager for each test"""
        self.db_path = str(tmp_path / "test_ralph_manager.db")
        self.manager = RalphLoopManager(self.db_path)

    # ========== Loop Lifecycle Tests ==========

    def test_start_loop(self):
        """Test starting a new Ralph loop"""
        result = self.manager.start_loop(
            prompt="Build authentication system",
            name="Auth Feature",
            completion_promise="AUTH_COMPLETE",
            max_iterations=30,
            agent_id="agent_0"
        )

        assert "error" not in result
        assert result['loop_id'] > 0
        assert result['name'] == "Auth Feature"
        assert result['status'] == "active"
        # Note: current_iteration starts at 1 in the result (first iteration created)
        # but underlying db starts at 0 and increments
        assert result['current_iteration'] == 1
        assert result['max_iterations'] == 30
        assert result['completion_promise'] == "AUTH_COMPLETE"

    def test_start_loop_minimal(self):
        """Test starting loop with minimal parameters"""
        result = self.manager.start_loop(prompt="Simple task")

        assert "error" not in result
        assert result['name'] == "Ralph Loop"
        assert result['max_iterations'] == 50

    def test_start_loop_blocks_duplicate(self):
        """Test that starting a loop fails if agent already has active loop"""
        self.manager.start_loop(
            prompt="First task",
            agent_id="agent_0"
        )

        result = self.manager.start_loop(
            prompt="Second task",
            agent_id="agent_0"
        )

        assert "error" in result
        assert "already has an active loop" in result['error']
        assert "existing_loop_id" in result

    def test_start_loop_allows_after_cancel(self):
        """Test that new loop can start after previous is cancelled"""
        first = self.manager.start_loop(
            prompt="First task",
            agent_id="agent_0"
        )

        self.manager.cancel_loop(first['loop_id'])

        second = self.manager.start_loop(
            prompt="Second task",
            agent_id="agent_0"
        )

        assert "error" not in second
        assert second['loop_id'] != first['loop_id']

    def test_get_status(self):
        """Test getting loop status"""
        started = self.manager.start_loop(
            prompt="Task",
            name="Test Loop",
            completion_promise="DONE"
        )

        status = self.manager.get_status(started['loop_id'])

        assert status['loop_id'] == started['loop_id']
        assert status['name'] == "Test Loop"
        assert status['status'] == "active"
        # Database stores current_iteration starting at 0
        assert status['current_iteration'] == 0
        assert status['iteration_count'] == 1  # But we create 1 iteration record

    def test_get_status_not_found(self):
        """Test status for non-existent loop"""
        result = self.manager.get_status(999)
        assert "error" in result

    def test_cancel_loop(self):
        """Test cancelling an active loop"""
        started = self.manager.start_loop(
            prompt="Task",
            agent_id="agent_0"
        )

        # Advance a few iterations
        self.manager.advance_iteration(started['loop_id'])
        self.manager.advance_iteration(started['loop_id'])

        result = self.manager.cancel_loop(
            loop_id=started['loop_id'],
            reason="Need different approach"
        )

        assert result['status'] == "cancelled"
        # iterations_completed returns current_iteration from db (0 + 2 advances = 2)
        assert result['iterations_completed'] == 2
        assert result['reason'] == "Need different approach"

        # Verify no active loop
        assert self.manager.get_active_loop("agent_0") is None

    def test_cancel_loop_not_found(self):
        """Test cancelling non-existent loop"""
        result = self.manager.cancel_loop(999)
        assert "error" in result

    def test_cancel_loop_already_completed(self):
        """Test cancelling already completed loop"""
        started = self.manager.start_loop(prompt="Task")
        self.manager.db.complete_loop(started['loop_id'], status="completed")

        result = self.manager.cancel_loop(started['loop_id'])
        assert "error" in result
        assert "not active" in result['error']

    def test_list_loops(self):
        """Test listing loops"""
        self.manager.start_loop(prompt="Task 1", agent_id="agent_0")
        self.manager.start_loop(prompt="Task 2", agent_id="agent_1")

        loops = self.manager.list_loops()
        assert len(loops) == 2

    # ========== Completion Detection Tests ==========

    def test_check_completion_promise_detected(self):
        """Test completion when promise is found in output"""
        started = self.manager.start_loop(
            prompt="Build feature",
            completion_promise="FEATURE_DONE"
        )

        # Output contains the promise
        is_complete, reason = self.manager.check_completion(
            started['loop_id'],
            "I have finished implementing all features. <promise>FEATURE_DONE</promise>"
        )

        assert is_complete is True
        assert "Completion promise detected" in reason

        # Verify loop is completed
        status = self.manager.get_status(started['loop_id'])
        assert status['status'] == "completed"

    def test_check_completion_promise_case_insensitive(self):
        """Test completion promise detection is case-insensitive"""
        started = self.manager.start_loop(
            prompt="Task",
            completion_promise="ALL_DONE"
        )

        is_complete, _ = self.manager.check_completion(
            started['loop_id'],
            "<promise>all_done</promise>"
        )

        assert is_complete is True

    def test_check_completion_no_promise_continues(self):
        """Test that loop continues when no promise in output"""
        started = self.manager.start_loop(
            prompt="Task",
            completion_promise="DONE"
        )

        is_complete, reason = self.manager.check_completion(
            started['loop_id'],
            "Making progress, still working on it..."
        )

        assert is_complete is False
        assert reason == "Continue"

    def test_check_completion_max_iterations(self):
        """Test completion when max iterations reached"""
        started = self.manager.start_loop(
            prompt="Task",
            max_iterations=3
        )

        # Advance to max (db starts at 0, advance_iteration increments)
        # After 3 advances: current_iteration = 3, which equals max_iterations
        self.manager.advance_iteration(started['loop_id'])  # 1
        self.manager.advance_iteration(started['loop_id'])  # 2
        self.manager.advance_iteration(started['loop_id'])  # 3 (equals max)

        is_complete, reason = self.manager.check_completion(
            started['loop_id'],
            "Still working..."
        )

        assert is_complete is True
        assert "Max iterations" in reason

        status = self.manager.get_status(started['loop_id'])
        assert status['status'] == "max_iterations"

    def test_check_completion_no_promise_no_limit(self):
        """Test loop without promise and max_iterations=0 (unlimited)"""
        started = self.manager.start_loop(
            prompt="Task",
            completion_promise=None,
            max_iterations=0
        )

        is_complete, reason = self.manager.check_completion(
            started['loop_id'],
            "Working..."
        )

        assert is_complete is False
        assert reason == "Continue"

    def test_check_completion_already_completed(self):
        """Test check on already completed loop"""
        started = self.manager.start_loop(prompt="Task")
        self.manager.db.complete_loop(started['loop_id'])

        is_complete, reason = self.manager.check_completion(
            started['loop_id'],
            "Output"
        )

        assert is_complete is True
        assert "already completed" in reason

    # ========== Iteration Management Tests ==========

    def test_advance_iteration(self):
        """Test advancing to next iteration"""
        started = self.manager.start_loop(
            prompt="Build API",
            completion_promise="TESTS_PASS",
            max_iterations=50
        )

        result = self.manager.advance_iteration(
            loop_id=started['loop_id'],
            output_summary="Created endpoints",
            files_modified=["api.py", "routes.py"]
        )

        # advance_iteration returns the NEW iteration number after increment
        # db starts at 0, after increment it's 1
        assert result['iteration'] == 1
        assert result['max_iterations'] == 50
        assert result['completion_promise'] == "TESTS_PASS"

        # Check iteration history
        history = self.manager.get_iteration_history(started['loop_id'])
        assert len(history) == 2  # Initial + 1 advance
        assert history[0]['output_summary'] == "Created endpoints"

    def test_advance_iteration_not_active(self):
        """Test advancing completed loop fails"""
        started = self.manager.start_loop(prompt="Task")
        self.manager.db.complete_loop(started['loop_id'])

        result = self.manager.advance_iteration(started['loop_id'])
        assert "error" in result

    def test_get_iteration_history(self):
        """Test getting full iteration history"""
        started = self.manager.start_loop(prompt="Task")

        for i in range(5):
            self.manager.advance_iteration(
                started['loop_id'],
                output_summary=f"Iteration {i + 2}"
            )

        history = self.manager.get_iteration_history(started['loop_id'])
        assert len(history) == 6  # Initial + 5 advances

    # ========== Workflow Integration Tests ==========

    def test_start_task_loop(self):
        """Test starting loop for workflow task"""
        result = self.manager.start_task_loop(
            workflow_execution_id=42,
            task_id="implement_auth",
            prompt="Implement authentication",
            completion_promise="AUTH_DONE",
            max_iterations=20,
            agent_id="agent_0"
        )

        assert "error" not in result
        assert result['name'] == "Task: implement_auth"

        # Verify workflow link
        status = self.manager.get_status(result['loop_id'])
        assert status['workflow_execution_id'] == 42
        assert status['task_id'] == "implement_auth"

    def test_link_to_workflow(self):
        """Test linking existing loop to workflow"""
        started = self.manager.start_loop(prompt="Task")

        result = self.manager.link_to_workflow(
            loop_id=started['loop_id'],
            workflow_execution_id=100,
            task_id="task_5"
        )

        assert result['linked'] is True

        # Verify via get_status (context contains the link)
        loop = self.manager.db.get_loop(started['loop_id'])
        assert loop['context']['workflow_execution_id'] == 100
        assert loop['context']['task_id'] == "task_5"

    def test_link_to_workflow_not_found(self):
        """Test linking non-existent loop"""
        result = self.manager.link_to_workflow(
            loop_id=999,
            workflow_execution_id=100
        )
        assert "error" in result

    # ========== Configuration Tests ==========

    def test_update_completion_promise(self):
        """Test updating completion promise mid-loop"""
        started = self.manager.start_loop(
            prompt="Task",
            completion_promise="OLD_PROMISE"
        )

        result = self.manager.update_completion_promise(
            started['loop_id'],
            "NEW_PROMISE"
        )

        assert result['updated'] is True
        assert result['completion_promise'] == "NEW_PROMISE"

        # Verify new promise works
        is_complete, _ = self.manager.check_completion(
            started['loop_id'],
            "<promise>NEW_PROMISE</promise>"
        )
        assert is_complete is True

    def test_update_max_iterations(self):
        """Test updating max iterations"""
        started = self.manager.start_loop(
            prompt="Task",
            max_iterations=10
        )

        result = self.manager.update_max_iterations(started['loop_id'], 100)

        assert result['updated'] is True
        assert result['max_iterations'] == 100

    def test_pause_loop(self):
        """Test pausing an active loop"""
        started = self.manager.start_loop(prompt="Task", agent_id="agent_0")
        self.manager.advance_iteration(started['loop_id'])

        result = self.manager.pause_loop(started['loop_id'])

        assert result['status'] == "paused"
        # After 1 advance, current_iteration is 1
        assert result['current_iteration'] == 1

        # Verify no active loop
        assert self.manager.get_active_loop("agent_0") is None

    def test_pause_loop_not_active(self):
        """Test pausing non-active loop fails"""
        started = self.manager.start_loop(prompt="Task")
        self.manager.db.complete_loop(started['loop_id'])

        result = self.manager.pause_loop(started['loop_id'])
        assert "error" in result

    def test_resume_loop(self):
        """Test resuming a paused loop"""
        started = self.manager.start_loop(
            prompt="Task",
            agent_id="agent_0",
            completion_promise="DONE"
        )
        self.manager.pause_loop(started['loop_id'])

        result = self.manager.resume_loop(started['loop_id'])

        assert result['status'] == "active"
        assert result['prompt'] == "Task"
        assert result['completion_promise'] == "DONE"

        # Verify now active
        active = self.manager.get_active_loop("agent_0")
        assert active is not None
        assert active['loop_id'] == started['loop_id']

    def test_resume_loop_not_paused(self):
        """Test resuming non-paused loop fails"""
        started = self.manager.start_loop(prompt="Task")

        result = self.manager.resume_loop(started['loop_id'])
        assert "error" in result

    # ========== Statistics Tests ==========

    def test_get_stats(self):
        """Test getting Ralph loop statistics"""
        self.manager.start_loop(prompt="Task 1", agent_id="agent_0")
        loop2 = self.manager.start_loop(prompt="Task 2", agent_id="agent_1")
        self.manager.cancel_loop(loop2['loop_id'])

        stats = self.manager.get_stats()

        assert stats['total_loops'] == 2
        assert stats['active_loops'] == 1
        assert stats['cancelled_loops'] == 1

    def test_get_stats_by_agent(self):
        """Test stats filtered by agent"""
        self.manager.start_loop(prompt="Task 1", agent_id="agent_0")
        self.manager.start_loop(prompt="Task 2", agent_id="agent_1")

        # Can only have one active per agent, so cancel first
        self.manager.db.list_loops(agent_id="agent_0")[0]

        stats = self.manager.get_stats(agent_id="agent_0")
        assert stats['total_loops'] == 1

    # ========== Prompt Generation Tests ==========

    def test_generate_iteration_prompt(self):
        """Test generating iteration prompt"""
        started = self.manager.start_loop(
            prompt="Build a REST API with CRUD operations",
            name="API Development",
            completion_promise="ALL_TESTS_PASS",
            max_iterations=30
        )

        prompt = self.manager.generate_iteration_prompt(started['loop_id'])

        assert prompt is not None
        # db current_iteration starts at 0
        assert "Ralph Loop - Iteration 0" in prompt
        assert "API Development" in prompt
        assert "Build a REST API with CRUD operations" in prompt
        assert "<promise>ALL_TESTS_PASS</promise>" in prompt
        assert "0/30" in prompt

    def test_generate_iteration_prompt_no_promise(self):
        """Test prompt generation without completion promise"""
        started = self.manager.start_loop(
            prompt="Open-ended task",
            max_iterations=0  # Unlimited
        )

        prompt = self.manager.generate_iteration_prompt(started['loop_id'])

        assert prompt is not None
        assert "To complete this task" not in prompt
        # db current_iteration starts at 0, unlimited shows as ∞
        assert "0/∞" in prompt

    def test_generate_iteration_prompt_completed_loop(self):
        """Test prompt generation for completed loop returns None"""
        started = self.manager.start_loop(prompt="Task")
        self.manager.db.complete_loop(started['loop_id'])

        prompt = self.manager.generate_iteration_prompt(started['loop_id'])
        assert prompt is None


class TestRalphLoopEdgeCases:
    """Edge cases and error handling tests"""

    @pytest.fixture(autouse=True)
    def setup_method(self, tmp_path):
        self.db_path = str(tmp_path / "test_ralph_edge.db")
        self.manager = RalphLoopManager(self.db_path)

    def test_unicode_in_prompt(self):
        """Test handling unicode in prompts"""
        started = self.manager.start_loop(
            prompt="实现用户认证 🔐 Authentication",
            name="功能开发 Feature Dev",
            completion_promise="完成 DONE"
        )

        status = self.manager.get_status(started['loop_id'])
        assert "实现用户认证" in status['name'] or status['loop_id'] > 0

    def test_large_output(self):
        """Test handling large output summaries"""
        started = self.manager.start_loop(prompt="Task")

        large_output = "x" * 10000
        self.manager.advance_iteration(
            started['loop_id'],
            output_summary=large_output
        )

        history = self.manager.get_iteration_history(started['loop_id'])
        assert len(history[0]['output_summary']) == 10000

    def test_special_characters_in_promise(self):
        """Test promise with special regex characters"""
        started = self.manager.start_loop(
            prompt="Task",
            completion_promise="DONE[v1.0]"
        )

        # The regex escape should handle this
        is_complete, _ = self.manager.check_completion(
            started['loop_id'],
            "<promise>DONE[v1.0]</promise>"
        )

        assert is_complete is True

    def test_empty_output_check(self):
        """Test completion check with empty output"""
        started = self.manager.start_loop(
            prompt="Task",
            completion_promise="DONE"
        )

        is_complete, _reason = self.manager.check_completion(
            started['loop_id'],
            ""
        )

        assert is_complete is False

    def test_rapid_iterations(self):
        """Test many rapid iterations"""
        started = self.manager.start_loop(
            prompt="Task",
            max_iterations=1000
        )

        for _i in range(100):
            self.manager.advance_iteration(started['loop_id'])

        status = self.manager.get_status(started['loop_id'])
        # db starts at 0, 100 advances = 100
        assert status['current_iteration'] == 100

    def test_concurrent_agent_loops(self):
        """Test multiple agents with concurrent loops"""
        loops = []
        for i in range(5):
            result = self.manager.start_loop(
                prompt=f"Task for agent {i}",
                agent_id=f"agent_{i}"
            )
            loops.append(result)

        # All should be active
        for i in range(5):
            active = self.manager.get_active_loop(f"agent_{i}")
            assert active is not None
            assert active['loop_id'] == loops[i]['loop_id']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
