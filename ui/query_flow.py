"""
Chat flow.

Single chat with two modes (segmented toggle above the input):

  * Explore  → text-only answer + supporting bullets, no SQL ever executed
  * Query    → LLM drafts SQL only; user must press Run to execute. After Run
               the result table, analysis card, auto chart, and a custom-chart
               builder are shown.

Suggested questions come from the cached dataset brief (one LLM call per
dataset). Clicking a suggestion sets `pending_run_question` and reuses the
same draft path.
"""
from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from core.config import (
    BRIEF_SUGGESTED_QUESTIONS,
    TOKENS_ANALYSIS,
    TOKENS_EXPLORE,
    TOKENS_SQL_GEN,
)
from core.dataset_brief import brief_as_text, get_cached_brief, get_or_build_brief
from core.prompts import (
    ANALYSIS_SYS,
    EXPLORE_SYS,
    SQL_GEN_SYS,
    analysis_user,
    explore_user,
    sql_gen_user,
)
from ingest.database import Database, Dataset
from ingest.schema import ColumnStats, schema_to_prompt_text
from llm.base import LLMClient
from ui.chart import render_chart
from ui.components import error_block, section_label
from ui.custom_chart import custom_chart_builder


# ── Session helpers ──────────────────────────────────────────────────────
def _ensure_session_keys() -> None:
    st.session_state.setdefault("history", [])
    st.session_state.setdefault("current_query", None)


# ── Suggested questions (from cached brief) ──────────────────────────────
def render_suggested_questions(
    client: LLMClient,
    dataset: Dataset,
    stats: list[ColumnStats],
) -> None:
    _ensure_session_keys()

    brief = get_or_build_brief(dataset, stats, client)
    if not brief:
        return
    suggestions = (brief.get("suggested_questions") or [])[:BRIEF_SUGGESTED_QUESTIONS]
    if not suggestions:
        return

    section_label("Suggested questions")
    for i, q in enumerate(suggestions):
        key = f"sugg_{dataset.table}_{i}"
        if st.button(q, key=key, use_container_width=True, type="secondary"):
            st.session_state.pending_run_question = {"q": q, "mode": "Query"}
            st.rerun()


# ── Input bar with mode toggle ───────────────────────────────────────────
def render_input(client_ready: bool) -> None:
    _ensure_session_keys()

    # When `key` is set, Streamlit owns the value via session state — don't
    # also pass `index=`. Initialize the session key once if missing.
    if "ask_mode" not in st.session_state:
        st.session_state["ask_mode"] = "Query"
    mode = st.radio(
        "Mode",
        options=["Explore", "Query"],
        horizontal=True,
        key="ask_mode",
        help=(
            "Explore: plain-English insights, no SQL run.  "
            "Query: SQL is drafted; you press Run to execute."
        ),
    )

    cols = st.columns([1, 0.15])
    with cols[0]:
        placeholder = (
            "Ask anything about the data…"
            if client_ready
            else "Configure your API key in secrets to begin."
        )
        question = st.text_input(
            "Ask anything",
            placeholder=placeholder,
            disabled=not client_ready,
            label_visibility="collapsed",
            key="question_input",
        )
    with cols[1]:
        send_label = "Explore" if mode == "Explore" else "Draft SQL"
        send_disabled = (
            not client_ready
            or not (question or "").strip()
            or bool(st.session_state.get("pending_run_question"))
        )
        send = st.button(
            send_label,
            use_container_width=True,
            disabled=send_disabled,
            type="primary",
        )

    if send and question and question.strip():
        st.session_state.pending_run_question = {"q": question.strip(), "mode": mode}
        st.rerun()


# ── Draft generator (NO execution) ───────────────────────────────────────
def generate_draft_for_pending(
    client: LLMClient,
    dataset: Dataset,
    stats: list[ColumnStats],
) -> None:
    payload = st.session_state.pop("pending_run_question", None)
    if not payload:
        return
    if isinstance(payload, str):
        payload = {"q": payload, "mode": "Query"}

    q = payload["q"]
    mode = payload.get("mode", "Query")

    schema_text = schema_to_prompt_text(dataset.table, dataset.description, stats)
    brief_text = brief_as_text(get_cached_brief(dataset.table))

    if mode == "Explore":
        try:
            with st.spinner("Thinking…"):
                res = client.complete_json(
                    EXPLORE_SYS,
                    explore_user(q, dataset.name, schema_text, brief_text),
                    max_tokens=TOKENS_EXPLORE,
                )
            st.session_state.current_query = {
                "mode": "Explore",
                "question": q,
                "answer": res.get("answer", ""),
                "bullets": res.get("bullets", []) or [],
                "switch_to_query": bool(res.get("switch_to_query")),
                "error": None,
            }
        except Exception as e:
            st.session_state.current_query = {
                "mode": "Explore",
                "question": q,
                "answer": "",
                "bullets": [],
                "switch_to_query": False,
                "error": f"Couldn't explore: {e}",
            }
        return

    # Query mode → DRAFT SQL ONLY. Do not execute.
    history_for_llm = [
        {"question": h["question"], "sql": h["sql"]}
        for h in st.session_state.history
    ]
    try:
        with st.spinner("Drafting SQL…"):
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
                max_tokens=TOKENS_SQL_GEN,
            )
        sql = (res.get("sql") or "").strip()
        reasoning = res.get("reasoning", "")
        st.session_state.current_query = {
            "mode": "Query",
            "question": q,
            "sql": sql,
            "reasoning": reasoning,
            "results": None,
            "analysis": None,
            "error": None,
        }
    except Exception as e:
        st.session_state.current_query = {
            "mode": "Query",
            "question": q,
            "sql": "",
            "reasoning": "",
            "results": None,
            "analysis": None,
            "error": f"Couldn't draft SQL: {e}",
        }


