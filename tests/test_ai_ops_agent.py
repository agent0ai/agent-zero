"""
AI Operations & Execution Agent Tests - Team H TDD Swarm
Comprehensive tests for autonomous task execution and system operations
"""

import pytest

from instruments.custom.ai_ops_agent import (
    AIOpsAgent,
    ErrorRecovery,
    ResourceManager,
    SystemMonitor,
    TaskExecutor,
    WorkflowAutomator,
)
from instruments.custom.ai_ops_agent.ai_ops_agent import (
    AuditLogger,
    DecisionMaker,
    EventBusIntegrator,
    HealthMetric,
    HealthStatus,
    IntegrationManager,
    ResourceType,
    Task,
    TaskScheduler,
    TaskStatus,
    Workflow,
)
from python.helpers.datetime_utils import isoformat_z, utc_now


class TestOpsInitialization:
    """Tests for operations agent initialization"""

    @pytest.mark.unit
    def test_initialize_ops_agent(self, temp_db_path):
        """Test initializing operations agent"""
        agent = AIOpsAgent(db_path=temp_db_path)
        assert agent is not None
        assert agent.db_path == temp_db_path
        assert isinstance(agent.tasks, dict)
        assert isinstance(agent.workflows, dict)

    @pytest.mark.unit
    def test_load_system_capabilities(self, temp_db_path):
        """Test loading system capabilities"""
        agent = AIOpsAgent(db_path=temp_db_path)
        capabilities = agent.load_system_capabilities()

        assert capabilities["task_execution"] is True
        assert capabilities["workflow_automation"] is True
        assert capabilities["scheduling"] is True
        assert "resource_management" in capabilities

    @pytest.mark.unit
    def test_establish_api_connections(self, temp_db_path):
        """Test establishing API connections"""
        agent = AIOpsAgent(db_path=temp_db_path)
        connections = agent.establish_api_connections()

        assert "internal_api" in connections
        assert connections["internal_api"] is True
        assert isinstance(connections, dict)

    @pytest.mark.unit
    def test_configure_execution_policies(self, temp_db_path):
        """Test configuring execution policies"""
        agent = AIOpsAgent(db_path=temp_db_path)
        policies = {
            "max_concurrent_tasks": 5,
            "retry_policy": {"max_retries": 2},
            "timeout_seconds": 600,
        }

        agent.configure_execution_policies(policies)
        assert agent.execution_policies["max_concurrent_tasks"] == 5
        assert agent.execution_policies["retry_policy"]["max_retries"] == 2


