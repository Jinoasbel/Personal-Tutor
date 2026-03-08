"""
colors.py — Central color palette for Personal Tutor
All colors used in the application are defined here.
No color values should appear anywhere else in the codebase.
"""


class Colors:
    #Theme: Midnight Indigo (Deep Focus Dark Mode) ───────────────────────────────────────────────────────────────
    # ── Base / Background ─────────────────────────────────────────────────────
    BG_PRIMARY        = "#0F172A"   # Main app background (deep navy)
    BG_SECONDARY      = "#1E293B"   # Sidebar / panel background
    BG_TERTIARY       = "#334155"   # Deeper panel / overlay background

    # ── Surface / Card ────────────────────────────────────────────────────────
    SURFACE_DARK      = "#020617"   # Dark input fields, button faces
    SURFACE_MID       = "#1E293B"   # Mid-tone cards, scrollable areas
    SURFACE_LIGHT     = "#334155"   # Hover state for surface elements

    # ── Sidebar ───────────────────────────────────────────────────────────────
    SIDEBAR_BG        = "#1E293B"   # Sidebar background
    SIDEBAR_BTN_BG    = "#334155"   # Sidebar nav button background
    SIDEBAR_BTN_HOVER = "#475569"   # Sidebar button hover
    SIDEBAR_ACTIVE    = "#475569"   # Active/selected nav button

    # ── Upload Panel ──────────────────────────────────────────────────────────
    UPLOAD_PANEL_BG   = "#1E293B"   # Upload dialog panel background
    LINK_INPUT_BG     = "#020617"   # Link entry field background
    LINK_ICON_BG      = "#334155"   # Link icon container background

    # ── Buttons ───────────────────────────────────────────────────────────────
    BTN_PRIMARY_BG    = "#3B82F6"   # Primary button (vibrant focus blue)
    BTN_PRIMARY_HOVER = "#2563EB"   # Primary button hover
    BTN_ADD_BG        = "#334155"   # Add (+) button background
    BTN_ADD_HOVER     = "#475569"   # Add (+) button hover
    BTN_UPLOAD_BG     = "#334155"   # UPLOAD FAB background
    BTN_UPLOAD_HOVER  = "#475569"   # UPLOAD FAB hover
    BTN_UPLOAD_BORDER = "#475569"   # UPLOAD FAB border

    # ── Text ──────────────────────────────────────────────────────────────────
    TEXT_PRIMARY      = "#F8FAFC"   # Main white text
    TEXT_SECONDARY    = "#94A3B8"   # Secondary/muted text
    TEXT_PLACEHOLDER  = "#64748B"   # Placeholder text in inputs
    TEXT_DISABLED     = "#475569"   # Disabled state text
    TEXT_ACCENT       = "#60A5FA"   # Accent / highlighted text (bright blue)

    # ── Icons ─────────────────────────────────────────────────────────────────
    ICON_DEFAULT      = "#94A3B8"   # Default icon color
    ICON_ACTIVE       = "#60A5FA"   # Active icon color
    ICON_FOLDER       = "#3B82F6"   # Folder icon

    # ── Borders & Dividers ────────────────────────────────────────────────────
    BORDER_DEFAULT    = "#334155"   # Default border/divider
    BORDER_FOCUS      = "#60A5FA"   # Focused input border
    BORDER_SUBTLE     = "#1E293B"   # Very subtle border

    # ── Scrollbar ─────────────────────────────────────────────────────────────
    SCROLLBAR_BG      = "#0F172A"
    SCROLLBAR_HANDLE  = "#334155"
    SCROLLBAR_HOVER   = "#475569"

    # ── State Colors ──────────────────────────────────────────────────────────
    SUCCESS           = "#10B981"   # Success green
    WARNING           = "#F59E0B"   # Warning amber
    ERROR             = "#EF4444"   # Error red
    INFO              = "#3B82F6"   # Info blue


    # #Bright
    # #---Theme: Parchment & Ink (Clean Light Mode)──────────────────────────────────────────────────────────────
    # # ── Base / Background ─────────────────────────────────────────────────────
    # BG_PRIMARY        = "#F8FAFC"   # Main app background (soft off-white)
    # BG_SECONDARY      = "#F1F5F9"   # Sidebar / panel background
    # BG_TERTIARY       = "#E2E8F0"   # Deeper panel / overlay background

    # # ── Surface / Card ────────────────────────────────────────────────────────
    # SURFACE_DARK      = "#FFFFFF"   # White input fields, bright cards
    # SURFACE_MID       = "#F1F5F9"   # Mid-tone cards, scrollable areas
    # SURFACE_LIGHT     = "#E2E8F0"   # Hover state for surface elements

    # # ── Sidebar ───────────────────────────────────────────────────────────────
    # SIDEBAR_BG        = "#F1F5F9"   # Sidebar background
    # SIDEBAR_BTN_BG    = "#E2E8F0"   # Sidebar nav button background
    # SIDEBAR_BTN_HOVER = "#CBD5E1"   # Sidebar button hover
    # SIDEBAR_ACTIVE    = "#CBD5E1"   # Active/selected nav button

    # # ── Upload Panel ──────────────────────────────────────────────────────────
    # UPLOAD_PANEL_BG   = "#F1F5F9"   # Upload dialog panel background
    # LINK_INPUT_BG     = "#FFFFFF"   # Link entry field background
    # LINK_ICON_BG      = "#E2E8F0"   # Link icon container background

    # # ── Buttons ───────────────────────────────────────────────────────────────
    # BTN_PRIMARY_BG    = "#0F172A"   # Primary button (high contrast dark slate)
    # BTN_PRIMARY_HOVER = "#334155"   # Primary button hover
    # BTN_ADD_BG        = "#E2E8F0"   # Add (+) button background
    # BTN_ADD_HOVER     = "#CBD5E1"   # Add (+) button hover
    # BTN_UPLOAD_BG     = "#E2E8F0"   # UPLOAD FAB background
    # BTN_UPLOAD_HOVER  = "#CBD5E1"   # UPLOAD FAB hover
    # BTN_UPLOAD_BORDER = "#94A3B8"   # UPLOAD FAB border

    # # ── Text ──────────────────────────────────────────────────────────────────
    # TEXT_PRIMARY      = "#0F172A"   # Main dark text (near black)
    # TEXT_SECONDARY    = "#475569"   # Secondary/muted text
    # TEXT_PLACEHOLDER  = "#94A3B8"   # Placeholder text in inputs
    # TEXT_DISABLED     = "#CBD5E1"   # Disabled state text
    # TEXT_ACCENT       = "#2563EB"   # Accent / highlighted text (strong blue)

    # # ── Icons ─────────────────────────────────────────────────────────────────
    # ICON_DEFAULT      = "#64748B"   # Default icon color
    # ICON_ACTIVE       = "#2563EB"   # Active icon color
    # ICON_FOLDER       = "#3B82F6"   # Folder icon

    # # ── Borders & Dividers ────────────────────────────────────────────────────
    # BORDER_DEFAULT    = "#CBD5E1"   # Default border/divider
    # BORDER_FOCUS      = "#3B82F6"   # Focused input border
    # BORDER_SUBTLE     = "#E2E8F0"   # Very subtle border

    # # ── Scrollbar ─────────────────────────────────────────────────────────────
    # SCROLLBAR_BG      = "#F8FAFC"
    # SCROLLBAR_HANDLE  = "#CBD5E1"
    # SCROLLBAR_HOVER   = "#94A3B8"

    # # ── State Colors ──────────────────────────────────────────────────────────
    # SUCCESS           = "#059669"   # Success green (slightly darker for light bg)
    # WARNING           = "#D97706"   # Warning amber
    # ERROR             = "#DC2626"   # Error red
    # INFO              = "#2563EB"   # Info blue
