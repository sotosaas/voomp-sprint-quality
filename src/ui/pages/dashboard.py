"""Dashboard page - Sprint analysis for a single project."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import pandas as pd

from src.config import AppConfig
from src.services import JiraService, MetricsService, JiraAuthError, JiraNotFoundError
from src.repositories import CacheRepository
from src.ui.icons import get_emoji
from src.ui.components import (
    Sidebar,
    render_kpi_row,
    create_card_ranking_chart,
    create_trend_chart,
    render_issues_table,
    render_dev_ranking_table,
    render_card_ranking_table,
)

if TYPE_CHECKING:
    import streamlit


class DashboardPage:
    """Dashboard page for sprint analysis."""

    def __init__(
        self,
        st: "streamlit",
        config: AppConfig,
        jira_service: JiraService,
        metrics_service: MetricsService,
    ) -> None:
        self._st = st
        self._config = config
        self._jira = jira_service
        self._metrics = metrics_service

    def render(self) -> None:
        """Render the dashboard page."""
        # Initialize session state
        self._init_session_state()

        # Get current selections
        project_key = self._st.session_state.selected_project
        project = self._config.get_project(project_key)

        if not project:
            self._st.error(f"Projeto {project_key} não encontrado.")
            return

        # Header
        self._st.markdown(f"# {project.emoji} {project.name}")

        # Load sprints
        sprints = self._load_sprints(project_key)
        if not sprints:
            self._st.warning(f"Nenhuma sprint encontrada para {project.name}.")
            return

        # Sprint selector
        sprint = self._render_sprint_selector(sprints)

        # Save selected sprint
        self._st.session_state.selected_sprint_id = sprint["id"]
        self._st.session_state.selected_sprint_name = sprint["name"]

        self._st.markdown("---")

        # Load issues
        try:
            df = self._load_issues(project_key, sprint["id"], sprint["name"])
        except JiraAuthError as e:
            self._st.error(f"❌ Erro de autenticação: {e}")
            return
        except JiraNotFoundError as e:
            self._st.error(f"❌ Recurso não encontrado: {e}")
            return
        except Exception as e:
            self._st.error(f"❌ Erro ao buscar dados: {e}")
            return

        if df.empty:
            status_display = ", ".join(f"**'{s}'**" for s in self._config.production_statuses)
            self._st.info(f"Nenhum card com status {status_display} na sprint **{sprint['name']}**.")
            return

        # KPIs
        self._render_kpis(df)
        self._st.markdown("---")

        # Cards table
        self._st.markdown("### 📋 Cards da Sprint")
        render_issues_table(self._st, df)

        # Dev ranking
        self._st.markdown("---")
        self._st.markdown("### 🏆 Ranking de Desenvolvedores")
        self._st.caption("Score = cards entregues ÷ (sub-bugs + 1) · quanto maior, melhor")
        issues = self._metrics.get_sprint_issues(project_key, sprint["id"])
        ranking = self._metrics.compute_dev_ranking(issues)
        render_dev_ranking_table(self._st, [r.to_dict() for r in ranking])

        # Card ranking
        self._st.markdown("---")
        self._st.markdown("### 🔴 Cards com Mais Sub-bugs")
        card_ranking = self._metrics.compute_card_ranking(issues, top_n=10)
        
        if card_ranking:
            col_bars, col_detail = self._st.columns([3, 2], gap="large")
            
            with col_bars:
                fig = create_card_ranking_chart(
                    keys=[c.key for c in card_ranking],
                    bug_counts=[c.sub_bug_count for c in card_ranking],
                )
                self._st.plotly_chart(fig, use_container_width=True)
            
            with col_detail:
                self._st.markdown("##### Detalhes")
                render_card_ranking_table(self._st, [c.to_dict() for c in card_ranking])
        else:
            self._st.success("🎉 Nenhum card gerou sub-bugs nessa sprint!")

        # Trend chart
        self._st.markdown("---")
        self._st.markdown("### 📈 Tendência de Qualidade por Sprint")
        self._render_trend_section(project_key)

    def _init_session_state(self) -> None:
        """Initialize session state variables."""
        if "selected_project" not in self._st.session_state:
            self._st.session_state.selected_project = self._config.project_keys[0]
        if "selected_sprint_id" not in self._st.session_state:
            self._st.session_state.selected_sprint_id = None
        if "selected_sprint_name" not in self._st.session_state:
            self._st.session_state.selected_sprint_name = ""

    @property
    def _cache_ttl(self) -> int:
        return self._config.streamlit_cache_ttl

    def _load_sprints(self, project_key: str) -> list[dict]:
        """Load sprints with caching. Returns list of dicts for serializability."""
        @self._st.cache_data(ttl=self._cache_ttl, show_spinner=False)
        def _fetch(_project_key: str) -> list[dict]:
            sprints = self._jira.get_sprints_for_project(
                _project_key,
                state="active,closed",
                max_results=50,
                year=datetime.now().year,
            )
            # Convert to dicts for pickle serialization
            return [s.to_dict() for s in reversed(sprints)]
        
        return _fetch(project_key)

    def _load_issues(self, project_key: str, sprint_id: int, sprint_name: str) -> pd.DataFrame:
        """Load issues with caching."""
        @self._st.cache_data(ttl=self._cache_ttl, show_spinner=False)
        def _fetch(_project_key: str, _sprint_id: int, _sprint_name: str):
            df = self._metrics.build_issues_dataframe(_project_key, _sprint_id, _sprint_name)
            if "sub_bugs" in df.columns:
                df = df.drop(columns=["sub_bugs"])
            return df
        
        return _fetch(project_key, sprint_id, sprint_name)

    def _render_sprint_selector(self, sprints: list[dict]) -> dict:
        """Render sprint selector and return selected sprint dict."""
        sprint_labels = [s["name"] for s in sprints]
        sprint_ids = [s["id"] for s in sprints]

        default_idx = 0
        if self._st.session_state.selected_sprint_id in sprint_ids:
            default_idx = sprint_ids.index(self._st.session_state.selected_sprint_id)

        col_sprint, col_status, _ = self._st.columns([3, 1, 4])

        with col_sprint:
            chosen_label = self._st.selectbox(
                "Sprint",
                options=sprint_labels,
                index=default_idx,
                key="main_sprint_selector",
            )

        chosen_idx = sprint_labels.index(chosen_label)
        chosen_sprint = sprints[chosen_idx]

        with col_status:
            state = chosen_sprint.get("state", "")
            status_label = "🟢 Ativa" if state == "active" else "✅ Fechada"
            self._st.markdown(f"**{status_label}**")

        return chosen_sprint

    def _render_kpis(self, df: pd.DataFrame) -> None:
        """Render KPI metrics."""
        total_cards = len(df)
        total_bugs = int(df["sub_bug_count"].sum())
        cards_with_bugs = int((df["sub_bug_count"] > 0).sum())
        avg_bugs = round(float(df["sub_bug_count"].mean()), 2)
        bug_rate = round(float((df["sub_bug_count"] > 0).mean() * 100), 1)

        render_kpi_row(self._st, total_cards, total_bugs, cards_with_bugs, avg_bugs, bug_rate)

    def _render_trend_section(self, project_key: str) -> None:
        """Render the trend analysis section."""
        with self._st.expander("📊 Ver tendência", expanded=False):
            col_ctrl1, col_ctrl2, _ = self._st.columns([1, 1, 4])
            
            with col_ctrl1:
                n_sprints = self._st.slider("Nº de sprints", min_value=2, max_value=10, value=5, step=1)
            
            with col_ctrl2:
                trend_metric = self._st.selectbox(
                    "Métrica",
                    options=["total_sub_bugs", "avg_bugs_per_card", "bug_rate_pct", "total_cards"],
                    format_func=lambda x: {
                        "total_sub_bugs": "Total de sub-bugs",
                        "avg_bugs_per_card": "Média bugs/card",
                        "bug_rate_pct": "Taxa de bugs (%)",
                        "total_cards": "Cards em produção",
                    }[x],
                )

            with self._st.spinner("Carregando tendência..."):
                try:
                    trend_data = self._load_trend(project_key, n_sprints)
                except Exception as e:
                    self._st.error(f"❌ Erro: {e}")
                    return

            if not trend_data:
                self._st.info("Sem dados suficientes para exibir tendência.")
                return

            self._render_trend_chart(trend_data, trend_metric)

    def _load_trend(self, project_key: str, n_sprints: int) -> list[dict]:
        """Load trend data with caching."""
        @self._st.cache_data(ttl=self._cache_ttl, show_spinner=False)
        def _fetch(_project_key: str, _n_sprints: int):
            trend_metrics = self._metrics.compute_sprint_trend(_project_key, _n_sprints)
            return [m.to_dict() for m in trend_metrics]
        
        return _fetch(project_key, n_sprints)

    def _render_trend_chart(self, trend_data: list[dict], metric_key: str) -> None:
        """Render the trend chart with metrics."""
        metric_labels = {
            "total_sub_bugs": "Total de Sub-bugs",
            "avg_bugs_per_card": "Média Bugs / Card",
            "bug_rate_pct": "Taxa de Bugs (%)",
            "total_cards": "Cards em Produção",
        }
        y_label = metric_labels[metric_key]
        y_values = [d[metric_key] for d in trend_data]
        x_labels = [d["sprint_name"] for d in trend_data]

        is_bug_metric = metric_key != "total_cards"
        delta = y_values[-1] - y_values[-2] if len(y_values) >= 2 else None

        # Trend indicator
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

        # KPI row
        tm1, tm2, tm3, tm4 = self._st.columns(4)
        tm1.metric("Última sprint", f"{y_values[-1]}", delta=f"{delta:+.1f} vs anterior" if delta else None, delta_color=trend_color)
        tm2.metric("Melhor sprint", f"{min(y_values)}" if is_bug_metric else f"{max(y_values)}")
        tm3.metric("Pior sprint", f"{max(y_values)}" if is_bug_metric else f"{min(y_values)}")
        tm4.metric("Tendência", trend_icon)

        # Chart
        active_sprints = [d["sprint_name"] for d in trend_data if d["sprint_state"] == "active"]
        fig = create_trend_chart(
            x_labels=x_labels,
            y_values=y_values,
            y_label=y_label,
            active_sprints=active_sprints,
            is_bug_metric=is_bug_metric,
        )
        self._st.plotly_chart(fig, use_container_width=True)

        # Data table
        with self._st.expander("Ver tabela de dados"):
            from src.ui.components.tables import render_trend_table
            render_trend_table(self._st, trend_data)