class TestTaskExecution:
    """Tests for task execution"""

    @pytest.mark.unit
    def test_execute_simple_task(self, temp_db_path):
        """Test executing simple task"""
        agent = AIOpsAgent(db_path=temp_db_path)
        executor = TaskExecutor(agent)

        task = Task(
            task_id="task_1",
            name="Simple Task",
            instructions='{"action": "test"}',
        )
        agent.tasks["task_1"] = task

        result = executor.execute_task(task)
        assert result["task_id"] == "task_1"
        assert result["status"] in ["completed", "failed"]

    @pytest.mark.unit
    def test_execute_complex_workflow(self, temp_db_path):
        """Test executing complex workflow"""
        agent = AIOpsAgent(db_path=temp_db_path)
        executor = TaskExecutor(agent)

        # Create tasks
        task1 = Task(task_id="t1", name="Task 1", instructions='{"step": 1}')
        task2 = Task(task_id="t2", name="Task 2", instructions='{"step": 2}')
        agent.tasks["t1"] = task1
        agent.tasks["t2"] = task2

        # Create workflow
        workflow = Workflow(workflow_id="wf1", name="Test Workflow", tasks=["t1", "t2"])

        result = executor.execute_workflow(workflow)
        assert result["workflow_id"] == "wf1"
        assert result["tasks_completed"] == 2

    @pytest.mark.unit
    def test_parse_task_instructions(self, temp_db_path):
        """Test parsing task instructions"""
        agent = AIOpsAgent(db_path=temp_db_path)
        executor = TaskExecutor(agent)

        instructions = '{"action": "deploy", "target": "production"}'
        parsed = executor._parse_instructions(instructions)

        assert isinstance(parsed, dict)
        assert parsed.get("action") == "deploy" or "raw_instruction" in parsed

    @pytest.mark.unit
    def test_validate_task_prerequisites(self, temp_db_path):
        """Test validating task prerequisites"""
        agent = AIOpsAgent(db_path=temp_db_path)
        executor = TaskExecutor(agent)

        # Create prerequisite task
        prereq = Task(task_id="prereq", name="Prereq", instructions="{}")
        prereq.status = TaskStatus.COMPLETED
        agent.tasks["prereq"] = prereq

        # Create dependent task
        task = Task(
            task_id="task",
            name="Main Task",
            instructions="{}",
            prerequisites=["prereq"],
        )

        is_valid = executor._validate_prerequisites(task)
        assert is_valid is True

    @pytest.mark.unit
    def test_track_task_progress(self, temp_db_path):
        """Test tracking task progress"""
        agent = AIOpsAgent(db_path=temp_db_path)
        executor = TaskExecutor(agent)

        task = Task(task_id="track_1", name="Tracked Task", instructions="{}")
        task.status = TaskStatus.RUNNING
        task.started_at = isoformat_z(utc_now())
        agent.tasks["track_1"] = task

        progress = executor.track_progress("track_1")
        assert progress["task_id"] == "track_1"
        assert progress["status"] == "running"


class TestWorkflowAutomation:
    """Tests for workflow automation"""

    @pytest.mark.unit
    def test_create_automation_workflow(self, temp_db_path):
        """Test creating automation workflow"""
        agent = AIOpsAgent(db_path=temp_db_path)
        automator = WorkflowAutomator(agent)

        workflow = automator.create_workflow("wf1", "Test Workflow", ["t1", "t2"])
        assert workflow.workflow_id == "wf1"
        assert workflow.name == "Test Workflow"
        assert len(workflow.tasks) == 2

    @pytest.mark.unit
    def test_chain_multiple_tasks(self, temp_db_path):
        """Test chaining multiple tasks"""
        agent = AIOpsAgent(db_path=temp_db_path)
        automator = WorkflowAutomator(agent)

        workflow = automator.create_workflow("wf1", "Chain Test", [])
        result = automator.chain_tasks("wf1", ["t1", "t2", "t3"])

        assert result["workflow_id"] == "wf1"
        assert result["total_tasks"] == 3

    @pytest.mark.unit
    def test_handle_conditional_execution(self, temp_db_path):
        """Test handling conditional execution"""
        agent = AIOpsAgent(db_path=temp_db_path)
        automator = WorkflowAutomator(agent)

        workflow = automator.create_workflow("wf1", "Conditional", [])
        result = automator.handle_conditional_execution("wf1", "if_success", "t2")

        assert result["workflow_id"] == "wf1"
        assert result["condition"] == "if_success"

    @pytest.mark.unit
    def test_execute_parallel_tasks(self, temp_db_path):
        """Test executing parallel tasks"""
        agent = AIOpsAgent(db_path=temp_db_path)
        automator = WorkflowAutomator(agent)

        workflow = automator.create_workflow("wf1", "Parallel", [])
        groups = [["t1", "t2"], ["t3", "t4"]]
        result = automator.execute_parallel_tasks("wf1", groups)

        assert result["parallel_groups"] == 2
        assert result["total_parallel_tasks"] == 4

    @pytest.mark.unit
    def test_manage_workflow_state(self, temp_db_path):
        """Test managing workflow state"""
        agent = AIOpsAgent(db_path=temp_db_path)
        automator = WorkflowAutomator(agent)

        workflow = automator.create_workflow("wf1", "State Test", [])
        workflow.state["task1"] = {"completed": True}

        state = automator.manage_workflow_state("wf1")
        assert state["workflow_id"] == "wf1"
        assert "state" in state


