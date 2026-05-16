"""
Global CSS injection. Overrides Streamlit defaults to enforce the design system
from core/design.py. Pulls fonts from Google Fonts.

Every visual decision routes through here so the look is consistent and tunable.
"""
from __future__ import annotations

import streamlit as st

from core.design import Color, Font, Radius, Size, Space


def inject_global_styles() -> None:
    css = f"""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,300..700;1,6..72,400&family=Geist:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">

    <style>
      :root {{
        --c-bg: {Color.bg};
        --c-surface: {Color.surface};
        --c-surface-2: {Color.surface_2};
        --c-surface-dark: {Color.surface_dark};
        --c-border: {Color.border};
        --c-border-strong: {Color.border_strong};
        --c-border-dashed: {Color.border_dashed};
        --c-ink: {Color.ink};
        --c-ink-2: {Color.ink_2};
        --c-ink-3: {Color.ink_3};
        --c-ink-muted: {Color.ink_muted};
        --c-ink-on-dark: {Color.ink_on_dark};
        --c-ink-on-dark-muted: {Color.ink_on_dark_muted};
        --c-accent: {Color.accent};
        --c-accent-hover: {Color.accent_hover};
        --c-accent-soft: {Color.accent_soft};
        --c-critical: {Color.critical};
        --c-warning: {Color.warning};
        --c-success: {Color.success};

        --f-display: {Font.display};
        --f-body: {Font.body};
        --f-mono: {Font.mono};

        --r-sm: {Radius.sm};
        --r-md: {Radius.md};
        --r-lg: {Radius.lg};
        --r-pill: {Radius.pill};
      }}

      /* ── Reset / page ─────────────────────────────────────────────── */
      html, body, [class*="stApp"] {{
        background: var(--c-bg) !important;
        color: var(--c-ink) !important;
        font-family: var(--f-body) !important;
        font-feature-settings: "ss01", "ss02", "cv11";
      }}

      /* Hide default Streamlit chrome */
      #MainMenu, header[data-testid="stHeader"], footer, .stDeployButton {{
        display: none !important;
      }}

      /* Tighten main container */
      .main .block-container {{
        max-width: 1080px;
        padding-top: {Space.x4};
        padding-bottom: {Space.x16};
      }}

      /* Hide Streamlit's "running" indicator spinner top-right (we have our own) */
      [data-testid="stStatusWidget"] {{ display: none; }}

      /* ── Typography helpers ───────────────────────────────────────── */
      h1, h2, h3, h4, h5, h6 {{
        font-family: var(--f-display);
        font-weight: 400;
        letter-spacing: -0.01em;
        color: var(--c-ink);
        margin-bottom: {Space.x2};
      }}

      .label {{
        font-family: var(--f-body);
        font-size: {Size.xs}px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--c-ink-muted);
        font-weight: 500;
      }}

      .mono {{ font-family: var(--f-mono); }}

      /* ── Streamlit overrides ──────────────────────────────────────── */

      /* Buttons */
      .stButton > button {{
        background: var(--c-ink) !important;
        color: var(--c-ink-on-dark) !important;
        border: 1px solid var(--c-ink) !important;
        border-radius: var(--r-sm) !important;
        font-family: var(--f-body) !important;
        font-size: {Size.sm}px !important;
        font-weight: 500 !important;
        letter-spacing: 0.02em !important;
        padding: 8px 16px !important;
        transition: opacity 0.15s !important;
        box-shadow: none !important;
        line-height: 1.4 !important;
      }}
      .stButton > button:hover {{
        opacity: 0.85;
      }}
      .stButton > button:focus {{
        outline: 2px solid var(--c-accent-soft) !important;
        outline-offset: 2px !important;
      }}
      /* Secondary button variant */
      .stButton.btn-secondary > button, button[kind="secondary"] {{
        background: transparent !important;
        color: var(--c-ink) !important;
        border: 1px solid var(--c-border) !important;
      }}

      /* Text inputs */
      .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {{
        background: var(--c-surface) !important;
        border: 1px solid var(--c-border) !important;
        border-radius: var(--r-sm) !important;
        color: var(--c-ink) !important;
        font-family: var(--f-body) !important;
        font-size: {Size.base}px !important;
        padding: 10px 12px !important;
        box-shadow: none !important;
      }}
      .stTextInput input:focus, .stTextArea textarea:focus {{
        border-color: var(--c-ink) !important;
        outline: none !important;
      }}

      /* SQL editor variant (dark) */
      .sql-editor textarea {{
        background: var(--c-surface-dark) !important;
        color: #e8e6d8 !important;
        font-family: var(--f-mono) !important;
        font-size: 13px !important;
        line-height: 1.6 !important;
        border: 1px solid var(--c-surface-dark) !important;
      }}

      /* Selectbox */
      .stSelectbox label, .stTextInput label, .stTextArea label, .stFileUploader label {{
        font-size: {Size.xs}px !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
        color: var(--c-ink-muted) !important;
        font-weight: 500 !important;
      }}

      /* Sidebar */
      section[data-testid="stSidebar"] {{
        background: var(--c-surface) !important;
        border-right: 1px solid var(--c-border) !important;
      }}
      section[data-testid="stSidebar"] .block-container {{
        padding-top: {Space.x4};
      }}

      /* File uploader */
      [data-testid="stFileUploader"] section {{
        background: var(--c-surface) !important;
        border: 1px dashed var(--c-border-dashed) !important;
        border-radius: var(--r-sm) !important;
      }}
      [data-testid="stFileUploader"] section:hover {{
        border-color: var(--c-ink) !important;
      }}

      /* Dataframe styling */
      [data-testid="stDataFrame"] {{
        border: 1px solid var(--c-border) !important;
        border-radius: var(--r-sm) !important;
      }}

      /* Alerts */
      [data-testid="stAlert"] {{
        border-radius: var(--r-sm) !important;
        border: 1px solid var(--c-border) !important;
        font-family: var(--f-body) !important;
        font-size: {Size.sm}px !important;
      }}

      /* Code blocks */
      .stCodeBlock pre {{
        background: var(--c-surface-dark) !important;
        font-family: var(--f-mono) !important;
        border-radius: var(--r-sm) !important;
        font-size: 13px !important;
      }}

      /* Expander */
      [data-testid="stExpander"] {{
        border: 1px solid var(--c-border) !important;
        border-radius: var(--r-sm) !important;
        background: var(--c-surface) !important;
        box-shadow: none !important;
      }}
      [data-testid="stExpander"] summary {{
        font-family: var(--f-body) !important;
        font-size: {Size.sm}px !important;
        color: var(--c-ink) !important;
      }}

      /* Tabs */
      [data-baseweb="tab-list"] {{
        border-bottom: 1px solid var(--c-border) !important;
        gap: {Space.x6};
      }}
      [data-baseweb="tab"] {{
        font-family: var(--f-body) !important;
        font-size: {Size.sm}px !important;
        font-weight: 500 !important;
        color: var(--c-ink-3) !important;
      }}
      [data-baseweb="tab"][aria-selected="true"] {{
        color: var(--c-ink) !important;
      }}

      /* Spinner */
      [data-testid="stSpinner"] > div {{
        border-top-color: var(--c-accent) !important;
      }}

      /* ── Custom component classes ─────────────────────────────────── */

      /* Page header */
      .ap-header {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding-bottom: {Space.x4};
        margin-bottom: {Space.x6};
        border-bottom: 1px solid var(--c-border);
      }}
      .ap-brand {{
        display: flex; align-items: baseline; gap: {Space.x3};
      }}
      .ap-brand-mark {{
        font-family: var(--f-display);
        font-size: {Size.xl2}px;
        color: var(--c-accent);
        line-height: 1;
      }}
      .ap-brand-name {{
        font-family: var(--f-display);
        font-size: {Size.xl}px;
        color: var(--c-ink);
        letter-spacing: -0.01em;
      }}
      .ap-brand-tag {{
        font-family: var(--f-body);
        font-size: {Size.xs}px;
        color: var(--c-ink-muted);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-left: {Space.x2};
      }}
      .ap-model-badge {{
        display: inline-flex; align-items: center; gap: {Space.x2};
        padding: 5px 10px;
        background: var(--c-surface);
        border: 1px solid var(--c-border);
        border-radius: var(--r-pill);
        font-family: var(--f-mono);
        font-size: {Size.xs}px;
        color: var(--c-ink-2);
      }}
      .ap-model-badge .dot {{
        width: 6px; height: 6px; border-radius: 50%;
        background: var(--c-success);
      }}
      .ap-model-badge .dot.warn {{ background: var(--c-warning); }}
      .ap-model-badge .provider {{ color: var(--c-ink-muted); }}
      .ap-model-badge .sep {{ color: var(--c-ink-muted); margin: 0 2px; }}

      /* Section heading */
      .ap-section-label {{
        font-family: var(--f-body);
        font-size: {Size.xs}px;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: var(--c-ink-muted);
        margin: {Space.x6} 0 {Space.x3} 0;
        display: flex;
        align-items: center;
        gap: {Space.x2};
      }}

      /* Card */
      .ap-card {{
        background: var(--c-surface);
        border: 1px solid var(--c-border);
        border-radius: var(--r-sm);
        padding: {Space.x5} {Space.x6};
      }}
      .ap-card.accent-left {{
        border-left: 3px solid var(--c-accent);
      }}

      /* Hero (dataset summary on load) */
      .ap-hero {{
        background: var(--c-surface);
        border: 1px solid var(--c-border);
        padding: {Space.x6};
        margin-bottom: {Space.x4};
      }}
      .ap-hero h2 {{
        font-family: var(--f-display);
        font-size: {Size.xl2}px;
        margin: 0 0 {Space.x2} 0;
      }}
      .ap-hero .desc {{
        font-family: var(--f-display);
        font-style: italic;
        font-size: {Size.md}px;
        color: var(--c-ink-3);
        margin: 0 0 {Space.x4} 0;
        line-height: 1.5;
      }}
      .ap-stat-row {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: {Space.x6};
        border-top: 1px solid var(--c-border);
        padding-top: {Space.x4};
      }}
      .ap-stat .label {{
        font-size: {Size.xs}px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--c-ink-muted);
        margin-bottom: 2px;
      }}
      .ap-stat .value {{
        font-family: var(--f-mono);
        font-size: {Size.lg}px;
        color: var(--c-ink);
        font-weight: 500;
      }}

      /* Suggested question pill */
      .ap-question-pill {{
        background: var(--c-surface);
        border: 1px solid var(--c-border);
        border-left: 3px solid var(--c-accent);
        padding: {Space.x3} {Space.x4};
        font-family: var(--f-display);
        font-size: {Size.md}px;
        color: var(--c-ink);
        cursor: pointer;
        transition: background 0.1s;
      }}
      .ap-question-pill:hover {{
        background: var(--c-surface-2);
      }}

      /* Analysis card */
      .ap-analysis {{
        background: var(--c-surface);
        border: 1px solid var(--c-border);
        border-left: 3px solid var(--c-accent);
        padding: {Space.x5} {Space.x6};
      }}
      .ap-analysis .headline {{
        font-family: var(--f-display);
        font-size: {Size.xl}px;
        color: var(--c-ink);
        line-height: 1.3;
        margin: {Space.x2} 0 {Space.x4} 0;
      }}
      .ap-analysis .finding {{
        display: flex;
        gap: {Space.x3};
        margin-bottom: {Space.x3};
        font-size: {Size.base}px;
        line-height: 1.55;
        color: var(--c-ink-2);
      }}
      .ap-analysis .finding .num {{
        font-family: var(--f-mono);
        font-size: {Size.xs}px;
        color: var(--c-accent);
        font-weight: 600;
        margin-top: 4px;
        flex-shrink: 0;
      }}
      .ap-analysis .caveats {{
        margin-top: {Space.x4};
        padding-top: {Space.x3};
        border-top: 1px dashed var(--c-border-dashed);
        font-family: var(--f-body);
        font-size: {Size.sm}px;
        color: var(--c-ink-muted);
        font-style: italic;
      }}
      .ap-analysis .caveats strong {{
        color: var(--c-warning);
        font-style: normal;
        font-weight: 500;
        margin-right: 6px;
      }}

      /* SQL editor surround */
      .ap-sql-frame {{
        background: var(--c-surface-dark);
        color: var(--c-ink-on-dark);
        border-radius: var(--r-sm);
        overflow: hidden;
      }}
      .ap-sql-header {{
        display: flex; align-items: center; justify-content: space-between;
        padding: 10px 14px;
        background: #1a1614;
        border-bottom: 1px solid #2a2522;
      }}
      .ap-sql-label {{
        font-family: var(--f-mono);
        font-size: {Size.xs}px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #a8a29e;
      }}
      .ap-sql-reasoning {{
        padding: 10px 14px;
        background: #15110f;
        border-top: 1px solid #2a2522;
        font-family: var(--f-display);
        font-style: italic;
        font-size: {Size.sm}px;
        color: #a8a29e;
        line-height: 1.5;
      }}
      .ap-sql-reasoning .tag {{
        font-family: var(--f-body);
        font-style: normal;
        font-size: {Size.xs}px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--c-accent-soft);
        margin-right: 8px;
      }}

      /* ── Auth screen ──────────────────────────────────────────────── */
      .auth-screen {{
        max-width: 360px;
        margin: 120px auto 0;
        text-align: center;
      }}
      .auth-brand {{
        display: flex; align-items: baseline; justify-content: center; gap: {Space.x2};
        margin-bottom: {Space.x2};
      }}
      .auth-mark {{
        font-family: var(--f-display);
        font-size: {Size.xl2}px;
        color: var(--c-accent);
        line-height: 1;
      }}
      .auth-name {{
        font-family: var(--f-display);
        font-size: {Size.xl}px;
        color: var(--c-ink);
      }}
      .auth-tag {{
        font-family: var(--f-body);
        font-size: {Size.xs}px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--c-ink-muted);
        margin: 0 0 {Space.x6} 0;
      }}

      /* Footer */
      .ap-footer {{
        margin-top: {Space.x16};
        padding-top: {Space.x4};
        border-top: 1px solid var(--c-border);
        font-family: var(--f-mono);
        font-size: {Size.xs}px;
        color: var(--c-ink-muted);
        line-height: 1.6;
      }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
