#!/usr/bin/env python3

import sys, os
from pathlib import Path

try:
    import PyQt5

    _qt_plugins = Path(PyQt5.__file__).resolve().parent / "Qt5" / "plugins"
    if _qt_plugins.is_dir():
        os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", str(_qt_plugins))
except Exception:
    pass

import threading, time, math, json
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from dataclasses import dataclass
import numpy as np
import pandas as pd

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QLineEdit, QTextEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QFrame, QScrollArea, QSizePolicy,
    QProgressBar, QDialog, QStackedWidget, QGridLayout,
    QCheckBox, QSpinBox, QDoubleSpinBox, QSlider, QTabWidget, QMessageBox,
    QAbstractItemView, QGraphicsDropShadowEffect, QButtonGroup, QRadioButton,
    QGroupBox, QSplitter, QDateEdit, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QSize, QRect, QRectF,
    QPropertyAnimation, QEasingCurve, QPoint, QDate, QSettings, QPointF
)
from PyQt5.QtGui import (
    QColor, QFont, QIcon, QCursor, QPixmap, QImage, QBrush, QPalette,
    QLinearGradient, QPainter, QPen, QFontDatabase, QRadialGradient,
    QPolygonF, QConicalGradient, QPainterPath
)

import matplotlib
matplotlib.use("Qt5Agg")
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.ticker

try:
    import qtawesome as qta
    QTA_OK = True
except ImportError:
    QTA_OK = False

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

try:
    from brains import get_brain_v2
    BRAIN_AVAILABLE = True
except ImportError:
    BRAIN_AVAILABLE = False

try:
    from translator import install_translator
    TRANSLATOR_AVAILABLE = True
except ImportError:
    TRANSLATOR_AVAILABLE = False

try:
    from humanize import get_response as _humanize
    HUMANIZE_AVAILABLE = True
except ImportError:
    _humanize = lambda _: None
    HUMANIZE_AVAILABLE = False


BG        = "#070709"
SURFACE   = "#0d0d10"
SURFACE2  = "#121216"
SURFACE3  = "#18181d"
SURFACE4  = "#1e1e24"
ACCENT    = "#941107"
ACCENT2   = "#6b0d05"
ACCENT3   = "#bf1a0a"
GREEN     = "#22c55e"
RED       = "#ef4444"
YELLOW    = "#eab308"
BLUE      = "#3b82f6"
PURPLE    = "#8b5cf6"
TEAL      = "#14b8a6"
TEXT      = "#f2f2f4"
TEXT2     = "#acacb8"
TEXT3     = "#636375"
TEXT4     = "#3a3a48"
BORDER    = "#1e1e26"
BORDER2   = "#28282f"
BORDER3   = "#323240"

PALADIN_ICON_PATH = Path(__file__).resolve().parent / "DATABASE" / "Paladin_Icon.png"
_paladin_png_source: Optional[QPixmap] = None


def _knock_out_light_background(pm: QPixmap) -> QPixmap:
    """Remove near-white / low-saturation backdrop so the logo sits flush on dark UI."""
    img = pm.toImage().convertToFormat(QImage.Format_ARGB32)
    w, h = img.width(), img.height()
    for y in range(h):
        for x in range(w):
            c = QColor(img.pixel(x, y))
            a = c.alpha()
            if a == 0:
                continue
            r, g, b = c.red(), c.green(), c.blue()
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            mx, mn = max(r, g, b), min(r, g, b)
            sat = (mx - mn) / max(float(mx), 1e-3)
            if lum > 158 and sat < 0.32:
                t = (lum - 158) / 97.0
                t = max(0.0, min(1.0, t))
                fade = t * t
                c.setAlpha(int(a * (1.0 - fade)))
            img.setPixelColor(x, y, c)
    out = QPixmap.fromImage(img)
    return out if not out.isNull() else pm


def _paladin_png() -> Optional[QPixmap]:
    global _paladin_png_source
    if _paladin_png_source is not None:
        return _paladin_png_source if not _paladin_png_source.isNull() else None
    if not PALADIN_ICON_PATH.is_file():
        return None
    pm = QPixmap(str(PALADIN_ICON_PATH))
    if pm.isNull():
        return None
    _paladin_png_source = _knock_out_light_background(pm)
    return _paladin_png_source


SERIF_FONT = "Georgia"
MONO_FONT  = "Consolas"
BODY_FONT  = "Georgia"

CHESS_PIECES = {
    "king":   {"icon": "fa5s.chess-king",   "emoji": "♔", "traits": "Strategic Leader",   "description": "Make bold, decisive moves that dominate the market with conviction"},
    "queen":  {"icon": "fa5s.chess-queen",  "emoji": "♕", "traits": "Versatile Master",   "description": "Command ultimate flexibility across all trading strategies"},
    "rook":   {"icon": "fa5s.chess-rook",   "emoji": "♖", "traits": "Straight Shooter",   "description": "Direct, powerful, and relentlessly reliable — hold the line"},
    "bishop": {"icon": "fa5s.chess-bishop", "emoji": "♗", "traits": "Diagonal Thinker",   "description": "See angles and opportunities the market hasn't priced in yet"},
    "knight": {"icon": "fa5s.chess-knight", "emoji": "♘", "traits": "Unconventional",     "description": "Leap over noise and land unexpected winning positions"},
    "pawn":   {"icon": "fa5s.chess-pawn",   "emoji": "♙", "traits": "Patient Builder",    "description": "Steady compounding gains that silently accumulate over time"},
}


def chess_icon_pixmap(piece_key: str, size: int = 44, color: Optional[str] = None):
    """Font Awesome solid chess piece icon as pixmap (qtawesome); None if unavailable."""
    if not QTA_OK or piece_key not in CHESS_PIECES:
        return None
    spec = CHESS_PIECES[piece_key].get("icon")
    if not spec:
        return None
    try:
        pm = qta.icon(spec, color=color or ACCENT).pixmap(QSize(size, size))
        return pm if pm is not None and not pm.isNull() else None
    except Exception:
        return None

INTERVAL_MAP = {
    "1m":  ("1d",  "1m"),
    "5m":  ("5d",  "5m"),
    "15m": ("5d",  "15m"),
    "1h":  ("60d", "1h"),
    "1d":  ("1y",  "1d"),
    "1wk": ("5y",  "1wk"),
}

SYMBOL_ALIAS = {
    "XAUUSD": "GC=F",
    "XAGUSD": "SI=F",
    "BTCUSD": "BTC-USD",
    "ETHUSD": "ETH-USD",
    "SOLUSD": "SOL-USD",
    "DOGEUSD":"DOGE-USD",
    "BNBUSD": "BNB-USD",
}

def resolve_symbol(symbol: str) -> str:
    return SYMBOL_ALIAS.get(symbol, symbol)

WATCHLIST_SYMBOLS = [
    "AAPL","MSFT","GOOGL","TSLA","NVDA","AMZN","META","NFLX",
    "JPM","V","SPY","QQQ","DIA","IWM","VTI","VOO",
    "XLK","XLF","XLE","XLV","BTC-USD","ETH-USD",
    "GC=F","CL=F","EURUSD=X","GBPUSD=X",
    "SPCE","IONQ","ARKG","ARKK","SOXL","TQQQ","SQQQ","UVXY","VXX","GLD",
]

LOW_VOL_SYMBOLS = [
    "JNJ","PG","KO","PEP","WMT","MCD","MMM","ABT","TMO","DHR",
    "UNH","CVS","LLY","MRK","PFE","ABBV","BMY","AMGN","GILD","BIIB",
    "VZ","T","TMUS","SO","DUK","NEE","AEP","D","EXC","SRE",
    "GLD","SLV","TLT","IEF","AGG","BND","VNQ","O","SPG","PSA",
]
MED_VOL_SYMBOLS = [
    "AAPL","MSFT","GOOGL","AMZN","META","NVDA","NFLX","TSLA","JPM","V",
    "MA","BAC","WFC","GS","MS","BLK","SCHW","AXP","C","USB",
    "XOM","CVX","COP","EOG","SLB","HAL","OXY","MPC","PSX","VLO",
    "INTC","AMD","QCOM","TXN","AVGO","MU","AMAT","LRCX","KLAC","ASML",
    "SPY","QQQ","DIA","IWM","VTI","VOO","XLK","XLF","XLE","XLV",
]
HIGH_VOL_SYMBOLS = [
    "TSLA","NVDA","AMD","MSTR","COIN","HOOD","RBLX","SNAP","UBER","LYFT",
    "PLTR","SOFI","RIVN","LCID","NIO","XPEV","LI","DKNG","PENN","WYNN",
    "BTC-USD","ETH-USD","GC=F","SI=F","CL=F","EURUSD=X","GBPUSD=X",
    "SPCE","IONQ","ARKG","ARKK","SOXL","TQQQ","SQQQ","UVXY","VXX",
]

ALL_SYMBOLS = sorted(set(WATCHLIST_SYMBOLS + LOW_VOL_SYMBOLS + MED_VOL_SYMBOLS + HIGH_VOL_SYMBOLS))
SYMBOL_VOLATILITY = {}
for _s in LOW_VOL_SYMBOLS:  SYMBOL_VOLATILITY[_s] = "Low"
for _s in MED_VOL_SYMBOLS:  SYMBOL_VOLATILITY[_s] = "Medium"
for _s in HIGH_VOL_SYMBOLS: SYMBOL_VOLATILITY[_s] = "High"


GLOBAL_QSS = f"""
QMainWindow, QDialog, QWidget {{
    background-color: {BG};
    color: {TEXT};
    font-family: '{BODY_FONT}', serif;
    font-size: 13px;
}}
QFrame {{ border: none; background: transparent; }}
QScrollBar:vertical {{
    background: {SURFACE};
    width: 4px;
    border: none;
}}
QScrollBar::handle:vertical {{
    background: {ACCENT2};
    border-radius: 2px;
    min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
QScrollBar:horizontal {{
    background: {SURFACE};
    height: 4px;
    border: none;
}}
QScrollBar::handle:horizontal {{
    background: {ACCENT2};
    border-radius: 2px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0px; }}
QComboBox {{
    background: {SURFACE3};
    color: {TEXT};
    border: 1px solid {BORDER2};
    padding: 5px 8px;
    font-family: '{MONO_FONT}';
    font-size: 12px;
}}
QComboBox::drop-down {{ border: none; width: 20px; }}
QComboBox QAbstractItemView {{
    background: {SURFACE2};
    color: {TEXT};
    border: 1px solid {BORDER2};
    selection-background-color: {ACCENT};
}}
QLineEdit {{
    background: {SURFACE3};
    color: {TEXT};
    border: 1px solid {BORDER2};
    padding: 7px 10px;
    font-family: '{BODY_FONT}';
    font-size: 13px;
}}
QLineEdit:focus {{ border-color: {ACCENT}; }}
QCheckBox {{ color: {TEXT2}; spacing: 8px; font-family: '{MONO_FONT}'; font-size: 11px; }}
QCheckBox::indicator {{
    width: 14px; height: 14px;
    border: 1px solid {BORDER2};
    background: {SURFACE3};
}}
QCheckBox::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; }}
QRadioButton {{ color: {TEXT2}; spacing: 8px; font-family: '{MONO_FONT}'; font-size: 11px; }}
QRadioButton::indicator {{
    width: 14px; height: 14px;
    border: 1px solid {BORDER2};
    background: {SURFACE3};
    border-radius: 7px;
}}
QRadioButton::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; }}
QTableWidget {{
    background: {SURFACE};
    color: {TEXT2};
    border: 1px solid {BORDER};
    gridline-color: {BORDER};
    font-size: 12px;
    font-family: '{MONO_FONT}';
}}
QTableWidget::item {{ padding: 6px 10px; border: none; }}
QTableWidget::item:selected {{ background: {SURFACE2}; color: {TEXT}; }}
QHeaderView::section {{
    background: {SURFACE2};
    color: {TEXT3};
    padding: 5px 10px;
    border: none;
    border-bottom: 1px solid {BORDER};
    font-family: '{MONO_FONT}';
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-weight: bold;
}}
QTextEdit {{
    background: {SURFACE3};
    color: {TEXT2};
    border: 1px solid {BORDER};
    padding: 8px;
    font-size: 12px;
    line-height: 1.6;
}}
QProgressBar {{
    background: {BORDER2};
    border: none;
    border-radius: 1px;
    height: 2px;
}}
QProgressBar::chunk {{
    background: {ACCENT};
    border-radius: 1px;
}}
QToolTip {{
    background: {SURFACE2};
    color: {TEXT};
    border: 1px solid {BORDER2};
    padding: 4px 8px;
    font-size: 12px;
}}
QSplitter::handle {{ background: {BORDER}; width: 1px; height: 1px; }}
QGroupBox {{
    border: 1px solid {BORDER2};
    margin-top: 8px;
    padding-top: 8px;
    color: {TEXT3};
    font-family: '{MONO_FONT}';
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 1px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    color: {TEXT3};
}}
QDateEdit {{
    background: {SURFACE3};
    color: {TEXT};
    border: 1px solid {BORDER2};
    padding: 5px 8px;
    font-family: '{MONO_FONT}';
    font-size: 12px;
}}
QListWidget {{
    background: {SURFACE};
    color: {TEXT2};
    border: 1px solid {BORDER};
    font-family: '{MONO_FONT}';
    font-size: 12px;
}}
QListWidget::item {{ padding: 6px 10px; border-bottom: 1px solid {BORDER}; }}
QListWidget::item:selected {{ background: {SURFACE2}; color: {TEXT}; }}
QListWidget::item:hover {{ background: {SURFACE2}; }}
QTabWidget::pane {{
    border: 1px solid {BORDER};
    background: {BG};
}}
QTabBar::tab {{
    background: {SURFACE};
    color: {TEXT3};
    border: 1px solid {BORDER};
    border-bottom: none;
    padding: 6px 16px;
    font-family: '{MONO_FONT}';
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background: {BG};
    color: {TEXT};
    border-color: {BORDER2};
    border-bottom: 2px solid {ACCENT};
}}
QTabBar::tab:hover {{ background: {SURFACE2}; color: {TEXT}; }}
QDoubleSpinBox, QSpinBox {{
    background: {SURFACE3};
    color: {TEXT};
    border: 1px solid {BORDER2};
    padding: 5px 8px;
    font-family: '{MONO_FONT}';
    font-size: 12px;
}}
"""


def make_btn_primary(text, parent=None):
    btn = QPushButton(text, parent)
    btn.setStyleSheet(f"""
        QPushButton {{
            background: {ACCENT};
            color: #ffffff;
            border: none;
            padding: 9px 20px;
            font-family: '{SERIF_FONT}';
            font-weight: bold;
            font-size: 12px;
            letter-spacing: 1px;
        }}
        QPushButton:hover {{ background: {ACCENT3}; }}
        QPushButton:disabled {{ background: {SURFACE3}; color: {TEXT3}; }}
    """)
    btn.setCursor(QCursor(Qt.PointingHandCursor))
    return btn


def make_btn_secondary(text, parent=None):
    btn = QPushButton(text, parent)
    btn.setStyleSheet(f"""
        QPushButton {{
            background: transparent;
            color: {TEXT2};
            border: 1px solid {BORDER2};
            padding: 8px 16px;
            font-family: '{SERIF_FONT}';
            font-size: 12px;
        }}
        QPushButton:hover {{ border-color: {ACCENT}; color: {TEXT}; }}
    """)
    btn.setCursor(QCursor(Qt.PointingHandCursor))
    return btn


def make_btn_ghost(text, parent=None):
    btn = QPushButton(text, parent)
    btn.setStyleSheet(f"""
        QPushButton {{
            background: transparent;
            color: {TEXT3};
            border: none;
            padding: 6px 10px;
            font-family: '{MONO_FONT}';
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        QPushButton:hover {{ color: {TEXT}; background: {SURFACE2}; }}
    """)
    btn.setCursor(QCursor(Qt.PointingHandCursor))
    return btn


def make_chart_btn(text, parent=None):
    btn = QPushButton(text, parent)
    btn.setStyleSheet(f"""
        QPushButton {{
            background: {SURFACE};
            color: {TEXT2};
            border: 1px solid {BORDER};
            padding: 3px 9px;
            font-family: '{MONO_FONT}';
            font-size: 11px;
        }}
        QPushButton:hover, QPushButton:checked {{
            background: {ACCENT};
            color: #ffffff;
            border-color: {ACCENT};
        }}
    """)
    btn.setCheckable(True)
    btn.setCursor(QCursor(Qt.PointingHandCursor))
    return btn


def make_label_section(text):
    lbl = QLabel(text)
    lbl.setStyleSheet(f"""
        color: {TEXT3};
        font-family: '{MONO_FONT}';
        font-size: 9px;
        text-transform: uppercase;
        letter-spacing: 2px;
        padding: 10px 14px 4px 14px;
    """)
    return lbl


def make_card(accent_color=None):
    frame = QFrame()
    border_left = f"border-left: 2px solid {accent_color};" if accent_color else ""
    frame.setStyleSheet(f"""
        QFrame {{
            background: {SURFACE};
            border: 1px solid {BORDER};
            {border_left}
        }}
    """)
    return frame


def make_separator():
    sep = QFrame()
    sep.setFixedHeight(1)
    sep.setStyleSheet(f"QFrame {{ background: {BORDER}; }}")
    return sep


def make_mono_label(text, color=None, size=10):
    lbl = QLabel(text)
    lbl.setFont(QFont(MONO_FONT, size))
    c = color or TEXT3
    lbl.setStyleSheet(f"color: {c}; background: transparent; border: none; text-transform: uppercase; letter-spacing: 1px;")
    return lbl


def make_value_label(text, color=None, size=12):
    lbl = QLabel(text)
    lbl.setFont(QFont(MONO_FONT, size))
    c = color or TEXT
    lbl.setStyleSheet(f"color: {c}; background: transparent; border: none;")
    return lbl


def _qta_icon(name, fallback=""):
    if QTA_OK:
        try:
            return qta.icon(name, color=TEXT3)
        except Exception:
            pass
    return QIcon()



class PaladinIcon(QWidget):
    def __init__(self, size=64, parent=None):
        super().__init__(parent)
        self._size = size
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(size, size)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        s = float(self._size)
        cx = s / 2.0
        cy = s / 2.0
        r = s / 2.0 - 1.0
        src = _paladin_png()
        if src is not None:
            side = int(s * 0.98)
            scaled = src.scaled(side, side, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            x = (s - scaled.width()) / 2.0
            y = (s - scaled.height()) / 2.0
            p.drawPixmap(int(round(x)), int(round(y)), scaled)
        else:
            p.setBrush(QColor(ACCENT))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QPointF(cx, cy), r * 0.88, r * 0.88)
        p.end()

class AnimatedProgressBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0.0
        self._glow_phase = 0.0
        self.setFixedHeight(3)

        self._glow_timer = QTimer(self)
        self._glow_timer.timeout.connect(self._tick_glow)
        self._glow_timer.start(40)

    def _tick_glow(self):
        self._glow_phase += 0.08
        self.update()

    def set_value(self, v):
        self._value = max(0.0, min(100.0, v))
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        p.setPen(Qt.NoPen)
        p.setBrush(QColor(BORDER2))
        p.drawRoundedRect(0, 0, w, h, 1, 1)

        fill_w = int(w * self._value / 100.0)
        if fill_w > 2:
            glow_shift = int(fill_w * 0.3 * (0.5 + 0.5 * math.sin(self._glow_phase)))
            grad = QLinearGradient(glow_shift, 0, fill_w, 0)
            grad.setColorAt(0.0, QColor(107, 13, 5))
            grad.setColorAt(0.5, QColor(191, 26, 10))
            grad.setColorAt(1.0, QColor(148, 17, 7))
            p.setBrush(QBrush(grad))
            p.drawRoundedRect(0, 0, fill_w, h, 1, 1)

        p.end()


