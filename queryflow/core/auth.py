"""Password gate. App halts here until a valid password is entered."""
from __future__ import annotations

import hmac

import streamlit as st

from core.design import APP_NAME, APP_TAGLINE


def _password_correct(entered: str) -> bool:
    expected = st.secrets.get("app_password", "")
    if not expected:
        # No password configured — let everyone in (dev mode).
        return True
    return hmac.compare_digest(entered, expected)


def require_password() -> None:
    """Render the password screen if not yet authenticated."""
    if st.session_state.get("authed"):
        return

    if "app_password" not in st.secrets:
        # Dev mode: no password configured.
        st.session_state.authed = True
        return

    st.markdown(
        f"""
        <div class="auth-screen">
          <div class="auth-card">
            <div class="auth-brand">
              <span class="auth-mark">◆</span>
              <span class="auth-name">{APP_NAME}</span>
            </div>
            <p class="auth-tag">{APP_TAGLINE}</p>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    entered = st.text_input(
        "Password",
        type="password",
        label_visibility="collapsed",
        placeholder="Enter access password",
        key="_password_input",
    )

    if entered:
        if _password_correct(entered):
            st.session_state.authed = True
            st.rerun()
        else:
            st.error("Incorrect password.")

    st.stop()
