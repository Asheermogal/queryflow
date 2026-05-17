"""
Full-width LLM-generated dashboard.

Flow:
  1. Right-rail button "Explore the dataset in a dashboard" calls
     `ensure_dashboard_spec`, which makes ONE cached LLM call producing a
     structured spec (insights + 6 chart specs).
  2. After that, the right-rail button becomes "Show the Dashboard". Clicking
     it sets st.session_state.view = "dashboard" and app.py routes here.
  3. We render the insights, run a deterministic templated SQL aggregation per
     chart, and plot with our existing chart renderer.
  4. Custom chart builder at the bottom lets the user plot any column from the
     FULL TABLE (not the dashboard's pre-aggregated results).

LLM never writes SQL for the dashboard — we template it from chart_type +
aggregation. This avoids the entire "LLM SQL was wrong" class of bug.
"""
from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from core.config import DASHBOARD_CHART_COUNT, DASHBOARD_DEFAULT_ROW_LIMIT, TOKENS_DASHBOARD
from core.dataset_brief import brief_as_text, get_cached_brief, get_or_build_brief
from core.prompts import DASHBOARD_SYS, dashboard_user
from ingest.database import Database, Dataset
from ingest.schema import ColumnStats, schema_to_prompt_text
from llm.base import LLMClient
from ui.chart import render_chart
from ui.components import section_label
from ui.custom_chart import custom_chart_builder


VALID_CHART_TYPES = {"bar", "line", "pie"}
VALID_AGGS = {"sum", "avg", "count", "min", "max"}


def _spec_key(table: str) -> str:
    return f"_dashboard_spec__{table}"


def get_cached_spec(table: str) -> dict[str, Any] | None:
    return st.session_state.get(_spec_key(table))


def ensure_dashboard_spec(
    dataset: Dataset,
    stats: list[ColumnStats],
    client: LLMClient | None,
) -> dict[str, Any] | None:
    """Build the dashboard spec on demand and cache it. Returns None if no LLM
    or generation failed."""
    key = _spec_key(dataset.table)
    cached = st.session_state.get(key)
    if cached:
        return cached
    if client is None:
        return None

    brief = get_or_build_brief(dataset, stats, client)
    schema_text = schema_to_prompt_text(dataset.table, dataset.description, stats)
    try:
        with st.spinner("Designing dashboard…"):
            spec = client.complete_json(
                DASHBOARD_SYS,
                dashboard_user(dataset.name, schema_text, brief_as_text(brief)),
                max_tokens=TOKENS_DASHBOARD,
            )
        spec.setdefault("insights", [])
        spec.setdefault("charts", [])
        spec["charts"] = spec["charts"][:DASHBOARD_CHART_COUNT]
        st.session_state[key] = spec
        return spec
    except Exception as e:
        st.error(f"Couldn't build the dashboard: {e}")
        return None


def _build_chart_sql(table: str, chart: dict[str, Any]) -> str:
    x_col = chart.get("x_column", "")
    y_col = chart.get("y_column", "")
    agg = (chart.get("aggregation") or "count").lower()
    chart_type = (chart.get("chart_type") or "bar").lower()
    limit = int(chart.get("limit") or DASHBOARD_DEFAULT_ROW_LIMIT)
    limit = max(3, min(limit, 50))

    if agg not in VALID_AGGS:
        agg = "count"
    if chart_type not in VALID_CHART_TYPES:
        chart_type = "bar"

    x = f'"{x_col}"'
    if agg == "count" or not y_col or y_col == "count":
        select_y = "COUNT(*) AS value"
        where = ""
    else:
        y = f'"{y_col}"'
        sql_agg = "AVG" if agg == "avg" else agg.upper()
        select_y = f"{sql_agg}({y}) AS value"
        where = f"WHERE {y} IS NOT NULL"

    if chart_type == "line":
        order_by = f"ORDER BY {x}"
    else:
        order_by = "ORDER BY value DESC"

    return (
        f"SELECT {x} AS x, {select_y} "
        f'FROM "{table}" '
        f"{where} "
        f"GROUP BY {x} "
        f"{order_by} "
        f"LIMIT {limit}"
    )


def _render_chart_tile(db: Database, dataset: Dataset, chart: dict[str, Any], idx: int) -> None:
    valid_cols = {s.name for s in []}  # filled at call site; we pass via dataset.* metadata instead
    title = chart.get("title") or "Chart"
    sql = _build_chart_sql(dataset.table, chart)

    try:
        cols, rows = db.query(sql)
        df = pd.DataFrame(rows, columns=cols)
    except Exception as e:
        st.markdown(f"**{title}**")
        st.warning(f"Couldn't run chart: {e}")
        with st.expander("SQL", expanded=False):
            st.code(sql, language="sql")
        return

    if df.empty:
        st.markdown(f"**{title}**")
        st.info("No rows.")
        return

    render_chart(
        {
            "chart_type": chart.get("chart_type", "bar"),
            "title": title,
            "x_column": "x",
            "y_column": "value",
            "limit": int(chart.get("limit") or DASHBOARD_DEFAULT_ROW_LIMIT),
        },
        df,
    )


def render_dashboard(
    db: Database,
    dataset: Dataset,
    stats: list[ColumnStats],
    client: LLMClient | None,
) -> None:
    """Full-width dashboard view. Routed via st.session_state.view == 'dashboard'."""

    # Header row: title + back button
    h1, h2 = st.columns([1, 0.18])
    with h1:
        st.markdown(
            f'<div class="qf-question" style="margin-top:0;">{dataset.name} · Dashboard</div>',
            unsafe_allow_html=True,
        )
    with h2:
        if st.button("← Back to chat", use_container_width=True, type="secondary"):
            st.session_state.view = "chat"
            st.rerun()

    spec = get_cached_spec(dataset.table)
    if not spec:
        spec = ensure_dashboard_spec(dataset, stats, client)
    if not spec:
        st.info(
            "Dashboard not generated yet. Go back to chat and click "
            "**Explore the dataset in a dashboard** in the right rail."
        )
        return

    insights = spec.get("insights") or []
    if insights:
        section_label("Overview")
        findings_html = "".join(
            f'<div class="finding"><span class="num">{i:02d}</span><span>{b}</span></div>'
            for i, b in enumerate(insights, start=1)
        )
        st.markdown(
            f'<div class="qf-analysis">'
            f'<div class="qf-analysis-headline">High-level insights</div>'
            f'{findings_html}'
            f'</div>',
            unsafe_allow_html=True,
        )

    charts = spec.get("charts") or []
    if charts:
        section_label("Charts")
        # 2-column grid
        for row_start in range(0, len(charts), 2):
            row_charts = charts[row_start : row_start + 2]
            cols = st.columns(len(row_charts), gap="medium")
            for col, ch in zip(cols, row_charts):
                with col:
                    _render_chart_tile(db, dataset, ch, idx=row_start)

    # Custom chart builder using the full table
    section_label("Build your own chart")
    all_cols = [s.name for s in stats]
    numeric_cols = [
        s.name for s in stats
        if (s.sql_type or "").upper().startswith(("INT", "REAL", "FLOAT", "NUM"))
    ]
    custom_chart_builder(
        key_prefix=f"cc_dash_{dataset.table}",
        db=db,
        table=dataset.table,
        all_columns=all_cols,
        numeric_columns=numeric_cols,
    )

    # Refresh / regenerate
    st.markdown("---")
    if st.button("Regenerate dashboard", key="dash_regen", type="secondary"):
        st.session_state.pop(_spec_key(dataset.table), None)
        st.rerun()
