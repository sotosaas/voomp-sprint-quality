"""Configuration module with typed dataclasses.

All configuration is centralized here with proper validation and typing.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Sequence

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True, slots=True)
class JiraConfig:
    """Jira API connection settings."""

    url: str
    email: str
    api_token: str

    def __post_init__(self) -> None:
        # Normalize URL (remove trailing slash)
        object.__setattr__(self, "url", self.url.rstrip("/"))

    @property
    def is_valid(self) -> bool:
        return bool(self.url and self.email and self.api_token)

    def validate(self) -> list[str]:
        """Return list of validation errors (empty if valid)."""
        errors: list[str] = []
        if not self.url:
            errors.append("JIRA_URL não configurado")
        if not self.email:
            errors.append("JIRA_EMAIL não configurado")
        if not self.api_token:
            errors.append("JIRA_API_TOKEN não configurado")
        return errors


@dataclass(frozen=True, slots=True)
class Project:
    """Represents a Jira project."""

    key: str
    name: str
    color: str
    emoji: str


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Application-wide settings."""

    # Jira settings
    jira: JiraConfig

    # Projects
    projects: tuple[Project, ...]

    # Issue types and statuses
    sub_bug_issue_type: str = "Sub-bug"
    production_statuses: tuple[str, ...] = (
        "Em produção",
        "Concluído",
        "Aceito",
        "Pendente de Produção",
    )

    # Cache settings
    cache_ttl_seconds: int = 900  # 15 minutes
    streamlit_cache_ttl: int = 1800  # 30 minutes

    @property
    def project_keys(self) -> list[str]:
        return [p.key for p in self.projects]

    @property
    def project_map(self) -> dict[str, str]:
        """Map project key to display name."""
        return {p.key: p.name for p in self.projects}

    @property
    def project_colors(self) -> dict[str, str]:
        """Map project key to color."""
        return {p.key: p.color for p in self.projects}

    @property
    def project_emojis(self) -> dict[str, str]:
        """Map project key to emoji."""
        return {p.key: p.emoji for p in self.projects}

    def get_project(self, key: str) -> Project | None:
        """Get project by key."""
        for p in self.projects:
            if p.key == key:
                return p
        return None


# Default projects configuration
DEFAULT_PROJECTS: tuple[Project, ...] = (
    Project(key="VADM", name="Admin", color="#4c7be1", emoji="⚙️"),
    Project(key="VPLY", name="Play", color="#50fa7b", emoji="▶️"),
    Project(key="VMPG", name="Meios de Pagamento", color="#ff79c6", emoji="💳"),
    Project(key="VSUS", name="Sustentação", color="#f5a623", emoji="🔧"),
    Project(key="VBEP", name="Backoffice ERP", color="#bd93f9", emoji="📊"),
)


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    """Get the application configuration (singleton).
    
    Configuration is loaded from environment variables and cached.
    """
    jira = JiraConfig(
        url=os.getenv("JIRA_URL", "https://cogna.atlassian.net"),
        email=os.getenv("JIRA_EMAIL", ""),
        api_token=os.getenv("JIRA_API_TOKEN", ""),
    )

    return AppConfig(
        jira=jira,
        projects=DEFAULT_PROJECTS,
    )


def inject_secrets(secrets: dict[str, str]) -> None:
    """Inject Streamlit secrets into configuration.
    
    This clears the config cache and re-creates with injected values.
    """
    get_config.cache_clear()

    # Update environment variables
    for key in ("JIRA_URL", "JIRA_EMAIL", "JIRA_API_TOKEN"):
        if key in secrets:
            os.environ[key] = str(secrets[key])
