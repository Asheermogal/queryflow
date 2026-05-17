"""
Right-rail dataset panel.

Shows dataset name + description, key stats, an LLM-generated brief, the
schema in an expander, and the dashboard launcher.

The dashboard launcher has two states:
  - no spec cached → "Explore the dataset in a dashboard" (triggers generation)
  - spec cached    → "Show the Dashboard" (switches view)
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from core.dataset_brief import get_or_build_brief
from ingest.database import Dataset
from ingest.schema import ColumnStats
from llm.base import LLMClient
from ui.dashboard import ensure_dashboard_spec, get_cached_spec


def render_dataset_overview(
    dataset: Dataset,
    stats: list[ColumnStats],
    client: LLMClient | None = None,
) -> None:
    """Right-rail content: hero + stats + brief + dashboard button + schema."""

    st.markdown(
        f"""
        <div class="qf-rail-hero">
          <div class="qf-rail-name">{_escape(dataset.name)}</div>
          <div class="qf-rail-desc">{_escape(dataset.description)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    stats_html = (
        '<div class="qf-rail-stats">'
        f'  <div class="qf-stat"><div class="lbl">Rows</div><div class="val">{dataset.row_count:,}</div></div>'
        f'  <div class="qf-stat"><div class="lbl">Columns</div><div class="val">{dataset.column_count}</div></div>'
        f'  <div class="qf-stat"><div class="lbl">Encoding</div><div class="val">{_escape(dataset.encoding or "—")}</div></div>'
        "</div>"
    )
    st.markdown(stats_html, unsafe_allow_html=True)

    if dataset.suppression_markers:
        markers = ", ".join(f"'{m}'" for m in dataset.suppression_markers)
        st.markdown(
            f'<div class="qf-rail-note">'
            f'Suppression markers found and replaced with NULL: {_escape(markers)}'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Brief ────────────────────────────────────────────────────────
    if client is not None:
        brief = get_or_build_brief(dataset, stats, client)
        if brief and not brief.get("_error"):
            headline = brief.get("headline", "")
            bullets = brief.get("bullets") or []
            bullets_html = "".join(
                f'<li>{_escape(b)}</li>' for b in bullets
            )
            st.markdown(
                f"""
                <div class="qf-brief-card">
                  <div class="qf-brief-headline">{_escape(headline)}</div>
                  <ul class="qf-brief-bullets">{bullets_html}</ul>
                </div>
                """,
                unsafe_allow_html=True,
            )
        elif brief and brief.get("_error"):
            st.caption(f"Couldn't build brief: {brief['_error']}")

    # ── Dashboard launcher ───────────────────────────────────────────
    if client is not None:
        spec = get_cached_spec(dataset.table)
        if spec is None:
            if st.button(
                "Explore the dataset in a dashboard",
                key=f"dash_build_{dataset.table}",
                type="primary",
                use_container_width=True,
            ):
                ensure_dashboard_spec(dataset, stats, client)
                st.rerun()
        else:
            if st.button(
                "Show the Dashboard",
                key=f"dash_show_{dataset.table}",
                type="primary",
                use_container_width=True,
            ):
                st.session_state.view = "dashboard"
                st.rerun()

    # ── Schema expander ──────────────────────────────────────────────
    with st.expander("Schema", expanded=False):
        schema_rows = []
        for s in stats:
            schema_rows.append({
                "Column": s.name,
                "Type": _humanize_type(s.sql_type),
                "Distinct": f"{s.n_distinct:,}",
                "Null %": f"{s.null_pct:.1f}%",
            })
        df = pd.DataFrame(schema_rows)
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            height=min(35 * len(stats) + 38, 420),
        )


def _humanize_type(sql_type: str) -> str:
    t = (sql_type or "").upper()
    if t.startswith("INT"):
        return "integer"
    if t.startswith("REAL") or t.startswith("FLOAT") or t.startswith("NUM"):
        return "number"
    if t.startswith("TEXT") or t.startswith("VARCHAR") or t.startswith("CHAR"):
        return "text"
    if t.startswith("DATE") or t.startswith("TIME"):
        return "date"
    return t.lower() or "text"


def _escape(s: str | None) -> str:
    if s is None:
        return ""
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
