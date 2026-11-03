"""pages/01_Visão_Geral.py

Overview page — Últimos 30 dias por produto.
Compares all 5 Voomp products side by side.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from config import PROJECTS, validate_config, PROJECT_COLORS
from data_processor import get_last_30_days_summary

# ------------------------------------------------------------------
# Page config
# ------------------------------------------------------------------

st.set_page_config(
    page_title="Visão Geral · Voomp",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

:root {
    --color-background: #f9fafb;
    --color-card:       #ffffff;
    --color-foreground: #18181b;
    --color-border:     #e5e7eb;
    --color-muted:      #f3f4f6;
    --color-muted-fg:   #71717a;
    --color-orange:     #f97316;
    --radius:           0.5rem;
    --shadow-sm: 0 1px 2px 0 rgba(0,0,0,.05);
}
html, body, [class*="st-"] { font-family: 'Inter', sans-serif !important; }
.stApp { background: var(--color-background) !important; }
[data-testid="metric-container"] {
    background: var(--color-card) !important;
    border: 1px solid var(--color-border) !important;
    border-radius: var(--radius) !important;
    padding: 1.25rem 1.5rem !important;
    box-shadow: var(--shadow-sm) !important;
}
[data-testid="metric-container"] label { color: var(--color-muted-fg) !important; font-size:.75rem !important; font-weight:600 !important; text-transform:uppercase !important; letter-spacing:.04em !important; }
[data-testid="metric-container"] [data-testid="stMetricValue"] { color: var(--color-foreground) !important; font-size:1.875rem !important; font-weight:700 !important; letter-spacing:-.5px !important; }
section[data-testid="stSidebar"] { background: var(--color-card) !important; border-right: 1px solid var(--color-border) !important; }
.stButton button { background: var(--color-orange) !important; color: #fff !important; border: none !important; border-radius: var(--radius) !important; font-weight: 600 !important; }
.stButton button:hover { background: #ea580c !important; }
hr { border-color: var(--color-border) !important; }
h3 { font-size: 1.125rem !important; font-weight: 600 !important; color: var(--color-foreground) !important; }
#MainMenu, footer, header { visibility: hidden !important; }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------
# Config check
# ------------------------------------------------------------------

errors = validate_config()
if errors:
    st.error("⚠️ Configuração incompleta. Verifique o arquivo `.env`.")
    st.stop()

# ------------------------------------------------------------------
# Data loading
# ------------------------------------------------------------------

@st.cache_data(ttl=900, show_spinner=False)
def load_all_summaries() -> list[dict]:
    """Load 30-day summaries for all products."""
    summaries = []
    for key in PROJECTS:
        try:
            summary = get_last_30_days_summary(key)
            summaries.append(summary)
        except Exception as e:
            summaries.append({
                "project_key":     key,
                "project_name":    PROJECTS[key],
                "total_cards":     0,
                "total_sub_bugs":  0,
                "cards_with_bugs": 0,
                "avg_bugs_per_card": 0.0,
                "bug_rate_pct":    0.0,
                "top_dev":         "—",
                "top_dev_score":   0.0,
                "_error":          str(e),
            })
    return summaries

# ------------------------------------------------------------------
# Sidebar controls
# ------------------------------------------------------------------

with st.sidebar:
    st.markdown("## 📊 Visão Geral")
    st.markdown("---")
    st.markdown("Mostrando os **últimos 30 dias** de cada produto.")
    st.markdown("---")
    if st.button("🔄 Atualizar", use_container_width=True):
        load_all_summaries.clear()
        st.rerun()
    st.caption("Cache: 15 min")

# ------------------------------------------------------------------
# Header
# ------------------------------------------------------------------

st.markdown("# 📊 Visão Geral — Últimos 30 dias")
st.markdown("Comparativo de qualidade de entrega entre os produtos Voomp.")
st.markdown("---")

# ------------------------------------------------------------------
# Load data
# ------------------------------------------------------------------

with st.spinner("Carregando dados de todos os produtos..."):
    summaries = load_all_summaries()

if not summaries:
    st.warning("Nenhum dado disponível.")
    st.stop()

# ------------------------------------------------------------------
# Product cards grid — 3 per row
# ------------------------------------------------------------------

st.markdown("### Métricas por Produto")

cols_per_row = 3
rows = [summaries[i:i+cols_per_row] for i in range(0, len(summaries), cols_per_row)]

for row in rows:
    cols = st.columns(len(row), gap="medium")
    for col, s in zip(cols, row):
        with col:
            has_error = "_error" in s
            bug_rate = s["bug_rate_pct"]
            color = (
                "🔴" if bug_rate >= 50
                else "🟠" if bug_rate >= 25
                else "🟢"
            )

            st.markdown(
                f"""
                <div style="
                    border: 1px solid {'#f97316' if bug_rate >= 50 else '#e5e7eb'};
                    border-radius: 8px;
                    padding: 16px 18px;
                    background: #ffffff;
                    margin-bottom: 8px;
                    box-shadow: 0 1px 2px 0 rgba(0,0,0,.05);
                    font-family: 'Inter', sans-serif;
                ">
                    <div style="font-size:1rem; font-weight:700; margin-bottom:10px; color:#18181b;">
                        {color} {s['project_name']}
                    </div>
                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; font-size:0.8125rem;">
                        <div><span style="color:#71717a; font-size:.7rem; font-weight:600; text-transform:uppercase; letter-spacing:.04em;">Cards</span><br><b style="color:#18181b; font-size:1.125rem;">{s['total_cards']}</b></div>
                        <div><span style="color:#71717a; font-size:.7rem; font-weight:600; text-transform:uppercase; letter-spacing:.04em;">Sub-bugs</span><br><b style="color:{'#ef4444' if s['total_sub_bugs'] > 0 else '#18181b'}; font-size:1.125rem;">{s['total_sub_bugs']}</b></div>
                        <div><span style="color:#71717a; font-size:.7rem; font-weight:600; text-transform:uppercase; letter-spacing:.04em;">Média bugs/card</span><br><b style="color:#18181b;">{s['avg_bugs_per_card']}</b></div>
                        <div><span style="color:#71717a; font-size:.7rem; font-weight:600; text-transform:uppercase; letter-spacing:.04em;">Taxa de bug</span><br><b style="color:{'#ef4444' if bug_rate >= 50 else '#f97316' if bug_rate >= 25 else '#18181b'};">{s['bug_rate_pct']}%</b></div>
                    </div>
                    <div style="margin-top:12px; padding-top:10px; border-top:1px solid #f3f4f6; font-size:0.8125rem; color:#71717a;">
                        🏆 Top dev: <b style="color:#f97316">{s['top_dev']}</b>
                        {'<br><span style="color:#ef4444; font-size:.75rem">⚠️ Erro ao carregar</span>' if has_error else ''}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

