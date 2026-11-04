"""Sprint domain model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class Sprint:
    """Represents a Jira sprint."""

    id: int
    name: str
    state: str  # 'active', 'closed', 'future'
    start_date: datetime | None = None
    end_date: datetime | None = None
    complete_date: datetime | None = None

    @property
    def is_active(self) -> bool:
        return self.state == "active"

    @property
    def is_closed(self) -> bool:
        return self.state == "closed"

    @property
    def status_label(self) -> str:
        return "🟢 Ativa" if self.is_active else "✅ Fechada"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "state": self.state,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
        }

    @classmethod
    def from_raw_jira(cls, raw: dict[str, Any]) -> Sprint:
        """Create Sprint from raw Jira API response."""
        return cls(
            id=raw.get("id", 0),
            name=raw.get("name", ""),
            state=raw.get("state", ""),
            start_date=cls._parse_datetime(raw.get("startDate")),
            end_date=cls._parse_datetime(raw.get("endDate")),
            complete_date=cls._parse_datetime(raw.get("completeDate")),
        )

    @staticmethod
    def _parse_datetime(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None
