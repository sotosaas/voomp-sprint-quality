"""Plotly chart components."""

from __future__ import annotations

import plotly.graph_objects as go

from src.ui.styles import COLORS, PLOTLY_THEME, PLOTLY_AXIS_STYLE


def create_bar_chart(
    x: list,
    y: list,
    title: str,
    y_label: str,
    colors: list[str] | str = None,
    height: int = 320,
) -> go.Figure:
    """Create a styled bar chart.
    
    Args:
        x: X-axis values
        y: Y-axis values
        title: Chart title
        y_label: Y-axis label
        colors: Bar colors (single color or list)
        height: Chart height in pixels
        
    Returns:
        Plotly Figure object
    """
    if colors is None:
        colors = COLORS["orange"]

    fig = go.Figure(go.Bar(
        x=x,
        y=y,
        marker_color=colors,
        marker_line_width=0,
        text=[str(round(v, 1)) for v in y],
        textposition="outside",
        textfont=dict(color=COLORS["muted_fg"], size=11),
        hovertemplate="<b>%{x}</b><br>" + y_label + ": %{y}<extra></extra>",
    ))

    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color=COLORS["foreground"])),
        yaxis_title=y_label,
        **PLOTLY_THEME,
        height=height,
    )
    
    fig.update_xaxes(**PLOTLY_AXIS_STYLE)
    fig.update_yaxes(**PLOTLY_AXIS_STYLE, rangemode="tozero")

    return fig


def create_card_ranking_chart(
    keys: list[str],
    bug_counts: list[int],
    height: int = 350,
) -> go.Figure:
    """Create a bar chart for card bug ranking.
    
    Bars are colored based on bug count (more bugs = more red).
    """
    max_bugs = max(bug_counts) if bug_counts else 1
    colors = [
        f"rgba(249, {max(115, 200 - int((v / max_bugs) * 85))}, {max(22, 80 - int((v / max_bugs) * 58))}, 0.9)"
        for v in bug_counts
    ]

    fig = go.Figure(go.Bar(
        x=keys,
        y=bug_counts,
        marker_color=colors,
        text=bug_counts,
        textposition="outside",
        textfont=dict(color=COLORS["muted_fg"], size=11),
    ))

    fig.update_layout(
        title=dict(text="Top 10 Cards por Sub-bugs", font=dict(size=14)),
        xaxis_title="Card",
        yaxis_title="Sub-bugs",
        height=height,
        **PLOTLY_THEME,
    )
    
    fig.update_xaxes(tickangle=-30, **PLOTLY_AXIS_STYLE)
    fig.update_yaxes(**PLOTLY_AXIS_STYLE, rangemode="tozero")

    return fig


def create_trend_chart(
    x_labels: list[str],
    y_values: list[float],
    y_label: str,
    active_sprints: list[str] = None,
    show_trendline: bool = True,
    is_bug_metric: bool = True,
    height: int = 380,
) -> go.Figure:
    """Create a line chart with trend analysis.
    
    Args:
        x_labels: Sprint names
        y_values: Metric values
        y_label: Y-axis label
        active_sprints: List of active sprint names (for highlighting)
        show_trendline: Whether to show linear trendline
        is_bug_metric: True if lower is better
        height: Chart height
        
    Returns:
        Plotly Figure object
    """
    fig = go.Figure()

    # Main line
    fig.add_trace(go.Scatter(
        x=x_labels,
        y=y_values,
        mode="lines+markers+text",
        name=y_label,
        line=dict(color=COLORS["orange"], width=3),
        marker=dict(size=9, color=COLORS["orange"], line=dict(width=2, color="#fff")),
        text=[str(round(v, 1)) for v in y_values],
        textposition="top center",
        textfont=dict(color=COLORS["foreground"], size=11),
    ))

    # Trendline
    if show_trendline and len(y_values) >= 2:
        try:
            import numpy as np
            x_num = list(range(len(y_values)))
            coef = np.polyfit(x_num, y_values, 1)
            trendline_y = [coef[0] * i + coef[1] for i in x_num]
            
            # Green if improving, red if worsening
            trend_color = COLORS["danger"] if (is_bug_metric and coef[0] > 0) else COLORS["success"]
            
            fig.add_trace(go.Scatter(
                x=x_labels,
                y=trendline_y,
                mode="lines",
                name="Tendência",
                line=dict(color=trend_color, width=2, dash="dash"),
            ))
        except Exception:
            pass

    # Highlight active sprints
    if active_sprints:
        active_x = [x for x in x_labels if x in active_sprints]
        active_y = [y_values[x_labels.index(x)] for x in active_x]
        
        if active_x:
            fig.add_trace(go.Scatter(
                x=active_x,
                y=active_y,
                mode="markers",
                name="Sprint ativa",
                marker=dict(size=14, color=COLORS["orange"], symbol="star", line=dict(width=2, color="#fff")),
            ))

    fig.update_layout(
        xaxis_title="Sprint",
        yaxis_title=y_label,
        height=height,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        **PLOTLY_THEME,
    )
    
    fig.update_xaxes(tickangle=-20, **PLOTLY_AXIS_STYLE)
    fig.update_yaxes(**PLOTLY_AXIS_STYLE, rangemode="tozero")

    return fig
