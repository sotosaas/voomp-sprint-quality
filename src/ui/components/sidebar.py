"""Sidebar component following Greenn/Voomp design patterns.

Collapsible sidebar that shows only icons when collapsed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.config import AppConfig, Project
from src.ui.icons import get_icon, colorize_icon, ICON_REFRESH, ICON_OVERVIEW, ICON_MENU

if TYPE_CHECKING:
    import streamlit


# CSS for collapsible sidebar
SIDEBAR_CSS = """
<style>
/* Sidebar collapsed state */
.sidebar-collapsed section[data-testid="stSidebar"] {
    width: 80px !important;
    min-width: 80px !important;
}

.sidebar-collapsed section[data-testid="stSidebar"] > div {
    width: 80px !important;
}

.sidebar-collapsed .sidebar-text {
    display: none !important;
}

.sidebar-collapsed .sidebar-logo-text {
    display: none !important;
}

/* Menu item container */
.menu-item-container {
    display: flex;
    align-items: center;
    padding: 12px 8px;
    margin: 4px 0;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s ease;
    text-decoration: none;
    color: #333;
}

.menu-item-container:hover {
    background: #f3f4f6;
}

.menu-item-container.active {
    background: #e8f0fe;
    color: #002363;
}

.menu-item-container.active::before {
    content: "";
    width: 4px;
    height: 100%;
    background: #002363;
    position: absolute;
    left: 0;
    border-radius: 0 4px 4px 0;
}

.menu-icon {
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}

.menu-text {
    margin-left: 12px;
    font-weight: 600;
    font-size: 14px;
    white-space: nowrap;
}

/* Toggle button */
.toggle-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 8px;
    margin-bottom: 16px;
    cursor: pointer;
    border-radius: 8px;
    transition: background 0.2s;
}

.toggle-btn:hover {
    background: #f3f4f6;
}

/* Logo section */
.logo-section {
    display: flex;
    align-items: center;
    padding: 16px 8px;
    margin-bottom: 8px;
}

.logo-icon {
    font-size: 24px;
    flex-shrink: 0;
}

.logo-text {
    margin-left: 12px;
    font-weight: 700;
    font-size: 16px;
    color: #333;
    white-space: nowrap;
}

/* Divider */
.sidebar-divider {
    height: 1px;
    background: #ededf0;
    margin: 16px 8px;
}
</style>
"""


class Sidebar:
    """Collapsible sidebar navigation component.
    
    Features:
    - Toggle button to collapse/expand
    - Collapsed: shows only icons
    - Expanded: shows icons + text
    - Active state indicator
    """

    def __init__(self, st: "streamlit", config: AppConfig) -> None:
        self._st = st
        self._config = config
        
        # Initialize collapse state
        if "sidebar_collapsed" not in st.session_state:
            st.session_state.sidebar_collapsed = False

    def render(
        self,
        selected_key: str,
        on_select: callable = None,
        on_refresh: callable = None,
        show_overview: bool = True,
    ) -> str | None:
        """Render the sidebar and return the selected project key."""
        new_selection = None
        collapsed = self._st.session_state.sidebar_collapsed

        with self._st.sidebar:
            # Inject CSS
            self._st.markdown(SIDEBAR_CSS, unsafe_allow_html=True)
            
            # Apply collapsed class to body if needed
            if collapsed:
                self._st.markdown(
                    '<script>document.body.classList.add("sidebar-collapsed");</script>',
                    unsafe_allow_html=True
                )
            else:
                self._st.markdown(
                    '<script>document.body.classList.remove("sidebar-collapsed");</script>',
                    unsafe_allow_html=True
                )

            # Toggle button (hamburger menu)
            col1, col2 = self._st.columns([1, 3] if not collapsed else [1, 1])
            with col1:
                if self._st.button("≡" if not collapsed else "≡", key="toggle_sidebar", help="Colapsar/Expandir menu"):
                    self._st.session_state.sidebar_collapsed = not collapsed
                    self._st.rerun()

            # Logo
            if not collapsed:
                self._st.markdown("""
                <div class="logo-section">
                    <span class="logo-icon">🐛</span>
                    <span class="logo-text sidebar-logo-text">Sprint Quality</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                self._st.markdown("""
                <div class="logo-section" style="justify-content: center;">
                    <span class="logo-icon">🐛</span>
                </div>
                """, unsafe_allow_html=True)

            self._st.markdown("---")

            # Overview button
            if show_overview:
                is_overview_active = selected_key == "overview"
                if collapsed:
                    btn_label = "📊"
                else:
                    btn_label = "📊 Visão Geral"
                
                btn_type = "primary" if is_overview_active else "secondary"
                if self._st.button(btn_label, key="menu_overview", use_container_width=True, type=btn_type, help="Visão Geral"):
                    if not is_overview_active:
                        new_selection = "overview"

            # Project menu items
            for project in self._config.projects:
                is_active = selected_key == project.key
                
                if collapsed:
                    btn_label = project.emoji
                else:
                    btn_label = f"{project.emoji} {project.name}"
                
                btn_type = "primary" if is_active else "secondary"
                if self._st.button(btn_label, key=f"menu_{project.key}", use_container_width=True, type=btn_type, help=project.name):
                    if not is_active:
                        new_selection = project.key

            self._st.markdown("---")

            # Refresh button
            if collapsed:
                refresh_label = "🔄"
            else:
                refresh_label = "🔄 Atualizar dados"
            
            if self._st.button(refresh_label, key="refresh_btn", use_container_width=True, help="Atualizar dados"):
                if on_refresh:
                    on_refresh()

            if not collapsed:
                self._st.caption("Cache: 30 min")

        # Handle selection change
        if new_selection and on_select:
            on_select(new_selection)

        return new_selection
