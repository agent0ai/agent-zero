"""
Portfolio Dashboard API
Provides aggregated data for the Portfolio Dashboard combining customers and projects
"""

import traceback

from python.helpers import files
from python.helpers.api import ApiHandler


class PortfolioDashboard(ApiHandler):
    """API endpoint for portfolio dashboard data"""

    async def process(self, input: dict, request) -> dict:
        """
        Get portfolio dashboard data including customers and projects.

        Optional input params:
        - include_customers: bool (default True)
        - include_projects: bool (default True)
        - customer_stage: str (filter by stage)
        - project_status: str (filter by status)
        """
        try:
            include_customers = input.get("include_customers", True)
            include_projects = input.get("include_projects", True)

            result = {
                "success": True,
                "stats": {
                    "total_customers": 0,
                    "active_customers": 0,
                    "total_projects": 0,
                    "active_projects": 0,
                    "pipeline_value": 0,
                    "health_avg": 0
                },
                "customers": [],
                "projects": [],
                "recent_activity": []
            }

            # Load customer data
            if include_customers:
                customer_data = await self._load_customers(input.get("customer_stage"))
                result["customers"] = customer_data.get("customers", [])
                result["stats"]["total_customers"] = customer_data.get("total", 0)
                result["stats"]["active_customers"] = customer_data.get("active", 0)
                result["stats"]["pipeline_value"] = customer_data.get("pipeline_value", 0)
                result["stats"]["health_avg"] = customer_data.get("health_avg", 0)

            # Load project data
            if include_projects:
                project_data = await self._load_projects(input.get("project_status"))
                result["projects"] = project_data.get("projects", [])
                result["stats"]["total_projects"] = project_data.get("total", 0)
                result["stats"]["active_projects"] = project_data.get("active", 0)

            return result

        except Exception as e:
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }

    async def _load_customers(self, stage_filter=None):
        """Load customer data from customer_lifecycle database"""
        try:
            from instruments.custom.customer_lifecycle.lifecycle_manager import CustomerLifecycleManager

            db_path = files.get_abs_path("./instruments/custom/customer_lifecycle/data/customer_lifecycle.db")
            manager = CustomerLifecycleManager(db_path)

            # Get all customers
            all_customers = manager.list_customers()
            customers = all_customers if isinstance(all_customers, list) else all_customers.get("customers", [])

            # Apply stage filter if provided
            if stage_filter:
                customers = [c for c in customers if c.get("stage") == stage_filter]

            # Calculate statistics
            active_stages = ["discovery", "requirements", "proposal", "negotiation", "implementation"]
            active = [c for c in customers if c.get("stage") in active_stages]

            # Calculate health average
            health_scores = [c.get("health_score", 0) for c in customers if c.get("health_score")]
            health_avg = sum(health_scores) / len(health_scores) if health_scores else 0

            # Calculate pipeline value (from proposals)
            pipeline_value = 0
            for customer in customers:
                if customer.get("proposals"):
                    for proposal in customer.get("proposals", []):
                        if proposal.get("status") == "pending":
                            pipeline_value += proposal.get("total_value", 0)

            return {
                "customers": customers[:50],  # Limit to 50 for dashboard
                "total": len(all_customers if isinstance(all_customers, list) else all_customers.get("customers", [])),
                "active": len(active),
                "pipeline_value": pipeline_value,
                "health_avg": round(health_avg, 1)
            }

        except Exception as e:
            print(f"Error loading customers: {e}")
            traceback.print_exc()
            return {"customers": [], "total": 0, "active": 0, "pipeline_value": 0, "health_avg": 0}

    async def _load_projects(self, status_filter=None):
        """Load project data from portfolio_manager database"""
        try:
            from instruments.custom.portfolio_manager.portfolio_db import PortfolioDatabase

            db = PortfolioDatabase()

            # Get all projects
            projects = db.get_projects(status=status_filter)

            # Calculate statistics
            active_statuses = ["active", "in_development", "maintenance"]
            active = [p for p in projects if p.get("status") in active_statuses]

            return {
                "projects": projects[:50],  # Limit to 50 for dashboard
                "total": len(projects),
                "active": len(active)
            }

        except Exception as e:
            print(f"Error loading projects: {e}")
            traceback.print_exc()
            return {"projects": [], "total": 0, "active": 0}


