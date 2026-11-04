"""Metrics calculation service.

Handles all metric computations: dev ranking, sprint trends, summaries.
Pure functions operating on domain models.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Callable

import pandas as pd

from src.config import AppConfig
from src.models import Issue, Sprint, DevMetrics, SprintMetrics, CardMetrics
from src.models.metrics import ProjectSummary
from src.services.jira_service import JiraService
from src.repositories.cache_repository import CacheRepository


class MetricsService:
    """Service for computing quality metrics."""

    def __init__(self, config: AppConfig, jira_service: JiraService, cache: CacheRepository) -> None:
        self._config = config
        self._jira = jira_service
        self._cache = cache

    # ------------------------------------------------------------------
    # Issue fetching with caching
    # ------------------------------------------------------------------

    def get_sprint_issues(
        self,
        project_key: str,
        sprint_id: int,
        force_refresh: bool = False,
    ) -> list[Issue]:
        """Get issues for a sprint with caching."""
        cache_key = f"{project_key}_sprint_{sprint_id}"

        if not force_refresh:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return [self._dict_to_issue(d) for d in cached]

        issues = self._jira.get_issues_in_sprint(sprint_id, project_key)
        self._cache.set(cache_key, [self._issue_to_dict(i) for i in issues])
        return issues

    def get_last_30_days_issues(
        self,
        project_key: str,
        force_refresh: bool = False,
    ) -> list[Issue]:
        """Get issues delivered in the last 30 days with caching."""
        cache_key = f"{project_key}_last30days"

        if not force_refresh:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return [self._dict_to_issue(d) for d in cached]

        issues = self._jira.get_issues_in_date_range(project_key, days=30)
        self._cache.set(cache_key, [self._issue_to_dict(i) for i in issues])
        return issues

    # ------------------------------------------------------------------
    # DataFrame builders
    # ------------------------------------------------------------------

    def build_issues_dataframe(
        self,
        project_key: str,
        sprint_id: int,
        sprint_name: str = "",
        force_refresh: bool = False,
    ) -> pd.DataFrame:
        """Build a DataFrame of issues for a single sprint."""
        issues = self.get_sprint_issues(project_key, sprint_id, force_refresh)
        return self._issues_to_dataframe(issues, project_key, sprint_id, sprint_name)

    def build_last_30_days_dataframe(
        self,
        project_key: str,
        force_refresh: bool = False,
    ) -> pd.DataFrame:
        """Build a DataFrame of issues delivered in the last 30 days."""
        issues = self.get_last_30_days_issues(project_key, force_refresh)
        return self._issues_to_dataframe(issues, project_key, None, "Últimos 30 dias")

    # ------------------------------------------------------------------
    # Metrics computations
    # ------------------------------------------------------------------

    def compute_dev_ranking(self, issues: list[Issue]) -> list[DevMetrics]:
        """Compute developer ranking by quality score."""
        # Group by developer
        by_dev: dict[str, list[Issue]] = defaultdict(list)
        for issue in issues:
            if not issue.is_subtask:
                by_dev[issue.assignee_name].append(issue)

        # Compute metrics
        metrics = []
        for name, dev_issues in by_dev.items():
            cards = len(dev_issues)
            bugs = sum(i.sub_bug_count for i in dev_issues)
            metrics.append(DevMetrics(name=name, cards_delivered=cards, total_sub_bugs=bugs))

        # Sort by quality score (descending)
        return sorted(metrics, key=lambda m: m.quality_score, reverse=True)

    def compute_card_ranking(self, issues: list[Issue], top_n: int = 20) -> list[CardMetrics]:
        """Get cards with most sub-bugs."""
        # Filter non-subtasks with bugs
        with_bugs = [i for i in issues if not i.is_subtask and i.sub_bug_count > 0]

        # Sort by bug count
        sorted_issues = sorted(with_bugs, key=lambda i: i.sub_bug_count, reverse=True)

        return [
            CardMetrics(
                key=i.key,
                summary=i.summary,
                assignee_name=i.assignee_name,
                sub_bug_count=i.sub_bug_count,
                issue_type=i.issue_type,
                jira_url=f"{self._config.jira.url}/browse/{i.key}",
            )
            for i in sorted_issues[:top_n]
        ]

    def compute_sprint_metrics(self, issues: list[Issue], sprint: Sprint) -> SprintMetrics:
        """Compute aggregated metrics for a sprint."""
        # Filter non-subtasks
        cards = [i for i in issues if not i.is_subtask]

        total_cards = len(cards)
        total_bugs = sum(i.sub_bug_count for i in cards)
        cards_with_bugs = sum(1 for i in cards if i.sub_bug_count > 0)

        return SprintMetrics(
            sprint_id=sprint.id,
            sprint_name=sprint.name,
            sprint_state=sprint.state,
            total_cards=total_cards,
            total_sub_bugs=total_bugs,
            cards_with_bugs=cards_with_bugs,
        )

    def compute_sprint_trend(
        self,
        project_key: str,
        last_n_sprints: int = 5,
        force_refresh: bool = False,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> list[SprintMetrics]:
        """Compute trend data across multiple sprints."""
        board = self._jira.get_board(project_key)
        if not board:
            return []

        # Get sprints for current year
        current_year = datetime.now().year
        all_sprints = self._jira.get_sprints(
            board["id"],
            state="active,closed",
            max_results=50,
            year=current_year,
        )

        # Take last N sprints
        sprints = all_sprints[-last_n_sprints:] if len(all_sprints) >= last_n_sprints else all_sprints
        if not sprints:
            return []

        # Fetch issues (with caching)
        metrics_list = []
        total = len(sprints)

        for idx, sprint in enumerate(sprints):
            issues = self.get_sprint_issues(project_key, sprint.id, force_refresh)
            metrics = self.compute_sprint_metrics(issues, sprint)
            metrics_list.append(metrics)

            if progress_callback:
                progress_callback(idx + 1, total)

        return metrics_list

    def compute_project_summary(
        self,
        project_key: str,
        force_refresh: bool = False,
    ) -> ProjectSummary:
        """Compute summary stats for a project (last 30 days)."""
        project = self._config.get_project(project_key)
        project_name = project.name if project else project_key

        issues = self.get_last_30_days_issues(project_key, force_refresh)
        
        if not issues:
            return ProjectSummary.empty(project_key, project_name)

        # Filter non-subtasks
        cards = [i for i in issues if not i.is_subtask]

        if not cards:
            return ProjectSummary.empty(project_key, project_name)

        # Compute dev ranking for top dev
        dev_ranking = self.compute_dev_ranking(cards)
        top_dev = dev_ranking[0] if dev_ranking else None

        return ProjectSummary(
            project_key=project_key,
            project_name=project_name,
            total_cards=len(cards),
            total_sub_bugs=sum(i.sub_bug_count for i in cards),
            cards_with_bugs=sum(1 for i in cards if i.sub_bug_count > 0),
            top_dev=top_dev.name if top_dev else "—",
            top_dev_score=top_dev.quality_score if top_dev else 0.0,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _issues_to_dataframe(
        self,
        issues: list[Issue],
        project_key: str,
        sprint_id: int | None,
        sprint_name: str,
    ) -> pd.DataFrame:
        """Convert issues to DataFrame."""
        project = self._config.get_project(project_key)
        project_name = project.name if project else project_key

        rows = [
            i.to_row(project_key, project_name, sprint_id, sprint_name, self._config.jira.url)
            for i in issues
            if not i.is_subtask
        ]

        if not rows:
            return self._empty_dataframe()

        df = pd.DataFrame(rows)
        df["sub_bug_count"] = df["sub_bug_count"].fillna(0).astype(int)
        df["created"] = pd.to_datetime(df["created"], errors="coerce", utc=True)
        df["resolution_date"] = pd.to_datetime(df["resolution_date"], errors="coerce", utc=True)

        return df

    @staticmethod
    def _empty_dataframe() -> pd.DataFrame:
        """Return an empty DataFrame with expected schema."""
        return pd.DataFrame(columns=[
            "key", "summary", "assignee_name", "assignee_email",
            "project_key", "project_name", "sprint_id", "sprint_name",
            "issue_type", "sub_bug_count", "sub_bugs",
            "created", "resolution_date", "jira_url",
        ])

    @staticmethod
    def _issue_to_dict(issue: Issue) -> dict:
        """Convert Issue to dict for caching."""
        return {
            "key": issue.key,
            "summary": issue.summary,
            "assignee_name": issue.assignee_name,
            "assignee_email": issue.assignee_email,
            "status": issue.status,
            "issue_type": issue.issue_type,
            "is_subtask": issue.is_subtask,
            "created": issue.created.isoformat() if issue.created else None,
            "resolution_date": issue.resolution_date.isoformat() if issue.resolution_date else None,
            "sub_bugs": [{"key": sb.key, "summary": sb.summary, "type": sb.issue_type} for sb in issue.sub_bugs],
        }

    @staticmethod
    def _dict_to_issue(data: dict) -> Issue:
        """Convert dict to Issue (from cache)."""
        from src.models import SubBug

        sub_bugs = [
            SubBug(key=sb["key"], summary=sb["summary"], issue_type=sb.get("type", "Sub-bug"))
            for sb in data.get("sub_bugs", [])
        ]

        created = None
        if data.get("created"):
            try:
                created = datetime.fromisoformat(data["created"])
            except (ValueError, TypeError):
                pass

        resolution_date = None
        if data.get("resolution_date"):
            try:
                resolution_date = datetime.fromisoformat(data["resolution_date"])
            except (ValueError, TypeError):
                pass

        return Issue(
            key=data["key"],
            summary=data["summary"],
            assignee_name=data["assignee_name"],
            assignee_email=data.get("assignee_email", ""),
            status=data.get("status", ""),
            issue_type=data.get("issue_type", ""),
            is_subtask=data.get("is_subtask", False),
            created=created,
            resolution_date=resolution_date,
            sub_bugs=sub_bugs,
        )
