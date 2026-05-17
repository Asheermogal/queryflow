"""
Dataset brief generator.

One LLM call per dataset, cached for the life of the session. Produces:
  - a 1-sentence headline
  - 4-6 bullet observations
  - 3-5 key columns
  - 5 suggested starter questions

Consumed by the right-rail dataset panel and by the chat's suggested-questions
section.
"""
from __future__ import annotations

from typing import Any

import streamlit as st

from core.config import TOKENS_BRIEF
from core.prompts import DATASET_BRIEF_SYS, dataset_brief_user
from ingest.database import Dataset
from ingest.schema import ColumnStats, schema_to_prompt_text
from llm.base import LLMClient


def _brief_key(table: str) -> str:
    return f"_dataset_brief__{table}"


def get_cached_brief(table: str) -> dict[str, Any] | None:
    return st.session_state.get(_brief_key(table))


def clear_brief(table: str) -> None:
    st.session_state.pop(_brief_key(table), None)


def get_or_build_brief(
    dataset: Dataset,
    stats: list[ColumnStats],
    client: LLMClient | None,
) -> dict[str, Any] | None:
    """Return the cached brief for this dataset, generating it if needed.

    Returns None if no LLM client is available or if generation fails.
    """
    key = _brief_key(dataset.table)
    cached = st.session_state.get(key)
    if cached:
        return cached

    if client is None:
        return None

    schema_text = schema_to_prompt_text(dataset.table, dataset.description, stats)
    try:
        with st.spinner("Reading the dataset…"):
            brief = client.complete_json(
                DATASET_BRIEF_SYS,
                dataset_brief_user(dataset.name, schema_text),
                max_tokens=TOKENS_BRIEF,
            )
        # Defensive shape coercion
        brief.setdefault("headline", dataset.name)
        brief.setdefault("bullets", [])
        brief.setdefault("key_columns", [])
        brief.setdefault("suggested_questions", [])
        st.session_state[key] = brief
        return brief
    except Exception as e:
        st.session_state[key] = {
            "headline": dataset.name,
            "bullets": [],
            "key_columns": [],
            "suggested_questions": [],
            "_error": str(e),
        }
        return st.session_state[key]


def brief_as_text(brief: dict[str, Any] | None) -> str | None:
    """Serialize a brief for inclusion in other prompts (dashboard, explore)."""
    if not brief:
        return None
    parts = []
    if brief.get("headline"):
        parts.append(brief["headline"])
    bullets = brief.get("bullets") or []
    if bullets:
        parts.append("\n".join(f"- {b}" for b in bullets))
    return "\n".join(parts) if parts else None
