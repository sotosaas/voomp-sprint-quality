"""Table rendering components."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    import streamlit


def render_issues_table(st: "streamlit", df: pd.DataFrame) -> None:
    """Render the issues table with styling.
    
    Args:
        st: Streamlit module
        df: DataFrame with issue data
    """
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

    total_cards = len(df)
    total_bugs = int(df["sub_bug_count"].sum())
    st.caption(f"{total_cards} cards · {total_bugs} sub-bugs no total")


def render_dev_ranking_table(st: "streamlit", ranking_data: list[dict]) -> None:
    """Render the developer ranking table.
    
    Args:
        st: Streamlit module
        ranking_data: List of DevMetrics.to_dict() results
    """
    if not ranking_data:
        st.info("Sem dados de responsável para calcular o ranking.")
        return

    # Top dev highlight
    top = ranking_data[0]
    st.success(
        f"🥇 **Melhor qualidade:** {top['assignee_name']} — "
        f"{int(top['cards_delivered'])} card(s) com {int(top['total_sub_bugs'])} sub-bug(s) "
        f"(score: {top['quality_score']})"
    )

    # Table
    df = pd.DataFrame(ranking_data)
    medals = ["🥇", "🥈", "🥉"] + [""] * (len(df) - 3)
    df.insert(0, "#", medals[:len(df)])
    df = df.rename(columns={
        "assignee_name": "Dev",
        "cards_delivered": "Cards",
        "total_sub_bugs": "Bugs",
        "bug_ratio": "Bugs/Card",
        "quality_score": "Score",
    })[["#", "Dev", "Cards", "Bugs", "Bugs/Card", "Score"]]

    def color_bugs(val):
        return "color: #ff6b6b; font-weight: bold" if isinstance(val, (int, float)) and val > 0 else ""

    st.dataframe(
        df.style.map(color_bugs, subset=["Bugs"]).set_properties(
            **{"text-align": "center"}, subset=["Cards", "Bugs", "Bugs/Card", "Score"]
        ),
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


def render_card_ranking_table(st: "streamlit", cards_data: list[dict]) -> None:
    """Render the card ranking detail table.
    
    Args:
        st: Streamlit module
        cards_data: List of CardMetrics.to_dict() results
    """
    if not cards_data:
        st.success("🎉 Nenhum card gerou sub-bugs nessa sprint!")
        return

    df = pd.DataFrame(cards_data)
    detail_df = df[["key", "summary", "assignee_name", "sub_bug_count", "jira_url"]].copy()
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

    # Bug count summary
    df_bugs = pd.DataFrame(cards_data)
    b1 = int((df_bugs["sub_bug_count"] >= 3).sum())
    b2 = int(((df_bugs["sub_bug_count"] >= 1) & (df_bugs["sub_bug_count"] < 3)).sum())
    c1, c2 = st.columns(2)
    c1.metric("🔴 3+ bugs", b1)
    c2.metric("🟠 1–2 bugs", b2)


def render_trend_table(st: "streamlit", trend_data: list[dict]) -> None:
    """Render the sprint trend data table.
    
    Args:
        st: Streamlit module
        trend_data: List of SprintMetrics.to_dict() results
    """
    df = pd.DataFrame(trend_data)
    tbl = df[["sprint_name", "total_cards", "total_sub_bugs", "cards_with_bugs", "avg_bugs_per_card", "bug_rate_pct"]].rename(columns={
        "sprint_name": "Sprint",
        "total_cards": "Cards",
        "total_sub_bugs": "Sub-bugs",
        "cards_with_bugs": "C/ Bugs",
        "avg_bugs_per_card": "Média",
        "bug_rate_pct": "Taxa %",
    })
    st.dataframe(tbl, use_container_width=True, hide_index=True)
