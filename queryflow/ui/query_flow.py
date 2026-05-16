"""
The conversational query flow:

  question (typed or clicked from starter) → SQL auto-generated and auto-run
    → results table → AI analysis card → chart
    → user can edit SQL and Run Query again to re-execute
    → user can ask a follow-up at any time

All state lives in st.session_state.current_query and st.session_state.history.
"""
from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from core.prompts import (
    ANALYSIS_SYS,
    SAMPLE_QUESTIONS_SYS,
    SQL_GEN_SYS,
    analysis_user,
    sample_questions_user,
    sql_gen_user,
)
from ingest.database import Database, Dataset
from ingest.schema import ColumnStats, schema_to_prompt_text
from llm.base import LLMClient
from ui.chart import render_chart
from ui.components import error_block, section_label


def _ensure_session_keys() -> None:
    st.session_state.setdefault("history", [])
    st.session_state.setdefault("current_query", None)
    st.session_state.setdefault("suggested_questions", None)


# ── Starter questions ────────────────────────────────────────────────────
def render_starter_questions(
    client: LLMClient,
    dataset: Dataset,
    stats: list[ColumnStats],
) -> None:
    """Render suggested questions as clickable cards. Clicking auto-runs the flow."""
    _ensure_session_keys()

    if st.session_state.suggested_questions is None:
        schema_text = schema_to_prompt_text(dataset.table, dataset.description, stats)
        try:
            with st.spinner("Preparing suggested questions…"):
                res = client.complete_json(
                    SAMPLE_QUESTIONS_SYS,
                    sample_questions_user(
                        dataset.name, schema_text, dataset.dictionary_text
                    ),
                    max_tokens=600,
                )
                # Dedupe while preserving order
                seen: set[str] = set()
                qs: list[str] = []
                for q in res.get("questions", []):
                    if q and q not in seen:
                        seen.add(q)
                        qs.append(q)
                st.session_state.suggested_questions = qs[:5]
        except Exception as e:
            st.session_state.suggested_questions = []
            st.warning(f"Couldn't generate starter questions: {e}")

    questions = st.session_state.suggested_questions or []
    if not questions:
        return

    section_label("Suggested questions")
    # Use the dataset-aware key so questions don't conflict when switching datasets
    for i, q in enumerate(questions):
        key = f"starter_{dataset.table}_{i}"
        if st.button(q, key=key, use_container_width=True, type="secondary"):
            st.session_state.pending_run_question = q
            st.rerun()


# ── Input bar ────────────────────────────────────────────────────────────
def render_input(client_ready: bool) -> None:
    """The Ask anything input + send button."""
    cols = st.columns([1, 0.15])
    with cols[0]:
        question = st.text_input(
            "Ask anything about the data",
            placeholder=(
                "Ask anything about the data…"
                if client_ready
                else "Configure your API key in secrets to begin."
            ),
            disabled=not client_ready,
            label_visibility="collapsed",
            key="question_input",
        )
    with cols[1]:
        send = st.button("Ask", use_container_width=True, disabled=not client_ready, type="primary")

    if send and question.strip():
        st.session_state.pending_run_question = question.strip()
        st.rerun()


# ── Auto-execute pending question ────────────────────────────────────────
def process_pending_question(
    client: LLMClient,
    dataset: Dataset,
    stats: list[ColumnStats],
    db: Database,
) -> None:
    """If a question is pending (from starter click or input), run the full pipeline:
       generate SQL → execute → store results → trigger analysis.
    """
    q = st.session_state.pop("pending_run_question", None)
    if not q:
        return

    schema_text = schema_to_prompt_text(dataset.table, dataset.description, stats)
    history_for_llm = [
        {"question": h["question"], "sql": h["sql"]}
        for h in st.session_state.history
    ]

    # 1. Generate SQL
    try:
        with st.spinner("Translating to SQL…"):
            res = client.complete_json(
                SQL_GEN_SYS,
                sql_gen_user(
                    q,
                    dataset.table,
                    schema_text,
                    dataset.dictionary_text,
                    history_for_llm,
                    dataset.suppression_markers,
                ),
                max_tokens=800,
            )
        sql = res.get("sql", "").strip()
        reasoning = res.get("reasoning", "")
    except Exception as e:
        st.session_state.current_query = {
            "question": q,
            "sql": "",
            "reasoning": "",
            "results": None,
            "analysis": None,
            "error": f"Couldn't generate SQL: {e}",
        }
        return

    state = {
        "question": q,
        "sql": sql,
        "reasoning": reasoning,
        "results": None,
        "analysis": None,
        "error": None,
    }

    # 2. Auto-execute the SQL
    if sql:
        try:
            with st.spinner("Running query…"):
                columns, rows = db.query(sql)
                state["results"] = {"columns": columns, "rows": rows}
        except Exception as e:
            state["error"] = f"SQL error: {e}"

    # 3. Auto-generate analysis if we have rows
    if state["results"] and state["results"]["rows"]:
        try:
            with st.spinner("Reading the results…"):
                analysis = client.complete_json(
                    ANALYSIS_SYS,
                    analysis_user(
                        state["question"],
                        state["sql"],
                        state["results"]["columns"],
                        state["results"]["rows"],
                    ),
                    max_tokens=1200,
                )
            state["analysis"] = analysis
        except Exception as e:
            state["analysis"] = None
            state["analysis_error"] = str(e)

    st.session_state.current_query = state


