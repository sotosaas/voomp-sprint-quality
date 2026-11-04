"""Metrics domain models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class DevMetrics:
    """Developer quality metrics."""

    name: str
    cards_delivered: int
    total_sub_bugs: int

    @property
    def bug_ratio(self) -> float:
        """Bugs per card ratio."""
        if self.cards_delivered == 0:
            return 0.0
        return round(self.total_sub_bugs / self.cards_delivered, 2)

    @property
    def quality_score(self) -> float:
        """Quality score: cards / (bugs + 1). Higher is better."""
        return round(self.cards_delivered / (self.total_sub_bugs + 1), 2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "assignee_name": self.name,
            "cards_delivered": self.cards_delivered,
            "total_sub_bugs": self.total_sub_bugs,
            "bug_ratio": self.bug_ratio,
            "quality_score": self.quality_score,
        }


@dataclass(frozen=True, slots=True)
class SprintMetrics:
    """Aggregated sprint metrics."""

    sprint_id: int
    sprint_name: str
    sprint_state: str
    total_cards: int
    total_sub_bugs: int
    cards_with_bugs: int

    @property
    def avg_bugs_per_card(self) -> float:
        if self.total_cards == 0:
            return 0.0
        return round(self.total_sub_bugs / self.total_cards, 2)

    @property
    def bug_rate_pct(self) -> float:
        """Percentage of cards with at least one bug."""
        if self.total_cards == 0:
            return 0.0
        return round((self.cards_with_bugs / self.total_cards) * 100, 1)

    def to_dict(self) -> dict[str, Any]:
        return {
            "sprint_id": self.sprint_id,
            "sprint_name": self.sprint_name,
            "sprint_state": self.sprint_state,
            "total_cards": self.total_cards,
            "total_sub_bugs": self.total_sub_bugs,
            "cards_with_bugs": self.cards_with_bugs,
            "avg_bugs_per_card": self.avg_bugs_per_card,
            "bug_rate_pct": self.bug_rate_pct,
        }


@dataclass(frozen=True, slots=True)
class CardMetrics:
    """Card-level metrics for ranking."""

    key: str
    summary: str
    assignee_name: str
    sub_bug_count: int
    issue_type: str
    jira_url: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "summary": self.summary,
            "assignee_name": self.assignee_name,
            "sub_bug_count": self.sub_bug_count,
            "issue_type": self.issue_type,
            "jira_url": self.jira_url,
        }


@dataclass(slots=True)
class ProjectSummary:
    """Summary metrics for a project over a time period."""

    project_key: str
    project_name: str
    total_cards: int
    total_sub_bugs: int
    cards_with_bugs: int
    top_dev: str
    top_dev_score: float

    @property
    def avg_bugs_per_card(self) -> float:
        if self.total_cards == 0:
            return 0.0
        return round(self.total_sub_bugs / self.total_cards, 2)

    @property
    def bug_rate_pct(self) -> float:
        if self.total_cards == 0:
            return 0.0
        return round((self.cards_with_bugs / self.total_cards) * 100, 1)

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_key": self.project_key,
            "project_name": self.project_name,
            "total_cards": self.total_cards,
            "total_sub_bugs": self.total_sub_bugs,
            "cards_with_bugs": self.cards_with_bugs,
            "avg_bugs_per_card": self.avg_bugs_per_card,
            "bug_rate_pct": self.bug_rate_pct,
            "top_dev": self.top_dev,
            "top_dev_score": self.top_dev_score,
        }

    @classmethod
    def empty(cls, project_key: str, project_name: str) -> ProjectSummary:
        return cls(
            project_key=project_key,
            project_name=project_name,
            total_cards=0,
            total_sub_bugs=0,
            cards_with_bugs=0,
            top_dev="—",
            top_dev_score=0.0,
        )
