"""Reusable UI atoms used across the app."""
from __future__ import annotations

import streamlit as st

from core.config import APP_NAME, APP_TAGLINE, APP_VERSION


def section_label(text: str) -> None:
    """Small uppercase section heading."""
    st.markdown(
        f'<div class="qf-section-label">{text}</div>',
        unsafe_allow_html=True,
    )


def model_badge_html(provider_display: str, model_display: str, ready: bool) -> str:
    dot_class = "dot" if ready else "dot warn"
    return (
        f'<span class="qf-model-badge">'
        f'<span class="{dot_class}"></span>'
        f'<span class="provider">{provider_display}</span>'
        f'<span class="sep">/</span>'
        f'<span>{model_display}</span>'
        f'</span>'
    )


def page_header(provider_display: str, model_display: str, ready: bool) -> None:
    badge_html = model_badge_html(provider_display, model_display, ready)
    st.markdown(
        f"""
        <div class="qf-header">
          <div class="qf-brand">
            <span class="qf-brand-mark">◆</span>
            <span class="qf-brand-name">{APP_NAME}</span>
            <span class="qf-brand-tag">{APP_TAGLINE} · v{APP_VERSION}</span>
          </div>
          <div>{badge_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def footer(text: str) -> None:
    st.markdown(f'<div class="qf-footer">{text}</div>', unsafe_allow_html=True)


def error_block(message: str) -> None:
    st.markdown(
        f"""
        <div style="
            background: #fef2f2;
            border: 1px solid var(--c-border);
            border-left: 3px solid var(--c-critical);
            padding: 12px 16px;
            border-radius: var(--r-sm);
            font-family: var(--f-mono);
            font-size: 12px;
            color: #7a1f10;
            margin: 12px 0;
        ">{message}</div>
        """,
        unsafe_allow_html=True,
    )