# ── Render the current chat turn ─────────────────────────────────────────
def render_current_query(db: Database, client: LLMClient | None) -> None:
    state = st.session_state.current_query
    if not state:
        return

    mode = state.get("mode", "Query")

    st.markdown(
        f'<div class="qf-question">{state["question"]}</div>',
        unsafe_allow_html=True,
    )

    if state.get("error"):
        error_block(state["error"])

    if mode == "Explore":
        _render_explore_card(state)
        if st.button("Ask another", key="explore_new", type="secondary"):
            st.session_state.current_query = None
            st.rerun()
        return

    # ── Query mode ─────────────────────────────────────────────────────
    if not state.get("sql"):
        return

    st.markdown(
        '<div class="qf-sql-label">Generated SQL · review and edit, then Run</div>',
        unsafe_allow_html=True,
    )
    sql_edit_key = f"sql_edit_{hash(state['question'])}"
    new_sql = st.text_area(
        "SQL",
        value=state.get("sql", ""),
        height=140,
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

    if not state.get("results"):
        st.caption("SQL is drafted but not executed. Press **Run query** to see results.")

    b1, b2, _ = st.columns([0.2, 0.25, 1])
    run_disabled = not (new_sql or "").strip()
    run = b1.button(
        "Run query",
        use_container_width=True,
        key=f"btn_run_{sql_edit_key}",
        type="primary",
        disabled=run_disabled,
    )
    new_q = b2.button(
        "Ask another",
        use_container_width=True,
        key=f"btn_new_{sql_edit_key}",
        type="secondary",
    )

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
        _execute_and_analyze(state, db, client)
        st.rerun()

    _render_query_results(state)


def _execute_and_analyze(state: dict[str, Any], db: Database, client: LLMClient | None) -> None:
    state["error"] = None
    state["analysis"] = None
    sql = (state.get("sql") or "").strip()
    if not sql:
        state["error"] = "Enter some SQL before running."
        return
    try:
        with st.spinner("Running query…"):
            columns, rows = db.query(sql)
            state["results"] = {"columns": columns, "rows": rows}
    except Exception as e:
        state["error"] = f"SQL error: {e}"
        state["results"] = None
        return

    if state["results"]["rows"] and client is not None:
        try:
            with st.spinner("Reading the results…"):
                state["analysis"] = client.complete_json(
                    ANALYSIS_SYS,
                    analysis_user(
                        state["question"],
                        state["sql"],
                        state["results"]["columns"],
                        state["results"]["rows"],
                    ),
                    max_tokens=TOKENS_ANALYSIS,
                )
        except Exception as e:
            state["analysis"] = {"summary": "", "key_findings": [], "caveats": [f"Analysis failed: {e}"]}


def _render_query_results(state: dict[str, Any]) -> None:
    results = state.get("results")
    if results is None:
        return
    cols_, rows_ = results["columns"], results["rows"]
    section_label(f"Results · {len(rows_)} row{'s' if len(rows_) != 1 else ''}")
    if rows_:
        df = pd.DataFrame(rows_, columns=cols_)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No rows returned for this query.")
        return

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
        if spec:
            render_chart(spec, df)

    # Custom chart builder, operating on the result df
    with st.expander("+ Custom chart from these results", expanded=False):
        custom_chart_builder(
            key_prefix=f"cc_inline_{hash(state['question'])}",
            result_df=df,
        )


def _render_explore_card(state: dict[str, Any]) -> None:
    findings_html = "".join(
        f'<div class="finding"><span class="num">{i:02d}</span><span>{b}</span></div>'
        for i, b in enumerate(state.get("bullets", []), start=1)
    )
    extra = ""
    if state.get("switch_to_query"):
        extra = (
            '<div class="caveats"><strong>Tip —</strong> '
            'For a precise number, switch to <em>Query</em> mode and re-ask.</div>'
        )
    st.markdown(
        f'<div class="qf-analysis">'
        f'<div class="qf-analysis-headline">{state.get("answer", "")}</div>'
        f'{findings_html}'
        f'{extra}'
        f'</div>',
        unsafe_allow_html=True,
    )
