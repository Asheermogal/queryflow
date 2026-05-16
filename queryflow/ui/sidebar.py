"""
Sidebar UI.

Auto-detects which LLM provider is configured in secrets.toml and locks the
session to that provider. The user can still pick a specific model within
that provider. Datasets are listed below the model section, with upload
controls at the bottom.
"""
from __future__ import annotations

import streamlit as st

from ingest.database import Database, Dataset
from ingest.loader import load_file, normalize_column_name
from ingest.pdf_dictionary import parse_dictionary
from llm import registry as llm_registry


def _table_id_from_filename(filename: str, existing: set[str]) -> str:
    base = normalize_column_name(filename.rsplit(".", 1)[0])
    cand = base
    i = 1
    while cand in existing:
        i += 1
        cand = f"{base}_{i}"
    return cand


@st.cache_data(ttl=3600, show_spinner=False)
def _cached_live_models(provider_id: str, api_key: str):
    """Cache live model list for 1 hour per (provider, key) pair."""
    return llm_registry.fetch_live_models(provider_id, api_key)


def render_sidebar(db: Database) -> dict:
    """Render the sidebar and return the active LLM selection."""

    with st.sidebar:
        # Brand block
        st.markdown(
            """
            <div class="sb-brand">
              <span class="sb-mark">◆</span>
              <span class="sb-name">QueryFlow AI</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── Provider auto-detection ──────────────────────────────────
        provider_id, api_key = llm_registry.detect_provider_from_secrets(st.secrets)

        st.markdown('<div class="sb-section-label">Language model</div>', unsafe_allow_html=True)

        if not provider_id:
            st.markdown(
                """
                <div class="sb-empty">
                  No API key configured. Add one of <code>openai_api_key</code>,
                  <code>anthropic_api_key</code>, or <code>google_api_key</code> to
                  your Streamlit secrets, then reload.
                </div>
                """,
                unsafe_allow_html=True,
            )
            return {
                "provider_id": None,
                "model_id": None,
                "api_key": None,
                "ready": False,
                "provider_display": "—",
                "model_display": "—",
            }

        provider_disp = llm_registry.provider_display(provider_id)

        # Show the active provider as a locked pill
        st.markdown(
            f"""
            <div class="sb-provider-pill">
              <span class="sb-provider-dot"></span>
              <span class="sb-provider-name">{provider_disp}</span>
              <span class="sb-provider-tag">configured</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Fetch live models for the active provider
        models = _cached_live_models(provider_id, api_key)
        model_ids = [m.id for m in models]
        id_to_display = {m.id: m.display for m in models}

        # Default to first model, or previously chosen if still valid
        default_model = st.session_state.get(f"model__{provider_id}")
        if default_model not in model_ids:
            default_model = model_ids[0] if model_ids else None

        model_id = st.selectbox(
            "Model",
            options=model_ids,
            format_func=lambda mid: id_to_display.get(mid, mid),
            index=model_ids.index(default_model) if default_model in model_ids else 0,
            key="model_select",
            label_visibility="collapsed",
        )
        st.session_state[f"model__{provider_id}"] = model_id

        # Refresh button to re-pull the live list
        if st.button("↻ Refresh model list", key="btn_refresh_models", use_container_width=True, type="secondary"):
            _cached_live_models.clear()
            st.rerun()

        # ── Dataset section ───────────────────────────────────────────
        st.markdown('<div class="sb-section-label">Datasets</div>', unsafe_allow_html=True)

        existing = db.list_datasets()
        if existing:
            active_table = st.session_state.get("active_table") or existing[0].table
            available_tables = [d.table for d in existing]
            if active_table not in available_tables:
                active_table = available_tables[0]

            active_table = st.radio(
                "Active dataset",
                options=available_tables,
                format_func=lambda t: db.datasets[t].name,
                index=available_tables.index(active_table),
                key="dataset_radio",
                label_visibility="collapsed",
            )
            st.session_state.active_table = active_table

        # ── Upload ────────────────────────────────────────────────────
        with st.expander("Upload new dataset", expanded=False):
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
                            parsed = parse_dictionary(
                                dict_file.getvalue(),
                                list(res.df.columns),
                                dataset.display_names,
                            )
                            dataset.column_descriptions = parsed.column_descriptions
                            dataset.dictionary_text = parsed.full_text

                        db.add_dataset(res.df, dataset)
                        st.session_state.active_table = table
                        st.session_state.suggested_questions = None
                        st.session_state.current_query = None
                    st.success(f"Loaded {dataset.name}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Couldn't load: {e}")

        # ── Reset thread ─────────────────────────────────────────────
        if st.session_state.get("history") or st.session_state.get("current_query"):
            if st.button("Reset conversation", key="btn_reset_thread", use_container_width=True, type="secondary"):
                st.session_state.history = []
                st.session_state.current_query = None
                st.rerun()

    return {
        "provider_id": provider_id,
        "model_id": model_id,
        "api_key": api_key,
        "ready": bool(api_key and model_id),
        "provider_display": provider_disp,
        "model_display": id_to_display.get(model_id, model_id) if model_id else "—",
    }
