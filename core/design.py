"""
Design tokens. The single source of truth for visual primitives.

Every component reads from here. To re-theme the app, edit this file.
"""

# ── Color tokens ─────────────────────────────────────────────────────────
class Color:
    # Surfaces
    bg = "#fafaf9"            # Page background
    surface = "#ffffff"       # Card / elevated surface
    surface_2 = "#f5f3ee"     # Subtle alt surface (table headers, etc.)
    surface_dark = "#0c0a09"  # Inverted (SQL editor)

    # Borders
    border = "#e7e5e0"
    border_strong = "#0c0a09"
    border_dashed = "#d6d3cc"

    # Text
    ink = "#0c0a09"
    ink_2 = "#3f3d39"
    ink_3 = "#57534e"
    ink_muted = "#a8a29e"
    ink_on_dark = "#fafaf9"
    ink_on_dark_muted = "#a8a29e"

    # Brand / accent
    accent = "#0f766e"         # Deep teal
    accent_hover = "#134e4a"
    accent_soft = "#ccfbf1"
    accent_text = "#0f766e"

    # Semantic
    critical = "#b91c1c"
    critical_soft = "#fef2f2"
    warning = "#a16207"
    warning_soft = "#fef9c3"
    success = "#15803d"


# ── Typography tokens ────────────────────────────────────────────────────
class Font:
    # Loaded via Google Fonts in styles.py
    display = '"Newsreader", "Iowan Old Style", Georgia, serif'
    body = '"Geist", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
    mono = '"JetBrains Mono", "SF Mono", Menlo, Consolas, monospace'


class Size:
    """Type scale (px)."""
    xs = 11
    sm = 12
    base = 14
    md = 16
    lg = 18
    xl = 22
    xl2 = 28
    xl3 = 36
    xl4 = 48


# ── Spacing scale (4px base) ─────────────────────────────────────────────
class Space:
    x1 = "4px"
    x2 = "8px"
    x3 = "12px"
    x4 = "16px"
    x5 = "20px"
    x6 = "24px"
    x8 = "32px"
    x10 = "40px"
    x12 = "48px"
    x16 = "64px"


# ── Radii ────────────────────────────────────────────────────────────────
class Radius:
    none = "0"
    sm = "2px"
    md = "4px"
    lg = "8px"
    pill = "999px"


# App identity tokens (APP_NAME / APP_TAGLINE / APP_VERSION) live in
# core/config.py — import from there.
