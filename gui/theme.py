"""
gui/theme.py — Bootstrap-style design tokens (single source of truth).

Usage in QSS:  write  $primary, $border, etc.
               main.py substitutes them at load time via QSS_TOKENS.

Usage in Python:  import the constants directly.
"""

# ── Brand ──────────────────────────────────────────────────────────────────
PRIMARY        = "#90af13"
PRIMARY_HOVER  = "#7c9811"   # ~13 % darker — button hover
PRIMARY_ACTIVE = "#6c830e"   # ~25 % darker — button pressed

# ── Neutrals (Bootstrap 5 tokens) ─────────────────────────────────────────
WHITE          = "#ffffff"
BODY_BG        = "#f8f9fa"   # app window / sidebar background
BODY_COLOR     = "#212529"   # primary text
SECONDARY      = "#6c757d"   # muted / secondary text
BORDER         = "#dee2e6"   # standard border
BORDER_SUBTLE  = "#ced4da"   # slightly darker border (inputs on hover)
MUTED          = "#adb5bd"   # disabled / placeholder elements
SURFACE        = "#e9ecef"   # neutral hover background
SURFACE_ACTIVE = "#dee2e6"   # neutral pressed background

# ── Sidebar states (pre-computed solid — no alpha blending) ───────────────
# PRIMARY at 12% on BODY_BG (#f8f9fa) → fully opaque light green
SIDEBAR_HOVER  = "#ecf0de"
# PRIMARY at 25% on BODY_BG (#f8f9fa) → fully opaque medium green
SIDEBAR_SEL    = "#dee7c0"

# ── QSS substitution map ───────────────────────────────────────────────────
# Keys are sorted longest-first so that e.g. "$border-subtle" is replaced
# before "$border" when main.py iterates in insertion order.
QSS_TOKENS: dict[str, str] = {
    "$primary-hover":  PRIMARY_HOVER,
    "$primary-active": PRIMARY_ACTIVE,
    "$border-subtle":  BORDER_SUBTLE,
    "$surface-active": SURFACE_ACTIVE,
    "$body-color":     BODY_COLOR,
    "$secondary":      SECONDARY,
    "$primary":        PRIMARY,
    "$body-bg":        BODY_BG,
    "$border":         BORDER,
    "$surface":        SURFACE,
    "$muted":          MUTED,
    "$white":          WHITE,
}
