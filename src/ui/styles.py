"""Centralized CSS styles following Greenn/Voomp design system.

All styles are defined here to avoid duplication across pages.
"""

# Design system colors
COLORS = {
    "primary": "#002363",
    "primary_light": "#2A63AB",
    "background": "#f9fafb",
    "card": "#ffffff",
    "foreground": "#333333",
    "foreground_secondary": "#81858e",
    "border": "#ededf0",
    "muted": "#f3f4f6",
    "muted_fg": "#71717a",
    "orange": "#f97316",
    "orange_hover": "#ea580c",
    "success": "#22c55e",
    "danger": "#ef4444",
    "warning": "#f59e0b",
}

# Plotly chart theme
PLOTLY_THEME = {
    "plot_bgcolor": "#fff",
    "paper_bgcolor": "#fff",
    "font": {"family": "Inter, sans-serif", "color": "#18181b", "size": 12},
    "margin": {"l": 10, "r": 20, "t": 40, "b": 20},
}

PLOTLY_AXIS_STYLE = {
    "gridcolor": "#f3f4f6",
    "linecolor": "#e5e7eb",
    "tickfont": {"color": "#71717a"},
}


# Main CSS stylesheet
MAIN_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* === Variables === */
:root {
    --primary: #002363;
    --primary-light: #2A63AB;
    --bg: #f9fafb;
    --card: #ffffff;
    --fg: #333333;
    --fg-secondary: #81858e;
    --border: #ededf0;
    --orange: #f97316;
    --radius: 5px;
}

html, body, [class*="st-"] { 
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important; 
}

.stApp { 
    background: var(--bg) !important; 
}

/* === Sidebar - Greenn style === */
section[data-testid="stSidebar"] {
    background: #ffffff !important;
    border-right: 1px solid var(--border) !important;
    box-shadow: -2px 2px 8px rgba(0, 0, 0, 0.1) !important;
}

section[data-testid="stSidebar"] > div {
    padding-top: 20px !important;
    padding-left: 20px !important;
    padding-right: 20px !important;
}

/* Menu item styling */
.menu-item {
    display: flex;
    align-items: center;
    padding: 10px 0;
    cursor: pointer;
    color: var(--fg);
    font-weight: 600;
    font-size: 15px;
    text-decoration: none;
    transition: all 0.3s ease;
    position: relative;
}

.menu-item:hover {
    color: var(--primary);
}

.menu-item.active {
    color: var(--primary) !important;
}

.menu-item.active::before {
    content: "";
    width: 7px;
    height: 7px;
    background: var(--primary);
    border-radius: 50%;
    display: block;
    position: absolute;
    left: -20px;
}

.menu-item svg {
    margin-right: 40px;
    color: var(--fg-secondary);
    transition: all 0.3s ease;
    flex-shrink: 0;
}

.menu-item:hover svg,
.menu-item.active svg {
    color: var(--primary);
}

/* Sidebar button overrides */
section[data-testid="stSidebar"] .stButton button {
    background: transparent !important;
    color: var(--fg) !important;
    border: none !important;
    box-shadow: none !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    text-align: left !important;
    justify-content: flex-start !important;
    padding: 10px 0 !important;
    transition: all 0.3s ease !important;
}

section[data-testid="stSidebar"] .stButton button:hover {
    background: transparent !important;
    color: var(--primary) !important;
}

/* === Metric cards === */
[data-testid="metric-container"] {
    background: var(--card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    padding: 1rem 1.25rem !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
}

[data-testid="metric-container"] label {
    color: var(--fg-secondary) !important;
    font-size: .7rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: .04em !important;
}

[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: var(--fg) !important;
    font-size: 1.5rem !important;
    font-weight: 700 !important;
}

/* === DataFrames === */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    overflow: hidden !important;
}

/* === Primary buttons (main content) === */
.stApp .main .stButton button {
    background: var(--orange) !important;
    color: #fff !important;
    border: none !important;
    border-radius: var(--radius) !important;
    font-weight: 600 !important;
}

.stApp .main .stButton button:hover {
    background: #ea580c !important;
}

/* === Headers === */
h1, h2, h3 { 
    font-family: 'Inter', sans-serif !important; 
    color: var(--fg) !important; 
}

/* === Hide Streamlit branding === */
#MainMenu, footer, header { 
    visibility: hidden !important; 
}

/* === Responsive === */
@media(max-width:900px) {
    [data-testid="metric-container"] { padding: .75rem !important; }
    [data-testid="metric-container"] [data-testid="stMetricValue"] { font-size: 1.25rem !important; }
}
</style>
"""


def apply_styles(st) -> None:
    """Apply main CSS styles to Streamlit app."""
    st.markdown(MAIN_CSS, unsafe_allow_html=True)
