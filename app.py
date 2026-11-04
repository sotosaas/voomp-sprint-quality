"""Sprint Quality Dashboard — Voomp

Entry point for the Streamlit application.
Clean architecture with separation of concerns.
"""

from pathlib import Path

import streamlit as st

from src.config import get_config, inject_secrets
from src.services import JiraService, MetricsService
from src.repositories import CacheRepository
from src.ui import apply_styles
from src.ui.components import Sidebar
from src.ui.pages import DashboardPage, OverviewPage


# ------------------------------------------------------------------
# Page Configuration
# ------------------------------------------------------------------

st.set_page_config(
    page_title="Sprint Quality · Voomp",
    page_icon="🐛",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------------------
# Apply CSS Styles
# ------------------------------------------------------------------

apply_styles(st)


# ------------------------------------------------------------------
# Inject Streamlit Secrets
# ------------------------------------------------------------------

def _inject_streamlit_secrets() -> None:
    """Inject secrets from Streamlit Cloud into config."""
    try:
        secrets_dict = {}
        for key in ("JIRA_URL", "JIRA_EMAIL", "JIRA_API_TOKEN"):
            val = st.secrets.get(key)
            if val:
                secrets_dict[key] = str(val)
        if secrets_dict:
            inject_secrets(secrets_dict)
    except Exception:
        pass  # Running locally without secrets


_inject_streamlit_secrets()


# ------------------------------------------------------------------
# Configuration Validation
# ------------------------------------------------------------------

config = get_config()
errors = config.jira.validate()

if errors:
    st.error("⚠️ Configuração incompleta. Verifique o arquivo `.env`:")
    for e in errors:
        st.markdown(f"- {e}")
    st.stop()


# ------------------------------------------------------------------
# Initialize Services
# ------------------------------------------------------------------

@st.cache_resource
def _get_services():
    """Initialize services (singleton pattern)."""
    cfg = get_config()
    cache_dir = Path(__file__).parent / ".cache"
    cache = CacheRepository(cache_dir, default_ttl=cfg.cache_ttl_seconds)
    jira = JiraService(cfg)
    metrics = MetricsService(cfg, jira, cache)
    return cfg, jira, metrics, cache


config, jira_service, metrics_service, cache_repo = _get_services()


# ------------------------------------------------------------------
# Session State
# ------------------------------------------------------------------

if "selected_project" not in st.session_state:
    st.session_state.selected_project = config.project_keys[0]
if "current_view" not in st.session_state:
    st.session_state.current_view = "dashboard"  # or "overview"


# ------------------------------------------------------------------
# Sidebar Navigation
# ------------------------------------------------------------------

def on_menu_select(key: str) -> None:
    """Handle menu selection."""
    if key == "overview":
        st.session_state.current_view = "overview"
    else:
        st.session_state.selected_project = key
        st.session_state.current_view = "dashboard"
    st.rerun()


def on_refresh() -> None:
    """Handle refresh button click."""
    # Clear Streamlit caches
    st.cache_data.clear()
    # Clear file cache
    cache_repo.clear()
    st.rerun()


sidebar = Sidebar(st, config)

# Determine current selection for sidebar highlighting
current_key = (
    "overview" if st.session_state.current_view == "overview"
    else st.session_state.selected_project
)

sidebar.render(
    selected_key=current_key,
    on_select=on_menu_select,
    on_refresh=on_refresh,
    show_overview=True,
)


# ------------------------------------------------------------------
# Main Content
# ------------------------------------------------------------------

if st.session_state.current_view == "overview":
    page = OverviewPage(st, config, metrics_service)
else:
    page = DashboardPage(st, config, jira_service, metrics_service)

page.render()
