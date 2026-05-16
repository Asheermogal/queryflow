"""Reusable UI atoms. Anything used in 2+ places lives here."""
from __future__ import annotations

import streamlit as st

from core.design import APP_NAME, APP_TAGLINE, APP_VERSION


def section_label(text: str, icon: str = "") -> None:
    """Small uppercase section heading."""
    prefix = f"<span>{icon}</span> " if icon else ""
    st.markdown(
        f'<div class="ap-section-label">{prefix}{text}</div>',
        unsafe_allow_html=True,
    )


def model_badge(provider_display: str, model_display: str, ready: bool) -> str:
    """Returns HTML for the active-model badge shown in the page header."""
    dot_class = "dot" if ready else "dot warn"
    return (
        f'<span class="ap-model-badge">'
        f'<span class="{dot_class}"></span>'
        f'<span class="provider">{provider_display}</span>'
        f'<span class="sep">/</span>'
        f'<span>{model_display}</span>'
        f'</span>'
    )


def page_header(provider_display: str, model_display: str, ready: bool) -> None:
    badge_html = model_badge(provider_display, model_display, ready)
    st.markdown(
        f"""
        <div class="ap-header">
          <div class="ap-brand">
            <span class="ap-brand-mark">◆</span>
            <span class="ap-brand-name">{APP_NAME}</span>
            <span class="ap-brand-tag">{APP_TAGLINE} · v{APP_VERSION}</span>
          </div>
          <div>{badge_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def stat_row(items: list[tuple[str, str]]) -> str:
    """Build HTML for a row of label/value stats."""
    cells = "".join(
        f'<div class="ap-stat"><div class="label">{lbl}</div><div class="value">{val}</div></div>'
        for lbl, val in items
    )
    return f'<div class="ap-stat-row">{cells}</div>'


def dataset_hero(name: str, description: str, stats: list[tuple[str, str]]) -> None:
    """Hero block summarizing the active dataset."""
    stat_html = stat_row(stats)
    st.markdown(
        f"""
        <div class="ap-hero">
          <h2>{name}</h2>
          <p class="desc">{description}</p>
          {stat_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def question_pill_button(text: str, key: str) -> bool:
    """Render a suggested-question pill. Returns True when clicked.

    Streamlit doesn't support fully custom-styled clickable elements, so we use
    a real button but apply CSS to mimic the pill style.
    """
    # Wrap in a unique container class so CSS can target only suggestion buttons
    st.markdown(f'<div class="ap-question-wrap" id="qw-{key}"></div>', unsafe_allow_html=True)
    return st.button(text, key=key, use_container_width=True, type="secondary")


def footer(text: str) -> None:
    st.markdown(f'<div class="ap-footer">{text}</div>', unsafe_allow_html=True)


def error_block(message: str) -> None:
    st.markdown(
        f"""
        <div class="ap-card" style="
            border-left: 3px solid var(--c-critical);
            background: #fef2f2;
            font-family: var(--f-mono);
            font-size: 12px;
            color: #7a1f10;
        ">{message}</div>
        """,
        unsafe_allow_html=True,
    )
