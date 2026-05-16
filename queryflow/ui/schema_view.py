"""Schema panel. Lists every column with its stats and dictionary description."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from ingest.database import Dataset
from ingest.schema import ColumnStats


def render_schema_panel(dataset: Dataset, stats: list[ColumnStats]) -> None:
    """Renders the schema as an expandable section under the hero."""
    label = (
        f'Schema & data dictionary · <span style="font-family: var(--f-mono);">'
        f'{dataset.table}</span>'
    )
    with st.expander(label.replace("<", "&lt;"), expanded=False):
        st.markdown(
            f'<p style="font-family: var(--f-display); font-style: italic; '
            f'font-size: 15px; color: var(--c-ink-3); margin: 4px 0 16px 0;">'
            f"{dataset.description}</p>",
            unsafe_allow_html=True,
        )

        df = pd.DataFrame(
            [
                {
                    "column": s.name,
                    "label": s.display_name if s.display_name != s.name else "",
                    "type": s.sql_type,
                    "distinct": s.n_distinct,
                    "null %": f"{s.null_pct:.1f}%",
                    "samples": ", ".join(repr(v) for v in s.samples[:3]),
                    "description": s.description or "",
                }
                for s in stats
            ]
        )
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Surface dataset-level notes
        notes = []
        if dataset.encoding and dataset.encoding != "—":
            notes.append(f"Encoding: {dataset.encoding}")
        if dataset.suppression_markers:
            notes.append(
                f"Suppression markers found and replaced with NULL: "
                + ", ".join(f"'{m}'" for m in dataset.suppression_markers)
            )
        if notes:
            st.markdown(
                '<div style="font-family: var(--f-mono); font-size: 11px; '
                'color: var(--c-ink-muted); margin-top: 8px;">'
                + " · ".join(notes)
                + "</div>",
                unsafe_allow_html=True,
            )
