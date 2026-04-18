<!-- Icons: Font Awesome 6.5.1 Free — solid (`fas`) + brands (`fab`) SVGs via jsDelivr (FortAwesome/Font-Awesome) -->

<div align="center">

<img src="../PALADIN/DATABASE/Paladin_Icon.png" width="120" height="120" alt="Paladin" style="margin-top: 10px;" />

**Paladin: Dependencies & Setup**

*Desktop market analytics and signal generation for institutional-style workflows*

[![Python](https://img.shields.io/badge/python-3.11-941107?style=flat-square&logo=python&logoColor=f5f5f5&labelColor=0a0a0a)](https://www.python.org/downloads/)
[![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-941107?style=flat-square&labelColor=0a0a0a)](https://pypi.org/project/PyQt5/)
[![License](https://img.shields.io/badge/License-Proprietary-941107?style=flat-square&labelColor=0a0a0a)](#license)

<br/>

</div>

---

## <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/solid/list-ul.svg" width="20" height="20" alt="" /> Dependencies

Pinned versions and optional lines (e.g. MetaTrader5) are maintained in **`PALADIN/requirements.txt`**. Install with:

```bash
pip install -r requirements.txt
```

> Run from the `PALADIN/` directory with your virtual environment active.

### <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/solid/globe.svg" width="16" height="16" alt="" /> Core Framework & Data APIs

| Package | Version | Purpose |
|--:|:---:|:---|
| flask | >= 3.0 | Lightweight WSGI web application framework |
| flask-cors | >= 4.0 | Cross-Origin Resource Sharing extension for Flask endpoints |
| yfinance | >= 0.2.40 | Market data retrieval API for historical and live OHLCV data |

### <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/solid/microchip.svg" width="16" height="16" alt="" /> Data Processing & Machine Learning

| Package | Version | Purpose |
|--:|:---:|:---|
| pandas | >= 2.0 | Data manipulation and time-series analysis |
| numpy | >= 1.26 | Numerical computing and array utilities |
| scikit-learn | >= 1.4 | ML algorithms, scaling, and modeling tools |
| joblib | >= 1.3 | Model serialization and lightweight pipelining |
| lightgbm | >= 4.0 | Calibrated gradient boosting ensemble (primary brain) |
| xgboost | >= 2.0 | Optimized gradient boosting for pattern recognition |
| onnxruntime | >= 1.17 | ONNX graph inference for transformer-based signals |

### <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/solid/chart-line.svg" width="16" height="16" alt="" /> Technical Analysis

| Package | Version | Platform | Purpose |
|--:|:---:|:---:|:---|
| talib-binary | >= 0.4.28 | Linux / macOS | Precompiled TA library (avoids C build) |
| TA-Lib | >= 0.4.28 | Windows | Standard Technical Analysis library wrapper |

### <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/solid/display.svg" width="16" height="16" alt="" /> Visualization & Interface

| Package | Version | Purpose |
|--:|:---:|:---|
| PyQt5 | >= 5.15 | Qt5 framework for the desktop GUI |
| matplotlib | >= 3.7 | Static and interactive charting (candlesticks, overlays) |
| plotly | >= 5.17 | Interactive browser-based graphing library |
| qtawesome | >= 1.3 | Font Awesome icon integration for PyQt5 widgets |

### <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/solid/robot.svg" width="16" height="16" alt="" /> Local AI Integration

| Package | Version | Purpose |
|--:|:---:|:---|
| gpt4all | >= 2.7 | Local LLM inference engine for on-device AI processing |

### <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/solid/plug.svg" width="16" height="16" alt="" /> Optional Integrations

| Package | Version | Purpose |
|--:|:---:|:---|
| MetaTrader5 | >= 5.0 | Integration with MetaTrader 5 for live broker execution |

> [!NOTE]
> To enable **MetaTrader5**, uncomment the respective line in `requirements.txt` before running `pip install -r requirements.txt`.

---

<p align="center"><sub><img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/solid/file-lines.svg" width="14" height="14" alt="" /> Document <strong>v1.0</strong> · Last updated <strong>April 17, 2026</strong><br />Icons: <a href="https://fontawesome.com/">Font Awesome</a> 6 Free (CC BY 4.0)</sub></p>