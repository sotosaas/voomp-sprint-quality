"""jira_client.py

Optimized Jira Cloud API client with connection pooling and parallel fetching.
"""

import re
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import config as _config
from config import PROJECTS, PRODUCTION_STATUSES, SUB_BUG_ISSUE_TYPE


class JiraAuthError(Exception):
    """Raised when Jira returns 401 or 403."""
    pass


class JiraNotFoundError(Exception):
    """Raised when Jira returns 404."""
    pass


class JiraClient:
    """Thin wrapper around the Jira Cloud REST API with connection pooling."""

    # Class-level session for connection reuse across instances
    _session: requests.Session | None = None

    def __init__(self):
        self.base_url = _config.JIRA_URL.rstrip("/")
        self._email = _config.JIRA_EMAIL
        self._token = _config.JIRA_API_TOKEN

    @classmethod
    def _get_session(cls) -> requests.Session:
        """Return a shared session with connection pooling and retry logic."""
        if cls._session is None:
            cls._session = requests.Session()
            
            # Configure retry strategy
            retry_strategy = Retry(
                total=3,
                backoff_factor=0.5,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["HEAD", "GET", "POST", "OPTIONS"],
            )
            
            # Mount adapter with connection pooling
            adapter = HTTPAdapter(
                max_retries=retry_strategy,
                pool_connections=10,
                pool_maxsize=20,
            )
            cls._session.mount("https://", adapter)
            cls._session.mount("http://", adapter)
            
            cls._session.headers.update({
                "Accept": "application/json",
                "Content-Type": "application/json",
            })
        
        return cls._session

    @property
    def _auth(self):
        return (self._email, self._token)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get(self, endpoint: str, params: dict | None = None, timeout: int = 15) -> dict | list:
        """Execute a GET request with connection pooling."""
        url = f"{self.base_url}{endpoint}"
        session = self._get_session()
        
        try:
            response = session.get(url, auth=self._auth, params=params, timeout=timeout)
        except requests.exceptions.ConnectionError as exc:
            raise ConnectionError(
                f"Não foi possível conectar ao Jira ({self.base_url})."
            ) from exc
        except requests.exceptions.Timeout as exc:
            raise TimeoutError(f"Timeout ao conectar ao Jira ({url}).") from exc

        if response.status_code in (401, 403):
            raise JiraAuthError("Credenciais inválidas.")
        if response.status_code == 404:
            raise JiraNotFoundError(f"Recurso não encontrado: {url}")

        response.raise_for_status()
        return response.json()

    def _post(self, endpoint: str, body: dict, timeout: int = 20) -> dict | list:
        """Execute a POST request with connection pooling."""
        url = f"{self.base_url}{endpoint}"
        session = self._get_session()
        
        try:
            response = session.post(url, auth=self._auth, json=body, timeout=timeout)
        except requests.exceptions.ConnectionError as exc:
            raise ConnectionError(
                f"Não foi possível conectar ao Jira ({self.base_url})."
            ) from exc
        except requests.exceptions.Timeout as exc:
            raise TimeoutError(f"Timeout ao conectar ao Jira ({url}).") from exc

        if response.status_code in (401, 403):
            raise JiraAuthError("Credenciais inválidas.")
        if response.status_code == 404:
            raise JiraNotFoundError(f"Recurso não encontrado: {url}")

        response.raise_for_status()
        return response.json()

    # ------------------------------------------------------------------
    # Auth / connection
    # ------------------------------------------------------------------

    def get_current_user(self) -> dict:
        """Return the authenticated user's profile."""
        return self._get("/rest/api/3/myself")

    def test_connection(self) -> dict:
        """Validate credentials and return basic user info."""
        return self.get_current_user()

    # ------------------------------------------------------------------
    # Projects
    # ------------------------------------------------------------------

    def get_projects(self, project_keys: list[str] | None = None) -> list[dict]:
        """Fetch project details."""
        params: dict = {"maxResults": 50}
        if project_keys:
            params["keys"] = project_keys
        data = self._get("/rest/api/3/project/search", params=params)
        return data.get("values", [])

    def get_project(self, project_key: str) -> dict:
        """Fetch a single project by key."""
        return self._get(f"/rest/api/3/project/{project_key}")

    # ------------------------------------------------------------------
    # Boards — with caching
    # ------------------------------------------------------------------
    
    _board_cache: dict[str, dict | None] = {}

    def get_board(self, project_key: str) -> dict | None:
        """Return the first Scrum board associated with a project (cached)."""
        if project_key in self._board_cache:
            return self._board_cache[project_key]
        
        params = {"projectKeyOrId": project_key, "type": "scrum", "maxResults": 10}
        data = self._get("/rest/agile/1.0/board", params=params)
        boards = data.get("values", [])

        if not boards:
            params.pop("type")
            data = self._get("/rest/agile/1.0/board", params=params)
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
    ) -> list[dict]:
        """List sprints for a given board, optionally filtered by year."""
        params = {"state": state, "maxResults": max_results}
        data = self._get(f"/rest/agile/1.0/board/{board_id}/sprint", params=params)
        sprints = data.get("values", [])

        if year is not None:
            year_suffix = str(year)[-2:]
            pattern = re.compile(rf"\bSP\s+{re.escape(year_suffix)}\.", re.IGNORECASE)
            sprints = [s for s in sprints if pattern.search(s.get("name", ""))]

            def _sort_key(s: dict):
                m = re.search(r"SP\s+(\d{2})\.(\d+)\.(\d+)", s.get("name", ""), re.IGNORECASE)
                if m:
                    return (int(m.group(1)), int(m.group(2)), int(m.group(3)))
                return (0, 0, 0)

            sprints.sort(key=_sort_key)
        else:
            sprints.sort(key=lambda s: s.get("startDate", ""), reverse=True)

        return sprints

    def get_sprints_for_project(
        self,
        project_key: str,
        state: str = "active,closed",
        max_results: int = 50,
        year: int | None = None,
    ) -> list[dict]:
        """Convenience: get sprints for a project, optionally filtered by year."""
        board = self.get_board(project_key)
        if not board:
            return []
        return self.get_sprints(board["id"], state=state, max_results=max_results, year=year)

    # ------------------------------------------------------------------
    # Issues — optimized single-page fetch for typical sprint sizes
    # ------------------------------------------------------------------

    def get_issues_in_sprint(
        self,
        sprint_id: int,
        project_key: str,
        max_results: int = 200,
    ) -> list[dict]:
        """Fetch issues in a sprint that reached production.
        
        Optimized: most sprints have <100 issues, so we fetch in one request.
        """
        status_list = ", ".join(f'"{s}"' for s in PRODUCTION_STATUSES)
        jql = (
            f'project = "{project_key}" '
            f'AND sprint = {sprint_id} '
            f'AND status in ({status_list}) '
            f'AND issueType in standardIssueTypes()'
        )

        # Minimal fields for faster response
        fields = ["summary", "assignee", "status", "issuetype", "subtasks", "created", "resolutiondate"]
        
        body: dict = {"jql": jql, "fields": fields, "maxResults": max_results}
        data = self._post("/rest/api/3/search/jql", body)
        issues = data.get("issues", [])
        
        # Only paginate if we hit the limit (rare for sprints)
        next_page_token = data.get("nextPageToken")
        while next_page_token and len(issues) < 500:  # Safety cap
            body["nextPageToken"] = next_page_token
            data = self._post("/rest/api/3/search/jql", body)
            issues.extend(data.get("issues", []))
            next_page_token = data.get("nextPageToken")

        return [self._normalize_issue(issue) for issue in issues]

    def get_issues_in_date_range(
        self,
        project_key: str,
        days: int = 30,
        max_results: int = 500,
    ) -> list[dict]:
        """Fetch issues that reached production in the last N days."""
        status_list = ", ".join(f'"{s}"' for s in PRODUCTION_STATUSES)
        jql = (
            f'project = "{project_key}" '
            f'AND status in ({status_list}) '
            f'AND status CHANGED TO "{PRODUCTION_STATUSES[0]}" DURING (-{days}d, now()) '
            f'AND issueType in standardIssueTypes()'
        )

        fields = ["summary", "assignee", "status", "issuetype", "subtasks", "created", "resolutiondate", "sprint"]
        all_issues: list[dict] = []
        next_page_token: str | None = None

        while True:
            body: dict = {"jql": jql, "fields": fields, "maxResults": max_results}
            if next_page_token:
                body["nextPageToken"] = next_page_token

            data = self._post("/rest/api/3/search/jql", body)
            issues = data.get("issues", [])
            all_issues.extend(issues)

            next_page_token = data.get("nextPageToken")
            if not next_page_token or not issues:
                break

        return [
            self._normalize_issue(issue) for issue in all_issues
            if not (issue.get("fields", {}).get("issuetype") or {}).get("subtask", False)
        ]

    # ------------------------------------------------------------------
    # Parallel fetching — for trend data
    # ------------------------------------------------------------------

    def get_issues_for_sprints_parallel(
        self,
        sprints: list[dict],
        project_key: str,
        progress_callback: Callable[[int, int], None] | None = None,
        max_workers: int = 5,
    ) -> dict[int, list[dict]]:
        """Fetch issues for multiple sprints in parallel.
        
        Args:
            sprints: List of sprint dicts with 'id' and 'name'.
            project_key: Jira project key.
            progress_callback: Optional callback(completed, total) for progress updates.
            max_workers: Number of parallel threads.
        
        Returns:
            Dict mapping sprint_id -> list of normalized issues.
        """
        results: dict[int, list[dict]] = {}
        total = len(sprints)
        completed = 0

        def fetch_one(sprint: dict) -> tuple[int, list[dict]]:
            issues = self.get_issues_in_sprint(sprint["id"], project_key)
            return sprint["id"], issues

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
    # Internal normalizers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_issue(raw: dict) -> dict:
        """Flatten a raw Jira issue response into a clean dict."""
        fields = raw.get("fields", {})
        assignee = fields.get("assignee") or {}
        status = fields.get("status") or {}
        issue_type = fields.get("issuetype") or {}

        subtasks = fields.get("subtasks") or []
        subtask_details = [
            {
                "key": st.get("key", ""),
                "type": (st.get("fields", {}).get("issuetype") or {}).get("name", ""),
                "summary": (st.get("fields", {}) or {}).get("summary", ""),
            }
            for st in subtasks
            if st.get("key")
        ]

        sub_bugs = [s for s in subtask_details if s["type"] == SUB_BUG_ISSUE_TYPE]

        return {
            "key": raw.get("key", ""),
            "summary": fields.get("summary", ""),
            "assignee_name": assignee.get("displayName", "Sem responsável"),
            "assignee_email": assignee.get("emailAddress", ""),
            "status": status.get("name", ""),
            "issue_type": issue_type.get("name", ""),
            "is_subtask": bool(issue_type.get("subtask", False)),
            "subtask_details": subtask_details,
            "sub_bugs": sub_bugs,
            "sub_bug_count": len(sub_bugs),
            "created": fields.get("created", ""),
            "resolution_date": fields.get("resolutiondate", ""),
        }


# ------------------------------------------------------------------
# CLI entry point
# ------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    from config import validate_config

    errors = validate_config()
    if errors:
        print("❌ Configuração incompleta:")
        for e in errors:
            print(f"   • {e}")
        raise SystemExit(1)

    client = JiraClient()
    print("🔌 Testando conexão com o Jira...")
    user = client.test_connection()
    print(f"✅ Conectado como: {user.get('displayName')} ({user.get('emailAddress')})")
