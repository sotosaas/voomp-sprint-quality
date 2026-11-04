"""Jira business service - orchestrates API calls and transforms data.

This is the main service for interacting with Jira. It:
- Builds JQL queries
- Transforms raw API responses to domain models
- Handles parallel fetching for performance
"""

from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from functools import lru_cache
from typing import Any, Callable

from src.config import AppConfig
from src.models import Issue, Sprint
from src.services.jira_api import JiraApiClient


class JiraService:
    """High-level Jira service with domain models and business logic."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._api = JiraApiClient(config.jira)
        self._board_cache: dict[str, dict | None] = {}

    # ------------------------------------------------------------------
    # Connection / Auth
    # ------------------------------------------------------------------

    def test_connection(self) -> dict[str, Any]:
        """Test connection and return current user info."""
        return self._api.test_connection()

    # ------------------------------------------------------------------
    # Projects
    # ------------------------------------------------------------------

    def get_project(self, project_key: str) -> dict[str, Any]:
        """Fetch a single project by key."""
        return self._api.get(f"/rest/api/3/project/{project_key}")

    # ------------------------------------------------------------------
    # Boards (with caching)
    # ------------------------------------------------------------------

    def get_board(self, project_key: str) -> dict | None:
        """Get the Scrum board for a project (cached)."""
        if project_key in self._board_cache:
            return self._board_cache[project_key]

        params: dict[str, Any] = {
            "projectKeyOrId": project_key,
            "type": "scrum",
            "maxResults": 10,
        }
        data = self._api.get("/rest/agile/1.0/board", params=params)
        boards = data.get("values", [])

        # Fallback: try without type filter
        if not boards:
            params.pop("type")
            data = self._api.get("/rest/agile/1.0/board", params=params)
            boards = data.get("values", [])

        board = boards[0] if boards else None
        self._board_cache[project_key] = board
        return board

    # ------------------------------------------------------------------
    # Sprints
    # ------------------------------------------------------------------

    def get_sprints(
        self,
        board_id: int,
        state: str = "active,closed",
        max_results: int = 50,
        year: int | None = None,
    ) -> list[Sprint]:
        """Get sprints for a board, optionally filtered by year."""
        params = {"state": state, "maxResults": max_results}
        data = self._api.get(f"/rest/agile/1.0/board/{board_id}/sprint", params=params)
        raw_sprints = data.get("values", [])

        # Filter by year pattern (e.g., "SP 25.1.1")
        if year is not None:
            year_suffix = str(year)[-2:]
            pattern = re.compile(rf"\bSP\s+{re.escape(year_suffix)}\.", re.IGNORECASE)
            raw_sprints = [s for s in raw_sprints if pattern.search(s.get("name", ""))]

            # Sort by sprint number (e.g., SP 25.1.1 -> (25, 1, 1))
            def sort_key(s: dict) -> tuple[int, int, int]:
                m = re.search(r"SP\s+(\d{2})\.(\d+)\.(\d+)", s.get("name", ""), re.IGNORECASE)
                if m:
                    return (int(m.group(1)), int(m.group(2)), int(m.group(3)))
                return (0, 0, 0)

            raw_sprints.sort(key=sort_key)
        else:
            raw_sprints.sort(key=lambda s: s.get("startDate", ""), reverse=True)

        return [Sprint.from_raw_jira(s) for s in raw_sprints]

    def get_sprints_for_project(
        self,
        project_key: str,
        state: str = "active,closed",
        max_results: int = 50,
        year: int | None = None,
    ) -> list[Sprint]:
        """Convenience: get sprints for a project."""
        board = self.get_board(project_key)
        if not board:
            return []
        return self.get_sprints(board["id"], state=state, max_results=max_results, year=year)

    # ------------------------------------------------------------------
    # Issues
    # ------------------------------------------------------------------

    def get_issues_in_sprint(
        self,
        sprint_id: int,
        project_key: str,
        max_results: int = 200,
    ) -> list[Issue]:
        """Fetch issues in a sprint that reached production."""
        jql = self._build_sprint_jql(project_key, sprint_id)
        issues = self._fetch_issues(jql, max_results)
        return [Issue.from_raw_jira(i, self._config.sub_bug_issue_type) for i in issues]

    def get_issues_in_date_range(
        self,
        project_key: str,
        days: int = 30,
        max_results: int = 500,
    ) -> list[Issue]:
        """Fetch issues that reached production in the last N days."""
        jql = self._build_date_range_jql(project_key, days)
        issues = self._fetch_issues(jql, max_results)
        
        # Filter out subtasks
        return [
            Issue.from_raw_jira(i, self._config.sub_bug_issue_type)
            for i in issues
            if not (i.get("fields", {}).get("issuetype") or {}).get("subtask", False)
        ]

    def get_issues_for_sprints_parallel(
        self,
        sprints: list[Sprint],
        project_key: str,
        progress_callback: Callable[[int, int], None] | None = None,
        max_workers: int = 5,
    ) -> dict[int, list[Issue]]:
        """Fetch issues for multiple sprints in parallel."""
        results: dict[int, list[Issue]] = {}
        total = len(sprints)
        completed = 0

        def fetch_one(sprint: Sprint) -> tuple[int, list[Issue]]:
            issues = self.get_issues_in_sprint(sprint.id, project_key)
            return sprint.id, issues

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(fetch_one, s): s for s in sprints}

            for future in as_completed(futures):
                sprint_id, issues = future.result()
                results[sprint_id] = issues
                completed += 1
                if progress_callback:
                    progress_callback(completed, total)

        return results

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_sprint_jql(self, project_key: str, sprint_id: int) -> str:
        """Build JQL for sprint issues."""
        status_list = ", ".join(f'"{s}"' for s in self._config.production_statuses)
        return (
            f'project = "{project_key}" '
            f'AND sprint = {sprint_id} '
            f'AND status in ({status_list}) '
            f'AND issueType in standardIssueTypes()'
        )

    def _build_date_range_jql(self, project_key: str, days: int) -> str:
        """Build JQL for date range issues."""
        status_list = ", ".join(f'"{s}"' for s in self._config.production_statuses)
        primary_status = self._config.production_statuses[0]
        return (
            f'project = "{project_key}" '
            f'AND status in ({status_list}) '
            f'AND status CHANGED TO "{primary_status}" DURING (-{days}d, now()) '
            f'AND issueType in standardIssueTypes()'
        )

    def _fetch_issues(self, jql: str, max_results: int) -> list[dict[str, Any]]:
        """Fetch issues with pagination."""
        fields = ["summary", "assignee", "status", "issuetype", "subtasks", "created", "resolutiondate"]
        body: dict[str, Any] = {"jql": jql, "fields": fields, "maxResults": max_results}

        data = self._api.post("/rest/api/3/search/jql", body)
        issues = data.get("issues", [])

        # Paginate if needed (rare for sprints)
        next_page_token = data.get("nextPageToken")
        while next_page_token and len(issues) < 500:
            body["nextPageToken"] = next_page_token
            data = self._api.post("/rest/api/3/search/jql", body)
            issues.extend(data.get("issues", []))
            next_page_token = data.get("nextPageToken")

        return issues