# ── Render current query ─────────────────────────────────────────────────
def render_current_query(db: Database, client: LLMClient) -> None:
    state = st.session_state.current_query
    if not state:
        return

    # Question header
    st.markdown(
        f'<div class="qf-question">{state["question"]}</div>',
        unsafe_allow_html=True,
    )

    # SQL editor (always shown if we have an SQL string)
    if state.get("sql") or state.get("error"):
        st.markdown('<div class="qf-sql-label">Generated SQL · editable</div>', unsafe_allow_html=True)
        sql_edit_key = f"sql_edit_{hash(state['question'])}"
        new_sql = st.text_area(
            "SQL",
            value=state.get("sql", ""),
            height=130,
            label_visibility="collapsed",
            key=sql_edit_key,
        )
        state["sql"] = new_sql

        if state.get("reasoning"):
            st.markdown(
                f'<div class="qf-sql-reasoning">'
                f'<span class="tag">Approach</span>'
                f'{state["reasoning"]}'
                f'</div>',
                unsafe_allow_html=True,
            )

        # Run / Reset buttons
        b1, b2, _ = st.columns([0.2, 0.25, 1])
        run = b1.button("Run query", use_container_width=True, key=f"btn_run_{sql_edit_key}", type="primary")
        new_q = b2.button("Ask another", use_container_width=True, key=f"btn_new_{sql_edit_key}", type="secondary")

        if new_q:
            if state.get("analysis"):
                st.session_state.history.append({
                    "question": state["question"],
                    "sql": state["sql"],
                    "summary": state["analysis"].get("summary", ""),
                })
            st.session_state.current_query = None
            st.rerun()

        if run:
            try:
                with st.spinner("Running query…"):
                    columns, rows = db.query(state["sql"])
                    state["results"] = {"columns": columns, "rows": rows}
                    state["analysis"] = None   # force re-analysis
                    state["error"] = None
                # Re-run analysis
                if rows:
                    with st.spinner("Reading the results…"):
                        analysis = client.complete_json(
                            ANALYSIS_SYS,
                            analysis_user(state["question"], state["sql"], columns, rows),
                            max_tokens=1200,
                        )
                    state["analysis"] = analysis
                st.rerun()
            except Exception as e:
                state["error"] = f"SQL error: {e}"

    if state.get("error"):
        error_block(state["error"])

    # Results
    results = state.get("results")
    if results is not None:
        cols_, rows_ = results["columns"], results["rows"]
        section_label(f"Results · {len(rows_)} row{'s' if len(rows_) != 1 else ''}")
        if rows_:
            df = pd.DataFrame(rows_, columns=cols_)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No rows returned for this query.")

    # Analysis card
    analysis = state.get("analysis")
    if analysis:
        section_label("Analysis")
        findings_html = ""
        for i, f in enumerate(analysis.get("key_findings", []), start=1):
            findings_html += (
                f'<div class="finding">'
                f'<span class="num">{i:02d}</span>'
                f'<span>{f}</span>'
                f'</div>'
            )

        caveats_html = ""
        if analysis.get("caveats"):
            caveats_text = " ".join(analysis["caveats"])
            caveats_html = (
                f'<div class="caveats"><strong>Caveats —</strong> {caveats_text}</div>'
            )

        st.markdown(
            f'<div class="qf-analysis">'
            f'<div class="qf-analysis-headline">{analysis.get("summary", "")}</div>'
            f'{findings_html}'
            f'{caveats_html}'
            f'</div>',
            unsafe_allow_html=True,
        )

        spec = analysis.get("chart_spec")
        if spec and state.get("results"):
            df = pd.DataFrame(state["results"]["rows"], columns=state["results"]["columns"])
            render_chart(spec, df)
