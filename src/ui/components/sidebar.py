"""Sidebar component following Greenn/Voomp design patterns."""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.config import AppConfig, Project
from src.ui.icons import get_icon, colorize_icon, ICON_REFRESH, ICON_OVERVIEW
from src.ui.styles import COLORS

if TYPE_CHECKING:
    import streamlit


class Sidebar:
    """Sidebar navigation component.
    
    Renders a Greenn-style sidebar with:
    - Logo/title
    - Navigation menu items with icons
    - Active state indicator (dot)
    - Refresh button
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
            self._render_logo()

            # Overview link
            if show_overview:
                if self._render_overview_item(selected_key == "overview"):
                    new_selection = "overview"

            # Project menu items
            for project in self._config.projects:
                is_active = selected_key == project.key
                if self._render_menu_item(project, is_active):
                    new_selection = project.key

            self._st.markdown("<div style='height: 30px'></div>", unsafe_allow_html=True)
            self._st.markdown("---")

            # Refresh button
            self._render_refresh_button()
            if self._st.button("Atualizar", key="refresh_btn", label_visibility="collapsed"):
                if on_refresh:
                    on_refresh()

            self._st.caption("Cache: 30 min")

        # Handle selection change
        if new_selection and on_select:
            on_select(new_selection)

        return new_selection

    def _render_logo(self) -> None:
        """Render the logo/title."""
        self._st.markdown("""
        <div style="display: flex; align-items: center; margin-bottom: 20px; padding: 10px 0;">
            <span style="font-size: 24px; margin-right: 10px;">🐛</span>
            <span style="font-weight: 700; font-size: 16px; color: #333;">Sprint Quality</span>
        </div>
        """, unsafe_allow_html=True)

    def _render_overview_item(self, is_active: bool) -> bool:
        """Render the overview menu item."""
        icon_color = COLORS["primary"] if is_active else COLORS["foreground_secondary"]
        colored_icon = colorize_icon(ICON_OVERVIEW, icon_color)
        text_color = COLORS["primary"] if is_active else COLORS["foreground"]
        active_dot = self._get_active_dot() if is_active else ""

        self._st.markdown(f'''
        <div class="menu-item {'active' if is_active else ''}" style="position: relative; display: flex; align-items: center; padding: 12px 0; color: {text_color}; font-weight: 600; font-size: 15px;">
            {active_dot}
            <span style="margin-right: 35px; display: flex; color: {icon_color};">{colored_icon}</span>
            <span>Visão Geral</span>
        </div>
        ''', unsafe_allow_html=True)

        # Hidden button for click
        if not is_active:
            return self._st.button("Selecionar Visão Geral", key="menu_overview", label_visibility="collapsed")
        return False

    def _render_menu_item(self, project: Project, is_active: bool) -> bool:
        """Render a project menu item."""
        icon_svg = get_icon(project.key)
        icon_color = COLORS["primary"] if is_active else COLORS["foreground_secondary"]
        colored_icon = colorize_icon(icon_svg, icon_color)
        text_color = COLORS["primary"] if is_active else COLORS["foreground"]
        active_dot = self._get_active_dot() if is_active else ""

        self._st.markdown(f'''
        <div class="menu-item {'active' if is_active else ''}" style="position: relative; display: flex; align-items: center; padding: 12px 0; color: {text_color}; font-weight: 600; font-size: 15px;">
            {active_dot}
            <span style="margin-right: 35px; display: flex; color: {icon_color};">{colored_icon}</span>
            <span>{project.name}</span>
        </div>
        ''', unsafe_allow_html=True)

        # Hidden button for click
        if not is_active:
            return self._st.button(f"Selecionar {project.name}", key=f"menu_{project.key}", label_visibility="collapsed")
        return False

    def _render_refresh_button(self) -> None:
        """Render the refresh section."""
        refresh_icon = colorize_icon(ICON_REFRESH, COLORS["foreground_secondary"])
        self._st.markdown(f'''
        <div style="display: flex; align-items: center; padding: 10px 0; color: #333; font-weight: 600; font-size: 14px;">
            <span style="margin-right: 35px; display: flex; color: #81858e;">{refresh_icon}</span>
            <span>Atualizar dados</span>
        </div>
        ''', unsafe_allow_html=True)

    @staticmethod
    def _get_active_dot() -> str:
        """Get the active indicator dot HTML."""
        return f'<span style="width: 7px; height: 7px; background: {COLORS["primary"]}; border-radius: 50%; position: absolute; left: -15px;"></span>'
