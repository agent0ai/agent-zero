"""
Portfolio Dashboard API
Provides aggregated data for the Portfolio Dashboard combining customers and projects.
"""

from __future__ import annotations

import os
import traceback
from datetime import datetime
from typing import Any

from python.helpers import files, projects as core_projects
from python.helpers.api import ApiHandler

PORTFOLIO_STATUS_MAP = {
    "draft": "in_development",
    "ready": "in_development",
    "listed": "active",
    "sold": "archived",
}

ACTIVE_PROJECT_STATUSES = {"active", "in_development", "maintenance"}


class PortfolioDashboard(ApiHandler):
    """API endpoint for portfolio dashboard data."""

    async def process(self, input: dict, request) -> dict:
        """
        Get portfolio dashboard data including customers and projects.

        Optional input params:
        - include_customers: bool (default True)
        - include_projects: bool (default True)
        - include_workspace_projects: bool (default True)
        - customer_stage: str (filter by stage)
        - project_status: str (filter by status)
        - project_language: str (filter by language)
        - project_search: str (search by name/description/language)
        """
        try:
            include_customers = input.get("include_customers", True)
            include_projects = input.get("include_projects", True)
            include_workspace_projects = input.get("include_workspace_projects", True)

            result = {
                "success": True,
                "stats": {
                    "total_customers": 0,
                    "active_customers": 0,
                    "total_projects": 0,
                    "active_projects": 0,
                    "pipeline_value": 0,
                    "health_avg": 0,
                },
                "customers": [],
                "projects": [],
                "recent_activity": [],
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
                project_data = await self._load_projects(
                    status_filter=input.get("project_status"),
                    language_filter=input.get("project_language"),
                    search=input.get("project_search", ""),
                    include_workspace_projects=include_workspace_projects,
                )
                result["projects"] = project_data.get("projects", [])
                result["stats"]["total_projects"] = project_data.get("total", 0)
                result["stats"]["active_projects"] = project_data.get("active", 0)

            return result

        except Exception as e:
            traceback.print_exc()
            return {"success": False, "error": str(e)}

    async def _load_customers(self, stage_filter: str | None = None) -> dict[str, Any]:
        """Load customer data from customer_lifecycle database."""
        try:
            from instruments.custom.customer_lifecycle.lifecycle_manager import (
                CustomerLifecycleManager,
            )

            db_path = files.get_abs_path("./instruments/custom/customer_lifecycle/data/customer_lifecycle.db")
            manager = CustomerLifecycleManager(db_path)

            all_customers = manager.list_customers()
            customers = all_customers if isinstance(all_customers, list) else all_customers.get("customers", [])

            if stage_filter:
                customers = [c for c in customers if c.get("stage") == stage_filter]

            active_stages = [
                "discovery",
                "requirements",
                "proposal",
                "negotiation",
                "implementation",
            ]
            active = [c for c in customers if c.get("stage") in active_stages]

            health_scores = [c.get("health_score", 0) for c in customers if c.get("health_score")]
            health_avg = sum(health_scores) / len(health_scores) if health_scores else 0

            pipeline_value = 0
            for customer in customers:
                if customer.get("proposals"):
                    for proposal in customer.get("proposals", []):
                        if proposal.get("status") == "pending":
                            pipeline_value += proposal.get("total_value", 0)

            return {
                "customers": customers[:50],
                "total": len(all_customers if isinstance(all_customers, list) else all_customers.get("customers", [])),
                "active": len(active),
                "pipeline_value": pipeline_value,
                "health_avg": round(health_avg, 1),
            }

        except Exception as e:
            print(f"Error loading customers: {e}")
            traceback.print_exc()
            return {
                "customers": [],
                "total": 0,
                "active": 0,
                "pipeline_value": 0,
                "health_avg": 0,
            }

    async def _load_projects(
        self,
        status_filter: str | None = None,
        language_filter: str | None = None,
        search: str = "",
        include_workspace_projects: bool = True,
    ) -> dict[str, Any]:
        """Load project data from portfolio manager DB and core project workspace."""
        try:
            projects: list[dict[str, Any]] = []
            projects.extend(
                self._load_portfolio_projects(
                    status_filter=status_filter,
                    language_filter=language_filter,
                    search=search,
                )
            )

            if include_workspace_projects:
                projects.extend(
                    self._load_workspace_projects(
                        status_filter=status_filter,
                        language_filter=language_filter,
                        search=search,
                    )
                )

            projects = sorted(
                projects,
                key=lambda p: (
                    p.get("updated_at") or "",
                    p.get("name") or "",
                ),
                reverse=True,
            )

            active = [p for p in projects if p.get("status") in ACTIVE_PROJECT_STATUSES]

            return {
                "projects": projects[:50],
                "total": len(projects),
                "active": len(active),
            }

        except Exception as e:
            print(f"Error loading projects: {e}")
            traceback.print_exc()
            return {"projects": [], "total": 0, "active": 0}

    def _load_portfolio_projects(
        self,
        status_filter: str | None = None,
        language_filter: str | None = None,
        search: str = "",
    ) -> list[dict[str, Any]]:
        try:
            from instruments.custom.portfolio_manager.portfolio_db import PortfolioDatabase

            db = PortfolioDatabase()
            records = db.list_projects()
            result = []
            for record in records:
                metadata = db.get_metadata(record["id"]) or {}
                normalized = self._normalize_portfolio_project(record, metadata)
                if self._matches_project_filters(
                    normalized,
                    status_filter=status_filter,
                    language_filter=language_filter,
                    search=search,
                ):
                    result.append(normalized)
            return result
        except Exception:
            traceback.print_exc()
            return []

    def _load_workspace_projects(
        self,
        status_filter: str | None = None,
        language_filter: str | None = None,
        search: str = "",
    ) -> list[dict[str, Any]]:
        try:
            workspace_projects = core_projects.get_active_projects_list()
            result = []

            for project in workspace_projects:
                name = project.get("name") or ""
                title = project.get("title") or name
                path = files.get_abs_path(core_projects.PROJECTS_PARENT_DIR, name)

                normalized = {
                    "id": f"workspace:{name}",
                    "project_id": f"workspace:{name}",
                    "source": "workspace",
                    "source_id": name,
                    "name": title,
                    "slug": name,
                    "description": project.get("description") or "",
                    "language": self._detect_workspace_language(path),
                    "framework": None,
                    "path": path,
                    "status": "active",
                    "status_raw": "active",
                    "sale_readiness": 0,
                    "created_at": "",
                    "updated_at": self._get_path_mtime_iso(path),
                    "color": project.get("color") or "",
                }

                if self._matches_project_filters(
                    normalized,
                    status_filter=status_filter,
                    language_filter=language_filter,
                    search=search,
                ):
                    result.append(normalized)

            return result
        except Exception:
            traceback.print_exc()
            return []

    def _normalize_portfolio_project(self, record: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
        raw_status = (record.get("status") or "draft").lower()
        status = PORTFOLIO_STATUS_MAP.get(raw_status, raw_status)
        readiness = metadata.get("sale_readiness_score", record.get("sale_readiness_score", 0))

        return {
            "id": f"portfolio:{record['id']}",
            "project_id": f"portfolio:{record['id']}",
            "source": "portfolio",
            "source_id": record["id"],
            "name": record.get("name") or f"Project {record['id']}",
            "slug": record.get("name") or f"project-{record['id']}",
            "description": record.get("description") or "",
            "language": record.get("language") or "",
            "framework": record.get("framework") or "",
            "path": record.get("path") or "",
            "status": status,
            "status_raw": raw_status,
            "sale_readiness": int(readiness or 0),
            "created_at": record.get("created_at") or "",
            "updated_at": record.get("updated_at") or "",
        }

    def _matches_project_filters(
        self,
        project: dict[str, Any],
        status_filter: str | None = None,
        language_filter: str | None = None,
        search: str = "",
    ) -> bool:
        if status_filter and status_filter not in ("all", ""):
            if project.get("status") != status_filter:
                return False

        if language_filter and language_filter not in ("all", ""):
            if (project.get("language") or "").lower() != language_filter.lower():
                return False

        if search:
            text = search.lower()
            haystack = " ".join(
                [
                    project.get("name") or "",
                    project.get("description") or "",
                    project.get("language") or "",
                    project.get("framework") or "",
                ]
            ).lower()
            if text not in haystack:
                return False

        return True

    def _detect_workspace_language(self, path: str) -> str:
        markers = [
            ("typescript", ["tsconfig.json", "package.json"]),
            ("python", ["pyproject.toml", "requirements.txt", "setup.py"]),
            ("ruby", ["Gemfile"]),
            ("go", ["go.mod"]),
            ("rust", ["Cargo.toml"]),
            ("java", ["pom.xml", "build.gradle"]),
        ]

        try:
            for language, files_to_check in markers:
                for file_name in files_to_check:
                    if os.path.exists(os.path.join(path, file_name)):
                        return language
        except Exception:
            pass
        return ""

    def _get_path_mtime_iso(self, path: str) -> str:
        try:
            mtime = os.path.getmtime(path)
            return datetime.utcfromtimestamp(mtime).isoformat() + "Z"
        except Exception:
            return ""


class CustomerList(ApiHandler):
    """API endpoint for customer list operations."""

    async def process(self, input: dict, request) -> dict:
        """Get list of customers with optional filters."""
        try:
            from instruments.custom.customer_lifecycle.lifecycle_manager import (
                CustomerLifecycleManager,
            )

            db_path = files.get_abs_path("./instruments/custom/customer_lifecycle/data/customer_lifecycle.db")
            manager = CustomerLifecycleManager(db_path)

            stage = input.get("stage")
            search = input.get("search", "")

            all_customers = manager.list_customers()
            customers = all_customers if isinstance(all_customers, list) else all_customers.get("customers", [])

            if stage and stage != "all":
                customers = [c for c in customers if c.get("stage") == stage]

            if search:
                search_lower = search.lower()
                customers = [
                    c
                    for c in customers
                    if search_lower in (c.get("name", "") or "").lower()
                    or search_lower in (c.get("company", "") or "").lower()
                    or search_lower in (c.get("email", "") or "").lower()
                ]

            return {"success": True, "customers": customers}

        except Exception as e:
            traceback.print_exc()
            return {"success": False, "error": str(e), "customers": []}


class CustomerDetail(ApiHandler):
    """API endpoint for customer detail."""

    async def process(self, input: dict, request) -> dict:
        """Get detailed customer information."""
        try:
            customer_id = input.get("customer_id")
            if not customer_id:
                return {"success": False, "error": "customer_id required"}

            from instruments.custom.customer_lifecycle.lifecycle_manager import (
                CustomerLifecycleManager,
            )

            db_path = files.get_abs_path("./instruments/custom/customer_lifecycle/data/customer_lifecycle.db")
            manager = CustomerLifecycleManager(db_path)

            customer = manager.get_customer_view(customer_id)

            if not customer:
                return {"success": False, "error": "Customer not found"}

            return {"success": True, "customer": customer}

        except Exception as e:
            traceback.print_exc()
            return {"success": False, "error": str(e)}


class ProjectList(ApiHandler):
    """API endpoint for project list operations."""

    async def process(self, input: dict, request) -> dict:
        """Get list of projects with optional filters."""
        try:
            dashboard = PortfolioDashboard(self.app, self.thread_lock)
            project_data = await dashboard._load_projects(
                status_filter=input.get("status"),
                language_filter=input.get("language"),
                search=input.get("search", ""),
                include_workspace_projects=input.get("include_workspace_projects", True),
            )
            return {"success": True, "projects": project_data.get("projects", [])}

        except Exception as e:
            traceback.print_exc()
            return {"success": False, "error": str(e), "projects": []}


class ProjectDetail(ApiHandler):
    """API endpoint for project detail."""

    async def process(self, input: dict, request) -> dict:
        """Get detailed project information."""
        try:
            project_id = input.get("project_id")
            if not project_id:
                return {"success": False, "error": "project_id required"}

            project_id_str = str(project_id)

            if project_id_str.startswith("workspace:"):
                project_name = project_id_str.split(":", 1)[1]
                project_path = files.get_abs_path(core_projects.PROJECTS_PARENT_DIR, project_name)
                if not os.path.isdir(project_path):
                    return {"success": False, "error": "Project not found"}

                project = core_projects.load_edit_project_data(project_name)
                if not project:
                    return {"success": False, "error": "Project not found"}

                project["id"] = project_id_str
                project["project_id"] = project_id_str
                project["source"] = "workspace"
                project["path"] = project_path
                project["status"] = "active"
                project["sale_readiness"] = 0
                return {"success": True, "project": project}

            source_id = project_id_str
            if project_id_str.startswith("portfolio:"):
                source_id = project_id_str.split(":", 1)[1]

            from instruments.custom.portfolio_manager.portfolio_db import PortfolioDatabase

            db = PortfolioDatabase()
            project = db.get_project(int(source_id))
            if not project:
                return {"success": False, "error": "Project not found"}

            metadata = db.get_metadata(project["id"]) or {}
            normalized = PortfolioDashboard(self.app, self.thread_lock)._normalize_portfolio_project(project, metadata)
            normalized["metadata"] = metadata
            normalized["tags"] = db.get_tags(project["id"])
            normalized["documentation"] = db.get_documentation_status(project["id"])

            return {"success": True, "project": normalized}

        except Exception as e:
            traceback.print_exc()
            return {"success": False, "error": str(e)}
