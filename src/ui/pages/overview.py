"""Overview page - 30-day comparison across all projects."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

from src.config import AppConfig
from src.services import MetricsService
from src.ui.components import (
    render_project_card,
    create_bar_chart,
)

if TYPE_CHECKING:
    import streamlit


class OverviewPage:
    """Overview page for 30-day project comparison."""

    def __init__(
        self,
        st: "streamlit",
        config: AppConfig,
        metrics_service: MetricsService,
    ) -> None:
        self._st = st
        self._config = config
        self._metrics = metrics_service

    def render(self) -> None:
        """Render the overview page."""
        # Header
        self._st.markdown("# 📊 Visão Geral — Últimos 30 dias")
        self._st.markdown("Comparativo de qualidade de entrega entre os produtos Voomp.")
        self._st.markdown("---")

        # Load data
        with self._st.spinner("Carregando dados de todos os produtos..."):
            summaries = self._load_all_summaries()

        if not summaries:
            self._st.warning("Nenhum dado disponível.")
            return

        # Project cards
        self._st.markdown("### Métricas por Produto")
        self._render_project_cards(summaries)

        self._st.markdown("---")

        # Comparison charts
        self._st.markdown("### Comparativo entre Produtos")
        self._render_comparison_charts(summaries)

        # Ranking table
        self._st.markdown("---")
        self._st.markdown("### Ranking Geral de Qualidade")
        self._st.caption("Ordenado por menor taxa de bug nos últimos 30 dias")
        self._render_ranking_table(summaries)

    def _load_all_summaries(self) -> list[dict]:
        """Load 30-day summaries for all projects."""
        @self._st.cache_data(ttl=900, show_spinner=False)
        def _fetch():
            results = []
            for project in self._config.projects:
                try:
                    summary = self._metrics.compute_project_summary(project.key)
                    results.append(summary.to_dict())
                except Exception as e:
                    results.append({
                        "project_key": project.key,
                        "project_name": project.name,
                        "total_cards": 0,
                        "total_sub_bugs": 0,
                        "cards_with_bugs": 0,
                        "avg_bugs_per_card": 0.0,
                        "bug_rate_pct": 0.0,
                        "top_dev": "—",
                        "top_dev_score": 0.0,
                        "_error": str(e),
                    })
            return results
        
        return _fetch()

    def _render_project_cards(self, summaries: list[dict]) -> None:
        """Render project summary cards in a grid."""
        cols_per_row = 3
        rows = [summaries[i:i + cols_per_row] for i in range(0, len(summaries), cols_per_row)]

        for row in rows:
            cols = self._st.columns(len(row), gap="medium")
            for col, summary in zip(cols, row):
                with col:
                    render_project_card(
                        self._st,
                        project_name=summary["project_name"],
                        total_cards=summary["total_cards"],
                        total_sub_bugs=summary["total_sub_bugs"],
                        avg_bugs_per_card=summary["avg_bugs_per_card"],
                        bug_rate_pct=summary["bug_rate_pct"],
                        top_dev=summary["top_dev"],
                        has_error="_error" in summary,
                    )

    def _render_comparison_charts(self, summaries: list[dict]) -> None:
        """Render comparison charts in tabs."""
        names = [s["project_name"] for s in summaries]
        total_bugs = [s["total_sub_bugs"] for s in summaries]
        total_cards = [s["total_cards"] for s in summaries]
        bug_rates = [s["bug_rate_pct"] for s in summaries]

        product_colors = [
            self._config.project_colors.get(s["project_key"], "#4c7be1")
            for s in summaries
        ]

        tab_bugs, tab_rate, tab_cards = self._st.tabs([
            "🐛 Total de Sub-bugs",
            "📉 Taxa de Bug (%)",
            "📦 Cards Entregues",
        ])

        with tab_bugs:
            fig = create_bar_chart(
                x=names,
                y=total_bugs,
                title="Sub-bugs por Produto (30 dias)",
                y_label="Sub-bugs",
                colors=product_colors,
            )
            self._st.plotly_chart(fig, use_container_width=True)

        with tab_rate:
            fig = create_bar_chart(
                x=names,
                y=bug_rates,
                title="Taxa de Bug por Produto (%)",
                y_label="Taxa (%)",
                colors=product_colors,
            )
            self._st.plotly_chart(fig, use_container_width=True)

        with tab_cards:
            fig = create_bar_chart(
                x=names,
                y=total_cards,
                title="Cards em Produção por Produto (30 dias)",
                y_label="Cards",
                colors=product_colors,
            )
            self._st.plotly_chart(fig, use_container_width=True)

    def _render_ranking_table(self, summaries: list[dict]) -> None:
        """Render the quality ranking table."""
        df = pd.DataFrame([{
            "Produto": s["project_name"],
            "Cards": s["total_cards"],
            "Sub-bugs": s["total_sub_bugs"],
            "Média bugs/card": s["avg_bugs_per_card"],
            "Taxa bug %": s["bug_rate_pct"],
            "Top Dev": s["top_dev"],
        } for s in summaries]).sort_values("Taxa bug %").reset_index(drop=True)

        medals = ["🥇", "🥈", "🥉"] + [""] * (len(df) - 3)
        df.insert(0, "#", medals[:len(df)])

        def color_rate(val):
            if isinstance(val, (int, float)):
                if val >= 50:
                    return "color: #ff4444; font-weight:bold"
                if val >= 25:
                    return "color: #ff9944; font-weight:bold"
                if val == 0:
                    return "color: #50fa7b; font-weight:bold"
            return ""

        self._st.dataframe(
            df.style.map(color_rate, subset=["Taxa bug %"]),
            use_container_width=True,
            hide_index=True,
            column_config={
                "#": self._st.column_config.TextColumn("", width=40),
                "Produto": self._st.column_config.TextColumn("Produto", width=180),
                "Cards": self._st.column_config.NumberColumn("Cards", width=70),
                "Sub-bugs": self._st.column_config.NumberColumn("Sub-bugs", width=80),
                "Média bugs/card": self._st.column_config.NumberColumn("Média bugs/card", width=130),
                "Taxa bug %": self._st.column_config.NumberColumn("Taxa bug %", width=100),
                "Top Dev": self._st.column_config.TextColumn("🏆 Top Dev", width=160),
            },
        )
