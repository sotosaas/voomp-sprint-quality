"""app.py

Sprint Quality Dashboard — Voomp
Professional sidebar design following Greenn/Voomp design patterns.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

from config import PROJECTS, validate_config, PRODUCTION_STATUSES
from jira_client import JiraClient, JiraAuthError, JiraNotFoundError
from data_processor import (
    build_issues_dataframe,
    get_dev_ranking,
    get_card_ranking,
    get_sprint_trend,
    clear_cache,
)

# ------------------------------------------------------------------
# Page config
# ------------------------------------------------------------------

st.set_page_config(
    page_title="Sprint Quality · Voomp",
    page_icon="🐛",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------------------
# Session state
# ------------------------------------------------------------------

if "sidebar_collapsed" not in st.session_state:
    st.session_state.sidebar_collapsed = False
if "selected_project" not in st.session_state:
    st.session_state.selected_project = list(PROJECTS.keys())[0]
if "selected_sprint_id" not in st.session_state:
    st.session_state.selected_sprint_id = None
if "selected_sprint_name" not in st.session_state:
    st.session_state.selected_sprint_name = ""

# ------------------------------------------------------------------
# Inject secrets (Streamlit Cloud)
# ------------------------------------------------------------------

try:
    import config as _cfg
    for _key in ("JIRA_URL", "JIRA_EMAIL", "JIRA_API_TOKEN"):
        _val = st.secrets.get(_key)
        if _val:
            setattr(_cfg, _key, str(_val))
except Exception:
    pass

# ------------------------------------------------------------------
# CSS Styling - Greenn/Voomp design system
# ------------------------------------------------------------------

st.markdown("""
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

/* Menu item link style - matches Greenn */
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

/* Toggle menu button */
.menu-toggle {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 15px 0;
    cursor: pointer;
    font-weight: 600;
    font-size: 12px;
    text-transform: uppercase;
    color: var(--fg);
}