class WelcomeScreen(QWidget):
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SplashScreen)
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        self._progress_value = 0
        self._opacity = 0.0
        self._star_phase = 0.0
        self._stars = [(
            (i * 137.508 % 1.0) * screen.width(),
            (i * 97.333 % 1.0) * screen.height(),
            (i * 53.17 % 1.0) * 1.4 + 0.4,
            (i * 0.31 % 1.0) * math.pi * 2
        ) for i in range(120)]

        self._init_ui()
        self._start_animations()

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self._bg = QFrame()
        self._bg.setStyleSheet(f"QFrame {{ background: {BG}; }}")
        root.addWidget(self._bg)

        center = QVBoxLayout(self._bg)
        center.setAlignment(Qt.AlignCenter)
        center.setSpacing(0)

        self._inner = QWidget()
        self._inner.setFixedWidth(480)
        inner_ly = QVBoxLayout(self._inner)
        inner_ly.setAlignment(Qt.AlignCenter)
        inner_ly.setSpacing(0)
        inner_ly.setContentsMargins(24, 0, 24, 0)

        self._icon = PaladinIcon(size=88)
        icon_wrapper = QHBoxLayout()
        icon_wrapper.setAlignment(Qt.AlignCenter)
        icon_wrapper.addWidget(self._icon)
        inner_ly.addLayout(icon_wrapper)

        inner_ly.addSpacing(20)

        self._logo_lbl = QLabel("PALADIN")
        self._logo_lbl.setFont(QFont(SERIF_FONT, 48, QFont.Bold))
        self._logo_lbl.setStyleSheet(f"color: {ACCENT}; letter-spacing: 8px;")
        self._logo_lbl.setAlignment(Qt.AlignCenter)
        inner_ly.addWidget(self._logo_lbl)

        tagline = QLabel("AI — Powered Trading Intelligence")
        tagline.setFont(QFont(BODY_FONT, 12))
        tagline.setStyleSheet(f"color: {TEXT3}; font-style: italic; margin-bottom: 0px; letter-spacing: 1px;")
        tagline.setAlignment(Qt.AlignCenter)
        inner_ly.addWidget(tagline)

        inner_ly.addSpacing(8)

        oneliner = QLabel("Know the move before the market makes it.")
        oneliner.setFont(QFont(MONO_FONT, 9))
        oneliner.setStyleSheet(f"color: {TEXT4}; letter-spacing: 2px;")
        oneliner.setAlignment(Qt.AlignCenter)
        inner_ly.addWidget(oneliner)

        inner_ly.addSpacing(36)

        self._progress_bar = AnimatedProgressBar()
        inner_ly.addWidget(self._progress_bar)

        inner_ly.addSpacing(10)

        self._status_lbl = QLabel("Initialising engine…")
        self._status_lbl.setFont(QFont(MONO_FONT, 10))
        self._status_lbl.setStyleSheet(f"color: {TEXT3};")
        self._status_lbl.setAlignment(Qt.AlignLeft)
        inner_ly.addWidget(self._status_lbl)

        inner_ly.addSpacing(24)

        tech_lbl = QLabel("LightGBM  ·  isotonic calibration  ·  50+ technical features  ·  pattern recognition")
        tech_lbl.setFont(QFont(MONO_FONT, 9))
        tech_lbl.setStyleSheet(f"color: {TEXT4}; letter-spacing: 1px;")
        tech_lbl.setAlignment(Qt.AlignCenter)
        inner_ly.addWidget(tech_lbl)

        center.addWidget(self._inner)

        self.setWindowOpacity(0.0)

    def _start_animations(self):
        self._fade_timer = QTimer()
        self._fade_timer.timeout.connect(self._tick_fade)
        self._fade_timer.start(16)

        self._star_timer = QTimer()
        self._star_timer.timeout.connect(self._tick_stars)
        self._star_timer.start(50)

    def _tick_fade(self):
        if self._opacity < 1.0:
            self._opacity = min(1.0, self._opacity + 0.022)
            self.setWindowOpacity(self._opacity)
            if self._opacity >= 1.0:
                self._fade_timer.stop()

    def _tick_stars(self):
        self._star_phase += 0.03
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        for x, y, r, phase in self._stars:
            a = int(30 + 22 * math.sin(self._star_phase + phase))
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(148, 17, 7, a))
            p.drawEllipse(QPointF(x, y), r, r)
        p.end()

    def update_progress(self, value, message=""):
        self._progress_value = value
        self._progress_bar.set_value(value)
        if message:
            self._status_lbl.setText(message)
        QApplication.processEvents()
        if value >= 100:
            QTimer.singleShot(820, self.finished.emit)


class PieceCard(QFrame):
    clicked_piece = pyqtSignal(str)

    def __init__(self, piece, selected=False, parent=None):
        super().__init__(parent)
        self.piece = piece
        self._selected = selected
        self.setFixedSize(220, 176)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self._apply_style(selected)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 14)
        layout.setSpacing(5)

        icon_lbl = QLabel()
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet("background: transparent; border: none;")
        pm = chess_icon_pixmap(piece, 48, ACCENT)
        if pm is not None:
            icon_lbl.setPixmap(pm)
        else:
            icon_lbl.setText(CHESS_PIECES[piece]["emoji"])
            icon_lbl.setFont(QFont("Segoe UI Emoji", 34))
        layout.addWidget(icon_lbl)

        name_lbl = QLabel(piece.upper())
        name_lbl.setFont(QFont(SERIF_FONT, 12, QFont.Bold))
        name_lbl.setAlignment(Qt.AlignCenter)
        name_lbl.setStyleSheet(f"color: {ACCENT}; background: transparent; border: none; letter-spacing: 3px;")
        layout.addWidget(name_lbl)

        traits_lbl = QLabel(CHESS_PIECES[piece]["traits"])
        traits_lbl.setFont(QFont(BODY_FONT, 10))
        traits_lbl.setAlignment(Qt.AlignCenter)
        traits_lbl.setStyleSheet(f"color: {TEXT2}; background: transparent; border: none;")
        layout.addWidget(traits_lbl)

        desc_lbl = QLabel(CHESS_PIECES[piece]["description"])
        desc_lbl.setFont(QFont(BODY_FONT, 9))
        desc_lbl.setAlignment(Qt.AlignCenter)
        desc_lbl.setStyleSheet(f"color: {TEXT3}; background: transparent; border: none;")
        desc_lbl.setWordWrap(True)
        layout.addWidget(desc_lbl)

    def _apply_style(self, selected):
        border_color = ACCENT if selected else BORDER2
        bg = SURFACE2 if selected else SURFACE
        glow = f"border: 1px solid {ACCENT};" if selected else f"border: 1px solid {BORDER2};"
        self.setStyleSheet(f"""
            QFrame {{ background: {bg}; {glow} }}
            QFrame:hover {{ background: {SURFACE2}; border: 1px solid {ACCENT}; }}
        """)

    def set_selected(self, val):
        self._selected = val
        self._apply_style(val)

    def mousePressEvent(self, event):
        self.clicked_piece.emit(self.piece)


