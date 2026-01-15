"""
Test Virtual Team Orchestrator
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from instruments.custom.virtual_team.team_orchestrator import VirtualTeamOrchestrator
import json


def test_team_orchestration():
    """Test complete virtual team orchestration flow"""
    
    print("🧪 Testing Virtual Team Orchestrator\n")
    print("=" * 60)
    
    # Initialize orchestrator with test database
    test_db = "instruments/custom/virtual_team/data/test_team.db"
    if os.path.exists(test_db):
        os.remove(test_db)  # Clean start
    
    orchestrator = VirtualTeamOrchestrator(test_db)
    
    # Test 1: List agents
    print("\n1️⃣  Testing agent registration...")
    agents = orchestrator.db.list_agents()
    assert len(agents) > 0, "No agents registered"
    print(f"   ✓ Agents registered: {len(agents)}")
    for agent in agents:
        print(f"      - {agent['agent_name']} ({agent['agent_role']})")
    
    # Test 2: Route task (architecture)
    print("\n2️⃣  Testing task routing...")
    arch_task = orchestrator.route_task(
        task_name="Design microservices architecture",
        task_type="architecture_design",
        description="Design scalable microservices architecture for e-commerce platform",
        context={"customer_id": 1, "requirements": "high_availability"},
        priority="high"
    )
    assert arch_task['task_id'] > 0, "Task routing failed"
    assert arch_task['agent_role'] == 'architect', "Wrong agent assigned"
    print(f"   ✓ Task routed: task_id = {arch_task['task_id']}")
    print(f"   ✓ Assigned to: {arch_task['assigned_to']} ({arch_task['agent_role']})")
    
    # Test 3: Delegate to specialist
    print("\n3️⃣  Testing specialist delegation...")
    dba_task = orchestrator.delegate_to_specialist(
        task_name="Optimize database queries",
        specialist_role="dba",
        description="Optimize slow queries in orders table",
        priority="high"
    )
    assert dba_task['task_id'] > 0, "Delegation failed"
    assert dba_task['agent_role'] == 'dba', "Wrong specialist assigned"
    print(f"   ✓ Task delegated: task_id = {dba_task['task_id']}")
    print(f"   ✓ Specialist: {dba_task['assigned_to']} ({dba_task['agent_role']})")
    
    # Test 4: Start workflow (full-stack development)
    print("\n4️⃣  Testing workflow creation...")
    workflow = orchestrator.start_workflow(
        workflow_name="E-Commerce Platform Build",
        template="full_stack_development",
        customer_id=1,
        project_id=5
    )
    assert workflow['workflow_id'] > 0, "Workflow creation failed"
    assert workflow['tasks_created'] > 0, "No tasks created in workflow"
    workflow_id = workflow['workflow_id']
    print(f"   ✓ Workflow started: workflow_id = {workflow_id}")
    print(f"   ✓ Tasks created: {workflow['tasks_created']}")
    
    # Test 5: Get workflow progress
    print("\n5️⃣  Testing workflow progress tracking...")
    progress = orchestrator.get_workflow_progress(workflow_id)
    assert progress is not None, "Workflow progress retrieval failed"
    assert 'progress_percentage' in progress, "Progress percentage missing"
    print(f"   ✓ Workflow progress: {progress['progress_percentage']:.1f}%")
    print(f"   ✓ Tasks in workflow:")
    for task in progress.get('tasks', []):
        print(f"      - {task['task_name']} ({task['status']})")
    
    # Test 6: Coordinate parallel tasks
    print("\n6️⃣  Testing parallel task coordination...")
    parallel = orchestrator.coordinate_parallel_tasks([
        {
            "task_name": "Build REST API",
            "task_type": "backend_development",
            "priority": "high"
        },
        {
            "task_name": "Create React UI",
            "task_type": "frontend_development",
            "priority": "high"
        },
        {
            "task_name": "Setup CI/CD pipeline",
            "task_type": "ci_cd_setup",
            "priority": "medium"
        }
    ])
    assert parallel['parallel_tasks'] == 3, "Parallel coordination failed"
    print(f"   ✓ Parallel tasks coordinated: {parallel['parallel_tasks']}")
    for assignment in parallel['assignments']:
        if 'assigned_to' in assignment:
            print(f"      - {assignment.get('assigned_to', 'N/A')} working on task {assignment['task_id']}")
    
    # Test 7: Get task queue
    print("\n7️⃣  Testing task queue...")
    queue = orchestrator.get_task_queue()
    assert 'total_pending' in queue, "Task queue retrieval failed"
    print(f"   ✓ Total pending tasks: {queue['total_pending']}")
    if queue['by_role']:
        print(f"   ✓ Tasks by role:")
        for role, tasks in queue['by_role'].items():
            print(f"      - {role}: {len(tasks)} tasks")
    
    # Test 8: Get agent workload
    print("\n8️⃣  Testing agent workload...")
    workload = orchestrator.get_agent_workload(role="developer")
    assert 'total_active_tasks' in workload, "Workload retrieval failed"
    print(f"   ✓ Developer workload: {workload['total_active_tasks']} active tasks")
    if workload.get('workload'):
        print(f"   ✓ Breakdown: {json.dumps(workload['workload'], indent=6)}")
    
    # Test 9: Escalate task
    print("\n9️⃣  Testing task escalation...")
    escalation = orchestrator.escalate_task(
        task_id=arch_task['task_id'],
        escalation_reason="Requires senior architect review",
        target_role="architect"
    )
    assert escalation['task_id'] == arch_task['task_id'], "Escalation failed"
    print(f"   ✓ Task escalated: {escalation['task_id']}")
    print(f"   ✓ Escalated to: {escalation['escalated_to']}")
    print(f"   ✓ Reason: {escalation['reason']}")
    
    # Test 10: Update task status
    print("\n🔟 Testing task status update...")
    success = orchestrator.db.update_task_status(
        task_id=dba_task['task_id'],
        status="in_progress",
        progress_percentage=50
    )
    assert success, "Task status update failed"
    print(f"   ✓ Task {dba_task['task_id']} updated to: in_progress (50%)")
    
    # Test 11: Get team dashboard
    print("\n1️⃣1️⃣  Testing team dashboard...")
    dashboard = orchestrator.get_team_dashboard()
    assert dashboard['active_agents'] > 0, "Dashboard retrieval failed"
    print(f"   ✓ Team Dashboard:")
    print(f"      - Active agents: {dashboard['active_agents']}")
    print(f"      - Task stats: {json.dumps(dashboard.get('task_stats', {}), indent=8)}")
    print(f"      - Recent completions (7d): {dashboard.get('recent_completions_7d', 0)}")
    if dashboard.get('workload_by_role'):
        print(f"      - Workload by role:")
        for role, count in dashboard['workload_by_role'].items():
            print(f"         • {role}: {count} tasks")
    
    # Test 12: Available workflows
    print("\n1️⃣2️⃣  Testing available workflows...")
    workflows = orchestrator.get_available_workflows()
    assert len(workflows) > 0, "No workflows available"
    print(f"   ✓ Available workflow templates: {len(workflows)}")
    for wf in workflows:
        print(f"      - {wf}")
    
    # Test 13: Available roles
    print("\n1️⃣3️⃣  Testing available roles...")
    roles = orchestrator.get_available_roles()
    assert len(roles) > 0, "No roles available"
    print(f"   ✓ Available roles: {len(roles)}")
    for role, config in roles.items():
        print(f"      - {role}: {config['specialization']}")
        print(f"         Expertise: {', '.join(config['expertise'][:3])}...")
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ All Virtual Team Orchestration tests PASSED!")
    print(f"\nTest Results:")
    print(f"  - Agent registration: ✓")
    print(f"  - Task routing: ✓")
    print(f"  - Specialist delegation: ✓")
    print(f"  - Workflow creation: ✓")
    print(f"  - Progress tracking: ✓")
    print(f"  - Parallel coordination: ✓")
    print(f"  - Task queue: ✓")
    print(f"  - Agent workload: ✓")
    print(f"  - Task escalation: ✓")
    print(f"  - Status updates: ✓")
    print(f"  - Team dashboard: ✓")
    print(f"  - Workflow templates: ✓")
    print(f"  - Role capabilities: ✓")
    print("\n🎉 Virtual Team Orchestrator is fully functional!")


if __name__ == "__main__":
    test_team_orchestration()
