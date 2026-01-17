"""
Test Customer Lifecycle Manager
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json

from instruments.custom.customer_lifecycle.lifecycle_manager import CustomerLifecycleManager


def test_full_lifecycle():
    """Test complete customer lifecycle flow"""

    print("🧪 Testing Customer Lifecycle Manager\n")
    print("=" * 60)

    # Initialize manager with test database
    test_db = "instruments/custom/customer_lifecycle/data/test_lifecycle.db"
    if os.path.exists(test_db):
        os.remove(test_db)  # Clean start

    manager = CustomerLifecycleManager(test_db)

    # Test 1: Capture lead
    print("\n1️⃣  Testing lead capture...")
    lead = manager.capture_lead(
        name="Sarah Johnson",
        company="MedTech Inc",
        email="sarah@medtech.com",
        phone="+1-555-0100",
        industry="Healthcare",
        company_size="51-200",
        source="website_form",
        initial_notes="Interested in HIPAA-compliant patient portal"
    )
    assert lead['customer_id'] > 0, "Lead capture failed"
    assert lead['stage'] == 'lead', "Lead stage incorrect"
    customer_id = lead['customer_id']
    print(f"   ✓ Lead captured: customer_id = {customer_id}")

    # Test 2: Requirements interview
    print("\n2️⃣  Testing requirements interview...")
    interview = manager.conduct_requirements_interview(
        customer_id=customer_id,
        responses={
            "What business problem are you trying to solve?": "Need HIPAA-compliant patient portal for 50,000 patients",
            "Who are the primary users?": "Patients (50k), doctors (500), admin staff (50)",
            "What are your main pain points?": "Current system is slow, not mobile-friendly, no real-time updates",
            "What does success look like?": "Fast mobile app, real-time appointment booking, secure messaging",
            "What are your timeline expectations?": "Launch in 6 months",
            "What is your budget range?": "$100k-$200k",
            "Are there any specific technical constraints?": "Must integrate with existing EMR system (Epic)",
            "What integrations are required?": "Epic EMR, insurance verification API, payment gateway",
            "What are your scalability requirements?": "Support 100k patients within 2 years",
            "What compliance/security requirements exist?": "HIPAA, SOC2, data encryption at rest and in transit"
        }
    )
    assert interview['requirement_id'] > 0, "Interview failed"
    assert interview['stage'] == 'prospect', "Stage not updated to prospect"
    requirement_id = interview['requirement_id']
    print(f"   ✓ Requirements gathered: requirement_id = {requirement_id}")
    print(f"   ✓ Customer promoted to: {interview['stage']}")

    # Test 3: Solution design
    print("\n3️⃣  Testing solution design...")
    solution = manager.design_solution(
        customer_id=customer_id,
        requirement_id=requirement_id,
        solution_name="MedTech Patient Portal Platform"
    )
    assert solution['solution_id'] > 0, "Solution design failed"
    assert 'architecture' in solution, "Architecture not generated"
    solution_id = solution['solution_id']
    print(f"   ✓ Solution designed: solution_id = {solution_id}")
    print(f"   ✓ Architecture: {solution['architecture']['architecture_type']}")

    # Test 4: Proposal generation
    print("\n4️⃣  Testing proposal generation...")
    proposal = manager.generate_proposal(
        customer_id=customer_id,
        solution_id=solution_id,
        pricing_model="milestone_based",
        discount_percentage=10
    )
    assert proposal['proposal_id'] > 0, "Proposal generation failed"
    assert proposal['total_cost'] > 0, "Proposal cost not calculated"
    proposal_id = proposal['proposal_id']
    print(f"   ✓ Proposal generated: proposal_id = {proposal_id}")
    print(f"   ✓ Total cost: ${proposal['total_cost']:,.2f}")
    print(f"   ✓ Timeline: {proposal['timeline_weeks']} weeks")

    # Test 5: Proposal tracking
    print("\n5️⃣  Testing proposal tracking...")
    tracking = manager.track_proposal(proposal_id, new_status="sent")
    assert tracking['status'] == 'sent', "Proposal status not updated"
    print(f"   ✓ Proposal status: {tracking['status']}")
    print(f"   ✓ Follow-up action: {tracking['follow_up_action']}")

    # Test 6: Proposal acceptance
    print("\n6️⃣  Testing proposal acceptance...")
    acceptance = manager.track_proposal(proposal_id, new_status="accepted")
    assert acceptance['status'] == 'accepted', "Proposal not marked accepted"
    print("   ✓ Proposal accepted")

    # Verify customer stage updated
    customer = manager.db.get_customer(customer_id)
    assert customer['stage'] == 'customer', "Customer stage not updated on acceptance"
    print(f"   ✓ Customer stage: {customer['stage']}")

    # Test 7: Customer 360 view
    print("\n7️⃣  Testing customer 360 view...")
    customer_360 = manager.db.get_customer_360(customer_id)
    assert customer_360 is not None, "Customer 360 view failed"
    assert customer_360['requirements_sessions'] == 1, "Requirements count wrong"
    assert customer_360['solutions_designed'] == 1, "Solutions count wrong"
    print("   ✓ Customer 360 view:")
    print(f"      - Requirements sessions: {customer_360['requirements_sessions']}")
    print(f"      - Solutions designed: {customer_360['solutions_designed']}")
    print(f"      - Proposals: {json.dumps(customer_360['proposals'], indent=8)}")

    # Test 8: Customer health score
    print("\n8️⃣  Testing customer health score...")
    health = manager.get_customer_health_score(customer_id)
    assert health['health_score'] >= 0, "Health score invalid"
    print(f"   ✓ Health score: {health['health_score']}/100")
    print(f"   ✓ Health status: {health['health_status']}")
    print(f"   ✓ Recommendations: {health['recommendations']}")

    # Test 9: Pipeline summary
    print("\n9️⃣  Testing pipeline summary...")
    pipeline = manager.db.get_pipeline_summary()
    assert 'customers_by_stage' in pipeline, "Pipeline summary missing customer stages"
    assert 'proposals_by_status' in pipeline, "Pipeline summary missing proposal statuses"
    print(f"   ✓ Customers by stage: {json.dumps(pipeline['customers_by_stage'], indent=6)}")
    print(f"   ✓ Proposals by status: {json.dumps(pipeline['proposals_by_status'], indent=6)}")

    # Summary
    print("\n" + "=" * 60)
    print("✅ All Customer Lifecycle tests PASSED!")
    print("\nTest Results:")
    print("  - Lead captured: ✓")
    print("  - Requirements gathered: ✓")
    print("  - Solution designed: ✓")
    print("  - Proposal generated: ✓")
    print("  - Proposal tracking: ✓")
    print("  - Proposal acceptance: ✓")
    print("  - Customer 360 view: ✓")
    print("  - Health monitoring: ✓")
    print("  - Pipeline analytics: ✓")
    print("\n🎉 Customer Lifecycle Manager is fully functional!")


if __name__ == "__main__":
    test_full_lifecycle()
