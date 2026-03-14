"""
Customer Lifecycle Tool for Agent Jumbo
Enables AI agents to manage complete customer journey
"""

import asyncio
import json

from python.helpers import files
from python.helpers.tool import Response, Tool


class CustomerLifecycle(Tool):
    """
    Agent Jumbo tool for customer lifecycle management.
    Automates lead capture, requirements gathering, solution design,
    proposal generation, and customer health monitoring.
    """

    def __init__(self, agent, name: str, method: str | None, args: dict, message: str, loop_data=None, **kwargs):
        super().__init__(agent, name, method, args, message, loop_data, **kwargs)

        # Import manager here to avoid circular imports
        from instruments.custom.customer_lifecycle.lifecycle_manager import CustomerLifecycleManager

        # Initialize manager
        db_path = files.get_abs_path("./instruments/custom/customer_lifecycle/data/customer_lifecycle.db")
        self.manager = CustomerLifecycleManager(db_path)

    async def execute(self, **kwargs):
        """Execute customer lifecycle action"""

        action = self.args.get("action", "").lower()

        # Route to appropriate action handler
        if action == "capture_lead":
            return await self._capture_lead()
        elif action == "conduct_interview":
            return await self._conduct_interview()
        elif action == "design_solution":
            return await self._design_solution()
        elif action == "generate_proposal":
            return await self._generate_proposal()
        elif action == "track_proposal":
            return await self._track_proposal()
        elif action == "get_customer_view":
            return await self._get_customer_view()
        elif action == "check_customer_health":
            return await self._check_customer_health()
        elif action == "get_pipeline_summary":
            return await self._get_pipeline_summary()
        elif action == "update_customer_stage":
            return await self._update_customer_stage()
        elif action == "list_customers":
            return await self._list_customers()
        else:
            return Response(message=f"Unknown action: {action}", break_loop=False)

    async def _capture_lead(self):
        """Capture new lead"""
        result = self.manager.capture_lead(
            name=self.args.get("name"),
            company=self.args.get("company"),
            email=self.args.get("email"),
            phone=self.args.get("phone"),
            industry=self.args.get("industry"),
            company_size=self.args.get("company_size"),
            source=self.args.get("source"),
            initial_notes=self.args.get("notes"),
        )

        # MOS hook: fire-and-forget Linear issue creation
        try:
            from python.helpers.mos_orchestrator import MOSOrchestrator

            asyncio.create_task(
                MOSOrchestrator.on_lead_captured(
                    customer_name=self.args.get("name", ""),
                    company=self.args.get("company", ""),
                    customer_id=result.get("customer_id"),
                )
            )
        except Exception:
            pass

        return Response(message=self._format_result(result, "Lead Captured"), break_loop=False)

    async def _conduct_interview(self):
        """Conduct requirements interview"""
        customer_id = self.args.get("customer_id")

        # Get responses from args
        responses = self.args.get("responses", {})

        # Allow custom questions or use defaults
        questions = self.args.get("questions")

        result = self.manager.conduct_requirements_interview(
            customer_id=customer_id, interview_questions=questions, responses=responses
        )

        return Response(message=self._format_result(result, "Requirements Interview"), break_loop=False)

    async def _design_solution(self):
        """Design solution architecture"""
        result = self.manager.design_solution(
            customer_id=self.args.get("customer_id"),
            requirement_id=self.args.get("requirement_id"),
            solution_name=self.args.get("solution_name"),
            architecture_preferences=self.args.get("architecture_preferences"),
        )

        return Response(message=self._format_result(result, "Solution Design"), break_loop=False)

    async def _generate_proposal(self):
        """Generate customer proposal"""
        result = self.manager.generate_proposal(
            customer_id=self.args.get("customer_id"),
            solution_id=self.args.get("solution_id"),
            pricing_model=self.args.get("pricing_model", "fixed_price"),
            discount_percentage=self.args.get("discount_percentage", 0),
        )

        return Response(message=self._format_result(result, "Proposal Generated"), break_loop=False)

    async def _track_proposal(self):
        """Track proposal status"""
        result = self.manager.track_proposal(
            proposal_id=self.args.get("proposal_id"), new_status=self.args.get("status")
        )

        return Response(message=self._format_result(result, "Proposal Status"), break_loop=False)

    async def _get_customer_view(self):
        """Get 360-degree customer view"""
        customer_id = self.args.get("customer_id")
        result = self.manager.db.get_customer_360(customer_id)

        return Response(message=self._format_result(result, "Customer 360 View"), break_loop=False)

    async def _check_customer_health(self):
        """Check customer health score"""
        customer_id = self.args.get("customer_id")
        result = self.manager.get_customer_health_score(customer_id)

        return Response(message=self._format_result(result, "Customer Health"), break_loop=False)

    async def _get_pipeline_summary(self):
        """Get sales pipeline summary"""
        result = self.manager.db.get_pipeline_summary()

        return Response(message=self._format_result(result, "Pipeline Summary"), break_loop=False)

    async def _update_customer_stage(self):
        """Update customer lifecycle stage"""
        success = self.manager.db.update_customer_stage(
            customer_id=self.args.get("customer_id"), stage=self.args.get("stage")
        )

        result = {"success": success, "customer_id": self.args.get("customer_id"), "new_stage": self.args.get("stage")}

        return Response(message=self._format_result(result, "Customer Stage Updated"), break_loop=False)

    async def _list_customers(self):
        """List all customers with optional filters"""
        conn = self.manager.db.get_connection()
        cursor = conn.cursor()

        # Build query with filters
        query = "SELECT customer_id, name, company, email, stage, created_at FROM customers"
        conditions = []
        params = []

        if self.args.get("stage"):
            conditions.append("stage = ?")
            params.append(self.args.get("stage"))

        if self.args.get("industry"):
            conditions.append("industry = ?")
            params.append(self.args.get("industry"))

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY created_at DESC"

        if self.args.get("limit"):
            query += f" LIMIT {int(self.args.get('limit'))}"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        cols = [desc[0] for desc in cursor.description]
        conn.close()

        customers = [dict(zip(cols, row)) for row in rows]

        return Response(
            message=self._format_result({"customers": customers, "count": len(customers)}, "Customer List"),
            break_loop=False,
        )

    def _format_result(self, result: dict, title: str) -> str:
        """Format result for display"""
        if not result:
            return f"**{title}**: No data"

        if "error" in result:
            return f"**{title} - Error**: {result['error']}"

        # Pretty print JSON result
        formatted = f"**{title}**:\n```json\n{json.dumps(result, indent=2, default=str)}\n```"
        return formatted