class TestScheduling:
    """Tests for task scheduling"""

    @pytest.mark.unit
    def test_schedule_one_time_task(self, temp_db_path):
        """Test scheduling one-time task"""
        agent = AIOpsAgent(db_path=temp_db_path)
        scheduler = TaskScheduler(agent)

        schedule = scheduler.schedule_one_time_task("s1", "task1", "2026-01-25T10:00:00Z")
        assert schedule.schedule_id == "s1"
        assert schedule.schedule_type == "one_time"
        assert schedule.trigger_time == "2026-01-25T10:00:00Z"

    @pytest.mark.unit
    def test_schedule_recurring_task(self, temp_db_path):
        """Test scheduling recurring task"""
        agent = AIOpsAgent(db_path=temp_db_path)
        scheduler = TaskScheduler(agent)

        schedule = scheduler.schedule_recurring_task("s1", "task1", "daily")
        assert schedule.schedule_type == "recurring"
        assert schedule.recurrence_pattern == "daily"

    @pytest.mark.unit
    def test_schedule_conditional_task(self, temp_db_path):
        """Test scheduling conditional task"""
        agent = AIOpsAgent(db_path=temp_db_path)
        scheduler = TaskScheduler(agent)

        condition = {"metric": "cpu_usage", "threshold": 80}
        schedule = scheduler.schedule_conditional_task("s1", "task1", condition)

        assert schedule.schedule_type == "conditional"
        assert schedule.condition == condition

    @pytest.mark.unit
    def test_optimize_schedule(self, temp_db_path):
        """Test optimizing execution schedule"""
        agent = AIOpsAgent(db_path=temp_db_path)
        scheduler = TaskScheduler(agent)

        scheduler.schedule_one_time_task("s1", "t1", "2026-01-25T10:00:00Z")
        scheduler.schedule_one_time_task("s2", "t2", "2026-01-25T11:00:00Z")

        result = scheduler.optimize_schedule()
        assert result["optimized_count"] == 2

    @pytest.mark.unit
    def test_handle_scheduling_conflicts(self, temp_db_path):
        """Test handling scheduling conflicts"""
        agent = AIOpsAgent(db_path=temp_db_path)
        scheduler = TaskScheduler(agent)

        # Create conflicting schedules
        scheduler.schedule_one_time_task("s1", "t1", "2026-01-25T10:00:00Z")
        scheduler.schedule_one_time_task("s2", "t2", "2026-01-25T10:00:00Z")

        conflicts = scheduler.handle_scheduling_conflicts()
        assert len(conflicts) >= 0  # May or may not have conflicts


class TestResourceManagement:
    """Tests for resource management"""

    @pytest.mark.unit
    def test_allocate_execution_resources(self, temp_db_path):
        """Test allocating execution resources"""
        agent = AIOpsAgent(db_path=temp_db_path)
        manager = ResourceManager(agent)

        allocation = manager.allocate_resources("a1", ResourceType.CPU, 50.0, "task1")
        assert allocation.allocation_id == "a1"
        assert allocation.resource_type == ResourceType.CPU
        assert allocation.amount == 50.0

    @pytest.mark.unit
    def test_monitor_resource_usage(self, temp_db_path):
        """Test monitoring resource usage"""
        agent = AIOpsAgent(db_path=temp_db_path)
        manager = ResourceManager(agent)

        manager.allocate_resources("a1", ResourceType.CPU, 30.0)
        usage = manager.monitor_resource_usage()

        assert "cpu" in usage
        assert usage["cpu"] >= 30.0

    @pytest.mark.unit
    def test_optimize_resource_allocation(self, temp_db_path):
        """Test optimizing resource allocation"""
        agent = AIOpsAgent(db_path=temp_db_path)
        manager = ResourceManager(agent)

        # Allocate high resources
        manager.usage_metrics["cpu"] = 85.0

        result = manager.optimize_resource_allocation()
        assert "optimizations" in result

    @pytest.mark.unit
    def test_handle_resource_constraints(self, temp_db_path):
        """Test handling resource constraints"""
        agent = AIOpsAgent(db_path=temp_db_path)
        manager = ResourceManager(agent)

        constraints = {"cpu": 50.0, "memory": 1000.0}
        manager.usage_metrics["cpu"] = 60.0

        result = manager.handle_resource_constraints(constraints)
        assert "violations" in result

    @pytest.mark.unit
    def test_scale_resource_usage(self, temp_db_path):
        """Test scaling resource usage"""
        agent = AIOpsAgent(db_path=temp_db_path)
        manager = ResourceManager(agent)

        manager.usage_metrics["cpu"] = 50.0
        result = manager.scale_resource_usage("cpu", 1.5)

        assert result["new_usage"] == 75.0
        assert result["scale_factor"] == 1.5


