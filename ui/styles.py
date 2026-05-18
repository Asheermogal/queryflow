"""
Global CSS injection. Overrides Streamlit defaults to enforce the design system
from core/design.py. Pulls fonts from Google Fonts.
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

      /* Widen the main container to use full screen, with breathing room */
      .main .block-container {{
        max-width: 100% !important;
        padding-left: {Space.x8} !important;
        padding-right: {Space.x8} !important;
        padding-top: {Space.x6} !important;
        padding-bottom: {Space.x16} !important;
      }}

      /* Sidebar — fixed, non-collapsible */
      section[data-testid="stSidebar"] {{
        background: var(--c-surface) !important;
        border-right: 1px solid var(--c-border) !important;
      }}
      section[data-testid="stSidebar"] .block-container {{
        padding-top: {Space.x4};
      }}
      /* Hide every flavor of collapse/expand control */
      [data-testid="stSidebarCollapsedControl"],
      [data-testid="collapsedControl"],
      [data-testid="stSidebar"] [data-testid="stSidebarHeader"] button,
      [data-testid="stSidebar"] button[kind="headerNoPadding"],
      [aria-label="Open sidebar"],
      [aria-label="Close sidebar"] {{
        display: none !important;
        visibility: hidden !important;
      }}
      /* Disable the drag-to-resize handle on the right edge */
      section[data-testid="stSidebar"] > div:last-child {{
        pointer-events: none !important;
      }}

      /* ── Typography ────────────────────────────────────────────────── */
      h1, h2, h3, h4, h5, h6 {{
        font-family: var(--f-display);
        font-weight: 400;
        letter-spacing: -0.01em;
        color: var(--c-ink);
        margin-bottom: {Space.x2};
      }}

      /* ── Streamlit overrides ──────────────────────────────────────── */

      /* Inputs */
      .stTextInput input, .stTextArea textarea,
      .stSelectbox div[data-baseweb="select"] > div {{
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
      /* SQL editor uses monospace */
      .stTextArea textarea {{
        font-family: var(--f-mono) !important;
        font-size: 13px !important;
        line-height: 1.55 !important;
      }}

      .stSelectbox label, .stTextInput label, .stTextArea label, .stFileUploader label {{
        font-size: {Size.xs}px !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
        color: var(--c-ink-muted) !important;
        font-weight: 500 !important;
      }}

      /* ── Deep BaseWeb text color fixes ─────────────────────────────── */
      /* These reach the nested spans / popovers that the outer .stSelectbox
         rules never touched — fixes white-on-white text in 1.57+. */

      /* Selectbox: selected value, search input, dropdown arrow */
      .stSelectbox [data-baseweb="select"] *,
      .stSelectbox [data-baseweb="select"] input {{
        color: var(--c-ink) !important;
      }}

      /* Closed selectbox: readonly input / combobox value (WebKit often ignores color alone). */
      section[data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] input,
      [data-testid="stMain"] .stSelectbox [data-baseweb="select"] input,
      .main .stSelectbox [data-baseweb="select"] input,
      section[data-testid="stSidebar"] .stSelectbox [role="combobox"],
      section[data-testid="stSidebar"] .stSelectbox [role="combobox"] *,
      [data-testid="stMain"] .stSelectbox [role="combobox"],
      [data-testid="stMain"] .stSelectbox [role="combobox"] *,
      .main .stSelectbox [role="combobox"],
      .main .stSelectbox [role="combobox"] * {{
        color: var(--c-ink) !important;
        -webkit-text-fill-color: var(--c-ink) !important;
        caret-color: var(--c-ink) !important;
      }}

      /* Open dropdown menu: the popover lives at <body> root, NOT under .stSelectbox */
      [data-baseweb="popover"] [role="listbox"],
      [data-baseweb="popover"] [role="listbox"] *,
      [data-baseweb="menu"] [role="option"],
      [data-baseweb="menu"] [role="option"] * {{
        color: var(--c-ink) !important;
        background-color: var(--c-surface) !important;
      }}
      [data-baseweb="menu"] [role="option"]:hover,
      [data-baseweb="menu"] [role="option"][aria-selected="true"] {{
        background-color: var(--c-surface-2) !important;
      }}

      /* Radio (Explore / Query toggle and similar) */
      [data-testid="stRadio"] label,
      [data-testid="stRadio"] label * {{
        color: var(--c-ink) !important;
      }}

      /* Text input + textarea placeholders */
      .stTextInput input::placeholder,
      .stTextArea textarea::placeholder {{
        color: var(--c-ink-muted) !important;
        opacity: 1 !important;
      }}

      /* Slider value label (custom chart builder uses it) */
      [data-testid="stSlider"] [data-baseweb] * {{
        color: var(--c-ink) !important;
      }}

      /* Buttons — primary (filled dark) */
      .stButton > button[kind="primary"] {{
        background: var(--c-ink) !important;
        color: var(--c-ink-on-dark) !important;
        border: 1px solid var(--c-ink) !important;
        border-radius: var(--r-sm) !important;
        font-family: var(--f-body) !important;
        font-size: {Size.sm}px !important;
        font-weight: 500 !important;
        letter-spacing: 0.02em !important;
        padding: 8px 16px !important;
        box-shadow: none !important;
        line-height: 1.4 !important;
        transition: opacity 0.15s !important;
      }}
      .stButton > button[kind="primary"]:hover {{
        opacity: 0.85;
      }}
      /* Buttons — secondary (outline) — used for starter questions too */
      .stButton > button[kind="secondary"] {{
        background: var(--c-surface) !important;
        color: var(--c-ink) !important;
        border: 1px solid var(--c-border) !important;
        border-left: 3px solid var(--c-accent) !important;
        border-radius: var(--r-sm) !important;
        font-family: var(--f-display) !important;
        font-size: {Size.md}px !important;
        font-weight: 400 !important;
        text-align: left !important;
        padding: 12px 16px !important;
        white-space: normal !important;
        line-height: 1.4 !important;
        height: auto !important;
        box-shadow: none !important;
        transition: background 0.1s !important;
      }}
      .stButton > button[kind="secondary"]:hover {{
        background: var(--c-surface-2) !important;
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

      /* Dataframe */
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

      /* Expander */
      [data-testid="stExpander"] {{
        border: 1px solid var(--c-border) !important;
        border-radius: var(--r-sm) !important;
        background: var(--c-surface) !important;
        box-shadow: none !important;
        margin-bottom: {Space.x3} !important;
      }}
      [data-testid="stExpander"] summary {{
        font-family: var(--f-body) !important;
        font-size: {Size.sm}px !important;
        font-weight: 500 !important;
        color: var(--c-ink) !important;
        padding: 12px 14px !important;
      }}

      /* Spinner */
      [data-testid="stSpinner"] > div {{
        border-top-color: var(--c-accent) !important;
      }}

      /* Hide running-indicator (we use our own spinners) */
      [data-testid="stStatusWidget"] {{ display: none; }}

      /* ── App header ──────────────────────────────────────────────── */
      .qf-header {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding-bottom: {Space.x4};
        margin-bottom: {Space.x6};
        border-bottom: 1px solid var(--c-border);
      }}
      .qf-brand {{
        display: flex; align-items: baseline; gap: {Space.x3};
      }}
      .qf-brand-mark {{
        font-family: var(--f-display);
        font-size: {Size.xl2}px;
        color: var(--c-accent);
        line-height: 1;
      }}
      .qf-brand-name {{
        font-family: var(--f-display);
        font-size: {Size.xl}px;
        color: var(--c-ink);
        letter-spacing: -0.01em;
      }}
      .qf-brand-tag {{
        font-family: var(--f-body);
        font-size: {Size.xs}px;
        color: var(--c-ink-muted);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-left: {Space.x2};
      }}
      .qf-model-badge {{
        display: inline-flex; align-items: center; gap: {Space.x2};
        padding: 5px 10px;
        background: var(--c-surface);
        border: 1px solid var(--c-border);
        border-radius: var(--r-pill);
        font-family: var(--f-mono);
        font-size: {Size.xs}px;
        color: var(--c-ink-2);
      }}
      .qf-model-badge .dot {{
        width: 6px; height: 6px; border-radius: 50%; background: var(--c-success);
      }}
      .qf-model-badge .dot.warn {{ background: var(--c-warning); }}
      .qf-model-badge .provider {{ color: var(--c-ink-muted); }}
      .qf-model-badge .sep {{ color: var(--c-ink-muted); margin: 0 2px; }}

      /* ── Section heading ──────────────────────────────────────────── */
      .qf-section-label {{
        font-family: var(--f-body);
        font-size: {Size.xs}px;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: var(--c-ink-muted);
        margin: {Space.x6} 0 {Space.x3} 0;
        font-weight: 500;
      }}

      /* ── Sidebar styling ──────────────────────────────────────────── */
      .sb-brand {{
        display: flex; align-items: baseline; gap: {Space.x2};
        padding: 0 0 {Space.x4} 0;
      }}
      .sb-mark {{
        font-family: var(--f-display);
        font-size: {Size.xl2}px;
        color: var(--c-accent);
        line-height: 1;
      }}
      .sb-name {{
        font-family: var(--f-display);
        font-size: {Size.lg}px;
        color: var(--c-ink);
      }}
      .sb-section-label {{
        font-family: var(--f-body);
        font-size: {Size.xs}px;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: var(--c-ink-muted);
        margin: {Space.x6} 0 {Space.x2} 0;
        font-weight: 500;
      }}
      .sb-provider-pill {{
        display: flex; align-items: center; gap: 8px;
        padding: 10px 12px;
        background: var(--c-surface-2);
        border: 1px solid var(--c-border);
        border-radius: var(--r-sm);
        margin-bottom: {Space.x3};
      }}
      .sb-provider-dot {{
        width: 7px; height: 7px; border-radius: 50%;
        background: var(--c-success);
        flex-shrink: 0;
      }}
      .sb-provider-name {{
        font-family: var(--f-body);
        font-size: {Size.sm}px;
        font-weight: 500;
        color: var(--c-ink);
        flex: 1;
      }}
      .sb-provider-tag {{
        font-family: var(--f-mono);
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--c-success);
      }}
      .sb-empty {{
        padding: 12px;
        background: var(--c-surface-2);
        border: 1px dashed var(--c-border-dashed);
        border-radius: var(--r-sm);
        font-size: {Size.sm}px;
        color: var(--c-ink-3);
        line-height: 1.5;
      }}
      .sb-empty code {{
        font-family: var(--f-mono);
        font-size: 11px;
        background: var(--c-bg);
        padding: 1px 4px;
        border-radius: 2px;
      }}

      /* ── Right-rail dataset panel ─────────────────────────────────── */
      .qf-rail-hero {{
        padding: 0 0 {Space.x4} 0;
        border-bottom: 1px solid var(--c-border);
        margin-bottom: {Space.x4};
      }}
      .qf-rail-name {{
        font-family: var(--f-display);
        font-size: {Size.xl}px;
        color: var(--c-ink);
        line-height: 1.25;
        margin-bottom: {Space.x2};
        letter-spacing: -0.01em;
      }}
      .qf-rail-desc {{
        font-family: var(--f-display);
        font-style: italic;
        font-size: {Size.sm}px;
        color: var(--c-ink-3);
        line-height: 1.55;
      }}
      .qf-rail-stats {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: {Space.x3};
        margin-bottom: {Space.x4};
      }}
      .qf-stat {{
        background: var(--c-surface);
        border: 1px solid var(--c-border);
        border-radius: var(--r-sm);
        padding: 10px 12px;
      }}
      .qf-stat .lbl {{
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--c-ink-muted);
        margin-bottom: 2px;
        font-weight: 500;
      }}
      .qf-stat .val {{
        font-family: var(--f-mono);
        font-size: {Size.md}px;
        color: var(--c-ink);
        font-weight: 500;
      }}
      .qf-rail-note {{
        font-family: var(--f-mono);
        font-size: 11px;
        color: var(--c-ink-muted);
        line-height: 1.5;
        padding: 8px 10px;
        background: var(--c-surface);
        border: 1px solid var(--c-border);
        border-left: 3px solid var(--c-warning);
        border-radius: var(--r-sm);
        margin-bottom: {Space.x3};
      }}

      /* Dataset brief card */
      .qf-brief-card {{
        background: var(--c-surface);
        border: 1px solid var(--c-border);
        border-left: 3px solid var(--c-accent);
        border-radius: var(--r-sm);
        padding: 14px 16px;
        margin: 0 0 {Space.x3} 0;
      }}
      .qf-brief-headline {{
        font-family: var(--f-display);
        font-size: {Size.md}px;
        color: var(--c-ink);
        line-height: 1.35;
        margin-bottom: {Space.x2};
      }}
      .qf-brief-bullets {{
        margin: 0;
        padding: 0 0 0 18px;
        font-family: var(--f-body);
        font-size: {Size.sm}px;
        color: var(--c-ink-2);
        line-height: 1.55;
      }}
      .qf-brief-bullets li {{ margin-bottom: 4px; }}

      /* Dictionary entries */
      .qf-dict-entry {{
        padding: {Space.x2} 0;
        border-bottom: 1px solid var(--c-border);
      }}
      .qf-dict-entry:last-child {{ border-bottom: 0; }}
      .qf-dict-col {{
        font-family: var(--f-mono);
        font-size: {Size.xs}px;
        font-weight: 600;
        color: var(--c-ink);
        margin-bottom: 2px;
        text-transform: lowercase;
      }}
      .qf-dict-desc {{
        font-family: var(--f-body);
        font-size: {Size.xs}px;
        color: var(--c-ink-3);
        line-height: 1.55;
      }}

      /* ── Query flow ───────────────────────────────────────────────── */
      .qf-question {{
        font-family: var(--f-display);
        font-size: {Size.xl}px;
        color: var(--c-ink);
        line-height: 1.3;
        margin: {Space.x4} 0 {Space.x3} 0;
        letter-spacing: -0.01em;
      }}
      .qf-sql-label {{
        font-family: var(--f-mono);
        font-size: {Size.xs}px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--c-ink-muted);
        margin: {Space.x2} 0 {Space.x2} 0;
        font-weight: 500;
      }}
      .qf-sql-reasoning {{
        padding: 10px 12px;
        background: var(--c-surface-2);
        border-left: 3px solid var(--c-accent);
        font-family: var(--f-display);
        font-style: italic;
        font-size: {Size.sm}px;
        color: var(--c-ink-3);
        line-height: 1.5;
        margin: {Space.x2} 0 {Space.x3} 0;
        border-radius: var(--r-sm);
      }}
      .qf-sql-reasoning .tag {{
        font-family: var(--f-body);
        font-style: normal;
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--c-accent);
        margin-right: 6px;
        font-weight: 500;
      }}

      .qf-analysis {{
        background: var(--c-surface);
        border: 1px solid var(--c-border);
        border-left: 3px solid var(--c-accent);
        padding: {Space.x4} {Space.x5};
        border-radius: var(--r-sm);
        margin-top: {Space.x2};
      }}
      .qf-analysis-headline {{
        font-family: var(--f-display);
        font-size: {Size.lg}px;
        color: var(--c-ink);
        line-height: 1.3;
        margin: 0 0 {Space.x3} 0;
      }}
      .qf-analysis .finding {{
        display: flex; gap: {Space.x3};
        margin-bottom: {Space.x2};
        font-size: {Size.base}px;
        line-height: 1.55;
        color: var(--c-ink-2);
      }}
      .qf-analysis .finding .num {{
        font-family: var(--f-mono);
        font-size: 10px;
        color: var(--c-accent);
        font-weight: 600;
        margin-top: 4px;
        flex-shrink: 0;
      }}
      .qf-analysis .caveats {{
        margin-top: {Space.x3};
        padding-top: {Space.x2};
        border-top: 1px dashed var(--c-border-dashed);
        font-family: var(--f-body);
        font-size: {Size.sm}px;
        color: var(--c-ink-muted);
        font-style: italic;
      }}
      .qf-analysis .caveats strong {{
        color: var(--c-warning);
        font-style: normal;
        font-weight: 500;
        margin-right: 4px;
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
      .qf-footer {{
        margin-top: {Space.x12};
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
