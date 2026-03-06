"""
typography.py — Font families, sizes, and weights for Personal Tutor
All typography values are defined here. Never hard-code fonts in UI files.
"""

from PySide6.QtGui import QFont


class FontFamily:
    PRIMARY   = "Segoe UI"       # Main UI font
    MONO      = "Consolas"       # Monospace (extracted text)
    FALLBACK  = "Arial"          # System fallback


class FontSize:
    # Points
    TINY      = 8
    SMALL     = 9
    BODY      = 10
    BODY_LG   = 11
    LABEL     = 12
    BUTTON    = 11
    HEADING_S = 13
    HEADING_M = 15
    HEADING_L = 18
    TITLE     = 22
    HERO      = 28


class FontWeight:
    THIN      = QFont.Weight.Thin
    LIGHT     = QFont.Weight.Light
    NORMAL    = QFont.Weight.Normal
    MEDIUM    = QFont.Weight.Medium
    SEMIBOLD  = QFont.Weight.DemiBold
    BOLD      = QFont.Weight.Bold
    EXTRABOLD = QFont.Weight.ExtraBold
    BLACK     = QFont.Weight.Black


class Fonts:
    """Pre-built QFont instances for common UI roles."""

    @staticmethod
    def nav_button() -> QFont:
        f = QFont(FontFamily.PRIMARY)
        f.setPointSize(FontSize.BUTTON)
        f.setWeight(FontWeight.BOLD)
        f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.5)
        return f

    @staticmethod
    def upload_button() -> QFont:
        f = QFont(FontFamily.PRIMARY)
        f.setPointSize(FontSize.LABEL)
        f.setWeight(FontWeight.SEMIBOLD)
        f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.2)
        return f

    @staticmethod
    def body() -> QFont:
        f = QFont(FontFamily.PRIMARY)
        f.setPointSize(FontSize.BODY)
        f.setWeight(FontWeight.NORMAL)
        return f

    @staticmethod
    def label() -> QFont:
        f = QFont(FontFamily.PRIMARY)
        f.setPointSize(FontSize.LABEL)
        f.setWeight(FontWeight.MEDIUM)
        return f

    @staticmethod
    def placeholder() -> QFont:
        f = QFont(FontFamily.PRIMARY)
        f.setPointSize(FontSize.BODY)
        f.setItalic(True)
        return f

    @staticmethod
    def mono() -> QFont:
        f = QFont(FontFamily.MONO)
        f.setPointSize(FontSize.BODY)
        f.setWeight(FontWeight.NORMAL)
        return f

    @staticmethod
    def heading() -> QFont:
        f = QFont(FontFamily.PRIMARY)
        f.setPointSize(FontSize.HEADING_M)
        f.setWeight(FontWeight.BOLD)
        return f