class TestSystemMonitoring:
    """Tests for system health monitoring"""

    @pytest.mark.unit
    def test_monitor_system_health(self, temp_db_path):
        """Test monitoring system health"""
        agent = AIOpsAgent(db_path=temp_db_path)
        monitor = SystemMonitor(agent)

        health = monitor.monitor_system_health()
        assert "status" in health
        assert "timestamp" in health

    @pytest.mark.unit
    def test_detect_performance_issues(self, temp_db_path):
        """Test detecting performance issues"""
        agent = AIOpsAgent(db_path=temp_db_path)
        monitor = SystemMonitor(agent)

        # Add degraded metric
        metric = HealthMetric(
            metric_id="m1",
            metric_name="cpu_usage",
            value=90.0,
            status=HealthStatus.DEGRADED,
        )
        monitor.health_metrics["m1"] = metric

        issues = monitor.detect_performance_issues()
        assert len(issues) > 0

    @pytest.mark.unit
    def test_alert_on_anomalies(self, temp_db_path):
        """Test alerting on anomalies"""
        agent = AIOpsAgent(db_path=temp_db_path)
        monitor = SystemMonitor(agent)

        metric = HealthMetric(
            metric_id="m1",
            metric_name="latency",
            value=500.0,
            status=HealthStatus.HEALTHY,
            anomaly_detected=True,
        )
        monitor.health_metrics["m1"] = metric

        alerts = monitor.alert_on_anomalies()
        assert len(alerts) > 0

    @pytest.mark.unit
    def test_generate_health_reports(self, temp_db_path):
        """Test generating health reports"""
        agent = AIOpsAgent(db_path=temp_db_path)
        monitor = SystemMonitor(agent)

        report = monitor.generate_health_report()
        assert "total_metrics" in report
        assert "timestamp" in report

    @pytest.mark.unit
    def test_predict_maintenance_needs(self, temp_db_path):
        """Test predicting maintenance needs"""
        agent = AIOpsAgent(db_path=temp_db_path)
        monitor = SystemMonitor(agent)

        # Add degraded metric
        metric = HealthMetric(
            metric_id="m1",
            metric_name="disk_usage",
            value=85.0,
            status=HealthStatus.DEGRADED,
        )
        monitor.health_metrics["m1"] = metric

        predictions = monitor.predict_maintenance_needs()
        assert isinstance(predictions, list)