.menu-toggle svg {
    width: 21px;
    height: 15px;
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
""", unsafe_allow_html=True)

# ------------------------------------------------------------------
# SVG Icons - Greenn/Voomp style (stroke-based, 21x21)
# ------------------------------------------------------------------

# Menu hamburguer icon (3 lines)
ICON_MENU = '''<svg width="21" height="15" viewBox="0 0 21 15" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M1 7.5H20M1 1.5H20M1 13.5H20" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</svg>'''

# Dashboard icon
ICON_DASHBOARD = '''<svg width="21" height="21" viewBox="0 0 21 21" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M1.5 7.5H19.5M7.5 19.5V7.5M3.5 1.5H17.5C18.6 1.5 19.5 2.4 19.5 3.5V17.5C19.5 18.6 18.6 19.5 17.5 19.5H3.5C2.4 19.5 1.5 18.6 1.5 17.5V3.5C1.5 2.4 2.4 1.5 3.5 1.5Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</svg>'''

# Play icon
ICON_PLAY = '''<svg width="21" height="21" viewBox="0 0 21 21" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M5.5 3.5L17.5 10.5L5.5 17.5V3.5Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</svg>'''

# Card/Payment icon
ICON_CARD = '''<svg width="21" height="21" viewBox="0 0 21 21" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M1.5 8.5H19.5M3.5 3.5H17.5C18.6 3.5 19.5 4.4 19.5 5.5V15.5C19.5 16.6 18.6 17.5 17.5 17.5H3.5C2.4 17.5 1.5 16.6 1.5 15.5V5.5C1.5 4.4 2.4 3.5 3.5 3.5Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</svg>'''

# Settings/Wrench icon
ICON_SETTINGS = '''<svg width="21" height="21" viewBox="0 0 21 21" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M13.5 6.5L17.5 2.5M19 4L17.5 2.5M17.5 2.5L15.5 4.5L17.5 2.5ZM10 8C10 8 8.5 6.5 6.5 6.5C4.5 6.5 2.5 8.5 2.5 10.5C2.5 12.5 4.5 14.5 6.5 14.5C8.5 14.5 10 13 10 13L14.5 17.5C15 18 15.7 18.3 16.5 18.3C18 18.3 19.3 17 19.3 15.5C19.3 14.7 19 14 18.5 13.5L14 9C14 9 15.5 7.5 15.5 5.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</svg>'''

# Chart/Report icon
ICON_CHART = '''<svg width="21" height="21" viewBox="0 0 21 21" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M17.5 17.5V7.5M10.5 17.5V3.5M3.5 17.5V11.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</svg>'''

# Refresh icon
ICON_REFRESH = '''<svg width="21" height="21" viewBox="0 0 21 21" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M1.5 3.5V8.5H6.5M19.5 17.5V12.5H14.5M17.5 7.5C16.9 5.8 15.8 4.3 14.3 3.3C12.8 2.3 11 1.8 9.2 2C5.4 2.4 2.3 5.5 2 9.3M3.5 13.5C4.1 15.2 5.2 16.7 6.7 17.7C8.2 18.7 10 19.2 11.8 19C15.6 18.6 18.7 15.5 19 11.7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</svg>'''

# Product icons mapping
PRODUCT_ICONS = {
    "VADM": ICON_DASHBOARD,
    "VPLY": ICON_PLAY,
    "VMPG": ICON_CARD,
    "VSUS": ICON_SETTINGS,
    "VBEP": ICON_CHART,
}

# Emoji fallback for main content header
PRODUCT_EMOJI = {
    "VADM": "⚙️",
    "VPLY": "▶️",
    "VMPG": "💳",
    "VSUS": "🔧",
    "VBEP": "📊",
}

# ------------------------------------------------------------------
# Config validation
# ------------------------------------------------------------------

errors = validate_config()
if errors:
    st.error("⚠️ Configuração incompleta. Verifique o arquivo `.env`:")
    for e in errors:
        st.markdown(f"- {e}")
    st.stop()

# ------------------------------------------------------------------
# Cached loaders
# ------------------------------------------------------------------

@st.cache_data(ttl=1800, show_spinner=False)
def load_sprints(project_key: str) -> list[dict]:
    """Fetch sprint list for the current year."""
    client = JiraClient()
    board = client.get_board(project_key)
    if not board:
        return []
    return list(reversed(client.get_sprints(
        board["id"],
        state="active,closed",
        max_results=50,
        year=datetime.now().year,
    )))


@st.cache_data(ttl=1800, show_spinner=False)
def load_issues(project_key: str, sprint_id: int, sprint_name: str) -> pd.DataFrame:
    """Fetch sprint issues."""
    df = build_issues_dataframe(project_key, sprint_id, sprint_name)
    if "sub_bugs" in df.columns:
        df = df.drop(columns=["sub_bugs"])
    return df


@st.cache_data(ttl=1800, show_spinner=False)
def load_sprint_trend(project_key: str, last_n_sprints: int) -> pd.DataFrame:
    """Fetch trend data with parallel loading."""
    return get_sprint_trend(project_key, last_n_sprints=last_n_sprints)


# ------------------------------------------------------------------
# Plotly theme - base layout WITHOUT xaxis/yaxis (to avoid conflicts)
# ------------------------------------------------------------------

PLOTLY_BASE = dict(
    plot_bgcolor="#fff",
    paper_bgcolor="#fff",
    font=dict(family="Inter, sans-serif", color="#18181b", size=12),
    margin=dict(l=10, r=20, t=40, b=20),
)

COLOR_PRIMARY = "#f97316"


# ------------------------------------------------------------------
# Sidebar — Greenn/Voomp style navigation
# ------------------------------------------------------------------

with st.sidebar:
    # Logo
    st.markdown("""
    <div style="display: flex; align-items: center; margin-bottom: 20px; padding: 10px 0;">
        <span style="font-size: 24px; margin-right: 10px;">🐛</span>
        <span style="font-weight: 700; font-size: 16px; color: #333;">Sprint Quality</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Menu items - following Greenn pattern
    for key, name in PROJECTS.items():
        is_active = st.session_state.selected_project == key
        icon_svg = PRODUCT_ICONS.get(key, ICON_DASHBOARD)
        
        # Color the icon based on active state
        icon_color = "#002363" if is_active else "#81858e"
        colored_icon = icon_svg.replace('stroke="currentColor"', f'stroke="{icon_color}"')
        
        # Active indicator dot
        active_dot = '<span style="width: 7px; height: 7px; background: #002363; border-radius: 50%; position: absolute; left: -15px;"></span>' if is_active else ''
        
        # Render menu item as HTML
        text_color = "#002363" if is_active else "#333"
        st.markdown(f'''
        <div class="menu-item {'active' if is_active else ''}" style="position: relative; display: flex; align-items: center; padding: 12px 0; color: {text_color}; font-weight: 600; font-size: 15px;">
            {active_dot}
            <span style="margin-right: 35px; display: flex; color: {icon_color};">{colored_icon}</span>
            <span>{name}</span>
        </div>
        ''', unsafe_allow_html=True)
        
        # Hidden button for click handling
        if not is_active:
            if st.button(f"Selecionar {name}", key=f"menu_{key}", label_visibility="collapsed"):
                st.session_state.selected_project = key
                st.session_state.selected_sprint_id = None
                st.session_state.selected_sprint_name = ""
                st.rerun()
    
    st.markdown("<div style='height: 30px'></div>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Refresh button
    refresh_icon = ICON_REFRESH.replace('stroke="currentColor"', 'stroke="#81858e"')
    st.markdown(f'''
    <div style="display: flex; align-items: center; padding: 10px 0; color: #333; font-weight: 600; font-size: 14px;">
        <span style="margin-right: 35px; display: flex; color: #81858e;">{refresh_icon}</span>
        <span>Atualizar dados</span>
    </div>
    ''', unsafe_allow_html=True)
    
    if st.button("Atualizar", key="refresh_btn", label_visibility="collapsed"):
        load_sprints.clear()
        load_issues.clear()
        load_sprint_trend.clear()
        clear_cache()
        st.rerun()
    
    st.caption("Cache: 30 min")


# ------------------------------------------------------------------
# Main content
# ------------------------------------------------------------------

chosen_key = st.session_state.selected_project
product_name = PROJECTS[chosen_key]
product_emoji = PRODUCT_EMOJI.get(chosen_key, "📁")

# Header
st.markdown(f"# {product_emoji} {product_name}")

# Load sprints
sprints = load_sprints(chosen_key)

if not sprints:
    st.warning(f"Nenhuma sprint encontrada para {product_name}.")
    st.stop()

sprint_labels = [s["name"] for s in sprints]
sprint_ids = [s["id"] for s in sprints]

# Default to most recent sprint
default_idx = 0
if st.session_state.selected_sprint_id in sprint_ids:
    default_idx = sprint_ids.index(st.session_state.selected_sprint_id)

# Sprint filter in main content area
col_sprint, col_status, col_spacer = st.columns([3, 1, 4])

with col_sprint:
    chosen_sprint_label = st.selectbox(
        "Sprint",
        options=sprint_labels,
        index=default_idx,
        key="main_sprint_selector",
    )

chosen_sprint_idx = sprint_labels.index(chosen_sprint_label)
chosen_sprint_id = sprint_ids[chosen_sprint_idx]
chosen_sprint = sprints[chosen_sprint_idx]

st.session_state.selected_sprint_id = chosen_sprint_id
st.session_state.selected_sprint_name = chosen_sprint_label

with col_status:
    state = chosen_sprint.get("state", "")
    status_badge = "🟢 Ativa" if state == "active" else "✅ Fechada"
    st.markdown(f"**{status_badge}**")

st.markdown("---")

# Load issues
try:
    df = load_issues(chosen_key, chosen_sprint_id, chosen_sprint_label)
except JiraAuthError as e:
    st.error(f"❌ Erro de autenticação: {e}")
    st.stop()
except JiraNotFoundError as e:
    st.error(f"❌ Recurso não encontrado: {e}")
    st.stop()
except Exception as e:
    st.error(f"❌ Erro ao buscar dados: {e}")
    st.stop()

if df.empty:
    status_display = ", ".join(f"**'{s}'**" for s in PRODUCTION_STATUSES)
    st.info(f"Nenhum card com status {status_display} na sprint **{chosen_sprint_label}**.")
    st.stop()

# ------------------------------------------------------------------
# KPI cards
# ------------------------------------------------------------------

total_cards = len(df)
total_bugs = int(df["sub_bug_count"].sum())
cards_with_bugs = int((df["sub_bug_count"] > 0).sum())
avg_bugs = round(float(df["sub_bug_count"].mean()), 2)
bug_rate = round(float((df["sub_bug_count"] > 0).mean() * 100), 1)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Cards em Produção", total_cards)
k2.metric("Total de Sub-bugs", total_bugs)
k3.metric("Cards com Sub-bugs", f"{cards_with_bugs} ({bug_rate}%)")
k4.metric("Média Bugs / Card", avg_bugs)

st.markdown("---")

# ------------------------------------------------------------------
# Cards table
# ------------------------------------------------------------------

st.markdown("### 📋 Cards da Sprint")

display_df = df[["key", "summary", "assignee_name", "sub_bug_count", "issue_type", "jira_url"]].copy()
display_df.columns = ["Key", "Título", "Responsável", "Sub-bugs", "Tipo", "Link"]
display_df = display_df.sort_values("Sub-bugs", ascending=False).reset_index(drop=True)

def highlight_bugs(row):
    return ["background-color: rgba(255, 80, 80, 0.08)"] * len(row) if row["Sub-bugs"] > 0 else [""] * len(row)

st.dataframe(
    display_df.style.apply(highlight_bugs, axis=1),
    use_container_width=True,
    hide_index=True,
    column_config={
        "Key": st.column_config.TextColumn("Key", width=100),
        "Título": st.column_config.TextColumn("Título", width=320),
        "Responsável": st.column_config.TextColumn("Responsável", width=160),
        "Sub-bugs": st.column_config.NumberColumn("Sub-bugs", width=90),
        "Tipo": st.column_config.TextColumn("Tipo", width=100),
        "Link": st.column_config.LinkColumn("Jira", width=80),
    },
)

st.caption(f"{total_cards} cards · {total_bugs} sub-bugs no total")

# ------------------------------------------------------------------
# Dev Ranking
# ------------------------------------------------------------------

st.markdown("---")
st.markdown("### 🏆 Ranking de Desenvolvedores")
st.caption("Score = cards entregues ÷ (sub-bugs + 1) · quanto maior, melhor")

ranking = get_dev_ranking(df)

if ranking.empty:
    st.info("Sem dados de responsável para calcular o ranking.")
else:
    top = ranking.iloc[0]
    st.success(
        f"🥇 **Melhor qualidade:** {top['assignee_name']} — "
        f"{int(top['cards_delivered'])} card(s) com {int(top['total_sub_bugs'])} sub-bug(s) "
        f"(score: {top['quality_score']})"
    )

    medals = ["🥇", "🥈", "🥉"] + [""] * (len(ranking) - 3)
    table_df = ranking.copy()
    table_df.insert(0, "#", medals[:len(table_df)])
    table_df = table_df.rename(columns={
        "assignee_name": "Dev",
        "cards_delivered": "Cards",
        "total_sub_bugs": "Bugs",
        "bug_ratio": "Bugs/Card",
        "quality_score": "Score",
    })[["#", "Dev", "Cards", "Bugs", "Bugs/Card", "Score"]]

    def color_bugs(val):
        return "color: #ff6b6b; font-weight: bold" if isinstance(val, (int, float)) and val > 0 else ""

    st.dataframe(
        table_df.style.map(color_bugs, subset=["Bugs"]).set_properties(**{"text-align": "center"}, subset=["Cards", "Bugs", "Bugs/Card", "Score"]),
        use_container_width=True,
        hide_index=True,
        column_config={
            "#": st.column_config.TextColumn("", width=40),
            "Dev": st.column_config.TextColumn("Dev", width=200),
            "Cards": st.column_config.NumberColumn("Cards", width=70),
            "Bugs": st.column_config.NumberColumn("Bugs", width=65),
            "Bugs/Card": st.column_config.NumberColumn("Bugs/Card", width=90),
            "Score": st.column_config.NumberColumn("Score ↑", width=80),
        },
    )

# ------------------------------------------------------------------
# Cards com mais bugs
# ------------------------------------------------------------------

st.markdown("---")
st.markdown("### 🔴 Cards com Mais Sub-bugs")

card_rank = get_card_ranking(df, top_n=10)

if card_rank.empty:
    st.success("🎉 Nenhum card gerou sub-bugs nessa sprint!")
else:
    col_bars, col_detail = st.columns([3, 2], gap="large")

    with col_bars:
        max_bugs = card_rank["sub_bug_count"].max()
        colors = [
            f"rgba(249, {max(115, 200 - int((v / max_bugs) * 85))}, {max(22, 80 - int((v / max_bugs) * 58))}, 0.9)" 
            for v in card_rank["sub_bug_count"]
        ]

        fig_cards = go.Figure(go.Bar(
            x=card_rank["key"],
            y=card_rank["sub_bug_count"],
            marker_color=colors,
            text=card_rank["sub_bug_count"],
            textposition="outside",
            textfont=dict(color="#71717a", size=11),
        ))
        
        # FIXED: Apply layout without conflicting xaxis
        fig_cards.update_layout(
            title=dict(text="Top 10 Cards por Sub-bugs", font=dict(size=14)),
            xaxis_title="Card",
            yaxis_title="Sub-bugs",
            height=350,
            **PLOTLY_BASE,
        )
        fig_cards.update_xaxes(tickangle=-30, gridcolor="#f3f4f6", linecolor="#e5e7eb", tickfont=dict(color="#71717a"))
        fig_cards.update_yaxes(gridcolor="#f3f4f6", linecolor="#e5e7eb", tickfont=dict(color="#71717a"), rangemode="tozero")
        
        st.plotly_chart(fig_cards, use_container_width=True)

    with col_detail:
        st.markdown("##### Detalhes")
        detail_df = card_rank[["key", "summary", "assignee_name", "sub_bug_count", "jira_url"]].copy()
        detail_df.columns = ["Key", "Título", "Responsável", "Sub-bugs", "Link"]

        def color_count(val):
            if isinstance(val, (int, float)):
                if val >= 3:
                    return "color: #ff4444; font-weight: bold"
                if val >= 1:
                    return "color: #ff9944; font-weight: bold"
            return ""

        st.dataframe(
            detail_df.style.map(color_count, subset=["Sub-bugs"]),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Key": st.column_config.TextColumn("Key", width=90),
                "Título": st.column_config.TextColumn("Título", width=200),
                "Responsável": st.column_config.TextColumn("Dev", width=130),
                "Sub-bugs": st.column_config.NumberColumn("Bugs", width=60),
                "Link": st.column_config.LinkColumn("Jira", width=60),
            },
        )

        b1 = int((card_rank["sub_bug_count"] >= 3).sum())
        b2 = int(((card_rank["sub_bug_count"] >= 1) & (card_rank["sub_bug_count"] < 3)).sum())
        c1, c2 = st.columns(2)
        c1.metric("🔴 3+ bugs", b1)
        c2.metric("🟠 1–2 bugs", b2)

# ------------------------------------------------------------------
# Trend chart
# ------------------------------------------------------------------

st.markdown("---")
st.markdown("### 📈 Tendência de Qualidade por Sprint")

with st.expander("📊 Ver tendência", expanded=False):
    col_ctrl1, col_ctrl2, _ = st.columns([1, 1, 4])
    with col_ctrl1:
        n_sprints = st.slider("Nº de sprints", min_value=2, max_value=10, value=5, step=1)
    with col_ctrl2:
        trend_metric = st.selectbox(
            "Métrica",
            options=["total_sub_bugs", "avg_bugs_per_card", "bug_rate_pct", "total_cards"],
            format_func=lambda x: {
                "total_sub_bugs": "Total de sub-bugs",
                "avg_bugs_per_card": "Média bugs/card",
                "bug_rate_pct": "Taxa de bugs (%)",
                "total_cards": "Cards em produção",
            }[x],
        )

    with st.spinner("Carregando tendência..."):
        try:
            trend_df = load_sprint_trend(chosen_key, n_sprints)
        except Exception as e:
            st.error(f"❌ Erro: {e}")
            trend_df = None

    if trend_df is None or trend_df.empty:
        st.info("Sem dados suficientes para exibir tendência.")
    else:
        metric_labels = {
            "total_sub_bugs": "Total de Sub-bugs",
            "avg_bugs_per_card": "Média Bugs / Card",
            "bug_rate_pct": "Taxa de Bugs (%)",
            "total_cards": "Cards em Produção",
        }
        y_label = metric_labels[trend_metric]
        y_values = trend_df[trend_metric].tolist()
        x_labels = trend_df["sprint_name"].tolist()

        is_bug_metric = trend_metric != "total_cards"
        delta = y_values[-1] - y_values[-2] if len(y_values) >= 2 else None

        if delta is not None:
            if is_bug_metric:
                trend_icon = "📉 Melhorando" if delta < 0 else ("📈 Piorando" if delta > 0 else "➡️ Estável")
                trend_color = "normal" if delta < 0 else ("inverse" if delta > 0 else "off")
            else:
                trend_icon = "📈 Crescendo" if delta > 0 else ("📉 Diminuindo" if delta < 0 else "➡️ Estável")
                trend_color = "normal"
        else:
            trend_icon = "—"
            trend_color = "off"

        tm1, tm2, tm3, tm4 = st.columns(4)
        tm1.metric("Última sprint", f"{y_values[-1]}", delta=f"{delta:+.1f} vs anterior" if delta else None, delta_color=trend_color)
        tm2.metric("Melhor sprint", f"{min(y_values)}" if is_bug_metric else f"{max(y_values)}")
        tm3.metric("Pior sprint", f"{max(y_values)}" if is_bug_metric else f"{min(y_values)}")
        tm4.metric("Tendência", trend_icon)

        fig_trend = go.Figure()

        fig_trend.add_trace(go.Scatter(
            x=x_labels,
            y=y_values,
            mode="lines+markers+text",
            name=y_label,
            line=dict(color=COLOR_PRIMARY, width=3),
            marker=dict(size=9, color=COLOR_PRIMARY, line=dict(width=2, color="#fff")),
            text=[str(round(v, 1)) for v in y_values],
            textposition="top center",
            textfont=dict(color="#18181b", size=11),
        ))

        try:
            import numpy as np
            x_num = list(range(len(y_values)))
            coef = np.polyfit(x_num, y_values, 1)
            trendline_y = [coef[0] * i + coef[1] for i in x_num]
            trend_line_color = "#ef4444" if (is_bug_metric and coef[0] > 0) else "#22c55e"
            fig_trend.add_trace(go.Scatter(
                x=x_labels,
                y=trendline_y,
                mode="lines",
                name="Tendência",
                line=dict(color=trend_line_color, width=2, dash="dash"),
            ))
        except Exception:
            pass

        active_sprints = trend_df[trend_df["sprint_state"] == "active"]["sprint_name"].tolist()
        if active_sprints:
            active_y = trend_df[trend_df["sprint_name"].isin(active_sprints)][trend_metric].tolist()
            fig_trend.add_trace(go.Scatter(
                x=active_sprints,
                y=active_y,
                mode="markers",
                name="Sprint ativa",
                marker=dict(size=14, color=COLOR_PRIMARY, symbol="star", line=dict(width=2, color="#fff")),
            ))

        # FIXED: Apply layout without conflicting xaxis/yaxis
        fig_trend.update_layout(
            xaxis_title="Sprint",
            yaxis_title=y_label,
            height=380,
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            **PLOTLY_BASE,
        )
        fig_trend.update_xaxes(tickangle=-20, gridcolor="#f3f4f6", linecolor="#e5e7eb", tickfont=dict(color="#71717a"))
        fig_trend.update_yaxes(gridcolor="#f3f4f6", linecolor="#e5e7eb", tickfont=dict(color="#71717a"), rangemode="tozero")

        st.plotly_chart(fig_trend, use_container_width=True)

        with st.expander("Ver tabela de dados"):
            tbl = trend_df[["sprint_name", "total_cards", "total_sub_bugs", "cards_with_bugs", "avg_bugs_per_card", "bug_rate_pct"]].rename(columns={
                "sprint_name": "Sprint",
                "total_cards": "Cards",
                "total_sub_bugs": "Sub-bugs",
                "cards_with_bugs": "C/ Bugs",
                "avg_bugs_per_card": "Média",
                "bug_rate_pct": "Taxa %",
            })
            st.dataframe(tbl, use_container_width=True, hide_index=True)
