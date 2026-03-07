"""
icon_loader.py — Loads icon files into QIcon / QPixmap objects.

Supports SVG and PNG. SVGs are rendered at the requested size so
they stay crisp on any DPI.

Usage:
    from icons.icon_loader import load_icon, load_pixmap
    btn.setIcon(load_icon(icons.MENU, size=22))
"""

from __future__ import annotations
from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer


def load_pixmap(path: str, size: int = 24) -> QPixmap:
    """
    Load an SVG or PNG file and return a QPixmap at the given pixel size.
    Falls back to a blank pixmap if the file is missing.
    """
    p = Path(path)
    if not p.exists():
        px = QPixmap(size, size)
        px.fill(Qt.GlobalColor.transparent)
        return px

    if p.suffix.lower() == ".svg":
        renderer = QSvgRenderer(str(p))
        px = QPixmap(size, size)
        px.fill(Qt.GlobalColor.transparent)
        painter = QPainter(px)
        renderer.render(painter)
        painter.end()
        return px
    else:
        # PNG / any raster format
        px = QPixmap(str(p))
        if px.isNull():
            px = QPixmap(size, size)
            px.fill(Qt.GlobalColor.transparent)
        else:
            px = px.scaled(
                size, size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        return px


def load_icon(path: str, size: int = 24) -> QIcon:
    """Return a QIcon from an SVG or PNG file."""
    return QIcon(load_pixmap(path, size))