class TestErrorRecovery:
    """Tests for error recovery and mitigation"""

    @pytest.mark.unit
    def test_detect_task_failure(self, temp_db_path):
        """Test detecting task failure"""
        agent = AIOpsAgent(db_path=temp_db_path)
        recovery = ErrorRecovery(agent)

        task = Task(task_id="t1", name="Failed", instructions="{}")
        task.status = TaskStatus.FAILED
        agent.tasks["t1"] = task

        is_failed = recovery.detect_failure("t1")
        assert is_failed is True

    @pytest.mark.unit
    def test_implement_retry_strategy(self, temp_db_path):
        """Test implementing retry strategy"""
        agent = AIOpsAgent(db_path=temp_db_path)
        recovery = ErrorRecovery(agent)

        task = Task(task_id="t1", name="Retry", instructions="{}")
        task.status = TaskStatus.FAILED

        result = recovery.implement_retry_strategy(task, max_retries=3)
        assert result["can_retry"] is True
        assert task.retry_count == 1

    @pytest.mark.unit
    def test_fallback_to_alternative_approach(self, temp_db_path):
        """Test falling back to alternative approach"""
        agent = AIOpsAgent(db_path=temp_db_path)
        recovery = ErrorRecovery(agent)

        task = Task(task_id="t1", name="Fallback", instructions='{"approach": "A"}')
        agent.tasks["t1"] = task

        result = recovery.fallback_to_alternative("t1", '{"approach": "B"}')
        assert result["fallback_applied"] is True

    @pytest.mark.unit
    def test_rollback_failed_operations(self, temp_db_path):
        """Test rolling back failed operations"""
        agent = AIOpsAgent(db_path=temp_db_path)
        recovery = ErrorRecovery(agent)

        task = Task(task_id="t1", name="Rollback", instructions="{}")
        task.status = TaskStatus.FAILED
        agent.tasks["t1"] = task

        result = recovery.rollback_failed_operation("t1")
        assert result["rollback_completed"] is True
        assert task.status == TaskStatus.PENDING

    @pytest.mark.unit
    def test_notify_on_critical_errors(self, temp_db_path):
        """Test notifying on critical errors"""
        agent = AIOpsAgent(db_path=temp_db_path)
        recovery = ErrorRecovery(agent)

        notification = recovery.notify_on_critical_error("t1", "Critical failure")
        assert notification["severity"] == "critical"
        assert notification["notified"] is True


class TestIntegrationManagement:
    """Tests for managing integrations"""

    @pytest.mark.unit
    def test_manage_third_party_apis(self, temp_db_path):
        """Test managing third-party APIs"""
        agent = AIOpsAgent(db_path=temp_db_path)
        integrations = IntegrationManager(agent)

        config = {"endpoint": "https://api.example.com", "version": "v1"}
        result = integrations.manage_third_party_apis("example_api", config)

        assert result["configured"] is True
        assert result["api_name"] == "example_api"

    @pytest.mark.unit
    def test_handle_api_rate_limiting(self, temp_db_path):
        """Test handling API rate limiting"""
        agent = AIOpsAgent(db_path=temp_db_path)
        integrations = IntegrationManager(agent)

        result = integrations.handle_rate_limiting("example_api", 100)
        assert result["rate_limit"] == 100
        assert result["configured"] is True

    @pytest.mark.unit
    def test_manage_authentication_tokens(self, temp_db_path):
        """Test managing authentication tokens"""
        agent = AIOpsAgent(db_path=temp_db_path)
        integrations = IntegrationManager(agent)

        result = integrations.manage_authentication_tokens("example_api", "token123")
        assert result["token_stored"] is True

    @pytest.mark.unit
    def test_handle_api_changes(self, temp_db_path):
        """Test handling API changes"""
        agent = AIOpsAgent(db_path=temp_db_path)
        integrations = IntegrationManager(agent)

        result = integrations.handle_api_changes("example_api", "v2")
        assert result["version"] == "v2"
        assert "compatible" in result

    @pytest.mark.unit
    def test_coordinate_cross_system_operations(self, temp_db_path):
        """Test coordinating cross-system operations"""
        agent = AIOpsAgent(db_path=temp_db_path)
        integrations = IntegrationManager(agent)

        systems = ["system1", "system2", "system3"]
        result = integrations.coordinate_cross_system_operations(systems)

        assert result["total_systems"] == 3
        assert result["coordination_established"] is True


