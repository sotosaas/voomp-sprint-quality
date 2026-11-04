"""Issue and SubBug domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class SubBug:
    """Represents a sub-bug (subtask of type Sub-bug)."""

    key: str
    summary: str
    issue_type: str = "Sub-bug"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SubBug:
        return cls(
            key=data.get("key", ""),
            summary=data.get("summary", ""),
            issue_type=data.get("type", "Sub-bug"),
        )


@dataclass(slots=True)
class Issue:
    """Represents a Jira issue with its sub-bugs."""

    key: str
    summary: str
    assignee_name: str
    assignee_email: str
    status: str
    issue_type: str
    is_subtask: bool
    created: datetime | None
    resolution_date: datetime | None
    sub_bugs: list[SubBug] = field(default_factory=list)

    @property
    def sub_bug_count(self) -> int:
        return len(self.sub_bugs)

    @property
    def has_bugs(self) -> bool:
        return self.sub_bug_count > 0

    def to_row(self, project_key: str, project_name: str, sprint_id: int | None, sprint_name: str, jira_base_url: str) -> dict[str, Any]:
        """Convert to DataFrame row dict."""
        return {
            "key": self.key,
            "summary": self.summary,
            "assignee_name": self.assignee_name,
            "assignee_email": self.assignee_email,
            "project_key": project_key,
            "project_name": project_name,
            "sprint_id": sprint_id,
            "sprint_name": sprint_name,
            "issue_type": self.issue_type,
            "sub_bug_count": self.sub_bug_count,
            "sub_bugs": [{"key": sb.key, "summary": sb.summary} for sb in self.sub_bugs],
            "created": self.created,
            "resolution_date": self.resolution_date,
            "jira_url": f"{jira_base_url}/browse/{self.key}",
        }

    @classmethod
    def from_raw_jira(cls, raw: dict[str, Any], sub_bug_type: str = "Sub-bug") -> Issue:
        """Create Issue from raw Jira API response."""
        fields = raw.get("fields", {})
        assignee = fields.get("assignee") or {}
        status = fields.get("status") or {}
        issue_type = fields.get("issuetype") or {}

        # Parse subtasks
        subtasks = fields.get("subtasks") or []
        sub_bugs: list[SubBug] = []
        
        for st in subtasks:
            st_fields = st.get("fields", {}) or {}
            st_type = (st_fields.get("issuetype") or {}).get("name", "")
            if st_type == sub_bug_type:
                sub_bugs.append(SubBug(
                    key=st.get("key", ""),
                    summary=st_fields.get("summary", ""),
                    issue_type=st_type,
                ))

        # Parse dates
        created = cls._parse_datetime(fields.get("created"))
        resolution_date = cls._parse_datetime(fields.get("resolutiondate"))

        return cls(
            key=raw.get("key", ""),
            summary=fields.get("summary", ""),
            assignee_name=assignee.get("displayName", "Sem responsável"),
            assignee_email=assignee.get("emailAddress", ""),
            status=status.get("name", ""),
            issue_type=issue_type.get("name", ""),
            is_subtask=bool(issue_type.get("subtask", False)),
            created=created,
            resolution_date=resolution_date,
            sub_bugs=sub_bugs,
        )

    @staticmethod
    def _parse_datetime(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            # Jira returns ISO format with timezone
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None