class CustomerList(ApiHandler):
    """API endpoint for customer list operations"""

    async def process(self, input: dict, request) -> dict:
        """Get list of customers with optional filters"""
        try:
            from instruments.custom.customer_lifecycle.lifecycle_manager import CustomerLifecycleManager

            db_path = files.get_abs_path("./instruments/custom/customer_lifecycle/data/customer_lifecycle.db")
            manager = CustomerLifecycleManager(db_path)

            stage = input.get("stage")
            search = input.get("search", "")

            all_customers = manager.list_customers()
            customers = all_customers if isinstance(all_customers, list) else all_customers.get("customers", [])

            # Apply filters
            if stage and stage != "all":
                customers = [c for c in customers if c.get("stage") == stage]

            if search:
                search_lower = search.lower()
                customers = [c for c in customers
                            if search_lower in (c.get("name", "") or "").lower()
                            or search_lower in (c.get("company", "") or "").lower()
                            or search_lower in (c.get("email", "") or "").lower()]

            return {
                "success": True,
                "customers": customers
            }

        except Exception as e:
            traceback.print_exc()
            return {"success": False, "error": str(e), "customers": []}


class CustomerDetail(ApiHandler):
    """API endpoint for customer detail"""

    async def process(self, input: dict, request) -> dict:
        """Get detailed customer information"""
        try:
            customer_id = input.get("customer_id")
            if not customer_id:
                return {"success": False, "error": "customer_id required"}

            from instruments.custom.customer_lifecycle.lifecycle_manager import CustomerLifecycleManager

            db_path = files.get_abs_path("./instruments/custom/customer_lifecycle/data/customer_lifecycle.db")
            manager = CustomerLifecycleManager(db_path)

            customer = manager.get_customer_view(customer_id)

            if not customer:
                return {"success": False, "error": "Customer not found"}

            return {
                "success": True,
                "customer": customer
            }

        except Exception as e:
            traceback.print_exc()
            return {"success": False, "error": str(e)}


class ProjectList(ApiHandler):
    """API endpoint for project list operations"""

    async def process(self, input: dict, request) -> dict:
        """Get list of projects with optional filters"""
        try:
            from instruments.custom.portfolio_manager.portfolio_db import PortfolioDatabase

            db = PortfolioDatabase()

            status = input.get("status")
            language = input.get("language")
            search = input.get("search", "")

            projects = db.get_projects(
                status=status if status and status != "all" else None,
                language=language if language and language != "all" else None
            )

            # Apply search filter
            if search:
                search_lower = search.lower()
                projects = [p for p in projects
                          if search_lower in (p.get("name", "") or "").lower()
                          or search_lower in (p.get("description", "") or "").lower()]

            return {
                "success": True,
                "projects": projects
            }

        except Exception as e:
            traceback.print_exc()
            return {"success": False, "error": str(e), "projects": []}


class ProjectDetail(ApiHandler):
    """API endpoint for project detail"""

    async def process(self, input: dict, request) -> dict:
        """Get detailed project information"""
        try:
            project_id = input.get("project_id")
            if not project_id:
                return {"success": False, "error": "project_id required"}

            from instruments.custom.portfolio_manager.portfolio_manager import PortfolioManager

            pm = PortfolioManager()
            project = pm.get_project(project_id)

            if not project:
                return {"success": False, "error": "Project not found"}

            return {
                "success": True,
                "project": project
            }

        except Exception as e:
            traceback.print_exc()
            return {"success": False, "error": str(e)}
