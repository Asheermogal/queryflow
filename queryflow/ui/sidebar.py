"""
Sidebar UI: provider/model selector, API key entry, dataset upload, dataset switcher.

All UI here is data-driven from the registry and the database.
"""
from __future__ import annotations

import io

import pandas as pd
import streamlit as st

from ingest.database import Database, Dataset
from ingest.loader import load_file, normalize_column_name
from ingest.pdf_dictionary import parse_dictionary
from ingest.schema import scan_table
from llm import registry as llm_registry


def _table_id_from_filename(filename: str, existing: set[str]) -> str:
    base = normalize_column_name(filename.rsplit(".", 1)[0])
    cand = base
    i = 1
    while cand in existing:
        i += 1
        cand = f"{base}_{i}"
    return cand


def render_sidebar(db: Database) -> dict:
    """Render the sidebar. Returns the active LLM selection (provider_id, model_id, api_key)."""

    with st.sidebar:
        # ── Brand ────────────────────────────────────────────────────
        st.markdown(
            """
            <div style="padding: 0 0 16px 0;">
              <div style="font-family: var(--f-display); font-size: 22px; color: var(--c-ink);">◆ Settings</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── LLM section ───────────────────────────────────────────────
        st.markdown('<div class="label">Language model</div>', unsafe_allow_html=True)

        provider_opts = llm_registry.provider_options()
        provider_ids = [pid for pid, _ in provider_opts]
        provider_labels = {pid: name for pid, name in provider_opts}

        default_provider = st.session_state.get("provider_id", "openai")
        if default_provider not in provider_ids:
            default_provider = provider_ids[0]

        provider_id = st.selectbox(
            "Provider",
            options=provider_ids,
            format_func=lambda pid: provider_labels[pid],
            index=provider_ids.index(default_provider),
            key="provider_select",
        )

        models = llm_registry.models_for(provider_id)
        model_ids = [m.id for m in models]
        default_model = st.session_state.get(f"model_id__{provider_id}", model_ids[0])
        if default_model not in model_ids:
            default_model = model_ids[0]

        model_id = st.selectbox(
            "Model",
            options=model_ids,
            format_func=lambda mid: next(m.display for m in models if m.id == mid),
            index=model_ids.index(default_model),
            key="model_select",
        )

        # API key — prefer secrets-baked one; otherwise let user enter
        secrets_key = llm_registry.secrets_key_for(provider_id)
        prebaked = st.secrets.get(secrets_key, "")

        if prebaked:
            st.markdown(
                f'<div style="font-size: 11px; color: var(--c-success); '
                f'font-family: var(--f-mono); padding: 6px 0;">'
                f'● API key configured</div>',
                unsafe_allow_html=True,
            )
            api_key = prebaked
        else:
            api_key = st.text_input(
                "API key",
                type="password",
                value=st.session_state.get(f"apikey__{provider_id}", ""),
                placeholder=f"Enter your {provider_labels[provider_id]} key",
                key=f"apikey_input__{provider_id}",
            )
            st.session_state[f"apikey__{provider_id}"] = api_key

        st.session_state.provider_id = provider_id
        st.session_state[f"model_id__{provider_id}"] = model_id

        # ── Dataset section ──────────────────────────────────────────
        st.markdown('<div class="label" style="margin-top: 24px;">Datasets</div>', unsafe_allow_html=True)

        # List active datasets with select-to-make-active behavior
        existing = db.list_datasets()
        if existing:
            active_table = st.session_state.get("active_table") or existing[0].table
            active_table = st.radio(
                "Active dataset",
                options=[d.table for d in existing],
                format_func=lambda t: db.datasets[t].name,
                index=[d.table for d in existing].index(active_table)
                if active_table in [d.table for d in existing] else 0,
                key="dataset_radio",
                label_visibility="collapsed",
            )
            st.session_state.active_table = active_table

        # ── Upload ───────────────────────────────────────────────────
        st.markdown('<div class="label" style="margin-top: 18px;">Upload new</div>', unsafe_allow_html=True)
        data_file = st.file_uploader(
            "Data file (CSV / Excel)",
            type=["csv", "xlsx", "xls"],
            key="upload_data",
        )
        dict_file = st.file_uploader(
            "Data dictionary (PDF, optional)",
            type=["pdf"],
            key="upload_dict",
        )

        if data_file and st.button("Load dataset", key="btn_load", use_container_width=True):
            try:
                with st.spinner("Loading…"):
                    res = load_file(data_file.getvalue(), data_file.name)
                    existing_tables = set(db.datasets.keys())
                    table = _table_id_from_filename(data_file.name, existing_tables)

                    dataset = Dataset(
                        table=table,
                        name=data_file.name.rsplit(".", 1)[0],
                        description=f"Uploaded {data_file.name} · {len(res.df):,} rows × {len(res.df.columns)} columns",
                        row_count=len(res.df),
                        column_count=len(res.df.columns),
                        encoding=res.encoding,
                        suppression_markers=res.suppression_markers_found,
                        display_names={v: k for k, v in res.column_map.items()},
                    )

                    if dict_file:
                        normalized_cols = list(res.df.columns)
                        parsed = parse_dictionary(
                            dict_file.getvalue(),
                            normalized_cols,
                            dataset.display_names,
                        )
                        dataset.column_descriptions = parsed.column_descriptions
                        dataset.dictionary_text = parsed.full_text

                    db.add_dataset(res.df, dataset)
                    st.session_state.active_table = table
                    st.session_state.suggested_questions = None  # force refresh
                    st.session_state.current_query = None
                st.success(f"Loaded {dataset.name}")
                st.rerun()
            except Exception as e:
                st.error(f"Couldn't load: {e}")

        # ── Reset thread ─────────────────────────────────────────────
        if st.session_state.get("history"):
            st.markdown('<div class="label" style="margin-top: 18px;">Conversation</div>', unsafe_allow_html=True)
            if st.button(
                "Reset thread",
                key="btn_reset_thread",
                use_container_width=True,
                type="secondary",
            ):
                st.session_state.history = []
                st.session_state.current_query = None
                st.rerun()

    return {
        "provider_id": provider_id,
        "model_id": model_id,
        "api_key": api_key,
        "ready": bool(api_key),
    }