st.markdown("---")

# ------------------------------------------------------------------
# Comparison charts
# ------------------------------------------------------------------

st.markdown("### Comparativo entre Produtos")

names = [s["project_name"] for s in summaries]
total_bugs = [s["total_sub_bugs"] for s in summaries]
total_cards = [s["total_cards"] for s in summaries]
bug_rates = [s["bug_rate_pct"] for s in summaries]
avg_bugs = [s["avg_bugs_per_card"] for s in summaries]

tab_bugs, tab_rate, tab_cards = st.tabs([
    "🐛 Total de Sub-bugs",
    "📉 Taxa de Bug (%)",
    "📦 Cards Entregues",
])

PLOTLY_LIGHT = dict(
    plot_bgcolor  = "#ffffff",
    paper_bgcolor = "#ffffff",
    font          = dict(family="Inter, sans-serif", color="#18181b", size=12),
    margin        = dict(l=10, r=20, t=40, b=20),
    xaxis         = dict(gridcolor="#f3f4f6", linecolor="#e5e7eb", tickfont=dict(color="#71717a")),
    yaxis         = dict(gridcolor="#f3f4f6", linecolor="#e5e7eb", tickfont=dict(color="#71717a"), rangemode="tozero"),
)

def bar_chart(x, y, title, yaxis_title, colors, height=320):
    fig = go.Figure(go.Bar(
        x=x, y=y,
        marker_color=colors,
        marker_line_width=0,
        text=[str(round(v, 1)) for v in y],
        textposition="outside",
        textfont=dict(color="#71717a", size=11),
        hovertemplate="<b>%{x}</b><br>" + yaxis_title + ": %{y}<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color="#18181b")),
        yaxis_title=yaxis_title,
        **PLOTLY_LIGHT,
        height=height,
    )
    return fig

product_colors = [PROJECT_COLORS.get(s["project_key"], "#4c7be1") for s in summaries]

with tab_bugs:
    st.plotly_chart(
        bar_chart(names, total_bugs, "Sub-bugs por Produto (30 dias)", "Sub-bugs", product_colors),
        use_container_width=True,
    )

with tab_rate:
    st.plotly_chart(
        bar_chart(names, bug_rates, "Taxa de Bug por Produto (%)", "Taxa (%)", product_colors),
        use_container_width=True,
    )

with tab_cards:
    st.plotly_chart(
        bar_chart(names, total_cards, "Cards em Produção por Produto (30 dias)", "Cards", product_colors),
        use_container_width=True,
    )

# ------------------------------------------------------------------
# Summary ranking table
# ------------------------------------------------------------------

st.markdown("---")
st.markdown("### Ranking Geral de Qualidade")
st.caption("Ordenado por menor taxa de bug nos últimos 30 dias")

rank_df = pd.DataFrame([{
    "Produto":       s["project_name"],
    "Cards":         s["total_cards"],
    "Sub-bugs":      s["total_sub_bugs"],
    "Média bugs/card": s["avg_bugs_per_card"],
    "Taxa bug %":    s["bug_rate_pct"],
    "Top Dev":       s["top_dev"],
} for s in summaries]).sort_values("Taxa bug %").reset_index(drop=True)

medals = ["🥇", "🥈", "🥉"] + ["" for _ in range(len(rank_df) - 3)]
rank_df.insert(0, "#", medals[:len(rank_df)])

def color_rate(val):
    if isinstance(val, (int, float)):
        if val >= 50: return "color: #ff4444; font-weight:bold"
        if val >= 25: return "color: #ff9944; font-weight:bold"
        if val == 0:  return "color: #50fa7b; font-weight:bold"
    return ""

st.dataframe(
    rank_df.style.map(color_rate, subset=["Taxa bug %"]),
    use_container_width=True,
    hide_index=True,
    column_config={
        "#":              st.column_config.TextColumn("", width=40),
        "Produto":        st.column_config.TextColumn("Produto", width=180),
        "Cards":          st.column_config.NumberColumn("Cards", width=70),
        "Sub-bugs":       st.column_config.NumberColumn("Sub-bugs", width=80),
        "Média bugs/card":st.column_config.NumberColumn("Média bugs/card", width=130),
        "Taxa bug %":     st.column_config.NumberColumn("Taxa bug %", width=100),
        "Top Dev":        st.column_config.TextColumn("🏆 Top Dev", width=160),
    },
)