class TutorialCard(QWidget):
    def __init__(self, step_num, total, title, body_lines, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background: {SURFACE2}; border: 1px solid {BORDER2};")
        ly = QVBoxLayout(self)
        ly.setContentsMargins(28, 24, 28, 24)
        ly.setSpacing(12)

        step_lbl = QLabel(f"STEP {step_num:02d} / {total:02d}")
        step_lbl.setFont(QFont(MONO_FONT, 10))
        step_lbl.setStyleSheet(f"color: {ACCENT}; text-transform: uppercase; letter-spacing: 3px; background: transparent;")
        ly.addWidget(step_lbl)

        title_lbl = QLabel(title)
        title_lbl.setFont(QFont(SERIF_FONT, 20, QFont.Bold))
        title_lbl.setStyleSheet(f"color: {TEXT}; background: transparent;")
        ly.addWidget(title_lbl)

        ly.addWidget(make_separator())

        for line in body_lines:
            row = QHBoxLayout()
            row.setSpacing(10)
            bullet = QLabel("▸")
            bullet.setFixedWidth(16)
            bullet.setStyleSheet(f"color: {ACCENT}; background: transparent; font-size: 13px;")
            txt = QLabel(line)
            txt.setFont(QFont(BODY_FONT, 11))
            txt.setStyleSheet(f"color: {TEXT2}; background: transparent;")
            txt.setWordWrap(True)
            row.addWidget(bullet, 0, Qt.AlignTop)
            row.addWidget(txt, 1)
            container = QWidget()
            container.setStyleSheet("background: transparent;")
            container.setLayout(row)
            ly.addWidget(container)


TUTORIAL_CONTENT = [
    ("Welcome to Paladin", [
        "Paladin is a professional AI trading platform combining machine learning and market intelligence.",
        "Live charts with SMA 20/50/200, Bollinger Bands, RSI and MACD sub-charts.",
        "AI signals: BUY / SELL / HOLD with auto-calculated stop-loss and take-profit.",
        "Multi-symbol scanner, portfolio tracker, trade journal, and risk calculator.",
    ]),
    ("Reading the Signal", [
        "Every signal shows direction, confidence %, entry, stop-loss, and take-profit.",
        "Confidence above 65% — high conviction. Below 50% — stay out.",
        "Regime badges show market structure: BULL TREND, BEAR TREND, COMPRESSION, RANGING.",
        "Divergence and volatility badges provide additional confluence context.",
    ]),
    ("Chart Navigation", [
        "Scroll wheel to zoom in/out. Middle-click or double-click to reset view.",
        "Arrow keys (← →) pan the chart left and right.",
        "Toggle SMA 20/50/200, Bollinger Bands, Volume, RSI and MACD via checkboxes.",
        "Press 'R' inside the chart to reset zoom to full history.",
    ]),
    ("Risk & Portfolio", [
        "Risk Calculator: enter capital, risk %, entry/SL/TP to get position size and expected value.",
        "Portfolio tracker shows real-time P&L on open positions — refresh prices anytime.",
        "Trade Journal logs every trade with notes, tags, and performance analytics.",
        "Never risk more than 1–2% of account capital per trade.",
    ]),
    ("AI Analyst Chat", [
        "Ask the AI analyst anything — entry strategy, risk, regime, or trade analysis.",
        "Quick buttons: Analyse current signal · Key risks · Entry strategy · Market regime.",
        "The analyst always references the latest signal for your active symbol.",
        "All responses are grounded in your current symbol and selected timeframe.",
    ]),
]


class SetupWizard(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setModal(True)
        self.setMinimumSize(760, 520)
        screen = QApplication.primaryScreen().geometry()
        w, h = 1060, 720
        self.setGeometry(
            screen.x() + (screen.width() - w) // 2,
            screen.y() + (screen.height() - h) // 2,
            w, h
        )
        self.setStyleSheet(f"QDialog {{ background: {BG}; border: 1px solid {BORDER2}; }}")
        self.selected_piece = None
        self._piece_cards = {}
        self._current_step = 0
        self._tut_step = 0
        self._drag_pos = None
        self._resize_margin = 8
        self._resizing = False
        self._resize_edge = None
        self.setMouseTracking(True)
        self._init_ui()

    def _is_on_titlebar(self, pos):
        """Returns True if pos is inside the top-bar area."""
        return pos.y() < 64

    def _resize_edge_at(self, pos):
        """Returns a string like 'bottom-right', 'right', etc., or None."""
        m = self._resize_margin
        w, h = self.width(), self.height()
        x, y = pos.x(), pos.y()
        right  = x >= w - m
        bottom = y >= h - m
        left   = x <= m
        top    = y <= m and not self._is_on_titlebar(pos)
        if bottom and right:  return "bottom-right"
        if bottom and left:   return "bottom-left"
        if top    and right:  return "top-right"
        if top    and left:   return "top-left"
        if right:             return "right"
        if bottom:            return "bottom"
        if left:              return "left"
        return None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            edge = self._resize_edge_at(event.pos())
            if edge:
                self._resizing    = True
                self._resize_edge = edge
                self._drag_pos    = event.globalPos()
                self._drag_geom   = self.geometry()
            elif self._is_on_titlebar(event.pos()):
                self._drag_pos  = event.globalPos() - self.frameGeometry().topLeft()
                self._resizing  = False

    def mouseMoveEvent(self, event):
        if self._resizing and self._drag_pos:
            delta = event.globalPos() - self._drag_pos
            geo   = self._drag_geom
            edge  = self._resize_edge
            x, y, w, h = geo.x(), geo.y(), geo.width(), geo.height()
            min_w, min_h = self.minimumWidth(), self.minimumHeight()
            if "right"  in edge: w = max(min_w, geo.width()  + delta.x())
            if "bottom" in edge: h = max(min_h, geo.height() + delta.y())
            if "left"   in edge:
                w = max(min_w, geo.width()  - delta.x())
                x = geo.x() + (geo.width() - w)
            if "top"    in edge:
                h = max(min_h, geo.height() - delta.y())
                y = geo.y() + (geo.height() - h)
            self.setGeometry(x, y, w, h)
        elif not self._resizing and self._drag_pos and (event.buttons() & Qt.LeftButton):
            self.move(event.globalPos() - self._drag_pos)
        else:
            edge = self._resize_edge_at(event.pos())
            cursors = {
                "bottom-right": Qt.SizeFDiagCursor, "top-left":    Qt.SizeFDiagCursor,
                "bottom-left":  Qt.SizeBDiagCursor, "top-right":   Qt.SizeBDiagCursor,
                "right": Qt.SizeHorCursor, "left": Qt.SizeHorCursor,
                "bottom": Qt.SizeVerCursor, "top": Qt.SizeVerCursor,
            }
            self.setCursor(QCursor(cursors.get(edge, Qt.ArrowCursor)))

    def mouseReleaseEvent(self, event):
        self._drag_pos    = None
        self._resizing    = False
        self._resize_edge = None
        self.setCursor(QCursor(Qt.ArrowCursor))

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        topbar = QFrame()
        topbar.setFixedHeight(60)
        topbar.setStyleSheet(f"QFrame {{ background: {SURFACE}; border-bottom: 1px solid {BORDER}; }}")
        tb = QHBoxLayout(topbar)
        tb.setContentsMargins(24, 0, 24, 0)
        tb.setSpacing(12)

        icon = PaladinIcon(size=36)
        tb.addWidget(icon)

        logo = QLabel("PALADIN")
        logo.setFont(QFont(SERIF_FONT, 15, QFont.Bold))
        logo.setStyleSheet(f"color: {ACCENT}; letter-spacing: 4px; background: transparent;")
        tb.addWidget(logo)

        sub = QLabel("Setup Wizard")
        sub.setFont(QFont(MONO_FONT, 10))
        sub.setStyleSheet(f"color: {TEXT3}; letter-spacing: 2px; background: transparent;")
        tb.addWidget(sub)
        tb.addStretch()

        self._step_indicator = QLabel("1 / 3")
        self._step_indicator.setFont(QFont(MONO_FONT, 10))
        self._step_indicator.setStyleSheet(f"color: {TEXT3}; background: transparent;")
        tb.addWidget(self._step_indicator)
        root.addWidget(topbar)

        self._prog_bar = AnimatedProgressBar()
        root.addWidget(self._prog_bar)

        self._stack = QStackedWidget()
        root.addWidget(self._stack, 1)

        self._stack.addWidget(self._build_step_piece())
        self._stack.addWidget(self._build_step_tutorial())
        self._stack.addWidget(self._build_step_confirm())

        bottom = QFrame()
        bottom.setFixedHeight(64)
        bottom.setStyleSheet(f"QFrame {{ background: {SURFACE}; border-top: 1px solid {BORDER}; }}")
        bb = QHBoxLayout(bottom)
        bb.setContentsMargins(28, 0, 28, 0)
        bb.setSpacing(10)

        self._status_lbl = QLabel("Select your trading archetype to continue")
        self._status_lbl.setFont(QFont(MONO_FONT, 10))
        self._status_lbl.setStyleSheet(f"color: {YELLOW}; background: transparent;")
        bb.addWidget(self._status_lbl)
        bb.addStretch()

        self._back_btn = make_btn_secondary("← Back")
        self._back_btn.setVisible(False)
        self._back_btn.clicked.connect(self._go_back)
        bb.addWidget(self._back_btn)

        self._next_btn = make_btn_primary("Next →")
        self._next_btn.setEnabled(False)
        self._next_btn.clicked.connect(self._go_next)
        bb.addWidget(self._next_btn)
        root.addWidget(bottom)

        self._update_progress()

    def _build_step_piece(self):
        page = QWidget()
        page.setStyleSheet(f"QWidget {{ background: {BG}; }}")
        ly = QVBoxLayout(page)
        ly.setContentsMargins(44, 36, 44, 28)
        ly.setSpacing(20)

        step_tag = QLabel("STEP 01 / 03  —  CHOOSE YOUR ARCHETYPE")
        step_tag.setFont(QFont(MONO_FONT, 10))
        step_tag.setStyleSheet(f"color: {ACCENT}; letter-spacing: 3px; background: transparent;")
        ly.addWidget(step_tag)

        title = QLabel("Select Your Trading Personality")
        title.setFont(QFont(SERIF_FONT, 26, QFont.Bold))
        title.setStyleSheet(f"color: {TEXT}; background: transparent;")
        ly.addWidget(title)

        desc = QLabel("Each chess piece represents a distinct trading archetype. Your choice configures the platform and shapes your default strategy.")
        desc.setFont(QFont(BODY_FONT, 12))
        desc.setStyleSheet(f"color: {TEXT3}; font-style: italic; background: transparent;")
        desc.setWordWrap(True)
        ly.addWidget(desc)

        ly.addSpacing(8)

        grid_w = QWidget()
        grid_w.setStyleSheet("background: transparent;")
        grid = QGridLayout(grid_w)
        grid.setSpacing(14)
        grid.setContentsMargins(0, 0, 0, 0)

        for idx, piece in enumerate(CHESS_PIECES.keys()):
            card = PieceCard(piece)
            card.clicked_piece.connect(self._on_piece_clicked)
            self._piece_cards[piece] = card
            grid.addWidget(card, idx // 3, idx % 3)

        ly.addWidget(grid_w)
        ly.addStretch()
        return page

    def _build_step_tutorial(self):
        page = QWidget()
        page.setStyleSheet(f"QWidget {{ background: {BG}; }}")
        ly = QVBoxLayout(page)
        ly.setContentsMargins(44, 36, 44, 28)
        ly.setSpacing(16)

        step_tag = QLabel("STEP 02 / 03  —  PLATFORM GUIDE")
        step_tag.setFont(QFont(MONO_FONT, 10))
        step_tag.setStyleSheet(f"color: {ACCENT}; letter-spacing: 3px; background: transparent;")
        ly.addWidget(step_tag)

        title = QLabel("Interactive Platform Tutorial")
        title.setFont(QFont(SERIF_FONT, 26, QFont.Bold))
        title.setStyleSheet(f"color: {TEXT}; background: transparent;")
        ly.addWidget(title)

        dot_row = QHBoxLayout()
        dot_row.setSpacing(8)
        self._tut_dots = []
        for i in range(len(TUTORIAL_CONTENT)):
            dot = QLabel("●")
            dot.setFont(QFont(MONO_FONT, 8))
            dot.setStyleSheet(f"color: {ACCENT if i == 0 else TEXT4}; background: transparent;")
            self._tut_dots.append(dot)
            dot_row.addWidget(dot)
        dot_row.addStretch()
        ly.addLayout(dot_row)

        self._tut_stack = QStackedWidget()
        for idx, (title_t, lines) in enumerate(TUTORIAL_CONTENT):
            card = TutorialCard(idx + 1, len(TUTORIAL_CONTENT), title_t, lines)
            self._tut_stack.addWidget(card)
        ly.addWidget(self._tut_stack, 1)

        nav_row = QHBoxLayout()
        nav_row.setSpacing(10)
        prev_btn = make_btn_secondary("← Prev")
        prev_btn.clicked.connect(self._tut_prev)
        next_btn = make_btn_secondary("Next →")
        next_btn.clicked.connect(self._tut_next)
        nav_row.addWidget(prev_btn)
        nav_row.addWidget(next_btn)
        nav_row.addStretch()
        ly.addLayout(nav_row)
        return page

    def _build_step_confirm(self):
        page = QWidget()
        page.setStyleSheet(f"QWidget {{ background: {BG}; }}")
        ly = QVBoxLayout(page)
        ly.setContentsMargins(44, 36, 44, 28)
        ly.setSpacing(20)

        step_tag = QLabel("STEP 03 / 03  —  CONFIRM & LAUNCH")
        step_tag.setFont(QFont(MONO_FONT, 10))
        step_tag.setStyleSheet(f"color: {ACCENT}; letter-spacing: 3px; background: transparent;")
        ly.addWidget(step_tag)

        title = QLabel("Ready to Begin")
        title.setFont(QFont(SERIF_FONT, 26, QFont.Bold))
        title.setStyleSheet(f"color: {TEXT}; background: transparent;")
        ly.addWidget(title)

        self._summary_card = make_card(ACCENT)
        sum_ly = QVBoxLayout(self._summary_card)
        sum_ly.setContentsMargins(24, 22, 24, 22)
        sum_ly.setSpacing(16)

        piece_row = QHBoxLayout()
        piece_row.setSpacing(20)

        icon_col = QVBoxLayout()
        icon_col.setAlignment(Qt.AlignCenter)
        self._sum_icon = PaladinIcon(size=56)
        icon_col.addWidget(self._sum_icon)
        self._sum_chess = QLabel("—")
        self._sum_chess.setFont(QFont("Segoe UI Emoji", 28))
        self._sum_chess.setAlignment(Qt.AlignCenter)
        self._sum_chess.setStyleSheet("background: transparent; border: none;")
        icon_col.addWidget(self._sum_chess)
        piece_row.addLayout(icon_col)

        text_col = QVBoxLayout()
        self._sum_name = QLabel("—")
        self._sum_name.setFont(QFont(SERIF_FONT, 20, QFont.Bold))
        self._sum_name.setStyleSheet(f"color: {ACCENT}; background: transparent; border: none; letter-spacing: 2px;")
        text_col.addWidget(self._sum_name)

        self._sum_traits = QLabel("—")
        self._sum_traits.setFont(QFont(BODY_FONT, 12))
        self._sum_traits.setStyleSheet(f"color: {TEXT2}; background: transparent; border: none;")
        text_col.addWidget(self._sum_traits)

        self._sum_desc = QLabel("—")
        self._sum_desc.setFont(QFont(BODY_FONT, 11))
        self._sum_desc.setStyleSheet(f"color: {TEXT3}; font-style: italic; background: transparent; border: none;")
        self._sum_desc.setWordWrap(True)
        text_col.addWidget(self._sum_desc)
        piece_row.addLayout(text_col, 1)
        sum_ly.addLayout(piece_row)
        sum_ly.addWidget(make_separator())

        features_lbl = make_mono_label("Platform Features", size=9)
        features_lbl.setStyleSheet(f"color: {TEXT3}; background: transparent; border: none; text-transform: uppercase; letter-spacing: 1px;")
        sum_ly.addWidget(features_lbl)

        for f in [
            "Live candlestick charts — accurate OHLCV data via yfinance",
            "AI signals: BUY / SELL / HOLD with stop-loss & take-profit",
            "Technical overlays: SMA 20/50/200, Bollinger Bands, RSI, MACD",
            "Multi-timeframe scanner: 1m · 5m · 15m · 1h · 1d · 1wk",
            "Portfolio tracker with real-time P&L and open position management",
            "Trade journal with notes, tags, and performance analytics",
            "Risk calculator: position size, R:R ratio, expected value, breakeven",
        ]:
            row = QHBoxLayout()
            arrow = QLabel("▸")
            arrow.setFixedWidth(14)
            arrow.setStyleSheet(f"color: {ACCENT}; background: transparent; border: none; font-size: 11px;")
            fl = QLabel(f)
            fl.setFont(QFont(BODY_FONT, 11))
            fl.setStyleSheet(f"color: {TEXT2}; background: transparent; border: none;")
            row.addWidget(arrow)
            row.addWidget(fl, 1)
            cw = QWidget()
            cw.setStyleSheet("background: transparent;")
            cw.setLayout(row)
            sum_ly.addWidget(cw)

        ly.addWidget(self._summary_card)
        ly.addStretch()

        launch_btn = make_btn_primary("Launch Paladin →")
        launch_btn.setFixedHeight(46)
        launch_btn.clicked.connect(self._launch)
        ly.addWidget(launch_btn)
        return page

    def _on_piece_clicked(self, piece):
        for p, card in self._piece_cards.items():
            card.set_selected(p == piece)
        self.selected_piece = piece
        self._next_btn.setEnabled(True)
        self._status_lbl.setText(f"Archetype selected: {CHESS_PIECES[piece]['traits']}  ·  Click Next to continue")
        self._status_lbl.setStyleSheet(f"color: {GREEN}; background: transparent;")

    def _go_next(self):
        if self._current_step == 0:
            self._stack.setCurrentIndex(1)
            self._current_step = 1
            self._back_btn.setVisible(True)
            self._status_lbl.setText("Review the platform guide  ·  Click Next when ready")
            self._status_lbl.setStyleSheet(f"color: {TEXT3}; background: transparent;")
            self._next_btn.setText("Next →")
        elif self._current_step == 1:
            self._update_summary()
            self._stack.setCurrentIndex(2)
            self._current_step = 2
            self._next_btn.setVisible(False)
            self._status_lbl.setText(f"Archetype: {self.selected_piece.upper()}  ·  Ready to launch")
            self._status_lbl.setStyleSheet(f"color: {GREEN}; background: transparent;")
        self._update_progress()

    def _go_back(self):
        self._current_step -= 1
        self._stack.setCurrentIndex(self._current_step)
        if self._current_step == 0:
            self._back_btn.setVisible(False)
            self._status_lbl.setText("Select your trading archetype to continue")
            self._status_lbl.setStyleSheet(f"color: {YELLOW}; background: transparent;")
        self._next_btn.setVisible(True)
        self._next_btn.setText("Next →")
        self._update_progress()

    def _tut_prev(self):
        if self._tut_step > 0:
            self._tut_step -= 1
            self._tut_stack.setCurrentIndex(self._tut_step)
            self._refresh_tut_dots()

    def _tut_next(self):
        if self._tut_step < len(TUTORIAL_CONTENT) - 1:
            self._tut_step += 1
            self._tut_stack.setCurrentIndex(self._tut_step)
            self._refresh_tut_dots()

    def _refresh_tut_dots(self):
        for i, dot in enumerate(self._tut_dots):
            dot.setStyleSheet(f"color: {ACCENT if i == self._tut_step else TEXT4}; background: transparent;")

    def _update_summary(self):
        if self.selected_piece:
            info = CHESS_PIECES[self.selected_piece]
            pm = chess_icon_pixmap(self.selected_piece, 42, ACCENT)
            if pm is not None:
                self._sum_chess.setPixmap(pm)
                self._sum_chess.setText("")
            else:
                self._sum_chess.setPixmap(QPixmap())
                self._sum_chess.setText(info["emoji"])
                self._sum_chess.setFont(QFont("Segoe UI Emoji", 28))
            self._sum_name.setText(self.selected_piece.upper())
            self._sum_traits.setText(info["traits"])
            self._sum_desc.setText(info["description"])

    def _update_progress(self):
        pct = (self._current_step / 2) * 100
        self._prog_bar.set_value(pct)
        self._step_indicator.setText(f"{self._current_step + 1} / 3")

    def _launch(self):
        if self.selected_piece:
            self.accept()


class YFinanceWorker(QThread):
    data_ready = pyqtSignal(object)
    error_occurred = pyqtSignal(str)

    def __init__(self, symbol, interval):
        super().__init__()
        self.symbol = symbol
        self.interval = interval

    def run(self):
        if not YFINANCE_AVAILABLE:
            self.error_occurred.emit("yfinance not installed")
            return
        try:
            sym = resolve_symbol(self.symbol)
            period, yf_interval = INTERVAL_MAP.get(self.interval, ("1y", "1d"))
            ticker = yf.Ticker(sym)
            df = ticker.history(period=period, interval=yf_interval)
            if df.empty:
                self.error_occurred.emit(f"No data for {self.symbol}")
                return
            df = df.rename(columns={"Open":"open","High":"high","Low":"low","Close":"close","Volume":"volume"})
            df.index = pd.to_datetime(df.index)
            df = df[["open","high","low","close","volume"]].dropna()
            self.data_ready.emit(df)
        except Exception as e:
            self.error_occurred.emit(str(e))


class WatchlistPriceWorker(QThread):
    prices_ready = pyqtSignal(dict)

    def __init__(self, symbols):
        super().__init__()
        self.symbols = symbols

    def run(self):
        if not YFINANCE_AVAILABLE:
            return
        result = {}
        try:
            tickers = yf.Tickers(" ".join(self.symbols))
            for sym in self.symbols:
                try:
                    resolved = resolve_symbol(sym)
                    t = tickers.tickers[resolved]
                    hist = t.history(period="2d", interval="1d")
                    if len(hist) >= 2:
                        prev = hist["Close"].iloc[-2]
                        last = hist["Close"].iloc[-1]
                        chg  = (last / prev - 1) * 100
                        result[sym] = (last, chg)
                    elif len(hist) == 1:
                        result[sym] = (hist["Close"].iloc[-1], 0.0)
                except Exception:
                    pass
        except Exception:
            pass
        self.prices_ready.emit(result)


class AIChatWorker(QThread):
    reply_ready = pyqtSignal(object)
    error       = pyqtSignal(str)

    def __init__(self, brain, symbol: str, interval: str, question: str, history: list):
        super().__init__()
        self._brain    = brain
        self._symbol   = symbol
        self._interval = interval
        self._question = question.lower().strip()

    def run(self):
        try:
            sig = self._brain.generate_signal(self._symbol, self._interval)
            self.reply_ready.emit(self._build_reply(sig))
        except Exception as e:
            self.error.emit(str(e))

    def _build_reply(self, sig) -> str:
        canned = _humanize(self._question)
        if canned:
            return canned
        q         = self._question
        direction = sig.direction
        conf      = int(sig.confidence * 100)
        entry     = sig.entry_price
        sl        = sig.stop_loss
        tp        = sig.take_profit
        rr        = sig.risk_reward
        pattern   = sig.pattern
        reasoning = sig.reasoning
        source    = sig.source
        rr_str    = "∞" if rr > 100 else f"{rr:.2f}"
        nl        = "\n"

        def all_lines():
            return [l for l in reasoning.split(nl) if l.strip()]

        def bullet_lines(*keywords):
            return [l for l in reasoning.split(nl) if l.startswith("•") and
                    any(w in l.lower() for w in keywords)]

        if any(w in q for w in ["risk","stop","loss","danger","downside"]):
            lines = [f"{self._symbol} — Risk Assessment [{source}]","",
                     f"Stop Loss:  ${sl:,.2f}",f"Entry:      ${entry:,.2f}",
                     f"Distance:   ${abs(entry-sl):,.2f}  ({abs(entry-sl)/entry*100:.2f}%)", ""]
            if direction == "BUY":
                lines.append(f"Risk if long: ${abs(entry-sl):,.2f} per share if SL hit.")
            elif direction == "SELL":
                lines.append(f"Risk if short: ${abs(sl-entry):,.2f} per share if SL hit.")
            else:
                lines.append("HOLD — no active position risk.")
            lines += ["","Key risk factors:"] + (bullet_lines("risk","resist","overbought","bear","diverge","vol","expand") or ["  None flagged."])

        elif any(w in q for w in ["entry","buy","long","short","sell","trade","strategy"]):
            lines = [f"{self._symbol} — Trade Setup [{source}]","",
                     f"Signal:      {direction}  ({conf}% confidence)",
                     f"Pattern:     {pattern}",f"Entry:       ${entry:,.2f}",
                     f"Stop Loss:   ${sl:,.2f}",f"Take Profit: ${tp:,.2f}",
                     f"R:R Ratio:   1:{rr_str}","","Model Reasoning:"] + all_lines()

        elif any(w in q for w in ["regime","trend","market","structure","condition"]):
            regime = bullet_lines("sma","trend","align","cross","golden","death","regime","squeeze","compress")
            lines  = [f"{self._symbol} — Market Regime [{source}]","",
                      f"Direction: {direction}  ({conf}% confidence)","","Structural Analysis:"] + (regime or ["  No strong regime signal."])

        elif any(w in q for w in ["confidence","certain","sure","reliable","probability"]):
            lines = [f"{self._symbol} — Model Confidence [{source}]","",
                     f"Confidence: {conf}%",f"Direction:  {direction}",""]
            if conf >= 70:   lines.append("HIGH — strong feature agreement.")
            elif conf >= 55: lines.append("MODERATE — some conflicting signals.")
            else:            lines.append("LOW — mixed signals, wait for clarity.")
            lines += ["","Supporting factors:"] + bullet_lines("•")

        elif any(w in q for w in ["hello","hi","hey","howdy","sup","what's up","whats up"]):
            lines = [f"PALADIN online. Watching {self._symbol} on {self._interval}.",
                     f"Current signal: {direction} ({conf}% confidence) — {pattern}.",
                     "Ask me about entry, risk, trend, or confidence."]

        elif any(w in q for w in ["analyse","analyze","analysis","overview","summary","current signal","what do you think"]):
            lines = [f"{self._symbol} — Full Analysis [{source}]","",
                     f"Signal: {direction}  |  Confidence: {conf}%  |  Pattern: {pattern}",
                     f"Entry ${entry:,.2f}  →  TP ${tp:,.2f}  |  SL ${sl:,.2f}  |  R:R 1:{rr_str}",""] + all_lines()

        else:
            lines = [f"{self._symbol} — PALADIN [{source}]","",
                     f"Signal: {direction}  |  Confidence: {conf}%  |  Pattern: {pattern}",
                     f"Entry ${entry:,.2f}  →  TP ${tp:,.2f}  |  SL ${sl:,.2f}  |  R:R 1:{rr_str}",""] + all_lines()

        return nl.join(lines)


class SignalWorker(QThread):
    signal_ready   = pyqtSignal(object)
    error_occurred = pyqtSignal(str)

    def __init__(self, brain, symbol, timeframe):
        super().__init__()
        self.brain     = brain
        self.symbol    = symbol
        self.timeframe = timeframe

    def run(self):
        try:
            resolved = resolve_symbol(self.symbol)
            signal   = self.brain.generate_signal(resolved, self.timeframe)
            signal.symbol = self.symbol
            self.signal_ready.emit(signal)
        except Exception as e:
            self.error_occurred.emit(str(e))


class ScanWorker(QThread):
    result_ready = pyqtSignal(str, object)
    all_done     = pyqtSignal()

    def __init__(self, brain, symbols, timeframe="1d"):
        super().__init__()
        self.brain     = brain
        self.symbols   = symbols
        self.timeframe = timeframe

    def run(self):
        for sym in self.symbols:
            try:
                resolved = resolve_symbol(sym)
                sig      = self.brain.generate_signal(resolved, self.timeframe)
                self.result_ready.emit(sym, sig)
            except Exception:
                pass
        self.all_done.emit()


class LiveAnalysisWorker(QThread):
    """Fetches a full rich TradeSignal for the live analysis sequencer."""
    signal_ready = pyqtSignal(object)
    error        = pyqtSignal(str)

    def __init__(self, brain, symbol, interval):
        super().__init__()
        self.brain    = brain
        self.symbol   = symbol
        self.interval = interval

    def run(self):
        try:
            resolved = resolve_symbol(self.symbol)
            sig      = self.brain.generate_signal(resolved, self.interval)
            sig.symbol = self.symbol
            self.signal_ready.emit(sig)
        except Exception as e:
            self.error.emit(str(e))


class AdvancedChartWidget(QWidget):
    annotation_added = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._df           = None
        self._symbol       = "—"
        self._interval     = "1d"
        self._chart_type   = "candle"
        self._show_sma20   = True
        self._show_sma50   = True
        self._show_sma200  = False
        self._show_volume  = True
        self._show_bb      = False
        self._show_rsi     = False
        self._show_macd    = False
        self._show_ai_levels = False
        self._ai_signal    = None
        self._ai_phase     = 4
        self._live_note    = ""
        self._last_df      = None
        self._annotations  = []
        self._note_mode    = False
        self._zoom_state   = None
        self._crosshair_h  = None
        self._crosshair_v  = None
        self._price_label  = None
        self._ax_price     = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._figure = Figure(facecolor=SURFACE2)
        self._canvas = FigureCanvas(self._figure)
        self._canvas.setStyleSheet(f"background-color: {SURFACE2};")
        self._canvas.mpl_connect("scroll_event",        self._on_scroll)
        self._canvas.mpl_connect("motion_notify_event", self._on_mouse_move)
        self._canvas.mpl_connect("button_press_event",  self._on_click)
        self._canvas.mpl_connect("key_press_event",     self._on_key)
        self._canvas.setFocusPolicy(Qt.StrongFocus)
        layout.addWidget(self._canvas)

        self._plot_placeholder()

    def _plot_placeholder(self):
        self._figure.clear()
        ax = self._figure.add_subplot(111)
        ax.set_facecolor(SURFACE3)
        ax.text(0.5, 0.5, "Select a symbol to load chart",
                ha="center", va="center", color=TEXT3,
                fontsize=13, fontfamily=BODY_FONT, fontstyle="italic",
                transform=ax.transAxes)
        ax.set_xticks([]); ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_color(BORDER)
        self._figure.tight_layout()
        self._canvas.draw()

    def set_symbol(self, s):   self._symbol = s
    def set_interval(self, i): self._interval = i

    def set_chart_type(self, ctype):
        self._chart_type = ctype
        if self._df is not None:
            self.plot(self._df)

    def set_indicator(self, name, val):
        setattr(self, f"_show_{name}", val)
        if self._df is not None:
            self.plot(self._df)

    def set_ai_signal(self, sig):
        self._ai_signal = sig
        self._ai_phase  = 4

    def set_ai_phase(self, phase: int):
        """Draw only annotations up to this phase index (0–4), then redraw."""
        self._ai_phase = phase
        if self._df is not None:
            self.plot(self._df)
    def set_live_note(self, text):
        self._live_note = text
        if self._last_df is not None:
            self.plot(self._last_df)

    def set_note_mode(self, enabled): self._note_mode = enabled

    def clear_annotations(self):
        self._annotations.clear()
        if self._df is not None:
            self.plot(self._df)

    def _on_scroll(self, event):
        if self._ax_price is None or self._df is None:
            return
        ax = self._ax_price
        n  = len(self._df)
        xmin, xmax = ax.get_xlim()
        span   = xmax - xmin
        factor = 0.85 if event.button == "up" else 1.15
        new_span = max(10, min(n * 1.5, span * factor))
        cx = event.xdata if event.xdata else (xmin + xmax) / 2
        new_xmin = cx - new_span * (cx - xmin) / span
        new_xmax = new_xmin + new_span
        ax.set_xlim(new_xmin, new_xmax)
        self._zoom_state = (new_xmin, new_xmax)
        self._canvas.draw_idle()

    def _on_mouse_move(self, event):
        if self._ax_price is None or event.xdata is None or event.ydata is None:
            return
        ax = self._ax_price
        for attr in ("_crosshair_h", "_crosshair_v", "_price_label"):
            obj = getattr(self, attr)
            if obj:
                try: obj.remove()
                except Exception: pass
        self._crosshair_v = ax.axvline(event.xdata, color=TEXT3, linewidth=0.6, alpha=0.7, linestyle="--")
        self._crosshair_h = ax.axhline(event.ydata, color=TEXT3, linewidth=0.6, alpha=0.7, linestyle="--")
        xi = int(round(event.xdata))
        if self._df is not None and 0 <= xi < len(self._df):
            c  = self._df["close"].iloc[xi]
            dt = self._df.index[xi]
            if self._interval in ("1m","5m","15m","1h"):
                ts = dt.strftime("%H:%M")
            elif self._interval == "1wk":
                ts = dt.strftime("%b %Y")
            else:
                ts = dt.strftime("%d %b %y")
            self._price_label = ax.text(
                0.01, 0.01, f"  {ts}   ${c:,.2f}  ",
                transform=ax.transAxes, fontsize=8,
                fontfamily=MONO_FONT, color=TEXT,
                bbox=dict(facecolor=SURFACE2, edgecolor=BORDER2, alpha=0.85, pad=3),
                verticalalignment="bottom"
            )
        self._canvas.draw_idle()

    def _on_click(self, event):
        if event.xdata is None or event.ydata is None or self._df is None:
            return
        if self._note_mode and event.button == 1:
            xi = int(round(event.xdata))
            xi = max(0, min(xi, len(self._df) - 1))
            dt    = self._df.index[xi]
            price = event.ydata
            from PyQt5.QtWidgets import QInputDialog
            text, ok = QInputDialog.getText(self, "Add Note", f"Note at {dt.strftime('%d %b %y')} ${price:.2f}:")
            if ok and text.strip():
                self._annotations.append({"xi": xi, "price": price, "text": text.strip()})
                self.annotation_added.emit(text.strip())
                self.plot(self._df)
        elif event.button == 2 or event.dblclick:
            self._zoom_state = None
            if self._df is not None:
                self.plot(self._df)

    def _on_key(self, event):
        if self._ax_price is None:
            return
        xmin, xmax = self._ax_price.get_xlim()
        span = xmax - xmin
        step = span * 0.1
        if event.key == "left":
            self._ax_price.set_xlim(xmin - step, xmax - step)
            self._canvas.draw_idle()
        elif event.key == "right":
            self._ax_price.set_xlim(xmin + step, xmax + step)
            self._canvas.draw_idle()
        elif event.key == "r":
            self._zoom_state = None
            if self._df is not None:
                self.plot(self._df)

    def _style_ax(self, ax):
        ax.set_facecolor(SURFACE3)
        ax.tick_params(colors=TEXT3, labelsize=8, which="both",
                       bottom=False, left=True, right=False, top=False)
        ax.yaxis.set_tick_params(labelcolor=TEXT3, labelsize=8)
        ax.xaxis.set_tick_params(labelcolor=TEXT3, labelsize=8)
        for spine in ax.spines.values():
            spine.set_color(BORDER)
        ax.grid(True, color=BORDER2, alpha=0.35, linewidth=0.4, linestyle="--")

    def plot(self, df: pd.DataFrame):
        self._last_df = df
        self._df      = df
        self._figure.clear()
        self._crosshair_h = None
        self._crosshair_v = None
        self._price_label = None

        n      = len(df)
        closes = df["close"].values
        opens  = df["open"].values
        highs  = df["high"].values
        lows   = df["low"].values
        vols   = df["volume"].values
        bull   = closes >= opens
        x      = np.arange(n)
        close_s = pd.Series(closes)

        sub_count = sum([self._show_volume, self._show_rsi, self._show_macd])
        ratios = [4.5]
        for _ in range(sub_count):
            ratios.append(1.0)

        self._figure.patch.set_facecolor(SURFACE)

        if sub_count > 0:
            axs = self._figure.subplots(1 + sub_count, 1,
                                        gridspec_kw={"height_ratios": ratios, "hspace": 0.03})
            ax_price = axs[0]
            sub_axs  = list(axs[1:])
        else:
            ax_price = self._figure.add_subplot(111)
            sub_axs  = []

        self._ax_price = ax_price
        self._style_ax(ax_price)

        ax_vol  = sub_axs.pop(0) if self._show_volume and sub_axs else None
        ax_rsi  = sub_axs.pop(0) if self._show_rsi  and sub_axs  else None
        ax_macd = sub_axs.pop(0) if self._show_macd and sub_axs  else None

        for sax in [ax_vol, ax_rsi, ax_macd]:
            if sax is not None:
                self._style_ax(sax)

        bar_w = max(0.3, min(0.85, 0.85 - n * 0.0004))

        if self._chart_type == "candle":
            for i in range(n):
                c  = GREEN if bull[i] else RED
                b  = min(opens[i], closes[i])
                h  = abs(closes[i] - opens[i])
                ax_price.bar(i, h, bottom=b, color=c, width=bar_w, zorder=3, linewidth=0)
                ax_price.plot([i, i], [lows[i], b],    color=c, linewidth=0.7, zorder=2)
                ax_price.plot([i, i], [b + h, highs[i]], color=c, linewidth=0.7, zorder=2)
        else:
            ax_price.plot(x, closes, color=ACCENT3, linewidth=1.4, zorder=3)
            ax_price.fill_between(x, closes, closes.min(), color=ACCENT, alpha=0.06)

        has_legend = False

        if self._show_sma20:
            sma20 = close_s.rolling(20).mean()
            ax_price.plot(x, sma20, color=BLUE, linewidth=1.0, alpha=0.85, label="SMA 20", zorder=4)
            has_legend = True

        if self._show_sma50:
            sma50 = close_s.rolling(50).mean()
            ax_price.plot(x, sma50, color=YELLOW, linewidth=1.0, alpha=0.85, label="SMA 50", zorder=4)
            has_legend = True

        if self._show_sma200:
            sma200 = close_s.rolling(200).mean()
            ax_price.plot(x, sma200, color=PURPLE, linewidth=1.0, alpha=0.7, label="SMA 200", zorder=4)
            has_legend = True

        if self._show_bb:
            bb_mid = close_s.rolling(20).mean()
            bb_std = close_s.rolling(20).std()
            bb_up  = bb_mid + 2 * bb_std
            bb_dn  = bb_mid - 2 * bb_std
            ax_price.plot(x, bb_up, color=ACCENT, linewidth=0.8, alpha=0.55, linestyle="--", label="BB", zorder=4)
            ax_price.plot(x, bb_dn, color=ACCENT, linewidth=0.8, alpha=0.55, linestyle="--", zorder=4)
            ax_price.fill_between(x, bb_up, bb_dn, color=ACCENT, alpha=0.04, zorder=1)
            has_legend = True

        if self._show_ai_levels and self._ai_signal and hasattr(self._ai_signal, "annotations"):
            sig        = self._ai_signal
            price_range = highs.max() - lows.min()
            label_offset = price_range * 0.025

            used_label_y = []

            def safe_y(y, used, gap=None):
                gap = gap or price_range * 0.02
                y_out = y
                for uy in used:
                    if abs(y_out - uy) < gap:
                        y_out = uy + gap
                used.append(y_out)
                return y_out

            for ann in (sig.annotations or []):
                if ann.phase > self._ai_phase:
                    continue
                col   = ann.color
                alpha = ann.alpha
                price = ann.price

                if ann.kind == "hline":
                    ax_price.axhline(price, color=col, linewidth=1.1,
                                     alpha=alpha, linestyle="--", zorder=5)
                    if ann.label:
                        ly = safe_y(price, used_label_y)
                        ax_price.text(n - 0.5, ly, f"  {ann.label}",
                                      color=col, fontsize=7.5, fontfamily=MONO_FONT,
                                      va="center", fontweight="bold",
                                      bbox=dict(facecolor=SURFACE, edgecolor=col,
                                                alpha=0.88, pad=2, linewidth=0.7),
                                      zorder=6)

                elif ann.kind == "zone":
                    ax_price.axhspan(ann.price, ann.price2,
                                     color=col, alpha=alpha, zorder=1)
                    if ann.label:
                        mid = (ann.price + ann.price2) / 2
                        ax_price.text(2, mid, f" {ann.label} ",
                                      color=col, fontsize=6.5, fontfamily=MONO_FONT,
                                      alpha=0.85, va="center",
                                      bbox=dict(facecolor=SURFACE2, edgecolor=col,
                                                alpha=0.7, pad=1.5, linewidth=0.5),
                                      zorder=4)

                elif ann.kind in ("callout", "marker"):
                    xi_a = ann.xi if ann.xi >= 0 else last
                    xi_a = max(0, min(xi_a, n - 1))
                    yp   = price
                    off  = label_offset * (1.8 if ann.kind == "callout" else 1.2)
                    ax_price.annotate(
                        ann.label,
                        xy=(xi_a, yp),
                        xytext=(xi_a, yp + off),
                        fontsize=7.5, color=col, fontfamily=MONO_FONT, fontweight="bold",
                        ha="center", va="bottom",
                        bbox=dict(facecolor=SURFACE2, edgecolor=col,
                                  alpha=0.9, pad=3, linewidth=0.8),
                        arrowprops=dict(arrowstyle="-|>", color=col,
                                        lw=1.0, mutation_scale=8),
                        zorder=7
                    )

                elif ann.kind == "arrow":
                    xi_a = ann.xi if ann.xi >= 0 else last
                    xi_a = max(0, min(xi_a, n - 1))
                    yp   = price
                    is_bull = any(w in ann.label for w in ("▲","BUY","Bull","Hammer","Soldier","Morning","Golden"))
                    y_from  = yp - label_offset * 2.2 if is_bull else yp + label_offset * 2.2
                    ax_price.annotate(
                        ann.label,
                        xy=(xi_a, yp),
                        xytext=(xi_a, y_from),
                        fontsize=7.5, color=col, fontfamily=MONO_FONT, fontweight="bold",
                        ha="center", va="top" if is_bull else "bottom",
                        bbox=dict(facecolor=SURFACE, edgecolor=col,
                                  alpha=0.92, pad=3, linewidth=0.9),
                        arrowprops=dict(arrowstyle="-|>", color=col,
                                        lw=1.2, mutation_scale=10),
                        zorder=7
                    )

                elif ann.kind == "signal":
                    xi_a   = ann.xi if ann.xi >= 0 else last
                    xi_a   = max(0, min(xi_a, n - 1))
                    is_buy = "BUY" in ann.label
                    is_sell= "SELL" in ann.label
                    yp     = price
                    offset = -(label_offset * 3) if is_buy else (label_offset * 3 if is_sell else 0)
                    ax_price.annotate(
                        ann.label,
                        xy=(xi_a, yp),
                        xytext=(xi_a, yp + offset),
                        fontsize=9, color=col, fontfamily=MONO_FONT, fontweight="bold",
                        ha="center",
                        va="top" if is_buy else ("bottom" if is_sell else "center"),
                        bbox=dict(facecolor=col, edgecolor="white",
                                  alpha=0.95, pad=4, linewidth=1.0),
                        arrowprops=dict(arrowstyle="-|>", color=col,
                                        lw=1.5, mutation_scale=12),
                        zorder=8
                    )

        for ann in self._annotations:
            xi = ann["xi"]
            yp = ann["price"]
            ax_price.annotate(ann["text"], xy=(xi, yp),
                              xytext=(xi, yp + (highs.max() - lows.min()) * 0.04),
                              arrowprops=dict(arrowstyle="->", color=YELLOW, lw=0.8),
                              fontsize=7, color=YELLOW, fontfamily=MONO_FONT,
                              bbox=dict(facecolor=SURFACE2, edgecolor=BORDER2, alpha=0.85, pad=2))

        if has_legend:
            leg = ax_price.legend(loc="upper left", fontsize=7.5,
                                  facecolor=SURFACE, edgecolor=BORDER2,
                                  labelcolor=TEXT2, framealpha=0.92,
                                  ncol=min(4, sum([self._show_sma20, self._show_sma50,
                                                   self._show_sma200, self._show_bb]) + 1))

        price_range = highs.max() - lows.min()
        if self._zoom_state:
            ax_price.set_xlim(*self._zoom_state)
        else:
            ax_price.set_xlim(-0.5, n + 0.5)
        ax_price.set_ylim(lows.min() - price_range * 0.04, highs.max() + price_range * 0.06)

        last_price = closes[-1]
        prev_price = closes[-2] if n > 1 else closes[-1]
        pct_chg    = (last_price / prev_price - 1) * 100
        pct_full   = (closes[-1] / closes[0] - 1) * 100 if closes[0] > 0 else 0
        sign       = "+" if pct_chg >= 0 else ""
        clr_chg    = GREEN if pct_chg >= 0 else RED

        ax_price.set_title(
            f"  {self._symbol}   ${last_price:,.2f}   {sign}{pct_chg:.2f}%  ({'+' if pct_full>=0 else ''}{pct_full:.2f}% period)",
            loc="left", color=TEXT, fontsize=10, fontweight="bold",
            fontfamily=SERIF_FONT, pad=8
        )

        ax_price.yaxis.set_major_formatter(
            matplotlib.ticker.FuncFormatter(lambda v, _: f"${v:,.0f}" if v >= 1000 else f"${v:.2f}")
        )

        xmin_v, xmax_v = ax_price.get_xlim()
        visible_n  = int(xmax_v - xmin_v)
        max_xticks = min(10, max(4, visible_n // 20))
        step_t     = max(1, n // max_xticks)
        tick_pos   = x[::step_t]
        tick_labels= []
        for ti in tick_pos:
            if ti < len(df):
                dt = df.index[ti]
                if self._interval in ("1m","5m","15m"):
                    tick_labels.append(dt.strftime("%H:%M"))
                elif self._interval == "1h":
                    tick_labels.append(dt.strftime("%d %b\n%H:%M"))
                elif self._interval == "1wk":
                    tick_labels.append(dt.strftime("%b '%y"))
                else:
                    tick_labels.append(dt.strftime("%d %b"))
            else:
                tick_labels.append("")
        ax_price.set_xticks(tick_pos)
        ax_price.set_xticklabels(tick_labels, rotation=0, ha="center", fontsize=7.5, color=TEXT3)

        ax_price.axhline(last_price, color=TEXT3, linewidth=0.5, linestyle=":", alpha=0.6)
        ax_price.text(
            0.0, last_price, f" ${last_price:,.2f} ",
            transform=ax_price.get_yaxis_transform(),
            fontsize=7, fontfamily=MONO_FONT, color=BG, fontweight="bold",
            va="center", bbox=dict(facecolor=clr_chg, edgecolor="none", pad=2)
        )

        if ax_vol is not None:
            vol_colors = [GREEN if b else RED for b in bull]
            ax_vol.bar(x, vols, color=vol_colors, alpha=0.5, width=bar_w)
            ax_vol.set_ylabel("VOL", color=TEXT3, fontsize=6)
            ax_vol.set_xlim(ax_price.get_xlim())
            ax_vol.set_xticks([])
            mx = vols.max()
            if mx > 0:
                ax_vol.set_ylim(0, mx * 1.4)
            ax_vol.yaxis.set_major_formatter(
                matplotlib.ticker.FuncFormatter(
                    lambda v, _: f"{v/1e6:.1f}M" if v >= 1e6 else f"{v/1e3:.0f}K"
                )
            )
            vol_sma = pd.Series(vols).rolling(20).mean().values
            ax_vol.plot(x, vol_sma, color=BLUE, linewidth=0.8, alpha=0.7)

        if ax_rsi is not None:
            delta     = close_s.diff()
            g         = delta.clip(lower=0).ewm(com=13, adjust=False).mean()
            l         = (-delta).clip(lower=0).ewm(com=13, adjust=False).mean()
            rsi_vals  = (100 - 100 / (1 + g / l.replace(0, np.nan))).values
            ax_rsi.plot(x, rsi_vals, color=TEAL, linewidth=0.9, alpha=0.9)
            ax_rsi.axhline(70, color=RED,   linewidth=0.5, linestyle="--", alpha=0.55)
            ax_rsi.axhline(50, color=TEXT3, linewidth=0.4, linestyle=":",  alpha=0.4)
            ax_rsi.axhline(30, color=GREEN, linewidth=0.5, linestyle="--", alpha=0.55)
            ax_rsi.set_ylim(0, 100)
            ax_rsi.set_ylabel("RSI", color=TEXT3, fontsize=6)
            ax_rsi.set_xlim(ax_price.get_xlim())
            ax_rsi.set_xticks([])
            ax_rsi.fill_between(x, rsi_vals, 70, where=(rsi_vals >= 70), color=RED,   alpha=0.1)
            ax_rsi.fill_between(x, rsi_vals, 30, where=(rsi_vals <= 30), color=GREEN, alpha=0.1)
            cur_rsi   = rsi_vals[-1] if not np.isnan(rsi_vals[-1]) else 50
            rsi_color = RED if cur_rsi > 70 else (GREEN if cur_rsi < 30 else TEXT2)
            ax_rsi.text(0.01, 0.85, f"RSI {cur_rsi:.1f}", transform=ax_rsi.transAxes,
                        fontsize=7, fontfamily=MONO_FONT, color=rsi_color)

        if ax_macd is not None:
            ema12        = close_s.ewm(span=12, adjust=False).mean()
            ema26        = close_s.ewm(span=26, adjust=False).mean()
            macd_line    = (ema12 - ema26).values
            signal_line  = pd.Series(macd_line).ewm(span=9, adjust=False).mean().values
            hist_vals    = macd_line - signal_line
            hist_colors  = [GREEN if v >= 0 else RED for v in hist_vals]
            ax_macd.bar(x, hist_vals, color=hist_colors, alpha=0.6, width=bar_w)
            ax_macd.plot(x, macd_line,   color=BLUE,   linewidth=0.9, alpha=0.9, label="MACD")
            ax_macd.plot(x, signal_line, color=YELLOW, linewidth=0.9, alpha=0.9, label="Signal")
            ax_macd.axhline(0, color=TEXT3, linewidth=0.4, linestyle="-", alpha=0.4)
            ax_macd.set_ylabel("MACD", color=TEXT3, fontsize=6)
            ax_macd.set_xlim(ax_price.get_xlim())
            ax_macd.set_xticks([])
            ax_macd.legend(loc="upper left", fontsize=6, facecolor=SURFACE,
                           edgecolor=BORDER, labelcolor=TEXT2, framealpha=0.8)

        self._figure.subplots_adjust(left=0.07, right=0.99, top=0.94, bottom=0.01, hspace=0.04)
        self._canvas.draw()

    def show_error(self, msg):
        self._figure.clear()
        ax = self._figure.add_subplot(111)
        ax.set_facecolor(SURFACE3)
        ax.text(0.5, 0.5, f"⚠  {msg}", ha="center", va="center",
                color=YELLOW, fontsize=11, fontfamily=MONO_FONT, transform=ax.transAxes)
        ax.set_xticks([]); ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_color(BORDER)
        self._figure.tight_layout()
        self._canvas.draw()


class TradingDashboard(QMainWindow):
    def __init__(self, piece):
        super().__init__()
        self.piece             = piece
        self._settings         = QSettings("Paladin", "TradingPlatform")
        self.current_symbol    = self._settings.value("last_symbol",   "AAPL")
        self.current_interval  = self._settings.value("last_interval", "1d")
        self._workers          = []
        self._brain            = None
        self._interval_btns    = {}
        self._watchlist_items  = {}
        self._signal_history   = []
        self._trades           = []
        self._journal_entries  = []
        self._clock_timer      = QTimer()
        self._nav_btns         = {}

        if BRAIN_AVAILABLE:
            try:
                self._brain = get_brain_v2()
            except Exception:
                pass

        self.setWindowTitle(f"Paladin — {CHESS_PIECES[piece]['traits']}")
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        self.setStyleSheet(GLOBAL_QSS)

        self._init_ui()
        self._load_chart()
        self._refresh_watchlist_prices()

        self._auto_timer = QTimer()
        self._auto_timer.timeout.connect(self._refresh_signal)
        self._auto_timer.start(30000)

        self._wl_timer = QTimer()
        self._wl_timer.timeout.connect(self._refresh_watchlist_prices)
        self._wl_timer.start(60000)

        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(1000)
        self._update_clock()

    def _update_clock(self):
        now = datetime.now()
        if hasattr(self, "_clock_lbl"):
            self._clock_lbl.setText(now.strftime("%H:%M:%S"))
        if hasattr(self, "_date_lbl"):
            self._date_lbl.setText(now.strftime("%a %d %b %Y"))

    def _init_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        outer.addWidget(self._build_topbar())

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        body.addWidget(self._build_sidebar())
        body.addWidget(self._build_main(), 1)
        outer.addLayout(body, 1)

        outer.addWidget(self._build_statusbar())

    def _build_topbar(self):
        bar = QFrame()
        bar.setFixedHeight(58)
        bar.setStyleSheet(f"QFrame {{ background: {SURFACE}; border-bottom: 1px solid {BORDER}; }}")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(18, 0, 18, 0)
        layout.setSpacing(12)

        icon = PaladinIcon(size=34)
        layout.addWidget(icon)

        logo = QLabel("PALADIN")
        logo.setFont(QFont(SERIF_FONT, 16, QFont.Bold))
        logo.setStyleSheet(f"color: {ACCENT}; letter-spacing: 4px; background: transparent;")
        layout.addWidget(logo)

        sub = QLabel("trading platform")
        sub.setFont(QFont(BODY_FONT, 10))
        sub.setStyleSheet(f"color: {TEXT3}; margin-left: 4px; font-style: italic; background: transparent;")
        layout.addWidget(sub)

        layout.addStretch()

        piece_info = CHESS_PIECES[self.piece]
        badge = QWidget()
        badge.setStyleSheet(f"""
            QWidget {{ color: #e05555; background: rgba(148,17,7,0.14); border: 1px solid rgba(148,17,7,0.28); border-radius: 2px; }}
            QLabel {{ background: transparent; border: none; color: #e05555; }}
        """)
        bly = QHBoxLayout(badge)
        bly.setContentsMargins(10, 3, 12, 3)
        bly.setSpacing(8)
        pm_b = chess_icon_pixmap(self.piece, 18, "#e05555")
        if pm_b is not None:
            ib = QLabel()
            ib.setPixmap(pm_b)
            bly.addWidget(ib)
        else:
            em = QLabel(piece_info["emoji"])
            em.setFont(QFont("Segoe UI Emoji", 12))
            bly.addWidget(em)
        bt = QLabel(f"{self.piece.upper()} MODE")
        bt.setFont(QFont(MONO_FONT, 10))
        bly.addWidget(bt)
        layout.addWidget(badge)

        layout.addSpacing(16)

        self._date_lbl = QLabel("")
        self._date_lbl.setFont(QFont(MONO_FONT, 9))
        self._date_lbl.setStyleSheet(f"color: {TEXT3}; background: transparent;")
        layout.addWidget(self._date_lbl)

        self._clock_lbl = QLabel("00:00:00")
        self._clock_lbl.setFont(QFont(MONO_FONT, 12, QFont.Bold))
        self._clock_lbl.setStyleSheet(f"color: {TEXT2}; background: transparent;")
        layout.addWidget(self._clock_lbl)

        layout.addSpacing(12)

        self._feed_dot = QLabel("●")
        self._feed_dot.setFont(QFont(MONO_FONT, 10))
        self._feed_dot.setStyleSheet(f"color: {GREEN}; background: transparent;")
        layout.addWidget(self._feed_dot)

        self._feed_status = QLabel("Live")
        self._feed_status.setFont(QFont(MONO_FONT, 10))
        self._feed_status.setStyleSheet(f"color: {TEXT3}; background: transparent;")
        layout.addWidget(self._feed_status)

        return bar

    def _build_statusbar(self):
        bar = QFrame()
        bar.setFixedHeight(24)
        bar.setStyleSheet(f"QFrame {{ background: {SURFACE}; border-top: 1px solid {BORDER}; }}")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(20)

        self._status_msg = QLabel("Ready  ·  Paladin Trading Platform")
        self._status_msg.setFont(QFont(MONO_FONT, 9))
        self._status_msg.setStyleSheet(f"color: {TEXT3}; background: transparent;")
        layout.addWidget(self._status_msg)

        layout.addStretch()

        brain_state = "AI Engine: Active" if self._brain else "AI Engine: Unavailable"
        brain_color = GREEN if self._brain else RED
        brain_lbl   = QLabel(brain_state)
        brain_lbl.setFont(QFont(MONO_FONT, 9))
        brain_lbl.setStyleSheet(f"color: {brain_color}; background: transparent;")
        layout.addWidget(brain_lbl)

        layout.addSpacing(16)

        yf_state = "yfinance: Connected" if YFINANCE_AVAILABLE else "yfinance: Missing"
        yf_color  = GREEN if YFINANCE_AVAILABLE else RED
        yf_lbl    = QLabel(yf_state)
        yf_lbl.setFont(QFont(MONO_FONT, 9))
        yf_lbl.setStyleSheet(f"color: {yf_color}; background: transparent;")
        layout.addWidget(yf_lbl)

        return bar

    def _build_sidebar(self):
        sidebar = QFrame()
        sidebar.setFixedWidth(234)
        sidebar.setStyleSheet(f"QFrame {{ background: {SURFACE}; border-right: 1px solid {BORDER}; }}")

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(make_label_section("Markets"))
        for lbl, icon_name, panel in [
            ("Dashboard",  "fa5s.chart-bar",  "dashboard"),
            ("Signals",    "fa5s.bolt",        "signals"),
            ("Chart",      "fa5s.chart-line",  "chart"),
        ]:
            btn = self._make_nav_btn(lbl, panel, icon_name)
            layout.addWidget(btn)

        layout.addWidget(make_label_section("Tools"))
        for lbl, icon_name, panel in [
            ("Portfolio",  "fa5s.wallet",      "portfolio"),
            ("Journal",    "fa5s.book",        "journal"),
            ("Risk Calc",  "fa5s.calculator",  "risk"),
        ]:
            btn = self._make_nav_btn(lbl, panel, icon_name)
            layout.addWidget(btn)

        layout.addWidget(make_label_section("System"))
        for lbl, icon_name, panel in [
            ("AI Chat",    "fa5s.magic",   "aichat"),
            ("Settings",   "fa5s.cog",         "settings"),
        ]:
            btn = self._make_nav_btn(lbl, panel, icon_name)
            layout.addWidget(btn)

        layout.addStretch()
        layout.addWidget(make_separator())
        layout.addWidget(make_label_section("Watchlist"))

        self._watchlist_container = QVBoxLayout()
        self._watchlist_container.setSpacing(0)
        self._watchlist_container.setContentsMargins(0, 0, 0, 0)
        for sym in WATCHLIST_SYMBOLS:
            item = self._make_watchlist_item(sym)
            self._watchlist_container.addWidget(item)
            self._watchlist_items[sym] = item

        wl_widget = QWidget()
        wl_widget.setLayout(self._watchlist_container)
        wl_scroll = QScrollArea()
        wl_scroll.setWidget(wl_widget)
        wl_scroll.setWidgetResizable(True)
        wl_scroll.setFrameShape(QFrame.NoFrame)
        wl_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        layout.addWidget(wl_scroll, 1)

        return sidebar

    def _make_nav_btn(self, label, panel, icon_name=""):
        btn = QPushButton(f"  {label}")
        btn.setCheckable(True)
        if icon_name and QTA_OK:
            try:
                btn.setIcon(qta.icon(icon_name, color=TEXT3))
                btn.setIconSize(QSize(15, 15))
            except Exception:
                pass
        btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {TEXT2};
                border: none;
                border-left: 2px solid transparent;
                padding: 10px 14px;
                text-align: left;
                font-family: '{BODY_FONT}';
                font-size: 13px;
            }}
            QPushButton:hover {{ background: {SURFACE2}; color: {TEXT}; }}
            QPushButton:checked {{
                background: {SURFACE2};
                color: {TEXT};
                border-left: 2px solid {ACCENT};
            }}
        """)
        btn.setCursor(QCursor(Qt.PointingHandCursor))
        if panel == "dashboard":
            btn.setChecked(True)
        btn.clicked.connect(lambda _, p=panel: self._switch_panel(p))
        self._nav_btns[panel] = btn
        return btn

    def _make_watchlist_item(self, sym):
        item = QFrame()
        item.setStyleSheet(f"""
            QFrame {{ background: transparent; border-bottom: 1px solid {BORDER}; }}
            QFrame:hover {{ background: {SURFACE2}; }}
        """)
        item.setCursor(QCursor(Qt.PointingHandCursor))
        item.setFixedHeight(46)

        layout = QHBoxLayout(item)
        layout.setContentsMargins(14, 0, 14, 0)

        sym_lbl = QLabel(sym)
        sym_lbl.setFont(QFont(MONO_FONT, 11, QFont.Bold))
        sym_lbl.setStyleSheet(f"color: {TEXT}; background: transparent; border: none;")
        layout.addWidget(sym_lbl)

        layout.addStretch()

        right_col = QVBoxLayout()
        right_col.setSpacing(1)
        right_col.setAlignment(Qt.AlignRight)

        price_lbl = QLabel("—")
        price_lbl.setFont(QFont(MONO_FONT, 10))
        price_lbl.setStyleSheet(f"color: {TEXT3}; background: transparent; border: none;")
        price_lbl.setAlignment(Qt.AlignRight)
        right_col.addWidget(price_lbl)

        chg_lbl = QLabel("")
        chg_lbl.setFont(QFont(MONO_FONT, 8))
        chg_lbl.setStyleSheet(f"color: {TEXT3}; background: transparent; border: none;")
        chg_lbl.setAlignment(Qt.AlignRight)
        right_col.addWidget(chg_lbl)

        layout.addLayout(right_col)

        item.mousePressEvent = lambda e, s=sym: self._switch_symbol(s)
        item.price_lbl = price_lbl
        item.chg_lbl   = chg_lbl
        return item

    def _refresh_watchlist_prices(self):
        w = WatchlistPriceWorker(WATCHLIST_SYMBOLS)
        w.prices_ready.connect(self._on_watchlist_prices)
        self._workers.append(w)
        w.start()

    def _on_watchlist_prices(self, prices: dict):
        for sym, item in self._watchlist_items.items():
            if sym in prices:
                price, chg = prices[sym]
                chg_color  = GREEN if chg >= 0 else RED
                sign       = "+" if chg >= 0 else ""
                item.price_lbl.setText(f"${price:,.2f}")
                item.price_lbl.setStyleSheet(f"color: {TEXT2}; background: transparent; border: none;")
                item.chg_lbl.setText(f"{sign}{chg:.2f}%")
                item.chg_lbl.setStyleSheet(f"color: {chg_color}; background: transparent; border: none;")

    def _build_main(self):
        main = QWidget()
        main.setStyleSheet(f"QWidget {{ background: {BG}; }}")
        layout = QVBoxLayout(main)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._panels = QStackedWidget()
        self._panels.setStyleSheet(f"QStackedWidget {{ background: {BG}; }}")
        layout.addWidget(self._panels, 1)

        self._panels.addWidget(self._build_dashboard_panel())
        self._panels.addWidget(self._build_signals_panel())
        self._panels.addWidget(self._build_chart_panel())
        self._panels.addWidget(self._build_portfolio_panel())
        self._panels.addWidget(self._build_journal_panel())
        self._panels.addWidget(self._build_risk_panel())
        self._panels.addWidget(self._build_aichat_panel())
        self._panels.addWidget(self._build_settings_panel())

        self._panel_index = {
            "dashboard": 0, "signals":   1, "chart":   2,
            "portfolio": 3, "journal":   4, "risk":    5,
            "aichat":    6, "settings":  7,
        }
        return main

    def _build_dashboard_panel(self):
        panel = QScrollArea()
        panel.setWidgetResizable(True)
        panel.setFrameShape(QFrame.NoFrame)
        panel.setStyleSheet(f"QScrollArea {{ background: {BG}; }}")

        content = QWidget()
        content.setStyleSheet(f"QWidget {{ background: {BG}; }}")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        panel.setWidget(content)

        stat_row = QHBoxLayout()
        stat_row.setSpacing(10)
        self._tiles = {}
        for key, lbl_text, default, color in [
            ("symbol", "Active Symbol", "AAPL",  TEXT),
            ("price",  "Last Price",    "—",     TEXT),
            ("signal", "Last Signal",   "—",     YELLOW),
            ("change", "Day Change",    "—",     TEXT2),
            ("volume", "Volume",        "—",     TEXT3),
            ("rr",     "Risk / Reward", "—",     TEAL),
        ]:
            tile = self._make_stat_tile(lbl_text, default, color)
            self._tiles[key] = tile
            stat_row.addWidget(tile)
        layout.addLayout(stat_row)

        chart_card = make_card()
        chart_card_layout = QVBoxLayout(chart_card)
        chart_card_layout.setContentsMargins(0, 0, 0, 0)
        chart_card_layout.setSpacing(0)

        chart_toolbar = QFrame()
        chart_toolbar.setFixedHeight(46)
        chart_toolbar.setStyleSheet(f"QFrame {{ background: {SURFACE}; border-bottom: 1px solid {BORDER}; }}")
        ctt = QHBoxLayout(chart_toolbar)
        ctt.setContentsMargins(14, 0, 14, 0)
        ctt.setSpacing(6)

        self._chart_title_lbl = QLabel("Price Chart")
        self._chart_title_lbl.setFont(QFont(SERIF_FONT, 12, QFont.Bold))
        self._chart_title_lbl.setStyleSheet(f"color: {TEXT}; background: transparent; border: none;")
        ctt.addWidget(self._chart_title_lbl)
        ctt.addStretch()

        self._symbol_combo = QComboBox()
        self._symbol_combo.addItems(WATCHLIST_SYMBOLS)
        self._symbol_combo.setFixedWidth(140)
        self._symbol_combo.currentTextChanged.connect(self._switch_symbol)
        ctt.addWidget(self._symbol_combo)

        for ivl in ["1m","5m","15m","1h","1d","1wk"]:
            btn = make_chart_btn(ivl.upper())
            btn.setChecked(ivl == self.current_interval)
            btn.clicked.connect(lambda _, i=ivl: self._set_interval(i))
            self._interval_btns[ivl] = btn
            ctt.addWidget(btn)

        chart_card_layout.addWidget(chart_toolbar)
        self._chart_widget = AdvancedChartWidget()
        self._chart_widget.setMinimumHeight(420)
        chart_card_layout.addWidget(self._chart_widget, 1)
        layout.addWidget(chart_card)

        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(12)

        signal_card = make_card(ACCENT)
        sig_layout  = QVBoxLayout(signal_card)
        sig_layout.setContentsMargins(14, 14, 14, 14)
        sig_layout.setSpacing(8)

        sig_hdr = QHBoxLayout()
        sig_card_title = QLabel("AI Signal")
        sig_card_title.setFont(QFont(SERIF_FONT, 12, QFont.Bold))
        sig_card_title.setStyleSheet(f"color: {TEXT}; background: transparent; border: none;")
        sig_hdr.addWidget(sig_card_title)
        sig_hdr.addStretch()
        self._sig_ts_lbl = QLabel("")
        self._sig_ts_lbl.setFont(QFont(MONO_FONT, 9))
        self._sig_ts_lbl.setStyleSheet(f"color: {TEXT3}; background: transparent; border: none;")
        sig_hdr.addWidget(self._sig_ts_lbl)
        sig_layout.addLayout(sig_hdr)

        sig_box = QFrame()
        sig_box.setStyleSheet(f"QFrame {{ background: {SURFACE2}; border: 1px solid {BORDER2}; }}")
        sig_box_layout = QVBoxLayout(sig_box)
        sig_box_layout.setContentsMargins(14, 14, 14, 14)
        sig_box_layout.setSpacing(10)

        top_row = QHBoxLayout()
        self._sig_dir_lbl = QLabel("—")
        self._sig_dir_lbl.setFont(QFont(SERIF_FONT, 28, QFont.Bold))
        self._sig_dir_lbl.setStyleSheet(f"color: {YELLOW}; background: transparent; border: none;")
        top_row.addWidget(self._sig_dir_lbl)
        top_row.addSpacing(16)

        meta_col  = QVBoxLayout()
        entry_col = QVBoxLayout()
        entry_col.addWidget(make_mono_label("Entry"))
        self._sig_entry = make_value_label("—")
        entry_col.addWidget(self._sig_entry)
        meta_col.addLayout(entry_col)

        sl_tp_row = QHBoxLayout()
        for attr_name, lbl_text, color in [("_sig_sl","Stop Loss",RED),("_sig_tp","Take Profit",GREEN)]:
            col = QVBoxLayout()
            col.addWidget(make_mono_label(lbl_text))
            val = make_value_label("—", color, 11)
            setattr(self, attr_name, val)
            col.addWidget(val)
            sl_tp_row.addLayout(col)
        meta_col.addLayout(sl_tp_row)

        rr_row_layout = QVBoxLayout()
        rr_row_layout.addWidget(make_mono_label("Risk / Reward"))
        self._sig_rr = make_value_label("—", TEAL, 11)
        rr_row_layout.addWidget(self._sig_rr)
        meta_col.addLayout(rr_row_layout)

        top_row.addLayout(meta_col, 1)
        sig_box_layout.addLayout(top_row)

        conf_bar = QProgressBar()
        conf_bar.setRange(0, 100)
        conf_bar.setValue(0)
        conf_bar.setFixedHeight(3)
        self._conf_bar = conf_bar
        sig_box_layout.addWidget(conf_bar)

        pattern_row = QHBoxLayout()
        self._sig_pattern_lbl = QLabel("Pattern: —")
        self._sig_pattern_lbl.setFont(QFont(MONO_FONT, 9))
        self._sig_pattern_lbl.setStyleSheet(f"color: {TEXT3}; background: transparent; border: none;")
        pattern_row.addWidget(self._sig_pattern_lbl)
        pattern_row.addStretch()
        self._sig_conf_pct = QLabel("0%")
        self._sig_conf_pct.setFont(QFont(MONO_FONT, 9))
        self._sig_conf_pct.setStyleSheet(f"color: {TEXT3}; background: transparent; border: none;")
        pattern_row.addWidget(self._sig_conf_pct)
        sig_box_layout.addLayout(pattern_row)

        self._sig_reason = QTextEdit()
        self._sig_reason.setReadOnly(True)
        self._sig_reason.setFixedHeight(120)
        self._sig_reason.setFont(QFont(MONO_FONT, 9))
        sig_box_layout.addWidget(self._sig_reason)

        badge_row = QHBoxLayout()
        badge_row.setSpacing(6)
        self._regime_badge = self._make_badge("REGIME",     TEXT3, SURFACE3)
        self._div_badge    = self._make_badge("DIVERGENCE", TEXT3, SURFACE3)
        self._vol_badge    = self._make_badge("VOLATILITY", TEXT3, SURFACE3)
        self._mtf_badge    = self._make_badge("MTF",        TEXT3, SURFACE3)
        for b in [self._regime_badge, self._div_badge, self._vol_badge, self._mtf_badge]:
            badge_row.addWidget(b)
        badge_row.addStretch()
        sig_box_layout.addLayout(badge_row)

        sig_layout.addWidget(sig_box)

        btn_row = QHBoxLayout()
        refresh_sig_btn = make_btn_primary("Refresh Signal")
        if QTA_OK:
            try:
                refresh_sig_btn.setIcon(qta.icon('fa5s.sync-alt', color="white"))
                refresh_sig_btn.setIconSize(QSize(13, 13))
            except Exception:
                pass
        refresh_sig_btn.clicked.connect(self._refresh_signal)
        btn_row.addWidget(refresh_sig_btn)

        add_trade_btn = make_btn_secondary("+ Add to Journal")
        add_trade_btn.clicked.connect(self._add_signal_to_journal)
        btn_row.addWidget(add_trade_btn)
        sig_layout.addLayout(btn_row)

        bottom_row.addWidget(signal_card, 3)

        ctrl_card   = make_card()
        ctrl_layout = QVBoxLayout(ctrl_card)
        ctrl_layout.setContentsMargins(14, 14, 14, 14)
        ctrl_layout.setSpacing(8)

        ctrl_title = QLabel("Chart Controls")
        ctrl_title.setFont(QFont(SERIF_FONT, 12, QFont.Bold))
        ctrl_title.setStyleSheet(f"color: {TEXT}; background: transparent; border: none;")
        ctrl_layout.addWidget(ctrl_title)

        chart_type_row = QHBoxLayout()
        candle_btn = make_chart_btn("Candlestick")
        candle_btn.setChecked(True)
        line_btn   = make_chart_btn("Line")

        def set_candle():
            candle_btn.setChecked(True); line_btn.setChecked(False)
            self._chart_widget.set_chart_type("candle")

        def set_line():
            line_btn.setChecked(True); candle_btn.setChecked(False)
            self._chart_widget.set_chart_type("line")

        candle_btn.clicked.connect(set_candle)
        line_btn.clicked.connect(set_line)
        chart_type_row.addWidget(candle_btn)
        chart_type_row.addWidget(line_btn)
        chart_type_row.addStretch()
        ctrl_layout.addLayout(chart_type_row)

        ctrl_layout.addWidget(make_separator())
        ctrl_layout.addWidget(make_mono_label("Overlays", size=9))

        for ind_name, lbl_text, default in [
            ("sma20",  "SMA 20",          True),
            ("sma50",  "SMA 50",          True),
            ("sma200", "SMA 200",         False),
            ("bb",     "Bollinger Bands", False),
            ("volume", "Volume Bars",     True),
            ("rsi",    "RSI Sub-chart",   False),
            ("macd",   "MACD Sub-chart",  False),
        ]:
            chk = QCheckBox(lbl_text)
            chk.setChecked(default)
            chk.stateChanged.connect(lambda state, n=ind_name: self._chart_widget.set_indicator(n, state == Qt.Checked))
            ctrl_layout.addWidget(chk)

        ai_chk = QCheckBox("AI Signal Levels")
        ai_chk.setChecked(False)
        ai_chk.stateChanged.connect(lambda state: self._chart_widget.set_indicator("ai_levels", state == Qt.Checked))
        ctrl_layout.addWidget(ai_chk)

        ctrl_layout.addWidget(make_separator())
        ctrl_layout.addWidget(make_mono_label("Signal History", size=9))

        self._sig_history_list = QListWidget()
        self._sig_history_list.setFixedHeight(120)
        ctrl_layout.addWidget(self._sig_history_list)

        ctrl_layout.addStretch()
        bottom_row.addWidget(ctrl_card, 2)
        layout.addLayout(bottom_row)
        return panel

    def _make_stat_tile(self, label, value, color=None):
        tile = QFrame()
        tile.setStyleSheet(f"QFrame {{ background: {SURFACE2}; border: 1px solid {BORDER}; }}")
        layout = QVBoxLayout(tile)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

        lbl = QLabel(label)
        lbl.setFont(QFont(MONO_FONT, 9))
        lbl.setStyleSheet(f"color: {TEXT3}; text-transform: uppercase; letter-spacing: 1px; background: transparent; border: none;")
        layout.addWidget(lbl)

        c   = color or TEXT
        val = QLabel(value)
        val.setFont(QFont(SERIF_FONT, 20, QFont.Bold))
        val.setStyleSheet(f"color: {c}; background: transparent; border: none;")
        layout.addWidget(val)

        tile.value_lbl = val
        return tile

    def _build_signals_panel(self):
        panel = QScrollArea()
        panel.setWidgetResizable(True)
        panel.setFrameShape(QFrame.NoFrame)
        panel.setStyleSheet(f"QScrollArea {{ background: {BG}; }}")

        content = QWidget()
        content.setStyleSheet(f"QWidget {{ background: {BG}; }}")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        panel.setWidget(content)

        hdr_row = QHBoxLayout()
        title = QLabel("Signal Scanner")
        title.setFont(QFont(SERIF_FONT, 16, QFont.Bold))
        title.setStyleSheet(f"color: {TEXT}; background: transparent;")
        hdr_row.addWidget(title)
        hdr_row.addStretch()

        self._scan_tf_combo = QComboBox()
        self._scan_tf_combo.addItems(["1m","5m","15m","1h","1d","1wk"])
        self._scan_tf_combo.setCurrentText("1d")
        self._scan_tf_combo.setFixedWidth(80)
        hdr_row.addWidget(self._scan_tf_combo)

        scan_btn = make_btn_primary("Scan All")
        scan_btn.clicked.connect(self._scan_all)
        hdr_row.addWidget(scan_btn)
        layout.addLayout(hdr_row)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(10)
        filter_row.addWidget(make_mono_label("Filter:", size=9))

        self._sig_filter_combo = QComboBox()
        self._sig_filter_combo.addItems(["All Signals","BUY only","SELL only","HOLD only"])
        self._sig_filter_combo.setFixedWidth(140)
        filter_row.addWidget(self._sig_filter_combo)

        filter_row.addWidget(make_mono_label("Min Conf:", size=9))
        self._min_conf_spin = QSpinBox()
        self._min_conf_spin.setRange(0, 99)
        self._min_conf_spin.setValue(50)
        self._min_conf_spin.setSuffix("%")
        self._min_conf_spin.setFixedWidth(80)
        filter_row.addWidget(self._min_conf_spin)

        self._scan_progress = QProgressBar()
        self._scan_progress.setFixedHeight(3)
        self._scan_progress.setVisible(False)
        filter_row.addWidget(self._scan_progress, 1)
        filter_row.addStretch()
        layout.addLayout(filter_row)

        summary_row = QHBoxLayout()
        summary_row.setSpacing(20)
        for attr, lbl_text, color in [
            ("_scan_total", "Scanned", TEXT2),
            ("_scan_buys",  "BUY",     GREEN),
            ("_scan_sells", "SELL",    RED),
            ("_scan_holds", "HOLD",    YELLOW),
        ]:
            col = QVBoxLayout()
            col.addWidget(make_mono_label(lbl_text, size=9))
            val = QLabel("0")
            val.setFont(QFont(SERIF_FONT, 18, QFont.Bold))
            val.setStyleSheet(f"color: {color}; background: transparent; border: none;")
            col.addWidget(val)
            setattr(self, attr, val)
            summary_row.addLayout(col)
        summary_row.addStretch()
        layout.addLayout(summary_row)

        sig_table_card = make_card()
        stl = QVBoxLayout(sig_table_card)
        stl.setContentsMargins(0, 0, 0, 0)

        self._signals_table = QTableWidget()
        self._signals_table.setColumnCount(8)
        self._signals_table.setHorizontalHeaderLabels(
            ["Symbol","Signal","Confidence","Entry","Stop Loss","Take Profit","R:R","Pattern"]
        )
        self._signals_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._signals_table.verticalHeader().setVisible(False)
        self._signals_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._signals_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._signals_table.setAlternatingRowColors(True)
        self._signals_table.setStyleSheet(f"QTableWidget {{ alternate-background-color: {SURFACE2}; }}")
        self._signals_table.setMinimumHeight(400)
        self._signals_table.doubleClicked.connect(self._on_signal_row_dblclick)
        stl.addWidget(self._signals_table)

        layout.addWidget(sig_table_card)
        layout.addStretch()
        return panel

    def _build_chart_panel(self):
        panel = QWidget()
        panel.setStyleSheet(f"QWidget {{ background: {BG}; }}")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        toolbar = QFrame()
        toolbar.setFixedHeight(46)
        toolbar.setStyleSheet(f"QFrame {{ background: {SURFACE}; border-bottom: 1px solid {BORDER}; }}")
        tt = QHBoxLayout(toolbar)
        tt.setContentsMargins(14, 0, 14, 0)
        tt.setSpacing(8)

        title = QLabel("Advanced Chart")
        title.setFont(QFont(SERIF_FONT, 12, QFont.Bold))
        title.setStyleSheet(f"color: {TEXT}; background: transparent; border: none;")
        tt.addWidget(title)
        tt.addStretch()

        self._chart2_sym = QComboBox()
        self._chart2_sym.addItems(WATCHLIST_SYMBOLS)
        self._chart2_sym.setFixedWidth(140)
        self._chart2_sym.currentTextChanged.connect(self._switch_symbol)
        tt.addWidget(self._chart2_sym)

        self._interval2_btns = {}
        for ivl in ["1m","5m","15m","1h","1d","1wk"]:
            btn = make_chart_btn(ivl.upper())
            btn.setChecked(ivl == self.current_interval)
            btn.clicked.connect(lambda _, i=ivl: self._set_interval(i))
            self._interval2_btns[ivl] = btn
            tt.addWidget(btn)

        layout.addWidget(toolbar)

        self._chart2_widget = AdvancedChartWidget()
        layout.addWidget(self._chart2_widget, 1)

        return panel

    def _build_portfolio_panel(self):
        panel = QScrollArea()
        panel.setWidgetResizable(True)
        panel.setFrameShape(QFrame.NoFrame)
        panel.setStyleSheet(f"QScrollArea {{ background: {BG}; }}")

        content = QWidget()
        content.setStyleSheet(f"QWidget {{ background: {BG}; }}")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        panel.setWidget(content)

        title = QLabel("Portfolio")
        title.setFont(QFont(SERIF_FONT, 16, QFont.Bold))
        title.setStyleSheet(f"color: {TEXT}; background: transparent;")
        layout.addWidget(title)

        metric_row = QHBoxLayout()
        metric_row.setSpacing(10)
        self._port_tiles = {}
        for key, lbl_text, color in [
            ("total_value","Portfolio Value",TEXT),
            ("total_pnl",  "Total P&L",     GREEN),
            ("win_rate",   "Win Rate",       TEAL),
            ("open_pos",   "Open Positions", TEXT2),
            ("closed_pos", "Closed Trades",  TEXT3),
        ]:
            tile = self._make_stat_tile(lbl_text, "—", color)
            self._port_tiles[key] = tile
            metric_row.addWidget(tile)
        layout.addLayout(metric_row)

        add_pos_card = make_card(ACCENT)
        add_pos_layout = QVBoxLayout(add_pos_card)
        add_pos_layout.setContentsMargins(14, 14, 14, 14)
        add_pos_layout.setSpacing(10)

        add_pos_title = QLabel("Add Position")
        add_pos_title.setFont(QFont(SERIF_FONT, 12, QFont.Bold))
        add_pos_title.setStyleSheet(f"color: {TEXT}; background: transparent; border: none;")
        add_pos_layout.addWidget(add_pos_title)

        fields_row = QHBoxLayout()
        fields_row.setSpacing(10)

        def labeled_field(label, placeholder, width=110):
            col = QVBoxLayout()
            col.addWidget(make_mono_label(label, size=8))
            le = QLineEdit()
            le.setPlaceholderText(placeholder)
            le.setFixedWidth(width)
            col.addWidget(le)
            return col, le

        col, self._port_sym   = labeled_field("Symbol",    "AAPL");       fields_row.addLayout(col)
        col, self._port_dir   = labeled_field("Direction", "BUY",    80); fields_row.addLayout(col)
        col, self._port_qty   = labeled_field("Qty",       "100",    70); fields_row.addLayout(col)
        col, self._port_entry = labeled_field("Entry $",   "150.00");     fields_row.addLayout(col)
        col, self._port_sl    = labeled_field("Stop Loss", "145.00");     fields_row.addLayout(col)
        col, self._port_tp    = labeled_field("Take Prof", "160.00");     fields_row.addLayout(col)

        fields_row.addStretch()
        add_btn = make_btn_primary("Add Position")
        add_btn.clicked.connect(self._add_position)
        fields_row.addWidget(add_btn)
        add_pos_layout.addLayout(fields_row)
        layout.addWidget(add_pos_card)

        tabs = QTabWidget()

        open_widget = QWidget()
        open_widget.setStyleSheet(f"QWidget {{ background: {BG}; }}")
        open_layout = QVBoxLayout(open_widget)
        open_layout.setContentsMargins(0, 8, 0, 0)
        open_layout.setSpacing(0)

        self._open_table = QTableWidget()
        self._open_table.setColumnCount(9)
        self._open_table.setHorizontalHeaderLabels(
            ["Symbol","Direction","Qty","Entry","Current","P&L","P&L %","Stop Loss","Take Profit"]
        )
        self._open_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._open_table.verticalHeader().setVisible(False)
        self._open_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._open_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._open_table.setAlternatingRowColors(True)
        self._open_table.setStyleSheet(f"QTableWidget {{ alternate-background-color: {SURFACE2}; }}")
        self._open_table.setMinimumHeight(220)
        open_layout.addWidget(self._open_table)

        btn_row_open = QHBoxLayout()
        btn_row_open.setContentsMargins(0, 8, 0, 0)
        btn_row_open.setSpacing(8)
        close_pos_btn = make_btn_secondary("Close Selected")
        close_pos_btn.clicked.connect(self._close_selected_position)
        btn_row_open.addWidget(close_pos_btn)
        refresh_pos_btn = make_btn_ghost("Refresh Prices")
        refresh_pos_btn.clicked.connect(self._refresh_position_prices)
        btn_row_open.addWidget(refresh_pos_btn)
        btn_row_open.addStretch()
        open_layout.addLayout(btn_row_open)
        tabs.addTab(open_widget, "Open Positions")

        closed_widget = QWidget()
        closed_widget.setStyleSheet(f"QWidget {{ background: {BG}; }}")
        closed_layout = QVBoxLayout(closed_widget)
        closed_layout.setContentsMargins(0, 8, 0, 0)

        self._closed_table = QTableWidget()
        self._closed_table.setColumnCount(8)
        self._closed_table.setHorizontalHeaderLabels(
            ["Symbol","Direction","Qty","Entry","Exit","P&L","P&L %","Date Closed"]
        )
        self._closed_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._closed_table.verticalHeader().setVisible(False)
        self._closed_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._closed_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._closed_table.setAlternatingRowColors(True)
        self._closed_table.setStyleSheet(f"QTableWidget {{ alternate-background-color: {SURFACE2}; }}")
        self._closed_table.setMinimumHeight(220)
        closed_layout.addWidget(self._closed_table)
        tabs.addTab(closed_widget, "Closed Trades")

        layout.addWidget(tabs)
        layout.addStretch()
        return panel

    def _add_position(self):
        sym   = self._port_sym.text().strip().upper()
        direc = self._port_dir.text().strip().upper()
        try:
            qty   = float(self._port_qty.text())
            entry = float(self._port_entry.text())
            sl    = float(self._port_sl.text())
            tp    = float(self._port_tp.text())
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter valid numeric values.")
            return
        if not sym:
            QMessageBox.warning(self, "Missing Symbol", "Please enter a symbol.")
            return

        trade = {
            "symbol": sym, "direction": direc, "qty": qty,
            "entry": entry, "current": entry, "sl": sl, "tp": tp,
            "status": "open", "opened_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        self._trades.append(trade)
        self._refresh_portfolio_tables()
        self._update_portfolio_metrics()
        for le in [self._port_sym, self._port_dir, self._port_qty,
                   self._port_entry, self._port_sl, self._port_tp]:
            le.clear()

    def _close_selected_position(self):
        row = self._open_table.currentRow()
        if row < 0:
            return
        open_trades = [t for t in self._trades if t["status"] == "open"]
        if row >= len(open_trades):
            return
        trade = open_trades[row]
        trade["status"]    = "closed"
        trade["exit"]      = trade["current"]
        trade["closed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        pnl_pct            = (trade["exit"] - trade["entry"]) / trade["entry"] * 100
        if trade["direction"] == "SELL":
            pnl_pct = -pnl_pct
        trade["pnl_pct"] = pnl_pct
        trade["pnl"]     = (trade["exit"] - trade["entry"]) * trade["qty"] * (1 if trade["direction"] == "BUY" else -1)
        self._refresh_portfolio_tables()
        self._update_portfolio_metrics()

    def _refresh_position_prices(self):
        open_trades = [t for t in self._trades if t["status"] == "open"]
        syms = list({t["symbol"] for t in open_trades})
        if not syms:
            return
        w = WatchlistPriceWorker(syms)
        w.prices_ready.connect(self._on_position_prices)
        self._workers.append(w)
        w.start()

    def _on_position_prices(self, prices: dict):
        for trade in self._trades:
            if trade["status"] == "open" and trade["symbol"] in prices:
                trade["current"] = prices[trade["symbol"]][0]
        self._refresh_portfolio_tables()
        self._update_portfolio_metrics()

    def _refresh_portfolio_tables(self):
        open_trades   = [t for t in self._trades if t["status"] == "open"]
        closed_trades = [t for t in self._trades if t["status"] == "closed"]

        self._open_table.setRowCount(len(open_trades))
        for r, t in enumerate(open_trades):
            pnl     = (t["current"] - t["entry"]) * t["qty"] * (1 if t["direction"] == "BUY" else -1)
            pnl_pct = (t["current"] - t["entry"]) / t["entry"] * 100 * (1 if t["direction"] == "BUY" else -1)
            pnl_col = GREEN if pnl >= 0 else RED
            for c, (val, color) in enumerate([
                (t["symbol"],              TEXT),
                (t["direction"],           GREEN if t["direction"] == "BUY" else RED),
                (str(t["qty"]),            TEXT2),
                (f"${t['entry']:,.2f}",    TEXT2),
                (f"${t['current']:,.2f}",  TEXT),
                (f"${pnl:+,.2f}",          pnl_col),
                (f"{pnl_pct:+.2f}%",       pnl_col),
                (f"${t['sl']:,.2f}",        RED),
                (f"${t['tp']:,.2f}",        GREEN),
            ]):
                item = QTableWidgetItem(val)
                item.setForeground(QColor(color))
                item.setTextAlignment(Qt.AlignCenter)
                self._open_table.setItem(r, c, item)

        self._closed_table.setRowCount(len(closed_trades))
        for r, t in enumerate(closed_trades):
            pnl     = t.get("pnl", 0)
            pnl_pct = t.get("pnl_pct", 0)
            pnl_col = GREEN if pnl >= 0 else RED
            for c, (val, color) in enumerate([
                (t["symbol"],              TEXT),
                (t["direction"],           GREEN if t["direction"] == "BUY" else RED),
                (str(t["qty"]),            TEXT2),
                (f"${t['entry']:,.2f}",    TEXT2),
                (f"${t.get('exit',0):,.2f}", TEXT2),
                (f"${pnl:+,.2f}",          pnl_col),
                (f"{pnl_pct:+.2f}%",       pnl_col),
                (t.get("closed_at", "—"),  TEXT3),
            ]):
                item = QTableWidgetItem(val)
                item.setForeground(QColor(color))
                item.setTextAlignment(Qt.AlignCenter)
                self._closed_table.setItem(r, c, item)

    def _update_portfolio_metrics(self):
        open_trades   = [t for t in self._trades if t["status"] == "open"]
        closed_trades = [t for t in self._trades if t["status"] == "closed"]
        total_value   = sum(t["current"] * t["qty"] for t in open_trades)
        total_pnl     = sum(t.get("pnl", 0) for t in closed_trades)
        total_pnl    += sum((t["current"] - t["entry"]) * t["qty"] *
                            (1 if t["direction"] == "BUY" else -1) for t in open_trades)
        wins     = [t for t in closed_trades if t.get("pnl", 0) > 0]
        win_rate = len(wins) / len(closed_trades) * 100 if closed_trades else 0
        pnl_color = GREEN if total_pnl >= 0 else RED
        sign      = "+" if total_pnl >= 0 else ""
        self._port_tiles["total_value"].value_lbl.setText(f"${total_value:,.2f}")
        self._port_tiles["total_pnl"].value_lbl.setText(f"{sign}${abs(total_pnl):,.2f}")
        self._port_tiles["total_pnl"].value_lbl.setStyleSheet(f"color: {pnl_color}; background: transparent; border: none;")
        self._port_tiles["win_rate"].value_lbl.setText(f"{win_rate:.1f}%")
        self._port_tiles["open_pos"].value_lbl.setText(str(len(open_trades)))
        self._port_tiles["closed_pos"].value_lbl.setText(str(len(closed_trades)))

    def _build_journal_panel(self):
        panel = QScrollArea()
        panel.setWidgetResizable(True)
        panel.setFrameShape(QFrame.NoFrame)
        panel.setStyleSheet(f"QScrollArea {{ background: {BG}; }}")

        content = QWidget()
        content.setStyleSheet(f"QWidget {{ background: {BG}; }}")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        panel.setWidget(content)

        title = QLabel("Trade Journal")
        title.setFont(QFont(SERIF_FONT, 16, QFont.Bold))
        title.setStyleSheet(f"color: {TEXT}; background: transparent;")
        layout.addWidget(title)

        desc = QLabel("Document your trades, thought process, and lessons learned.")
        desc.setFont(QFont(BODY_FONT, 11))
        desc.setStyleSheet(f"color: {TEXT3}; font-style: italic; background: transparent;")
        layout.addWidget(desc)

        entry_card   = make_card(ACCENT)
        entry_layout = QVBoxLayout(entry_card)
        entry_layout.setContentsMargins(14, 14, 14, 14)
        entry_layout.setSpacing(10)

        entry_title = QLabel("New Journal Entry")
        entry_title.setFont(QFont(SERIF_FONT, 12, QFont.Bold))
        entry_title.setStyleSheet(f"color: {TEXT}; background: transparent; border: none;")
        entry_layout.addWidget(entry_title)

        fields_row = QHBoxLayout()
        fields_row.setSpacing(10)

        def jfield(label, placeholder, width=110):
            col = QVBoxLayout()
            col.addWidget(make_mono_label(label, size=8))
            le = QLineEdit()
            le.setPlaceholderText(placeholder)
            le.setFixedWidth(width)
            col.addWidget(le)
            return col, le

        col, self._j_sym   = jfield("Symbol",    "AAPL");       fields_row.addLayout(col)
        col, self._j_dir   = jfield("Direction", "BUY",    80); fields_row.addLayout(col)
        col, self._j_entry = jfield("Entry $",   "150.00");     fields_row.addLayout(col)
        col, self._j_exit  = jfield("Exit $",    "155.00");     fields_row.addLayout(col)
        col, self._j_pnl   = jfield("P&L $",     "+500.00");    fields_row.addLayout(col)
        col, self._j_tags  = jfield("Tags",      "breakout, trend", 160); fields_row.addLayout(col)
        fields_row.addStretch()
        entry_layout.addLayout(fields_row)

        entry_layout.addWidget(make_mono_label("Notes / Reasoning", size=8))
        self._j_notes = QTextEdit()
        self._j_notes.setPlaceholderText("Describe your trade setup, entry reasoning, and any lessons learned...")
        self._j_notes.setFixedHeight(100)
        entry_layout.addWidget(self._j_notes)

        add_entry_btn = make_btn_primary("Save Entry")
        add_entry_btn.clicked.connect(self._save_journal_entry)
        entry_layout.addWidget(add_entry_btn)
        layout.addWidget(entry_card)

        journal_table_card = make_card()
        jtl = QVBoxLayout(journal_table_card)
        jtl.setContentsMargins(0, 0, 0, 0)

        self._journal_table = QTableWidget()
        self._journal_table.setColumnCount(7)
        self._journal_table.setHorizontalHeaderLabels(
            ["Date","Symbol","Direction","Entry","Exit","P&L","Tags"]
        )
        self._journal_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._journal_table.verticalHeader().setVisible(False)
        self._journal_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._journal_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._journal_table.setAlternatingRowColors(True)
        self._journal_table.setStyleSheet(f"QTableWidget {{ alternate-background-color: {SURFACE2}; }}")
        self._journal_table.setMinimumHeight(240)
        self._journal_table.clicked.connect(self._on_journal_row_click)
        jtl.addWidget(self._journal_table)

        notes_preview = QFrame()
        notes_preview.setStyleSheet(f"QFrame {{ background: {SURFACE2}; border-top: 1px solid {BORDER}; }}")
        np_layout = QVBoxLayout(notes_preview)
        np_layout.setContentsMargins(14, 10, 14, 10)
        np_layout.addWidget(make_mono_label("Notes Preview", size=8))
        self._journal_notes_preview = QTextEdit()
        self._journal_notes_preview.setReadOnly(True)
        self._journal_notes_preview.setFixedHeight(80)
        self._journal_notes_preview.setPlaceholderText("Click a row to view notes…")
        np_layout.addWidget(self._journal_notes_preview)
        jtl.addWidget(notes_preview)

        layout.addWidget(journal_table_card)
        layout.addStretch()
        return panel

    def _save_journal_entry(self):
        sym   = self._j_sym.text().strip().upper()
        direc = self._j_dir.text().strip().upper()
        entry = self._j_entry.text().strip()
        exit_ = self._j_exit.text().strip()
        pnl   = self._j_pnl.text().strip()
        tags  = self._j_tags.text().strip()
        notes = self._j_notes.toPlainText().strip()

        if not sym:
            QMessageBox.warning(self, "Missing Symbol", "Please enter a symbol.")
            return

        rec = {
            "date":      datetime.now().strftime("%Y-%m-%d %H:%M"),
            "symbol":    sym, "direction": direc, "entry": entry,
            "exit":      exit_, "pnl": pnl, "tags": tags, "notes": notes,
        }
        self._journal_entries.append(rec)
        self._refresh_journal_table()
        for le in [self._j_sym, self._j_dir, self._j_entry,
                   self._j_exit, self._j_pnl, self._j_tags]:
            le.clear()
        self._j_notes.clear()

    def _refresh_journal_table(self):
        self._journal_table.setRowCount(len(self._journal_entries))
        for r, rec in enumerate(self._journal_entries):
            pnl_val = 0.0
            try:
                pnl_val = float(rec["pnl"].replace("$","").replace(",",""))
            except Exception:
                pass
            pnl_color = GREEN if pnl_val >= 0 else RED
            for c, (val, color) in enumerate([
                (rec["date"],      TEXT3),
                (rec["symbol"],    TEXT),
                (rec["direction"], GREEN if rec["direction"] == "BUY" else RED),
                (rec["entry"],     TEXT2),
                (rec["exit"],      TEXT2),
                (rec["pnl"],       pnl_color),
                (rec["tags"],      TEXT3),
            ]):
                item = QTableWidgetItem(val)
                item.setForeground(QColor(color))
                item.setTextAlignment(Qt.AlignCenter)
                self._journal_table.setItem(r, c, item)

    def _on_journal_row_click(self, index):
        row = index.row()
        if 0 <= row < len(self._journal_entries):
            notes = self._journal_entries[row].get("notes","")
            self._journal_notes_preview.setPlainText(notes if notes else "No notes recorded.")

    def _add_signal_to_journal(self):
        if not self._signal_history:
            return
        sig = self._signal_history[-1]
        self._j_sym.setText(sig.symbol)
        self._j_dir.setText(sig.direction)
        self._j_entry.setText(f"{sig.entry_price:.2f}")
        self._j_exit.setText(f"{sig.take_profit:.2f}")
        self._j_tags.setText(sig.pattern)
        self._j_notes.setPlainText(sig.reasoning)
        self._switch_panel("journal")

    def _build_risk_panel(self):
        panel = QScrollArea()
        panel.setWidgetResizable(True)
        panel.setFrameShape(QFrame.NoFrame)
        panel.setStyleSheet(f"QScrollArea {{ background: {BG}; }}")

        content = QWidget()
        content.setStyleSheet(f"QWidget {{ background: {BG}; }}")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        panel.setWidget(content)

        title = QLabel("Risk Calculator")
        title.setFont(QFont(SERIF_FONT, 16, QFont.Bold))
        title.setStyleSheet(f"color: {TEXT}; background: transparent;")
        layout.addWidget(title)

        desc = QLabel("Calculate position size, risk-reward ratio, expected value, and breakeven probability.")
        desc.setFont(QFont(BODY_FONT, 11))
        desc.setStyleSheet(f"color: {TEXT3}; font-style: italic; background: transparent;")
        layout.addWidget(desc)

        main_row = QHBoxLayout()
        main_row.setSpacing(12)

        input_card   = make_card(ACCENT)
        input_layout = QVBoxLayout(input_card)
        input_layout.setContentsMargins(16, 16, 16, 16)
        input_layout.setSpacing(10)

        input_title = QLabel("Inputs")
        input_title.setFont(QFont(SERIF_FONT, 12, QFont.Bold))
        input_title.setStyleSheet(f"color: {TEXT}; background: transparent; border: none;")
        input_layout.addWidget(input_title)

        def risk_field(label, placeholder, default=""):
            col = QVBoxLayout()
            col.addWidget(make_mono_label(label, size=8))
            le = QLineEdit()
            le.setPlaceholderText(placeholder)
            le.setText(default)
            le.textChanged.connect(self._recalc_risk)
            col.addWidget(le)
            return col, le

        col, self._r_capital  = risk_field("Account Capital ($)", "e.g. 10000", "10000");  input_layout.addLayout(col)
        col, self._r_risk_pct = risk_field("Risk Per Trade (%)",  "e.g. 1.0",   "1.0");    input_layout.addLayout(col)
        col, self._r_entry    = risk_field("Entry Price ($)",     "e.g. 150.00","150.00"); input_layout.addLayout(col)
        col, self._r_sl       = risk_field("Stop Loss ($)",       "e.g. 145.00","145.00"); input_layout.addLayout(col)
        col, self._r_tp       = risk_field("Take Profit ($)",     "e.g. 162.00","162.00"); input_layout.addLayout(col)
        col, self._r_winrate  = risk_field("Est. Win Rate (%)",   "e.g. 55",    "55");     input_layout.addLayout(col)

        calc_btn = make_btn_primary("Calculate")
        calc_btn.clicked.connect(self._recalc_risk)
        input_layout.addWidget(calc_btn)
        input_layout.addStretch()
        main_row.addWidget(input_card, 1)

        results_card   = make_card()
        results_layout = QVBoxLayout(results_card)
        results_layout.setContentsMargins(16, 16, 16, 16)
        results_layout.setSpacing(10)

        results_title = QLabel("Results")
        results_title.setFont(QFont(SERIF_FONT, 12, QFont.Bold))
        results_title.setStyleSheet(f"color: {TEXT}; background: transparent; border: none;")
        results_layout.addWidget(results_title)

        self._risk_results = {}
        for key, lbl_text, color in [
            ("pos_size",    "Position Size (shares)", TEXT),
            ("dollar_risk", "Dollar Risk",            RED),
            ("rr_ratio",    "Risk : Reward",          TEAL),
            ("exp_value",   "Expected Value",         GREEN),
            ("breakeven",   "Breakeven Win Rate",     YELLOW),
            ("pot_profit",  "Potential Profit",       GREEN),
            ("pot_loss",    "Potential Loss",         RED),
        ]:
            row_frame = QFrame()
            row_frame.setStyleSheet(f"QFrame {{ background: {SURFACE2}; border: 1px solid {BORDER}; }}")
            row_layout = QHBoxLayout(row_frame)
            row_layout.setContentsMargins(12, 10, 12, 10)
            lbl = make_mono_label(lbl_text, size=9)
            row_layout.addWidget(lbl)
            row_layout.addStretch()
            val = make_value_label("—", color, 12)
            row_layout.addWidget(val)
            self._risk_results[key] = val
            results_layout.addWidget(row_frame)

        results_layout.addWidget(make_separator())

        self._risk_summary = QTextEdit()
        self._risk_summary.setReadOnly(True)
        self._risk_summary.setFixedHeight(100)
        self._risk_summary.setPlaceholderText("Risk summary will appear here after calculation…")
        results_layout.addWidget(self._risk_summary)

        results_layout.addStretch()
        main_row.addWidget(results_card, 1)
        layout.addLayout(main_row)
        layout.addStretch()
        return panel

    def _recalc_risk(self):
        try:
            capital  = float(self._r_capital.text())
            risk_pct = float(self._r_risk_pct.text()) / 100
            entry    = float(self._r_entry.text())
            sl       = float(self._r_sl.text())
            tp       = float(self._r_tp.text())
            win_rate = float(self._r_winrate.text()) / 100

            dollar_risk = capital * risk_pct
            risk_per_sh = abs(entry - sl)
            if risk_per_sh == 0:
                return
            pos_size   = dollar_risk / risk_per_sh
            pot_profit = pos_size * abs(tp - entry)
            pot_loss   = dollar_risk
            rr         = pot_profit / (pot_loss + 1e-9)
            exp_value  = (win_rate * pot_profit) - ((1 - win_rate) * pot_loss)
            breakeven  = 1 / (1 + rr) * 100

            self._risk_results["pos_size"].setText(f"{pos_size:.0f} shares")
            self._risk_results["dollar_risk"].setText(f"${dollar_risk:,.2f}")
            self._risk_results["rr_ratio"].setText(f"1 : {rr:.2f}")
            ev_color = GREEN if exp_value >= 0 else RED
            self._risk_results["exp_value"].setText(f"${exp_value:+,.2f}")
            self._risk_results["exp_value"].setStyleSheet(f"color: {ev_color}; background: transparent; border: none;")
            self._risk_results["breakeven"].setText(f"{breakeven:.1f}%")
            self._risk_results["pot_profit"].setText(f"${pot_profit:,.2f}")
            self._risk_results["pot_loss"].setText(f"${pot_loss:,.2f}")

            summary = (
                f"With ${capital:,.0f} capital risking {risk_pct*100:.1f}% per trade:\n"
                f"  • Buy {pos_size:.0f} shares at ${entry:.2f}\n"
                f"  • Risk ${pot_loss:,.2f}  |  Reward ${pot_profit:,.2f}  |  R:R 1:{rr:.2f}\n"
                f"  • At {win_rate*100:.0f}% win rate → Expected Value ${exp_value:+,.2f} per trade\n"
                f"  • Breakeven win rate: {breakeven:.1f}%"
            )
            self._risk_summary.setPlainText(summary)

        except (ValueError, ZeroDivisionError):
            pass

    def _build_aichat_panel(self):
        panel = QWidget()
        panel.setStyleSheet(f"QWidget {{ background: {BG}; }}")
        root = QVBoxLayout(panel)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        topbar = QFrame()
        topbar.setFixedHeight(52)
        topbar.setStyleSheet(f"QFrame {{ background: {SURFACE}; border-bottom: 1px solid {BORDER}; }}")
        tb = QHBoxLayout(topbar)
        tb.setContentsMargins(16, 0, 16, 0)
        tb.setSpacing(12)

        ai_icon = PaladinIcon(size=30)
        tb.addWidget(ai_icon)

        hdr_col = QVBoxLayout()
        hdr_col.setSpacing(0)
        hdr = QLabel("PALADIN  AI ANALYST")
        hdr.setFont(QFont(SERIF_FONT, 11, QFont.Bold))
        hdr.setStyleSheet(f"color: {TEXT}; background: transparent; letter-spacing: 2px;")
        hdr_col.addWidget(hdr)
        self._analyst_status = QLabel("Ready — select a symbol and click Analyse")
        self._analyst_status.setFont(QFont(MONO_FONT, 8))
        self._analyst_status.setStyleSheet(f"color: {TEXT3}; background: transparent;")
        hdr_col.addWidget(self._analyst_status)
        tb.addLayout(hdr_col)
        tb.addStretch()

        self._phase_dots = []
        phase_labels = ["Trend","Momentum","Volatility","Levels","Verdict"]
        for i, lbl in enumerate(phase_labels):
            dot_col = QVBoxLayout()
            dot_col.setSpacing(2)
            dot_col.setAlignment(Qt.AlignCenter)
            dot = QLabel("●")
            dot.setFont(QFont(MONO_FONT, 9))
            dot.setStyleSheet(f"color: {TEXT4}; background: transparent;")
            dot.setAlignment(Qt.AlignCenter)
            dot_lbl = QLabel(lbl)
            dot_lbl.setFont(QFont(MONO_FONT, 7))
            dot_lbl.setStyleSheet(f"color: {TEXT4}; background: transparent;")
            dot_lbl.setAlignment(Qt.AlignCenter)
            dot_col.addWidget(dot)
            dot_col.addWidget(dot_lbl)
            self._phase_dots.append(dot)
            tb.addLayout(dot_col)

        analyse_btn = make_btn_primary("Analyze")
        analyse_btn.setFixedHeight(34)
        analyse_btn.clicked.connect(self._run_live_analysis)
        tb.addWidget(analyse_btn)
        root.addWidget(topbar)

        body = QSplitter(Qt.Horizontal)
        body.setStyleSheet(f"QSplitter::handle {{ background: {BORDER}; width: 1px; }}")

        left = QWidget()
        left.setStyleSheet(f"QWidget {{ background: {BG}; }}")
        left_ly = QVBoxLayout(left)
        left_ly.setContentsMargins(12, 12, 8, 12)
        left_ly.setSpacing(8)

        phase_scroll = QScrollArea()
        phase_scroll.setWidgetResizable(True)
        phase_scroll.setFrameShape(QFrame.NoFrame)
        phase_scroll.setStyleSheet(f"QScrollArea {{ background: {BG}; border: none; }}")

        self._phase_cards_widget = QWidget()
        self._phase_cards_widget.setStyleSheet(f"QWidget {{ background: {BG}; }}")
        self._phase_cards_ly = QVBoxLayout(self._phase_cards_widget)
        self._phase_cards_ly.setSpacing(8)
        self._phase_cards_ly.setContentsMargins(0, 0, 0, 0)
        self._phase_cards_ly.addStretch()
        phase_scroll.setWidget(self._phase_cards_widget)
        left_ly.addWidget(phase_scroll, 1)

        self._typewriter_lbl = QLabel("Paladin is ready. Click ▶ Analyse to begin a live market scan.")
        self._typewriter_lbl.setFont(QFont(MONO_FONT, 9))
        self._typewriter_lbl.setStyleSheet(
            f"color: {TEXT3}; background: {SURFACE}; border: 1px solid {BORDER}; "
            f"padding: 8px 10px;"
        )
        self._typewriter_lbl.setWordWrap(True)
        self._typewriter_lbl.setFixedHeight(54)
        left_ly.addWidget(self._typewriter_lbl)

        body.addWidget(left)

        right = QWidget()
        right.setStyleSheet(f"QWidget {{ background: {BG}; }}")
        right_ly = QVBoxLayout(right)
        right_ly.setContentsMargins(8, 12, 12, 12)
        right_ly.setSpacing(8)

        chat_hdr = make_mono_label("Chat Terminal", size=9)
        right_ly.addWidget(chat_hdr)

        self._chat_display = QTextEdit()
        self._chat_display.setReadOnly(True)
        self._chat_display.setFont(QFont(MONO_FONT, 10))
        self._chat_display.setStyleSheet(f"""
            QTextEdit {{
                background: {SURFACE};
                color: {TEXT2};
                border: 1px solid {BORDER};
                padding: 10px;
                line-height: 1.7;
            }}
        """)
        right_ly.addWidget(self._chat_display, 1)

        quick_row = QHBoxLayout()
        quick_row.setSpacing(6)
        for qtext in [
            "Full Analysis",
            "Key Risks",
            "Entry Strategy",
            "Market Regime",
        ]:
            qbtn = make_btn_secondary(qtext)
            qbtn.setFont(QFont(MONO_FONT, 9))
            qbtn.clicked.connect(lambda _, t=qtext: self._send_chat(t))
            quick_row.addWidget(qbtn)
        quick_row.addStretch()
        right_ly.addLayout(quick_row)

        input_row = QHBoxLayout()
        input_row.setSpacing(8)
        self._chat_input = QLineEdit()
        self._chat_input.setPlaceholderText("Ask Paladin anything about this symbol…")
        self._chat_input.setFont(QFont(MONO_FONT, 11))
        self._chat_input.returnPressed.connect(lambda: self._send_chat(self._chat_input.text()))
        input_row.addWidget(self._chat_input, 1)

        send_btn = make_btn_primary("Send")
        if QTA_OK:
            try:
                send_btn.setIcon(qta.icon('fa5s.paper-plane', color="white"))
                send_btn.setIconSize(QSize(13, 13))
            except Exception:
                pass
        send_btn.clicked.connect(lambda: self._send_chat(self._chat_input.text()))
        input_row.addWidget(send_btn)

        clear_btn = make_btn_secondary("Clear")
        clear_btn.clicked.connect(self._chat_display.clear)
        input_row.addWidget(clear_btn)
        right_ly.addLayout(input_row)

        body.addWidget(right)
        body.setSizes([540, 460])
        root.addWidget(body, 1)

        self._chat_history        = []
        self._typewriter_queue    = []
        self._typewriter_idx      = 0
        self._typewriter_timer    = QTimer()
        self._typewriter_timer.timeout.connect(self._tick_typewriter)
        self._analysis_phase_cards = []
        return panel

    def _run_live_analysis(self):
        """Start a phased live analysis that draws chart annotations step-by-step."""
        if not self._brain:
            self._chat_display.append("\n[PALADIN]  AI engine not available.\n")
            return

        for card in self._analysis_phase_cards:
            card.setParent(None)
        self._analysis_phase_cards.clear()

        for dot in self._phase_dots:
            dot.setStyleSheet(f"color: {TEXT4}; background: transparent;")

        self._chart_widget.set_ai_phase(-1)
        self._chart_widget.set_ai_signal(None)

        self._analyst_status.setText(f"Scanning {self.current_symbol} on {self.current_interval}…")
        self._typewriter_lbl.setText("▌ Connecting to market data feed…")

        worker = LiveAnalysisWorker(self._brain, self.current_symbol, self.current_interval)
        worker.signal_ready.connect(self._on_live_signal_ready)
        worker.error.connect(lambda e: self._analyst_status.setText(f"Error: {e}"))
        self._workers.append(worker)
        worker.start()

    def _on_live_signal_ready(self, sig):
        """Signal is fetched — now sequence through phases with delays."""
        self._signal_history.append(sig)
        if len(self._signal_history) > 100:
            self._signal_history = self._signal_history[-100:]

        self._chart_widget.set_ai_signal(sig)
        self._chart_widget.set_ai_phase(-1)
        self._show_ai_levels_chk_sync(True)

        self._on_signal(sig)

        self._live_sig      = sig
        self._live_phase_i  = 0
        self._phase_delay   = 900

        self._phase_timer = QTimer()
        self._phase_timer.setSingleShot(True)
        self._phase_timer.timeout.connect(self._advance_analysis_phase)
        self._phase_timer.start(400)

    def _advance_analysis_phase(self):
        sig = self._live_sig
        i   = self._live_phase_i

        if i >= len(sig.phases):
            self._analyst_status.setText(
                f"Analysis complete — {self.current_symbol}  ·  "
                f"{sig.direction}  ·  {int(sig.confidence*100)}% confidence"
            )
            self._typewriter_lbl.setText(f"▶ {sig.phases[-1].title}: {sig.direction} — analysis complete.")
            return

        phase = sig.phases[i]

        verdict_colors = {
            "BULLISH": GREEN, "BEARISH": RED,
            "NEUTRAL": TEXT2, "CAUTION": YELLOW,
            "BUY": GREEN,    "SELL": RED, "HOLD": YELLOW,
        }
        dot_color = verdict_colors.get(phase.verdict, TEXT2)
        if i < len(self._phase_dots):
            self._phase_dots[i].setStyleSheet(f"color: {dot_color}; background: transparent;")

        self._chart_widget.set_ai_phase(i)

        card = self._make_phase_card(phase, dot_color)
        insert_idx = self._phase_cards_ly.count() - 1
        self._phase_cards_ly.insertWidget(insert_idx, card)
        self._analysis_phase_cards.append(card)

        self._analyst_status.setText(
            f"Phase {i+1}/5 — {phase.title}  [{phase.verdict}]"
        )

        self._start_typewriter(phase.detail[:160] + ("…" if len(phase.detail) > 160 else ""))

        self._live_phase_i += 1

        self._phase_timer = QTimer()
        self._phase_timer.setSingleShot(True)
        self._phase_timer.timeout.connect(self._advance_analysis_phase)
        self._phase_timer.start(self._phase_delay)

    def _make_phase_card(self, phase, color: str) -> QFrame:
        """Build a compact phase card widget."""
        verdict_bg = {
            GREEN: "#0a2a0a", RED: "#2a0a0a",
            YELLOW: "#2a2200", TEAL: "#002a2a", TEXT2: SURFACE2,
        }.get(color, SURFACE2)

        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background: {SURFACE}; border: 1px solid {BORDER2}; "
            f"border-left: 3px solid {color}; }}"
        )
        ly = QVBoxLayout(card)
        ly.setContentsMargins(12, 10, 12, 10)
        ly.setSpacing(4)

        hdr_row = QHBoxLayout()
        phase_tag = QLabel(f"PHASE {phase.phase + 1}")
        phase_tag.setFont(QFont(MONO_FONT, 7))
        phase_tag.setStyleSheet(f"color: {TEXT4}; background: transparent; border: none; letter-spacing: 2px;")
        hdr_row.addWidget(phase_tag)
        hdr_row.addStretch()
        verdict_lbl = QLabel(phase.verdict)
        verdict_lbl.setFont(QFont(MONO_FONT, 8, QFont.Bold))
        verdict_lbl.setStyleSheet(
            f"color: {color}; background: {verdict_bg}; border: 1px solid {BORDER2}; "
            f"padding: 1px 6px; border: none;"
        )
        hdr_row.addWidget(verdict_lbl)
        ly.addLayout(hdr_row)

        title_lbl = QLabel(phase.title)
        title_lbl.setFont(QFont(SERIF_FONT, 11, QFont.Bold))
        title_lbl.setStyleSheet(f"color: {TEXT}; background: transparent; border: none;")
        ly.addWidget(title_lbl)

        detail = QLabel(phase.detail[:200] + ("…" if len(phase.detail) > 200 else ""))
        detail.setFont(QFont(BODY_FONT, 9))
        detail.setStyleSheet(f"color: {TEXT3}; background: transparent; border: none;")
        detail.setWordWrap(True)
        ly.addWidget(detail)

        return card

    def _show_ai_levels_chk_sync(self, val: bool):
        """Enable AI level overlay on the chart without crashing if checkbox doesn't exist."""
        self._chart_widget.set_indicator("ai_levels", val)
        if hasattr(self, "_show_ai_chk"):
            self._show_ai_chk.setChecked(val)

    def _start_typewriter(self, text: str):
        self._typewriter_timer.stop()
        self._typewriter_full  = text
        self._typewriter_idx   = 0
        self._typewriter_timer.start(14)

    def _tick_typewriter(self):
        i = self._typewriter_idx
        if i >= len(self._typewriter_full):
            self._typewriter_timer.stop()
            return
        chunk = min(3, len(self._typewriter_full) - i)
        self._typewriter_lbl.setText(
            self._typewriter_full[:i + chunk] + "▌"
        )
        self._typewriter_idx += chunk

    def _send_chat(self, text: str):
        if not text.strip():
            return
        self._chat_input.clear()

        self._chat_history.append({"role": "user", "content": text})
        if len(self._chat_history) > 20:
            self._chat_history = self._chat_history[-20:]

        ts = datetime.now().strftime("%H:%M:%S")
        self._chat_display.append(
            f'\n<span style="color:{TEXT3};">[{ts}]</span> '
            f'<span style="color:{TEXT}; font-weight:bold;">YOU</span>  {text}\n'
        )
        self._chat_display.append(
            f'<span style="color:{ACCENT}; font-weight:bold;">PALADIN</span>  '
            f'<span style="color:{TEXT4};">▌ Analysing…</span>\n'
        )
        QApplication.processEvents()

        worker = AIChatWorker(
            self._brain, self.current_symbol, self.current_interval,
            text, list(self._chat_history)
        )
        worker.reply_ready.connect(self._on_chat_reply)
        worker.error.connect(lambda e: self._on_chat_reply(f"Error: {e}"))
        self._workers.append(worker)
        worker.start()

    def _on_chat_reply(self, reply: str):
        cursor = self._chat_display.textCursor()
        doc    = self._chat_display.document()
        block  = doc.lastBlock()
        while block.isValid():
            if "Analysing" in block.text() or "▌" in block.text():
                cursor.setPosition(block.position())
                cursor.select(cursor.BlockUnderCursor)
                cursor.removeSelectedText()
                cursor.deleteChar()
                break
            block = block.previous()

        ts = datetime.now().strftime("%H:%M:%S")
        colored = reply
        for word, col in [("BUY", GREEN), ("SELL", RED), ("HOLD", YELLOW),
                          ("BULLISH", GREEN), ("BEARISH", RED), ("NEUTRAL", TEXT2)]:
            colored = colored.replace(
                word, f'<span style="color:{col}; font-weight:bold;">{word}</span>'
            )

        self._chat_display.append(
            f'<span style="color:{TEXT3};">[{ts}]</span> '
            f'<span style="color:{ACCENT}; font-weight:bold;">PALADIN</span>'
        )
        self._chat_display.append(colored + "\n")
        self._chat_display.verticalScrollBar().setValue(
            self._chat_display.verticalScrollBar().maximum()
        )
        self._chat_history.append({"role": "assistant", "content": reply})

    def _build_settings_panel(self):
        panel = QScrollArea()
        panel.setWidgetResizable(True)
        panel.setFrameShape(QFrame.NoFrame)
        panel.setStyleSheet(f"QScrollArea {{ background: {BG}; }}")

        content = QWidget()
        content.setStyleSheet(f"QWidget {{ background: {BG}; }}")
        layout  = QVBoxLayout(content)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        panel.setWidget(content)

        title = QLabel("Settings")
        title.setFont(QFont(SERIF_FONT, 16, QFont.Bold))
        title.setStyleSheet(f"color: {TEXT}; background: transparent;")
        layout.addWidget(title)

        pref_card   = make_card(ACCENT)
        pref_layout = QVBoxLayout(pref_card)
        pref_layout.setContentsMargins(16, 16, 16, 16)
        pref_layout.setSpacing(12)

        pref_title = QLabel("Preferences")
        pref_title.setFont(QFont(SERIF_FONT, 12, QFont.Bold))
        pref_title.setStyleSheet(f"color: {TEXT}; background: transparent; border: none;")
        pref_layout.addWidget(pref_title)

        default_tf_row = QHBoxLayout()
        default_tf_row.addWidget(make_mono_label("Default Timeframe", size=9))
        self._settings_tf = QComboBox()
        self._settings_tf.addItems(["1m","5m","15m","1h","1d","1wk"])
        self._settings_tf.setCurrentText(self.current_interval)
        self._settings_tf.setFixedWidth(100)
        self._settings_tf.currentTextChanged.connect(lambda v: self._set_interval(v))
        default_tf_row.addWidget(self._settings_tf)
        default_tf_row.addStretch()
        pref_layout.addLayout(default_tf_row)

        autosig_chk = QCheckBox("Auto-refresh signal every 30 seconds")
        autosig_chk.setChecked(True)
        autosig_chk.stateChanged.connect(lambda s: self._auto_timer.start(30000) if s else self._auto_timer.stop())
        pref_layout.addWidget(autosig_chk)

        layout.addWidget(pref_card)

        about_card   = make_card()
        about_layout = QVBoxLayout(about_card)
        about_layout.setContentsMargins(16, 16, 16, 16)
        about_layout.setSpacing(8)

        about_title = QLabel("About Paladin")
        about_title.setFont(QFont(SERIF_FONT, 12, QFont.Bold))
        about_title.setStyleSheet(f"color: {TEXT}; background: transparent; border: none;")
        about_layout.addWidget(about_title)

        for line in [
            "Paladin AI Trading Platform  ·  Professional Edition",
            "LightGBM ensemble  ·  isotonic confidence calibration",
            "50+ technical features  ·  multi-timeframe pattern recognition",
            "yfinance data feed  ·  real-time watchlist pricing",
        ]:
            lbl = QLabel(line)
            lbl.setFont(QFont(BODY_FONT, 11))
            lbl.setStyleSheet(f"color: {TEXT3}; background: transparent; border: none;")
            about_layout.addWidget(lbl)

        layout.addWidget(about_card)
        layout.addStretch()
        return panel

    def _switch_panel(self, panel_id: str):
        idx = self._panel_index.get(panel_id, 0)
        self._panels.setCurrentIndex(idx)
        for pid, btn in self._nav_btns.items():
            btn.setChecked(pid == panel_id)

    def _switch_symbol(self, sym: str):
        self.current_symbol = sym
        self._settings.setValue("last_symbol", sym)
        idx = self._symbol_combo.findText(sym)
        if idx >= 0:
            self._symbol_combo.setCurrentIndex(idx)
        self._tiles["symbol"].value_lbl.setText(sym)
        self._chart_widget.set_symbol(sym)
        self._chart_title_lbl.setText(f"{sym}  ·  {self.current_interval.upper()}")
        self._load_chart()
        self._refresh_signal()

    def _set_interval(self, iv: str):
        self.current_interval = iv
        self._settings.setValue("last_interval", iv)
        for k, btn in self._interval_btns.items():
            btn.setChecked(k == iv)
        for k, btn in self._interval2_btns.items() if hasattr(self, "_interval2_btns") else {}:
            btn.setChecked(k == iv)
        self._chart_widget.set_interval(iv)
        self._chart_title_lbl.setText(f"{self.current_symbol}  ·  {iv.upper()}")
        self._load_chart()
        self._refresh_signal()

    def _load_chart(self):
        self._chart_widget.set_symbol(self.current_symbol)
        self._chart_widget.set_interval(self.current_interval)
        w = YFinanceWorker(self.current_symbol, self.current_interval)
        w.data_ready.connect(self._on_chart_data)
        w.error_occurred.connect(self._chart_widget.show_error)
        self._workers.append(w)
        w.start()

    def _on_chart_data(self, df):
        self._chart_widget.plot(df)
        if hasattr(self, "_chart2_widget"):
            self._chart2_widget.set_symbol(self.current_symbol)
            self._chart2_widget.set_interval(self.current_interval)
            self._chart2_widget.plot(df)
        last = df["close"].iloc[-1]
        prev = df["close"].iloc[-2] if len(df) > 1 else last
        chg  = (last / prev - 1) * 100
        vol  = df["volume"].iloc[-1]
        sign = "+" if chg >= 0 else ""
        chg_color = GREEN if chg >= 0 else RED
        self._tiles["price"].value_lbl.setText(f"${last:,.2f}")
        self._tiles["change"].value_lbl.setText(f"{sign}{chg:.2f}%")
        self._tiles["change"].value_lbl.setStyleSheet(f"color: {chg_color}; background: transparent; border: none;")
        self._tiles["volume"].value_lbl.setText(f"{vol/1e6:.1f}M" if vol >= 1e6 else f"{vol/1e3:.0f}K")

    def _refresh_signal(self):
        if not self._brain:
            self._sig_dir_lbl.setText("—")
            self._sig_dir_lbl.setStyleSheet(f"color: {TEXT3}; background: transparent; border: none;")
            return
        w = SignalWorker(self._brain, self.current_symbol, self.current_interval)
        w.signal_ready.connect(self._on_signal)
        w.error_occurred.connect(lambda e: self._set_status(f"Signal error: {e}"))
        self._workers.append(w)
        w.start()

    def _on_signal(self, sig):
        self._signal_history.append(sig)
        if len(self._signal_history) > 100:
            self._signal_history = self._signal_history[-100:]

        self._chart_widget.set_ai_signal(sig)

        dir_colors = {"BUY": GREEN, "SELL": RED, "HOLD": YELLOW}
        color      = dir_colors.get(sig.direction, TEXT2)

        self._sig_dir_lbl.setText(sig.direction)
        self._sig_dir_lbl.setStyleSheet(f"color: {color}; background: transparent; border: none;")
        self._sig_entry.setText(f"${sig.entry_price:,.2f}")
        self._sig_sl.setText(f"${sig.stop_loss:,.2f}")
        self._sig_tp.setText(f"${sig.take_profit:,.2f}")

        rr_text = "∞" if sig.risk_reward > 100 else f"{sig.risk_reward:.2f}"
        self._sig_rr.setText(f"1 : {rr_text}")
        self._sig_ts_lbl.setText(datetime.now().strftime("%H:%M:%S"))
        self._sig_pattern_lbl.setText(f"Pattern: {sig.pattern}")

        conf_pct = int(sig.confidence * 100)
        self._conf_bar.setValue(conf_pct)
        self._sig_conf_pct.setText(f"{conf_pct}%")

        if hasattr(sig, "phases") and sig.phases:
            lines = []
            for ph in sig.phases:
                lines.append(f"▶ {ph.title}  [{ph.verdict}]")
                lines.append(ph.detail[:180] + ("…" if len(ph.detail) > 180 else ""))
                lines.append("")
            self._sig_reason.setPlainText("\n".join(lines))
        else:
            self._sig_reason.setPlainText(sig.reasoning)

        self._tiles["signal"].value_lbl.setText(sig.direction)
        self._tiles["signal"].value_lbl.setStyleSheet(f"color: {color}; background: transparent; border: none;")
        self._tiles["rr"].value_lbl.setText(f"1:{rr_text}")

        hist_item = QListWidgetItem(
            f"{datetime.now().strftime('%H:%M')}  {sig.symbol}  {sig.direction}  {conf_pct}%"
        )
        hist_item.setForeground(QColor(color))
        hist_item.setFont(QFont(MONO_FONT, 9))
        self._sig_history_list.insertItem(0, hist_item)
        if self._sig_history_list.count() > 50:
            self._sig_history_list.takeItem(self._sig_history_list.count() - 1)

        self._update_signal_badges(sig)
        self._set_status(
            f"Signal: {sig.direction}  ·  Confidence {conf_pct}%  ·  "
            f"Confluence: {getattr(sig,'confluence',0)} signals  ·  Pattern: {sig.pattern}"
        )

    def _make_badge(self, text, color, bg):
        lbl = QLabel(text)
        lbl.setFont(QFont(MONO_FONT, 8))
        lbl.setStyleSheet(f"color: {color}; background: {bg}; border: 1px solid {BORDER2}; padding: 2px 6px;")
        lbl.setAlignment(Qt.AlignCenter)
        return lbl

    def _update_signal_badges(self, sig):
        regime    = getattr(sig, "regime",    None)
        divergence= getattr(sig, "divergence",None)
        vol_state = getattr(sig, "vol_state", None)
        reason    = sig.reasoning

        if regime is None:
            if "fully stacked bullish" in reason or "Golden Cross" in reason:
                regime = "BULL TREND"
            elif "fully stacked bearish" in reason or "Death Cross" in reason:
                regime = "BEAR TREND"
            elif "squeeze" in reason:
                regime = "COMPRESSION"
            else:
                regime = "RANGING"

        regime_styles = {
            "BULL TREND":  (GREEN,  "#0a2a0a"),
            "BEAR TREND":  (RED,    "#2a0a0a"),
            "COMPRESSION": (YELLOW, "#2a2200"),
            "RANGING":     (TEXT2,  SURFACE3),
        }
        rc, rbg = regime_styles.get(regime, (TEXT2, SURFACE3))
        self._regime_badge.setText(regime)
        self._regime_badge.setStyleSheet(
            f"color: {rc}; background: {rbg}; border: 1px solid {BORDER2}; padding: 2px 6px;"
        )

        if divergence is None:
            if "bullish divergence" in reason: divergence = "BULL DIV"
            elif "bearish divergence" in reason: divergence = "BEAR DIV"
            else: divergence = "NONE"

        if divergence == "BULL DIV":
            dc, dbg, dtxt = GREEN, "#0a2a0a", "BULL DIV"
        elif divergence == "BEAR DIV":
            dc, dbg, dtxt = RED, "#2a0a0a", "BEAR DIV"
        else:
            dc, dbg, dtxt = TEXT3, SURFACE3, "NO DIV"
        self._div_badge.setText(dtxt)
        self._div_badge.setStyleSheet(
            f"color: {dc}; background: {dbg}; border: 1px solid {BORDER2}; padding: 2px 6px;"
        )

        if vol_state is None:
            vol_state = "HIGH" if "expanded" in reason else ("LOW" if "low conviction" in reason else "NORMAL")

        vol_styles = {
            "HIGH":    (YELLOW, "#2a2200", "HIGH VOL"),
            "SQUEEZE": (PURPLE, "#1a0a2a", "SQUEEZE"),
            "LOW":     (TEXT3,  SURFACE3,  "LOW VOL"),
            "NORMAL":  (TEAL,   "#002a2a", "NORMAL VOL"),
        }
        vc, vbg, vtxt = vol_styles.get(vol_state, (TEAL, "#002a2a", "NORMAL VOL"))
        self._vol_badge.setText(vtxt)
        self._vol_badge.setStyleSheet(
            f"color: {vc}; background: {vbg}; border: 1px solid {BORDER2}; padding: 2px 6px;"
        )

        conf = sig.confidence
        if conf >= 0.70:   mc, mbg, mtxt = GREEN,  "#0a2a0a", "HIGH CONF"
        elif conf >= 0.55: mc, mbg, mtxt = YELLOW, "#2a2200", "MED CONF"
        else:              mc, mbg, mtxt = RED,    "#2a0a0a", "LOW CONF"
        self._mtf_badge.setText(mtxt)
        self._mtf_badge.setStyleSheet(
            f"color: {mc}; background: {mbg}; border: 1px solid {BORDER2}; padding: 2px 6px;"
        )

    def _scan_all(self):
        if not self._brain:
            QMessageBox.warning(self, "Unavailable", "AI brain is not available.")
            return
        self._signals_table.setRowCount(0)
        self._scan_buys.setText("0")
        self._scan_sells.setText("0")
        self._scan_holds.setText("0")
        self._scan_total.setText("0")
        self._scan_progress.setVisible(True)
        self._scan_progress.setRange(0, len(WATCHLIST_SYMBOLS))
        self._scan_progress.setValue(0)
        self._scan_counter = 0
        self._scan_counts  = {"BUY": 0, "SELL": 0, "HOLD": 0}

        tf     = self._scan_tf_combo.currentText()
        worker = ScanWorker(self._brain, WATCHLIST_SYMBOLS, tf)
        worker.result_ready.connect(self._on_scan_result)
        worker.all_done.connect(self._on_scan_done)
        self._workers.append(worker)
        worker.start()

    def _on_scan_result(self, symbol: str, sig):
        min_conf = self._min_conf_spin.value() / 100
        filt     = self._sig_filter_combo.currentText()

        if sig.confidence < min_conf:
            self._scan_counter += 1
            self._scan_progress.setValue(self._scan_counter)
            return

        if filt == "BUY only"  and sig.direction != "BUY":
            self._scan_counter += 1; self._scan_progress.setValue(self._scan_counter); return
        if filt == "SELL only" and sig.direction != "SELL":
            self._scan_counter += 1; self._scan_progress.setValue(self._scan_counter); return
        if filt == "HOLD only" and sig.direction != "HOLD":
            self._scan_counter += 1; self._scan_progress.setValue(self._scan_counter); return

        dir_colors = {"BUY": GREEN, "SELL": RED, "HOLD": YELLOW}
        color      = dir_colors.get(sig.direction, TEXT2)
        conf_pct   = int(sig.confidence * 100)

        row = self._signals_table.rowCount()
        self._signals_table.insertRow(row)

        rr_text = "∞" if sig.risk_reward > 100 else f"{sig.risk_reward:.2f}"

        for c, (val, clr) in enumerate([
            (sig.symbol,                TEXT),
            (sig.direction,             color),
            (f"{conf_pct}%",            color),
            (f"${sig.entry_price:,.2f}", TEXT2),
            (f"${sig.stop_loss:,.2f}",   RED),
            (f"${sig.take_profit:,.2f}", GREEN),
            (f"1:{rr_text}",            TEAL),
            (sig.pattern,               TEXT3),
        ]):
            item = QTableWidgetItem(val)
            item.setForeground(QColor(clr))
            item.setTextAlignment(Qt.AlignCenter)
            self._signals_table.setItem(row, c, item)

        self._scan_counts[sig.direction] = self._scan_counts.get(sig.direction, 0) + 1
        self._scan_counter += 1
        self._scan_progress.setValue(self._scan_counter)
        self._scan_total.setText(str(self._scan_counter))
        self._scan_buys.setText(str(self._scan_counts.get("BUY", 0)))
        self._scan_sells.setText(str(self._scan_counts.get("SELL", 0)))
        self._scan_holds.setText(str(self._scan_counts.get("HOLD", 0)))

    def _on_scan_done(self):
        self._scan_progress.setVisible(False)
        self._set_status(
            f"Scan complete  ·  {self._scan_counter} symbols scanned  ·  "
            f"BUY: {self._scan_counts.get('BUY',0)}  "
            f"SELL: {self._scan_counts.get('SELL',0)}  "
            f"HOLD: {self._scan_counts.get('HOLD',0)}"
        )

    def _on_signal_row_dblclick(self, index):
        row      = index.row()
        sym_item = self._signals_table.item(row, 0)
        if sym_item:
            self._switch_symbol(sym_item.text())
            self._switch_panel("dashboard")

    def _set_status(self, msg: str):
        if hasattr(self, "_status_msg"):
            self._status_msg.setText(msg)


class LoadingThread(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal()

    def __init__(self, brain_holder: list):
        super().__init__()
        self._brain_holder = brain_holder

    def run(self):
        self.progress.emit(10,  "Loading Qt framework…")
        time.sleep(0.3)
        self.progress.emit(25,  "Initialising colour theme…")
        time.sleep(0.2)
        self.progress.emit(40,  "Checking yfinance connection…")
        time.sleep(0.4)
        self.progress.emit(55,  "Loading AI engine…")
        if BRAIN_AVAILABLE:
            try:
                brain = get_brain_v2()
                self._brain_holder.append(brain)
                self.progress.emit(75, "AI engine loaded — LightGBM ready")
            except Exception as e:
                self.progress.emit(75, f"AI engine warning: {e}")
        else:
            self.progress.emit(75, "AI engine unavailable — running in data-only mode")
        time.sleep(0.3)
        self.progress.emit(88, "Building interface…")
        time.sleep(0.3)
        self.progress.emit(100,"Ready — launching Paladin…")
        time.sleep(0.2)
        self.finished.emit()


def main():
    app = QApplication(sys.argv)
    if PALADIN_ICON_PATH.is_file():
        app.setWindowIcon(QIcon(str(PALADIN_ICON_PATH)))
    app.setStyleSheet(GLOBAL_QSS)
    app.setApplicationName("Paladin Trading Platform")
    app.setOrganizationName("Paladin")

    welcome = WelcomeScreen()
    welcome.show()

    brain_holder: list = []
    loader = LoadingThread(brain_holder)
    loader.progress.connect(welcome.update_progress)

    done_flag = [False]

    def on_welcome_finished():
        done_flag[0] = True

    welcome.finished.connect(on_welcome_finished)
    loader.start()

    while not done_flag[0]:
        app.processEvents()
        time.sleep(0.01)

    welcome.close()

    SETUP_FLOW_VERSION = 2
    _settings_check = QSettings("Paladin", "TradingPlatform")
    try:
        _cur_setup = int(_settings_check.value("setup_flow_version", 0) or 0)
    except (TypeError, ValueError):
        _cur_setup = 0
    if _cur_setup < SETUP_FLOW_VERSION:
        _settings_check.remove("selected_piece")
        _settings_check.setValue("setup_flow_version", SETUP_FLOW_VERSION)

    saved_piece      = _settings_check.value("selected_piece", "")
    if saved_piece and saved_piece in CHESS_PIECES:
        selected_piece = saved_piece
    else:
        wizard = SetupWizard()
        if wizard.exec_() != QDialog.Accepted or not wizard.selected_piece:
            sys.exit(0)
        selected_piece = wizard.selected_piece
        _settings_check.setValue("selected_piece", selected_piece)

    dashboard = TradingDashboard(selected_piece)
    if brain_holder:
        dashboard._brain = brain_holder[0]
    dashboard.showMaximized()

    if TRANSLATOR_AVAILABLE:
        install_translator(app, "en")

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()