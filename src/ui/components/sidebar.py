"""Sidebar component following Greenn/Voomp design patterns."""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.config import AppConfig, Project

if TYPE_CHECKING:
    import streamlit


class Sidebar:
    """Sidebar navigation component.
    
    Uses native Streamlit buttons for maximum compatibility.
    """

    def __init__(self, st: "streamlit", config: AppConfig) -> None:
        self._st = st
        self._config = config

    def render(
        self,
        selected_key: str,
        on_select: callable = None,
        on_refresh: callable = None,
        show_overview: bool = True,
    ) -> str | None:
        """Render the sidebar and return the selected project key.
        
        Args:
            selected_key: Currently selected project key or 'overview'
            on_select: Callback when a menu item is selected
            on_refresh: Callback when refresh button is clicked
            show_overview: Whether to show the overview link
            
        Returns:
            Selected project key (or 'overview') if changed, None otherwise
        """
        new_selection = None

        with self._st.sidebar:
            # Logo
            self._st.markdown("""
            <div style="display: flex; align-items: center; margin-bottom: 20px; padding: 10px 0;">
                <span style="font-size: 24px; margin-right: 10px;">🐛</span>
                <span style="font-weight: 700; font-size: 16px; color: #333;">Sprint Quality</span>
            </div>
            """, unsafe_allow_html=True)

            # Overview button
            if show_overview:
                is_overview_active = selected_key == "overview"
                overview_type = "primary" if is_overview_active else "secondary"
                if self._st.button("📊 Visão Geral", key="menu_overview", use_container_width=True, type=overview_type):
                    if not is_overview_active:
                        new_selection = "overview"

            self._st.markdown("---")

            # Project menu items
            for project in self._config.projects:
                is_active = selected_key == project.key
                btn_type = "primary" if is_active else "secondary"
                if self._st.button(f"{project.emoji} {project.name}", key=f"menu_{project.key}", use_container_width=True, type=btn_type):
                    if not is_active:
                        new_selection = project.key

            self._st.markdown("---")

            # Refresh button
            if self._st.button("🔄 Atualizar dados", key="refresh_btn", use_container_width=True):
                if on_refresh:
                    on_refresh()

            self._st.caption("Cache: 30 min")

        # Handle selection change
        if new_selection and on_select:
            on_select(new_selection)

        return new_selection
