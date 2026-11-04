"""Metric cards and KPI components."""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.ui.styles import COLORS

if TYPE_CHECKING:
    import streamlit


def render_kpi_row(
    st: "streamlit",
    total_cards: int,
    total_bugs: int,
    cards_with_bugs: int,
    avg_bugs: float,
    bug_rate: float,
) -> None:
    """Render a row of KPI metric cards.
    
    Args:
        st: Streamlit module
        total_cards: Total number of cards delivered
        total_bugs: Total sub-bugs count
        cards_with_bugs: Number of cards with at least one bug
        avg_bugs: Average bugs per card
        bug_rate: Percentage of cards with bugs
    """
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Cards em Produção", total_cards)
    k2.metric("Total de Sub-bugs", total_bugs)
    k3.metric("Cards com Sub-bugs", f"{cards_with_bugs} ({bug_rate}%)")
    k4.metric("Média Bugs / Card", avg_bugs)


def render_project_card(
    st: "streamlit",
    project_name: str,
    total_cards: int,
    total_sub_bugs: int,
    avg_bugs_per_card: float,
    bug_rate_pct: float,
    top_dev: str,
    has_error: bool = False,
) -> None:
    """Render a project summary card.
    
    Args:
        st: Streamlit module
        project_name: Display name of the project
        total_cards: Cards delivered
        total_sub_bugs: Total bugs
        avg_bugs_per_card: Average bugs per card
        bug_rate_pct: Bug rate percentage
        top_dev: Name of top developer
        has_error: Whether there was an error loading data
    """
    # Color indicator based on bug rate
    color = (
        "🔴" if bug_rate_pct >= 50
        else "🟠" if bug_rate_pct >= 25
        else "🟢"
    )

    border_color = "#f97316" if bug_rate_pct >= 50 else "#e5e7eb"
    bugs_color = "#ef4444" if total_sub_bugs > 0 else "#18181b"
    rate_color = "#ef4444" if bug_rate_pct >= 50 else "#f97316" if bug_rate_pct >= 25 else "#18181b"

    error_msg = '<br><span style="color:#ef4444; font-size:.75rem">⚠️ Erro ao carregar</span>' if has_error else ""

    st.markdown(
        f"""
        <div style="
            border: 1px solid {border_color};
            border-radius: 8px;
            padding: 16px 18px;
            background: #ffffff;
            margin-bottom: 8px;
            box-shadow: 0 1px 2px 0 rgba(0,0,0,.05);
            font-family: 'Inter', sans-serif;
        ">
            <div style="font-size:1rem; font-weight:700; margin-bottom:10px; color:#18181b;">
                {color} {project_name}
            </div>
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; font-size:0.8125rem;">
                <div>
                    <span style="color:#71717a; font-size:.7rem; font-weight:600; text-transform:uppercase; letter-spacing:.04em;">Cards</span><br>
                    <b style="color:#18181b; font-size:1.125rem;">{total_cards}</b>
                </div>
                <div>
                    <span style="color:#71717a; font-size:.7rem; font-weight:600; text-transform:uppercase; letter-spacing:.04em;">Sub-bugs</span><br>
                    <b style="color:{bugs_color}; font-size:1.125rem;">{total_sub_bugs}</b>
                </div>
                <div>
                    <span style="color:#71717a; font-size:.7rem; font-weight:600; text-transform:uppercase; letter-spacing:.04em;">Média bugs/card</span><br>
                    <b style="color:#18181b;">{avg_bugs_per_card}</b>
                </div>
                <div>
                    <span style="color:#71717a; font-size:.7rem; font-weight:600; text-transform:uppercase; letter-spacing:.04em;">Taxa de bug</span><br>
                    <b style="color:{rate_color};">{bug_rate_pct}%</b>
                </div>
            </div>
            <div style="margin-top:12px; padding-top:10px; border-top:1px solid #f3f4f6; font-size:0.8125rem; color:#71717a;">
                🏆 Top dev: <b style="color:#f97316">{top_dev}</b>
                {error_msg}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