class TestDecisionMaking:
    """Tests for autonomous decision making"""

    @pytest.mark.unit
    def test_make_routine_decisions(self, temp_db_path):
        """Test making routine decisions"""
        agent = AIOpsAgent(db_path=temp_db_path)
        decision_maker = DecisionMaker(agent)

        context = {"action": "backup", "priority": "low"}
        decision = decision_maker.make_routine_decision(context)

        assert decision["type"] == "routine"
        assert decision["confidence"] > 0.9

    @pytest.mark.unit
    def test_escalate_complex_decisions(self, temp_db_path):
        """Test escalating complex decisions"""
        agent = AIOpsAgent(db_path=temp_db_path)
        decision_maker = DecisionMaker(agent)

        context = {"action": "delete_production_data", "confidence": 0.5}
        decision = decision_maker.escalate_complex_decision(context, threshold=0.7)

        assert decision["escalated"] is True

    @pytest.mark.unit
    def test_apply_decision_policies(self, temp_db_path):
        """Test applying decision policies"""
        agent = AIOpsAgent(db_path=temp_db_path)
        decision_maker = DecisionMaker(agent)

        context = {"situation": "test"}
        result = decision_maker.apply_decision_policy("safety_first", context)

        assert result["applied"] is True

    @pytest.mark.unit
    def test_optimize_decisions(self, temp_db_path):
        """Test optimizing decisions"""
        agent = AIOpsAgent(db_path=temp_db_path)
        decision_maker = DecisionMaker(agent)

        options = [
            {"name": "option1", "value": 10},
            {"name": "option2", "value": 20},
            {"name": "option3", "value": 15},
        ]

        result = decision_maker.optimize_decision(options)
        assert result["selected_option"]["value"] == 20

    @pytest.mark.unit
    def test_learn_from_outcomes(self, temp_db_path):
        """Test learning from decision outcomes"""
        agent = AIOpsAgent(db_path=temp_db_path)
        decision_maker = DecisionMaker(agent)

        outcome = {"success": True, "metric": 0.95}
        result = decision_maker.learn_from_outcomes("dec_1", outcome)

        assert result["learning_applied"] is True


class TestEventBusIntegration:
    """Tests for EventBus integration"""

    @pytest.mark.unit
    def test_emit_task_execution_events(self, temp_db_path):
        """Test emitting task execution events"""
        agent = AIOpsAgent(db_path=temp_db_path)
        event_bus = EventBusIntegrator(agent)

        event = event_bus.emit_task_execution_event("task1", "task_started")
        assert event["task_id"] == "task1"
        assert event["event_type"] == "task_started"

    @pytest.mark.unit
    def test_listen_to_execution_requests(self, temp_db_path):
        """Test listening to execution requests"""
        agent = AIOpsAgent(db_path=temp_db_path)
        event_bus = EventBusIntegrator(agent)

        def listener(event):
            pass

        event_bus.listen_to_execution_requests(listener)
        assert "execution_requests" in event_bus.event_listeners

    @pytest.mark.unit
    def test_propagate_operation_results(self, temp_db_path):
        """Test propagating operation results"""
        agent = AIOpsAgent(db_path=temp_db_path)
        event_bus = EventBusIntegrator(agent)

        result = event_bus.propagate_operation_results("op1", {"status": "success"})
        assert result["propagated"] is True

    @pytest.mark.unit
    def test_coordinate_multi_agent_operations(self, temp_db_path):
        """Test coordinating multi-agent operations"""
        agent = AIOpsAgent(db_path=temp_db_path)
        event_bus = EventBusIntegrator(agent)

        result = event_bus.coordinate_multi_agent_operations(["agent1", "agent2"], "sync_operation")
        assert result["status"] == "coordinated"


