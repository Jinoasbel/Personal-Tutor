"""
colors.py — Central color palette for Personal Tutor
All colors used in the application are defined here.
No color values should appear anywhere else in the codebase.
"""


class Colors:
    # ── Base / Background ─────────────────────────────────────────────────────
    BG_PRIMARY        = "#4A5568"   # Main app background (dark grey-blue)
    BG_SECONDARY      = "#3D4A5C"   # Sidebar / panel background
    BG_TERTIARY       = "#2D3748"   # Deeper panel / overlay background

    # ── Surface / Card ────────────────────────────────────────────────────────
    SURFACE_DARK      = "#1A202C"   # Dark input fields, button faces
    SURFACE_MID       = "#2D3748"   # Mid-tone cards, scrollable areas
    SURFACE_LIGHT     = "#4A5568"   # Hover state for surface elements

    # ── Sidebar ───────────────────────────────────────────────────────────────
    SIDEBAR_BG        = "#6B7280"   # Sidebar background (light grey)
    SIDEBAR_BTN_BG    = "#4B5563"   # Sidebar nav button background
    SIDEBAR_BTN_HOVER = "#374151"   # Sidebar button hover
    SIDEBAR_ACTIVE    = "#374151"   # Active/selected nav button

    # ── Upload Panel ──────────────────────────────────────────────────────────
    UPLOAD_PANEL_BG   = "#4A6080"   # Upload dialog panel background (blue-grey)
    LINK_INPUT_BG     = "#1A202C"   # Link entry field background
    LINK_ICON_BG      = "#3D4A5C"   # Link icon container background

    # ── Buttons ───────────────────────────────────────────────────────────────
    BTN_PRIMARY_BG    = "#2D3748"   # Primary button (SUBMIT, FILES) background
    BTN_PRIMARY_HOVER = "#374151"   # Primary button hover
    BTN_ADD_BG        = "#374151"   # Add (+) button background
    BTN_ADD_HOVER     = "#4B5563"   # Add (+) button hover
    BTN_UPLOAD_BG     = "#4B5563"   # UPLOAD FAB background
    BTN_UPLOAD_HOVER  = "#374151"   # UPLOAD FAB hover
    BTN_UPLOAD_BORDER = "#6B7280"   # UPLOAD FAB border

    # ── Text ──────────────────────────────────────────────────────────────────
    TEXT_PRIMARY      = "#F9FAFB"   # Main white text
    TEXT_SECONDARY    = "#D1D5DB"   # Secondary/muted text
    TEXT_PLACEHOLDER  = "#6B7280"   # Placeholder text in inputs
    TEXT_DISABLED     = "#4B5563"   # Disabled state text
    TEXT_ACCENT       = "#93C5FD"   # Accent / highlighted text (light blue)

    # ── Icons ─────────────────────────────────────────────────────────────────
    ICON_DEFAULT      = "#9CA3AF"   # Default icon color (grey)
    ICON_ACTIVE       = "#BFDBFE"   # Active icon color (light blue)
    ICON_FOLDER       = "#3B82F6"   # Folder icon (blue)

    # ── Borders & Dividers ────────────────────────────────────────────────────
    BORDER_DEFAULT    = "#374151"   # Default border/divider
    BORDER_FOCUS      = "#60A5FA"   # Focused input border
    BORDER_SUBTLE     = "#2D3748"   # Very subtle border

    # ── Scrollbar ─────────────────────────────────────────────────────────────
    SCROLLBAR_BG      = "#2D3748"
    SCROLLBAR_HANDLE  = "#4B5563"
    SCROLLBAR_HOVER   = "#6B7280"

    # ── State Colors ──────────────────────────────────────────────────────────
    SUCCESS           = "#34D399"   # Success green
    WARNING           = "#FBBF24"   # Warning amber
    ERROR             = "#F87171"   # Error red
    INFO              = "#60A5FA"   # Info blue
