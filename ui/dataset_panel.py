"""
Right-rail dataset panel: shows dataset name, description, key stats,
and clickable expanders for Schema and Data Dictionary.

All rendered with clean components — no leaked HTML.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from ingest.database import Dataset
from ingest.schema import ColumnStats


def render_dataset_overview(dataset: Dataset, stats: list[ColumnStats]) -> None:
    """Render the full right-rail content: hero + schema + dictionary tabs."""

    # ── Hero: name + description + 4 stat tiles ──────────────────────
    st.markdown(
        f"""
        <div class="qf-rail-hero">
          <div class="qf-rail-name">{_escape(dataset.name)}</div>
          <div class="qf-rail-desc">{_escape(dataset.description)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 2x2 stat grid
    stats_html = (
        '<div class="qf-rail-stats">'
        f'  <div class="qf-stat"><div class="lbl">Rows</div><div class="val">{dataset.row_count:,}</div></div>'
        f'  <div class="qf-stat"><div class="lbl">Columns</div><div class="val">{dataset.column_count}</div></div>'
        f'  <div class="qf-stat"><div class="lbl">Encoding</div><div class="val">{_escape(dataset.encoding or "—")}</div></div>'
        f'  <div class="qf-stat"><div class="lbl">Dictionary</div><div class="val">{"Loaded" if dataset.dictionary_text else "None"}</div></div>'
        "</div>"
    )
    st.markdown(stats_html, unsafe_allow_html=True)

    # Suppression note (only if relevant)
    if dataset.suppression_markers:
        markers = ", ".join(f"'{m}'" for m in dataset.suppression_markers)
        st.markdown(
            f'<div class="qf-rail-note">'
            f'Suppression markers found and replaced with NULL: {_escape(markers)}'
            f'</div>',
            unsafe_allow_html=True,
        )

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
        st.dataframe(df, use_container_width=True, hide_index=True, height=min(35 * len(stats) + 38, 420))

    # ── Data Dictionary expander ─────────────────────────────────────
    with st.expander("Data dictionary", expanded=False):
        has_descriptions = any(s.description for s in stats)
        if has_descriptions:
            for s in stats:
                if s.description:
                    label = s.display_name if s.display_name and s.display_name != s.name else s.name
                    st.markdown(
                        f'<div class="qf-dict-entry">'
                        f'<div class="qf-dict-col">{_escape(label)}</div>'
                        f'<div class="qf-dict-desc">{_escape(s.description)}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
        else:
            st.markdown(
                '<div class="qf-rail-note">No data dictionary loaded for this dataset.</div>',
                unsafe_allow_html=True,
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
