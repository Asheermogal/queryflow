"""
Chart renderer. Takes a chart_spec from the LLM and produces a Plotly figure.

Critically: we DO NOT let the LLM emit raw plot code. It emits a structured spec
and we render it deterministically. This is how we avoid the "bar chart counted
instances instead of summing values" class of bug.
"""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from core.design import Color, Font


def render_chart(spec: dict, df: pd.DataFrame) -> None:
    if not spec:
        return
    chart_type = spec.get("chart_type")
    if chart_type in (None, "none", "table", ""):
        return

    x_col = spec.get("x_column")
    y_col = spec.get("y_column")

    if x_col not in df.columns or y_col not in df.columns:
        st.warning(
            f"Chart skipped — referenced columns "
            f"('{x_col}', '{y_col}') aren't in the result set."
        )
        return

    # Drop nulls in y column; sometimes also need to ensure y is numeric
    plot_df = df[df[y_col].notna()].copy()
    if not pd.api.types.is_numeric_dtype(plot_df[y_col]):
        plot_df[y_col] = pd.to_numeric(plot_df[y_col], errors="coerce")
        plot_df = plot_df[plot_df[y_col].notna()]

    limit = spec.get("limit") or 25
    plot_df = plot_df.head(limit)

    if plot_df.empty:
        st.info("No plottable rows after filtering nulls.")
        return

    title = spec.get("title", "")

    if chart_type == "bar":
        fig = px.bar(
            plot_df, x=x_col, y=y_col, title=title,
            color_discrete_sequence=[Color.accent],
        )
    elif chart_type == "line":
        fig = px.line(
            plot_df, x=x_col, y=y_col, title=title, markers=True,
            color_discrete_sequence=[Color.accent],
        )
    elif chart_type == "pie":
        fig = px.pie(
            plot_df, names=x_col, values=y_col, title=title,
            color_discrete_sequence=px.colors.sequential.Teal,
        )
    else:
        return

    # Consistent styling
    fig.update_layout(
        font_family=Font.body,
        plot_bgcolor=Color.surface,
        paper_bgcolor=Color.surface,
        title_font_family=Font.display,
        title_font_size=20,
        title_font_color=Color.ink,
        title_x=0.0,
        margin=dict(l=20, r=20, t=60, b=20),
        xaxis=dict(
            showgrid=False,
            tickfont=dict(family=Font.mono, size=11, color=Color.ink_2),
            title_font=dict(family=Font.body, size=12, color=Color.ink_muted),
        ),
        yaxis=dict(
            gridcolor=Color.border,
            tickfont=dict(family=Font.mono, size=11, color=Color.ink_2),
            title_font=dict(family=Font.body, size=12, color=Color.ink_muted),
        ),
    )

    st.plotly_chart(fig, use_container_width=True)
