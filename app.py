"""
QueryFlow AI — conversational analytics for any CSV/Excel dataset.

Layout:
  ┌──────────┬───────────────────────────────────────────────────────┐
  │          │  header (brand · model badge)                          │
  │          ├──────────────────────────────┬─────────────────────────┤
  │ sidebar  │  70%  conversation           │  30%  dataset overview   │
  │ settings │  - starter questions          │  - name + description    │
  │ + data   │  - ask anything input         │  - stat tiles            │
  │  picker  │  - SQL → results → analysis   │  - schema (expander)     │
  │          │  - chart                      │  - dictionary (expander) │
  └──────────┴───────────────────────────────┴─────────────────────────┘
"""
from __future__ import annotations

import streamlit as st

from core.auth import require_password
from core.bootstrap import build_initial_database
from core.design import APP_NAME
from ingest.schema import scan_table
from llm.base import LLMConfig
from llm import registry as llm_registry
from ui.components import footer, page_header
from ui.dataset_panel import render_dataset_overview
from ui.query_flow import (
    process_pending_question,
    render_current_query,
    render_input,
    render_starter_questions,
)
from ui.sidebar import render_sidebar
from ui.sidebar_toggle import inject_sidebar_toggle
from ui.styles import inject_global_styles


# ── Page setup ───────────────────────────────────────────────────────────
st.set_page_config(
    page_title=APP_NAME,
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_global_styles()
inject_sidebar_toggle()

# ── Auth gate ────────────────────────────────────────────────────────────
require_password()

# ── Database ─────────────────────────────────────────────────────────────
db = build_initial_database()

# ── Sidebar (also returns active LLM selection) ──────────────────────────
llm_selection = render_sidebar(db)

# ── Header ───────────────────────────────────────────────────────────────
page_header(
    provider_display=llm_selection["provider_display"],
    model_display=llm_selection["model_display"],
    ready=llm_selection["ready"],
)

# ── Empty state ──────────────────────────────────────────────────────────
if not db.list_datasets():
    st.markdown(
        """
        <div style="text-align: center; padding: 80px 24px;
                    background: var(--c-surface); border: 1px solid var(--c-border);
                    border-radius: var(--r-sm); max-width: 560px; margin: 60px auto;">
          <div style="font-family: var(--f-display); font-size: 22px;
                      color: var(--c-ink); margin-bottom: 8px;">
            No datasets loaded yet
          </div>
          <div style="font-family: var(--f-body); font-size: 14px;
                      color: var(--c-ink-3); line-height: 1.5;">
            Upload a CSV or Excel file from the sidebar to begin.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    footer(f"{APP_NAME} · upload a dataset to start asking questions.")
    st.stop()

# ── Active dataset ───────────────────────────────────────────────────────
active_table = st.session_state.get("active_table") or db.list_datasets()[0].table
if active_table not in db.datasets:
    active_table = db.list_datasets()[0].table
    st.session_state.active_table = active_table

dataset = db.datasets[active_table]
stats = scan_table(
    db.conn,
    active_table,
    display_names=dataset.display_names,
    descriptions=dataset.column_descriptions,
)

# Reset session state when dataset changes
if st.session_state.get("_last_dataset") != active_table:
    st.session_state.suggested_questions = None
    st.session_state.current_query = None
    st.session_state._last_dataset = active_table

# ── LLM client ───────────────────────────────────────────────────────────
client = None
if llm_selection["ready"]:
    client = llm_registry.build_client(
        LLMConfig(
            provider_id=llm_selection["provider_id"],
            model_id=llm_selection["model_id"],
            api_key=llm_selection["api_key"],
        )
    )

# ── 70/30 split: conversation (left) + dataset overview (right) ──────────
left, right = st.columns([0.7, 0.3], gap="large")

with left:
    # 1. Input bar at top so it's always reachable
    render_input(client_ready=client is not None)

    # 2. Process any pending question (auto-runs SQL + analysis)
    if client and st.session_state.get("pending_run_question"):
        process_pending_question(client, dataset, stats, db)

    # 3. Show the current query state (SQL editor → results → analysis)
    if client and st.session_state.get("current_query"):
        render_current_query(db, client)

    # 4. Show starter questions only when there's nothing active
    if client and not st.session_state.get("current_query"):
        render_starter_questions(client, dataset, stats)

with right:
    render_dataset_overview(dataset, stats)

# ── Footer ───────────────────────────────────────────────────────────────
footer(
    f"{APP_NAME} · {llm_selection['provider_display']} {llm_selection['model_display']} · "
    f"data stays in-session, never persisted server-side."
)
