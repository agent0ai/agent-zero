"""
Async GraphQL client for the Linear API.

Uses aiohttp (already installed) — no new dependencies.
API key sourced from settings or LINEAR_API_KEY env var.
"""

import os
from typing import Any

import aiohttp

LINEAR_API_URL = "https://api.linear.app/graphql"


class LinearClient:
    """Thin async wrapper around Linear's GraphQL API."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("LINEAR_API_KEY", "")
        if not self.api_key:
            raise ValueError("Linear API key required. Set linear_api_key in settings or LINEAR_API_KEY env var.")

    async def execute(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute a GraphQL query against Linear."""
        headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables

        async with aiohttp.ClientSession() as session:
            async with session.post(LINEAR_API_URL, json=payload, headers=headers) as resp:
                data = await resp.json()
                if resp.status != 200:
                    raise LinearAPIError(f"HTTP {resp.status}: {data}")
                if "errors" in data:
                    raise LinearAPIError(f"GraphQL errors: {data['errors']}")
                return data.get("data", {})

    # ── Convenience methods ──────────────────────────────────────────

    async def create_issue(
        self,
        title: str,
        team_id: str,
        description: str = "",
        priority: int = 0,
        label_ids: list[str] | None = None,
        project_id: str | None = None,
        state_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a new issue."""
        mutation = """
        mutation CreateIssue($input: IssueCreateInput!) {
            issueCreate(input: $input) {
                success
                issue {
                    id
                    identifier
                    title
                    url
                    state { name }
                    priority
                }
            }
        }
        """
        input_vars: dict[str, Any] = {
            "title": title,
            "teamId": team_id,
            "description": description,
            "priority": priority,
        }
        if label_ids:
            input_vars["labelIds"] = label_ids
        if project_id:
            input_vars["projectId"] = project_id
        if state_id:
            input_vars["stateId"] = state_id

        result = await self.execute(mutation, {"input": input_vars})
        return result.get("issueCreate", {})

    async def update_issue(
        self,
        issue_id: str,
        title: str | None = None,
        description: str | None = None,
        state_id: str | None = None,
        priority: int | None = None,
        label_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """Update an existing issue."""
        mutation = """
        mutation UpdateIssue($id: String!, $input: IssueUpdateInput!) {
            issueUpdate(id: $id, input: $input) {
                success
                issue {
                    id
                    identifier
                    title
                    url
                    state { name }
                    priority
                }
            }
        }
        """
        input_vars: dict[str, Any] = {}
        if title is not None:
            input_vars["title"] = title
        if description is not None:
            input_vars["description"] = description
        if state_id is not None:
            input_vars["stateId"] = state_id
        if priority is not None:
            input_vars["priority"] = priority
        if label_ids is not None:
            input_vars["labelIds"] = label_ids

        return (await self.execute(mutation, {"id": issue_id, "input": input_vars})).get("issueUpdate", {})

    async def search_issues(
        self,
        query: str,
        team_id: str | None = None,
        limit: int = 25,
    ) -> list[dict[str, Any]]:
        """Search issues by text query."""
        gql = """
        query SearchIssues($filter: IssueFilter, $first: Int) {
            issues(filter: $filter, first: $first) {
                nodes {
                    id
                    identifier
                    title
                    description
                    url
                    priority
                    state { id name }
                    labels { nodes { id name } }
                    project { id name }
                    assignee { name }
                    createdAt
                    updatedAt
                }
            }
        }
        """
        filter_var: dict[str, Any] = {
            "or": [
                {"title": {"containsIgnoreCase": query}},
                {"description": {"containsIgnoreCase": query}},
            ]
        }
        if team_id:
            filter_var["team"] = {"id": {"eq": team_id}}

        result = await self.execute(gql, {"filter": filter_var, "first": limit})
        return result.get("issues", {}).get("nodes", [])

    async def get_project_issues(
        self,
        project_id: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Get all issues for a Linear project."""
        gql = """
        query ProjectIssues($projectId: String!, $first: Int) {
            issues(filter: { project: { id: { eq: $projectId } } }, first: $first) {
                nodes {
                    id
                    identifier
                    title
                    url
                    priority
                    state { id name }
                    labels { nodes { id name } }
                    assignee { name }
                    createdAt
                    updatedAt
                }
            }
        }
        """
        result = await self.execute(gql, {"projectId": project_id, "first": limit})
        return result.get("issues", {}).get("nodes", [])

    async def get_teams(self) -> list[dict[str, Any]]:
        """List all teams."""
        gql = """
        query { teams { nodes { id name key } } }
        """
        return (await self.execute(gql)).get("teams", {}).get("nodes", [])

    async def get_projects(self, team_id: str | None = None) -> list[dict[str, Any]]:
        """List projects, optionally filtered by team."""
        if team_id:
            gql = """
            query Projects($teamId: String!) {
                projects(filter: { accessibleTeams: { id: { eq: $teamId } } }) {
                    nodes { id name state slugId }
                }
            }
            """
            result = await self.execute(gql, {"teamId": team_id})
        else:
            gql = """
            query { projects { nodes { id name state slugId } } }
            """
            result = await self.execute(gql)
        return result.get("projects", {}).get("nodes", [])

    async def get_labels(self, team_id: str | None = None) -> list[dict[str, Any]]:
        """List labels, optionally filtered by team."""
        if team_id:
            gql = """
            query Labels($teamId: String!) {
                issueLabels(filter: { team: { id: { eq: $teamId } } }) {
                    nodes { id name color }
                }
            }
            """
            result = await self.execute(gql, {"teamId": team_id})
        else:
            gql = """
            query { issueLabels { nodes { id name color } } }
            """
            result = await self.execute(gql)
        return result.get("issueLabels", {}).get("nodes", [])

    async def get_workflow_states(self, team_id: str) -> list[dict[str, Any]]:
        """Get workflow states for a team."""
        gql = """
        query States($teamId: String!) {
            workflowStates(filter: { team: { id: { eq: $teamId } } }) {
                nodes { id name type position }
            }
        }
        """
        result = await self.execute(gql, {"teamId": team_id})
        return result.get("workflowStates", {}).get("nodes", [])


class LinearAPIError(Exception):
    """Raised when Linear API returns an error."""
