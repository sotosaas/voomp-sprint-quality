import os
from dotenv import load_dotenv

load_dotenv()

JIRA_URL       = os.getenv("JIRA_URL", "https://cogna.atlassian.net")
JIRA_EMAIL     = os.getenv("JIRA_EMAIL", "")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")

# --- Projects mapping: Jira project key → product display name ---
PROJECTS = {
    "VADM": "Admin",
    "VPLY": "Play",
    "VMPG": "Meios de Pagamento",
    "VSUS": "Sustentação",
    "VBEP": "Backoffice ERP",
}

# --- Issue type used for bugs (sub-tasks) ---
SUB_BUG_ISSUE_TYPE = "Sub-bug"

# --- Statuses that mark a card as delivered (used in JQL IN clause) ---
PRODUCTION_STATUSES = (
    "Em produção",
    "Concluído",
    "Aceito",
    "Pendente de Produção",
)

# Keep single-value alias for display/messages
PRODUCTION_STATUS = PRODUCTION_STATUSES[0]

# --- Consistent color palette per project (used across all charts) ---
PROJECT_COLORS = {
    "VADM": "#4c7be1",  # blue       — Admin
    "VPLY": "#50fa7b",  # green      — Play
    "VMPG": "#ff79c6",  # pink       — Meios de Pagamento
    "VSUS": "#f5a623",  # orange     — Sustentação
    "VBEP": "#bd93f9",  # purple     — Backoffice ERP
}

# --- Cache TTL in seconds (15 minutes) ---
CACHE_TTL_SECONDS = 900

def validate_config() -> list[str]:
    """Returns a list of error messages if any required config is missing."""
    errors = []
    if not JIRA_URL:
        errors.append("JIRA_URL não configurado no .env")
    if not JIRA_EMAIL:
        errors.append("JIRA_EMAIL não configurado no .env")
    if not JIRA_API_TOKEN:
        errors.append("JIRA_API_TOKEN não configurado no .env")
    return errors
