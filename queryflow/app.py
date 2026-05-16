"""
Ask the Data — conversational analytics for any CSV/Excel dataset.

Streamlit entry point. Orchestrates auth, sidebar, dataset display, and the
query flow. Every visual decision flows through core.design and ui.styles;
every dataset decision flows through manifest.json and the sidebar uploader.
Nothing about the two pilot datasets is hardcoded in app logic.
"""
from __future__ import annotations

import streamlit as st

from core.auth import require_password
from core.bootstrap import build_initial_database
from core.design import APP_NAME
from ingest.schema import scan_table
from llm import registry as llm_registry
from llm.base import LLMConfig
from ui.components import dataset_hero, footer, page_header, section_label
from ui.query_flow import (
    generate_sql_for_pending,
    render_current_query,
    render_history_footer,
    render_input,
    render_starter_questions,
)
from ui.schema_view import render_schema_panel
from ui.sidebar import render_sidebar
from ui.styles import inject_global_styles


# ── Page setup ───────────────────────────────────────────────────────────
st.set_page_config(
    page_title=APP_NAME,
    page_icon="◆",
    layout="centered",
    initial_sidebar_state="expanded",
)
inject_global_styles()

# ── Auth gate ────────────────────────────────────────────────────────────
require_password()

# ── Database (preloaded from manifest, one-time per session) ─────────────
db = build_initial_database()

# ── Sidebar ──────────────────────────────────────────────────────────────
llm_selection = render_sidebar(db)

# ── Active model badge in header ─────────────────────────────────────────
provider_display = next(
    (name for pid, name in llm_registry.provider_options() if pid == llm_selection["provider_id"]),
    llm_selection["provider_id"],
)
model_display = llm_registry.model_display(
    llm_selection["provider_id"], llm_selection["model_id"]
)
page_header(provider_display, model_display, ready=llm_selection["ready"])

# ── Empty state if no dataset ────────────────────────────────────────────
if not db.list_datasets():
    st.markdown(
        """
        <div class="ap-card" style="text-align: center; padding: 48px;">
          <div style="font-family: var(--f-display); font-size: 22px; color: var(--c-ink); margin-bottom: 8px;">
            No datasets loaded yet
          </div>
          <div style="font-family: var(--f-body); font-size: 14px; color: var(--c-ink-3);">
            Upload a CSV or Excel file in the sidebar to begin.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    footer(f"{APP_NAME} · upload any tabular dataset and ask questions in plain English.")
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

# ── Hero / dataset summary ───────────────────────────────────────────────
dataset_hero(
    name=dataset.name,
    description=dataset.description,
    stats=[
        ("Rows", f"{dataset.row_count:,}"),
        ("Columns", str(dataset.column_count)),
        ("Encoding", dataset.encoding),
        (
            "Dictionary",
            "loaded" if dataset.dictionary_text else "none",
        ),
    ],
)

render_schema_panel(dataset, stats)

# ── LLM client (only constructed when key is present) ────────────────────
client = None
if llm_selection["ready"]:
    client = llm_registry.build_client(
        LLMConfig(
            provider_id=llm_selection["provider_id"],
            model_id=llm_selection["model_id"],
            api_key=llm_selection["api_key"],
        )
    )

# ── Reset starter questions if user switches datasets ────────────────────
if st.session_state.get("_last_dataset") != active_table:
    st.session_state.suggested_questions = None
    st.session_state.current_query = None
    st.session_state._last_dataset = active_table

# ── Question input (always visible if client ready) ──────────────────────
render_input(client_ready=client is not None)

# ── Starter questions (only when no current query is in progress) ────────
if client and not st.session_state.get("current_query"):
    render_starter_questions(client, dataset, stats)

# ── Handle a freshly submitted question ──────────────────────────────────
if client and st.session_state.get("pending_run_question"):
    generate_sql_for_pending(client, dataset, stats)

# ── Render the active query state ────────────────────────────────────────
if client:
    render_current_query(db, client)

# ── History footnote ─────────────────────────────────────────────────────
render_history_footer()

# ── Footer ───────────────────────────────────────────────────────────────
footer(
    f"{APP_NAME} · runs on {provider_display.upper()} {model_display.upper()} · "
    f"data stays in-session, never persisted server-side."
)