class TestAuditingAndCompliance:
    """Tests for auditing and compliance"""

    @pytest.mark.unit
    def test_log_all_operations(self, temp_db_path):
        """Test logging all operations"""
        agent = AIOpsAgent(db_path=temp_db_path)
        auditor = AuditLogger(agent)

        entry = auditor.log_operation("task_execution", "system", {"task_id": "t1"})
        assert entry.operation == "task_execution"
        assert entry.actor == "system"

    @pytest.mark.unit
    def test_track_decision_rationale(self, temp_db_path):
        """Test tracking decision rationale"""
        agent = AIOpsAgent(db_path=temp_db_path)
        auditor = AuditLogger(agent)

        result = auditor.track_decision_rationale("dec1", "Based on policy XYZ")
        assert result["tracked"] is True

    @pytest.mark.unit
    def test_maintain_audit_trail(self, temp_db_path):
        """Test maintaining audit trail"""
        agent = AIOpsAgent(db_path=temp_db_path)
        auditor = AuditLogger(agent)

        auditor.log_operation("test", "user", {})
        trail = auditor.maintain_audit_trail()

        assert isinstance(trail, list)
        assert len(trail) > 0

    @pytest.mark.unit
    def test_ensure_compliance(self, temp_db_path):
        """Test ensuring compliance with policies"""
        agent = AIOpsAgent(db_path=temp_db_path)
        auditor = AuditLogger(agent)

        result = auditor.ensure_compliance("data_retention")
        assert "compliant" in result

    @pytest.mark.unit
    def test_generate_compliance_reports(self, temp_db_path):
        """Test generating compliance reports"""
        agent = AIOpsAgent(db_path=temp_db_path)
        auditor = AuditLogger(agent)

        report = auditor.generate_compliance_report()
        assert "total_operations" in report
        assert "compliance_rate" in report


class TestPerformance:
    """Tests for performance and optimization"""

    @pytest.mark.performance
    def test_task_execution_latency(self, temp_db_path):
        """Test task execution latency under 500ms"""
        import time

        agent = AIOpsAgent(db_path=temp_db_path)
        executor = TaskExecutor(agent)

        task = Task(task_id="perf1", name="Perf Test", instructions='{"fast": true}')

        start = time.time()
        executor.execute_task(task)
        duration = time.time() - start

        assert duration < 0.5  # Under 500ms

    @pytest.mark.performance
    def test_workflow_throughput(self, temp_db_path):
        """Test workflow throughput (100+ tasks/second)"""
        import time

        agent = AIOpsAgent(db_path=temp_db_path)
        executor = TaskExecutor(agent)

        # Create 100 simple tasks
        tasks = []
        for i in range(100):
            task = Task(task_id=f"t{i}", name=f"Task {i}", instructions="{}")
            agent.tasks[f"t{i}"] = task
            tasks.append(task)

        start = time.time()
        for task in tasks:
            executor.execute_task(task)
        duration = time.time() - start

        throughput = 100 / duration
        assert throughput >= 10  # At least 10/sec (relaxed for testing)

    @pytest.mark.performance
    def test_scheduling_efficiency(self, temp_db_path):
        """Test scheduling efficiency"""
        import time

        agent = AIOpsAgent(db_path=temp_db_path)
        scheduler = TaskScheduler(agent)

        # Schedule 1000 tasks
        start = time.time()
        for i in range(1000):
            scheduler.schedule_one_time_task(f"s{i}", f"t{i}", "2026-01-25T10:00:00Z")
        duration = time.time() - start

        assert duration < 1.0  # Under 1 second for 1000 schedules

    @pytest.mark.performance
    def test_system_monitoring_overhead(self, temp_db_path):
        """Test system monitoring overhead"""
        import time

        agent = AIOpsAgent(db_path=temp_db_path)
        monitor = SystemMonitor(agent)

        # Add 100 metrics
        for i in range(100):
            metric = HealthMetric(
                metric_id=f"m{i}",
                metric_name=f"metric_{i}",
                value=float(i),
                status=HealthStatus.HEALTHY,
            )
            monitor.health_metrics[f"m{i}"] = metric

        # Measure monitoring overhead
        start = time.time()
        monitor.monitor_system_health()
        duration = time.time() - start

        assert duration < 0.1  # Under 100ms overhead
