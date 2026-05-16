"""
The conversational query flow:

  question input
    → generated SQL (editable)
    → run → results table
    → AI analysis + chart
    → follow-up

All state lives in st.session_state.current_query and st.session_state.history.
"""
from __future__ import annotations

import json
import time
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


def _kickoff_question(text: str) -> None:
    st.session_state.pending_question = text


def render_starter_questions(
    client: LLMClient,
    dataset: Dataset,
    stats: list[ColumnStats],
) -> None:
    _ensure_session_keys()

    if st.session_state.suggested_questions is None:
        schema_text = schema_to_prompt_text(dataset.table, dataset.description, stats)
        try:
            with st.spinner("Generating starter questions…"):
                res = client.complete_json(
                    SAMPLE_QUESTIONS_SYS,
                    sample_questions_user(
                        dataset.name, schema_text, dataset.dictionary_text
                    ),
                    max_tokens=600,
                )
                st.session_state.suggested_questions = res.get("questions", [])
        except Exception as e:
            st.session_state.suggested_questions = []
            st.warning(f"Couldn't generate starter questions: {e}")

    questions = st.session_state.suggested_questions or []
    if not questions:
        return

    section_label("Suggested starter questions")

    # Render as a stack of pill-styled buttons
    for i, q in enumerate(questions):
        st.markdown(
            f"""
            <div class="ap-question-pill" onclick="window.parent.document.querySelector('[data-testid=stTextInput] input').value='{q.replace("'", "\\'")}';">
              {q}
            </div>
            """,
            unsafe_allow_html=True,
        )
        # Hidden button to make the pill actually trigger the question
        col = st.columns([0.0001, 1])[1]
        if col.button(q, key=f"q_starter_{i}", use_container_width=True, type="secondary"):
            _kickoff_question(q)
            st.rerun()


def render_input(client_ready: bool) -> None:
    """The big question input bar."""
    pending = st.session_state.pop("pending_question", "")
    cols = st.columns([1, 0.18])
    with cols[0]:
        question = st.text_input(
            "Ask the data",
            value=pending,
            placeholder=(
                "Ask anything about the data…"
                if client_ready
                else "Configure your API key in the sidebar to begin."
            ),
            disabled=not client_ready,
            label_visibility="collapsed",
            key="question_input",
        )
    with cols[1]:
        go = st.button("Ask", use_container_width=True, disabled=not client_ready)

    if go and question.strip():
        st.session_state.pending_run_question = question.strip()


def generate_sql_for_pending(
    client: LLMClient,
    dataset: Dataset,
    stats: list[ColumnStats],
) -> None:
    """If a question was just submitted, generate SQL and store as current_query."""
    q = st.session_state.pop("pending_run_question", None)
    if not q:
        return

    schema_text = schema_to_prompt_text(dataset.table, dataset.description, stats)
    history_for_llm = [
        {"question": h["question"], "sql": h["sql"]}
        for h in st.session_state.history
    ]
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
        st.session_state.current_query = {
            "question": q,
            "sql": res.get("sql", "").strip(),
            "reasoning": res.get("reasoning", ""),
            "results": None,
            "analysis": None,
            "error": None,
        }
    except Exception as e:
        st.session_state.current_query = {
            "question": q,
            "sql": "",
            "reasoning": "",
            "results": None,
            "analysis": None,
            "error": f"Couldn't generate SQL: {e}",
        }


def render_current_query(db: Database, client: LLMClient) -> None:
    """Show whatever is in st.session_state.current_query — SQL editor, results, analysis."""
    state = st.session_state.current_query
    if not state:
        return

    st.markdown(
        f'<div style="margin: {20}px 0 {12}px 0; '
        'font-family: var(--f-display); font-size: 22px; color: var(--c-ink);">'
        f"{state['question']}"
        "</div>",
        unsafe_allow_html=True,
    )

    if state.get("error") and not state.get("sql"):
        error_block(state["error"])
        return

    # SQL editor (dark frame)
    st.markdown('<div class="ap-sql-frame">', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="ap-sql-header">
          <span class="ap-sql-label">▸ SQL · editable</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="sql-editor">', unsafe_allow_html=True)
    sql = st.text_area(
        "SQL",
        value=state["sql"],
        height=130,
        label_visibility="collapsed",
        key=f"sql_edit_{id(state)}",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if state.get("reasoning"):
        st.markdown(
            f"""
            <div class="ap-sql-reasoning">
              <span class="tag">Approach</span>{state['reasoning']}
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

    # Update SQL in state if user edited
    state["sql"] = sql

    # Action row
    cols = st.columns([0.18, 0.18, 1])
    run = cols[0].button("Run query", use_container_width=True)
    new_q = cols[1].button("New question", use_container_width=True, type="secondary")

    if new_q:
        # Roll current into history if completed
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
                state["analysis"] = None
                state["error"] = None
        except Exception as e:
            state["error"] = f"SQL error: {e}"
            state["results"] = None

    # Error
    if state.get("error"):
        error_block(state["error"])

    # Results
    results = state.get("results")
    if results is not None:
        cols_, rows_ = results["columns"], results["rows"]
        section_label(
            f"Results · {len(rows_)} row{'s' if len(rows_) != 1 else ''}"
        )
        if rows_:
            df = pd.DataFrame(rows_, columns=cols_)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.markdown(
                '<div class="ap-card" style="font-family: var(--f-display); '
                'font-style: italic; color: var(--c-ink-muted); text-align: center;">'
                "No rows returned."
                "</div>",
                unsafe_allow_html=True,
            )

        # Analysis (auto-triggered after results)
        if rows_ and not state.get("analysis"):
            try:
                with st.spinner("Reading the results…"):
                    analysis = client.complete_json(
                        ANALYSIS_SYS,
                        analysis_user(state["question"], state["sql"], cols_, rows_),
                        max_tokens=1200,
                    )
                state["analysis"] = analysis
            except Exception as e:
                state["analysis"] = None
                st.warning(f"Analysis failed: {e}")

    # Analysis card + chart
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
                f'<div class="caveats"><strong>Caveats —</strong>{caveats_text}</div>'
            )

        st.markdown(
            f"""
            <div class="ap-analysis">
              <div class="headline">{analysis.get('summary', '')}</div>
              {findings_html}
              {caveats_html}
            </div>
            """,
            unsafe_allow_html=True,
        )

        spec = analysis.get("chart_spec")
        if spec and state.get("results"):
            cols_, rows_ = state["results"]["columns"], state["results"]["rows"]
            df = pd.DataFrame(rows_, columns=cols_)
            render_chart(spec, df)


def render_history_footer() -> None:
    h = st.session_state.get("history", [])
    if not h:
        return
    st.markdown(
        f'<div style="margin-top: 32px; padding-top: 16px; '
        f'border-top: 1px dashed var(--c-border-dashed); '
        f'font-family: var(--f-mono); font-size: 11px; color: var(--c-ink-muted);">'
        f"{len(h)} prior turn{'s' if len(h) != 1 else ''} in this thread — the model uses them as context for follow-ups."
        f"</div>",
        unsafe_allow_html=True,
    )
