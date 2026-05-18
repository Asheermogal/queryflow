"""
Central configuration for Data Explorer.

Single source of truth for app identity, upload limits, default model
preferences, and dashboard sizing. Change values here to re-tune the app
without touching feature code.
"""
from __future__ import annotations

# ── App identity ─────────────────────────────────────────────────────────
APP_NAME = "Data Explorer"
APP_TAGLINE = "Exploratory analytics for any dataset"
APP_VERSION = "0.3"

# ── Upload limits ────────────────────────────────────────────────────────
ALLOWED_UPLOAD_EXTS: tuple[str, ...] = ("csv", "xlsx")
MAX_UPLOAD_MB: int = 200
SOFT_WARN_UPLOAD_MB: int = 50

# ── LLM defaults ─────────────────────────────────────────────────────────
# Best available chat model per provider. Auto-selected in the sidebar
# when the live model list contains it; otherwise we fall back to the
# first listed model. Users can still override manually.
PROVIDER_DEFAULT_MODEL: dict[str, str] = {
    "anthropic": "claude-opus-4-7",
    "openai":    "gpt-5.5",
    "google":    "gemini-3.1-pro-preview",
}

# ── Dataset brief (cached, one LLM call per dataset) ─────────────────────
BRIEF_BULLET_COUNT: int = 6
BRIEF_SUGGESTED_QUESTIONS: int = 5
BRIEF_KEY_COLUMN_COUNT: int = 5

# ── Dashboard (cached, one LLM call per dataset) ─────────────────────────
DASHBOARD_CHART_COUNT: int = 6
DASHBOARD_INSIGHT_COUNT: int = 6
DASHBOARD_DEFAULT_ROW_LIMIT: int = 15

# ── LLM token budgets ────────────────────────────────────────────────────
TOKENS_BRIEF: int = 1500
TOKENS_DASHBOARD: int = 2000
TOKENS_SQL_GEN: int = 1000
TOKENS_ANALYSIS: int = 1500
TOKENS_EXPLORE: int = 1500
