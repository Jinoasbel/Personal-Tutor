"""
dimensions.py — Spacing, sizing, border radius, and layout constants.
All numeric layout values are defined here.
"""


class Spacing:
    XS   = 4
    SM   = 8
    MD   = 12
    LG   = 16
    XL   = 24
    XXL  = 32
    XXXL = 48


class Radius:
    NONE   = 0
    XS     = 3
    SM     = 6
    MD     = 8
    LG     = 12
    XL     = 16
    PILL   = 999   # Fully rounded (pill shape)


class IconSize:
    SM   = 16
    MD   = 20
    LG   = 24
    XL   = 32


class Layout:
    # Window
    WINDOW_MIN_W  = 900
    WINDOW_MIN_H  = 620
    WINDOW_DEF_W  = 1100
    WINDOW_DEF_H  = 720

    # Sidebar
    SIDEBAR_W_COLLAPSED = 52
    SIDEBAR_W_EXPANDED  = 260

    # Nav buttons
    NAV_BTN_H     = 52
    NAV_BTN_ICON_W = 36

    # Upload FAB
    FAB_H         = 44
    FAB_MIN_W     = 130

    # Upload dialog
    DIALOG_W      = 480
    DIALOG_H      = 480

    # Link row
    LINK_ROW_H    = 44
    LINK_ICON_W   = 44

    # Files button
    FILES_BTN_H   = 44

    # Submit button
    SUBMIT_BTN_H  = 44
    SUBMIT_BTN_W  = 180

    # Add button
    ADD_BTN_SIZE  = 36

    # Scrollable link area max height
    LINKS_AREA_MAX_H = 220

    # Content area padding
    CONTENT_PAD  = 32
