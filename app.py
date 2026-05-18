"""
Data Explorer — exploratory analytics for any CSV/Excel dataset.

Two views (switched via st.session_state.view):
  - "chat": 70/30 split with conversation + dataset overview panel
  - "dashboard": full-width LLM-generated dashboard + custom chart builder
"""
from __future__ import annotations

import streamlit as st

from core.auth import require_password
from core.bootstrap import build_initial_database
from core.config import APP_NAME
from ingest.schema import scan_table
from llm.base import LLMConfig
from llm import registry as llm_registry
from ui.components import footer, page_header
from ui.dashboard import render_dashboard
from ui.dataset_panel import render_dataset_overview
from ui.query_flow import (
    generate_draft_for_pending,
    render_current_query,
    render_input,
    render_suggested_questions,
)
from ui.sidebar import render_sidebar
from ui.styles import inject_global_styles


st.set_page_config(
    page_title=APP_NAME,
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_global_styles()

require_password()

try:
    db = build_initial_database()

    llm_selection = render_sidebar(db)

    page_header(
        provider_display=llm_selection["provider_display"],
        model_display=llm_selection["model_display"],
        ready=llm_selection["ready"],
    )

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

    if st.session_state.get("_last_dataset") != active_table:
        st.session_state.current_query = None
        st.session_state._last_dataset = active_table
        st.session_state.view = "chat"

    client = None
    if llm_selection["ready"]:
        client = llm_registry.build_client(
            LLMConfig(
                provider_id=llm_selection["provider_id"],
                model_id=llm_selection["model_id"],
                api_key=llm_selection["api_key"],
            )
        )

    view = st.session_state.get("view", "chat")

    if view == "dashboard":
        render_dashboard(db, dataset, stats, client)
    else:
        left, right = st.columns([0.7, 0.3], gap="large")

        with left:
            render_input(client_ready=client is not None)

            if client and st.session_state.get("pending_run_question"):
                generate_draft_for_pending(client, dataset, stats)

            if st.session_state.get("current_query"):
                render_current_query(db, client)

            if client and not st.session_state.get("current_query"):
                render_suggested_questions(client, dataset, stats)

        with right:
            render_dataset_overview(dataset, stats, client)

    footer(
        f"{APP_NAME} · {llm_selection['provider_display']} {llm_selection['model_display']} · "
        f"data stays in-session, never persisted server-side."
    )
except st.runtime.scriptrunner.StopException:
    # `st.stop()` raises this internally — let it propagate, NOT an error.
    raise
except Exception as _app_err:
    st.error(
        "Something went wrong rendering this page. "
        "Try clicking **Reset conversation** in the sidebar, or reload the page."
    )
    with st.expander("Technical details (for support)"):
        st.code(repr(_app_err))
    if st.button("Reset session", type="primary"):
        for _k in list(st.session_state.keys()):
            del st.session_state[_k]
        st.rerun()
