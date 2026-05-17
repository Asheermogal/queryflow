"""
Custom chart builder.

Two surfaces:
  - Inline in chat: operates on the result DataFrame returned by the user's SQL
  - In the dashboard: operates against the FULL TABLE via deterministic SQL
    aggregation (we build the SQL ourselves; LLM is never involved here)

Both surfaces share `render_chart` from ui.chart for actual rendering, so look
and feel are identical.
"""
from __future__ import annotations

from typing import Iterable

import pandas as pd
import streamlit as st

from ingest.database import Database
from ui.chart import render_chart


CHART_TYPES = ["bar", "line", "pie"]
AGG_FUNCS = ["sum", "avg", "count", "min", "max"]


def _is_numeric_col(df: pd.DataFrame, col: str) -> bool:
    return pd.api.types.is_numeric_dtype(df[col]) if col in df.columns else False


def _build_full_table_sql(
    table: str,
    x_col: str,
    y_col: str | None,
    agg: str,
    chart_type: str,
    limit: int,
) -> str:
    """Deterministic, parameter-templated SQL for the full-table case.
    Column names are wrapped in double quotes (SQLite identifiers)."""
    x = f'"{x_col}"'
    if agg == "count":
        select_y = "COUNT(*) AS value"
        where = ""
        order_by_col = "value"
    else:
        y = f'"{y_col}"'
        sql_agg = "AVG" if agg == "avg" else agg.upper()
        select_y = f"{sql_agg}({y}) AS value"
        where = f"WHERE {y} IS NOT NULL"
        order_by_col = "value"

    if chart_type == "line":
        order_by = f"ORDER BY {x}"
    else:
        order_by = f"ORDER BY {order_by_col} DESC"

    return (
        f"SELECT {x} AS x, {select_y} "
        f'FROM "{table}" '
        f"{where} "
        f"GROUP BY {x} "
        f"{order_by} "
        f"LIMIT {int(limit)}"
    )


def custom_chart_builder(
    *,
    key_prefix: str,
    result_df: pd.DataFrame | None = None,
    db: Database | None = None,
    table: str | None = None,
    all_columns: Iterable[str] | None = None,
    numeric_columns: Iterable[str] | None = None,
) -> None:
    """Render the custom chart UI.

    Mode 1 (result-driven): pass `result_df`. Columns are derived from the df.
    Mode 2 (full-table): pass `db`, `table`, `all_columns`, `numeric_columns`.
    """

    if result_df is not None and not result_df.empty:
        all_cols = list(result_df.columns)
        num_cols = [c for c in all_cols if _is_numeric_col(result_df, c)]
        source = "result"
    elif db is not None and table is not None and all_columns is not None:
        all_cols = list(all_columns)
        num_cols = list(numeric_columns or [])
        source = "table"
    else:
        st.info("No data available to plot.")
        return

    if not all_cols:
        st.info("No columns available.")
        return

    cols = st.columns([0.25, 0.3, 0.25, 0.2])
    chart_type = cols[0].selectbox(
        "Chart type",
        options=CHART_TYPES,
        key=f"{key_prefix}_ct",
    )
    x_col = cols[1].selectbox(
        "X (category / time)",
        options=all_cols,
        key=f"{key_prefix}_x",
    )

    agg = cols[2].selectbox(
        "Aggregation",
        options=AGG_FUNCS,
        index=0,
        key=f"{key_prefix}_agg",
    )

    if agg == "count":
        y_col = None
        cols[3].caption("y = COUNT(*)")
    else:
        y_options = num_cols or all_cols
        y_col = cols[3].selectbox(
            "Y (numeric)",
            options=y_options,
            key=f"{key_prefix}_y",
        )

    limit = st.slider(
        "Row limit",
        min_value=3,
        max_value=50,
        value=10 if chart_type == "pie" else 20,
        key=f"{key_prefix}_lim",
    )

    if not st.button("Build chart", key=f"{key_prefix}_build", type="primary"):
        return

    if source == "result":
        plot_df = result_df.copy()
        # Aggregate on the fly
        if agg == "count":
            agg_df = (
                plot_df.groupby(x_col, dropna=True).size().reset_index(name="value")
            )
        else:
            if y_col is None or y_col not in plot_df.columns:
                st.error("Pick a y column.")
                return
            plot_df[y_col] = pd.to_numeric(plot_df[y_col], errors="coerce")
            plot_df = plot_df[plot_df[y_col].notna()]
            pandas_agg = "mean" if agg == "avg" else agg
            agg_df = (
                plot_df.groupby(x_col, dropna=True)[y_col]
                .agg(pandas_agg)
                .reset_index()
                .rename(columns={y_col: "value"})
            )
        if chart_type == "line":
            agg_df = agg_df.sort_values(x_col).head(limit)
        else:
            agg_df = agg_df.sort_values("value", ascending=False).head(limit)
    else:
        sql = _build_full_table_sql(table, x_col, y_col, agg, chart_type, limit)
        try:
            with st.spinner("Aggregating…"):
                columns, rows = db.query(sql)
                agg_df = pd.DataFrame(rows, columns=columns)
        except Exception as e:
            st.error(f"Couldn't build chart: {e}")
            with st.expander("SQL"):
                st.code(sql, language="sql")
            return

    if agg_df.empty:
        st.info("No rows after aggregation.")
        return

    spec = {
        "chart_type": chart_type,
        "title": f"{agg.upper()}({y_col or '*'}) by {x_col}",
        "x_column": x_col if source == "table" else x_col,
        "y_column": "value" if source == "table" else "value",
        "limit": int(limit),
    }
    # render_chart expects the y column to be named in the df itself.
    if source == "result":
        spec["x_column"] = x_col
        agg_df = agg_df.rename(columns={x_col: x_col})
    else:
        spec["x_column"] = "x"
    render_chart(spec, agg_df)
