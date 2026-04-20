<!-- Icons: Font Awesome 6.5.1 Free — solid (`fas`) + brands (`fab`) SVGs via jsDelivr (FortAwesome/Font-Awesome) -->

<div align="center">

<img src="./PALADIN/DATABASE/Paladin_Icon.png" width="120" height="120" alt="Paladin" style="margin-top: 10px;" />

**Paladin**

*Desktop market analytics and signal generation for institutional-style workflows*

[![Python](https://img.shields.io/badge/python-3.11-941107?style=flat-square&logo=python&logoColor=f5f5f5&labelColor=0a0a0a)](https://www.python.org/downloads/)
[![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-941107?style=flat-square&labelColor=0a0a0a)](https://pypi.org/project/PyQt5/)
[![License](https://img.shields.io/badge/License-Proprietary-941107?style=flat-square&labelColor=0a0a0a)](#license)

<br/>

</div>

---

## Purpose

> [!NOTE]
> This document inventories the deliverable source tree for **operators, integrators, and internal engineering**.

**Paladin** is a proprietary trading intelligence application by **Red Rook, LLC.** It provides a PyQt5 workstation for charting, multi-timeframe market data, and machine-learning-assisted directional signals: a calibrated **LightGBM** ensemble, optional **ONNX** transformer inference, and engineered technical features over **Yahoo Finance** data via `yfinance`.

---

## Repository layout

### Application source (project root)

| File | Type | Role | Tech/Stats |
|:-----|:-----|:-----|:-----------|
| `main.py`         | ![Python](https://img.shields.io/badge/Python-3.11-941107?style=flat-square&logo=python&logoColor=white&labelColor=0a0a0a) ![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-FFD700?style=flat-square&logo=qt&logoColor=black) | PyQt5 shell: onboarding, charting, signal engine integration. | ![Desktop](https://img.shields.io/badge/Desktop_App-black?style=flat-square&logo=windows&logoColor=white) |
| `brains.py`       | ![Brain](https://img.shields.io/badge/Brain-Engine-941107?style=flat-square&logo=lightgbm&logoColor=white) ![ONNX](https://img.shields.io/badge/ONNX-Optional-FFD700?style=flat-square&logo=onnx&logoColor=black) | ML brain, ONNX/LightGBM, features, persistence | ![ML](https://img.shields.io/badge/ML-LightGBM-0a0a0a?style=flat-square&logo=lightgbm&logoColor=FFD700) |
| `humanize.py`     | ![Chat](https://img.shields.io/badge/Conversational-GPT4All-FFD700?style=flat-square&logo=comment&logoColor=941107) | GPT4All-compatible conversational layer | ![Orca](https://img.shields.io/badge/Orca-GGUF-941107?style=flat-square) |
| `translator.py`   | ![Lang](https://img.shields.io/badge/Translation-Hooks-FFD700?style=flat-square&logo=googletranslate&logoColor=941107) | GUI translation hooks | ![i18n](https://img.shields.io/badge/i18n-Supported-0a0a0a?style=flat-square&logo=translate&logoColor=FFD700) |
| `setup.py`        | ![Setup](https://img.shields.io/badge/Setup-Diagnostics-941107?style=flat-square&logo=python&logoColor=FFD700) | Dependency checks, training bootstrap, diagnostics | ![Diagnostics](https://img.shields.io/badge/Diagnostics-Ready-FFD700?style=flat-square) |
| `data4.json`      | ![Data](https://img.shields.io/badge/Data-Metadata-FFD700?style=flat-square&logo=json&logoColor=941107) | Brain metadata for setup/training | ![Meta](https://img.shields.io/badge/Meta-Info-0a0a0a?style=flat-square) |
| `requirements.txt`| ![Reqs](https://img.shields.io/badge/Requirements-Dependencies-941107?style=flat-square&logo=pypi&logoColor=FFD700) | Python dependencies | ![PyPI](https://img.shields.io/badge/PyPI-Listed-FFD700?style=flat-square&logo=pypi&logoColor=941107) |


### `DATABASE/`

| File | Type | Role | Tech/Stats |
|:-----|:-----|:-----|:-----------|
| `general_info.py`        | ![Python](https://img.shields.io/badge/Python-File-941107?style=flat-square&logo=python&logoColor=FFD700) | SYSTEM_PROMPT_JSON for export and conversational pipelines | ![Prompt](https://img.shields.io/badge/Prompt-JSON-FFD700?style=flat-square) |
| `convert_h5_onnx.py`     | ![ONNX](https://img.shields.io/badge/ONNX-Convert-FFD700?style=flat-square&logo=onnx&logoColor=941107) | Load `paladin.h5`, emit `paladin.onnx`, refresh context | ![Convert](https://img.shields.io/badge/Convert-h5→onnx-0a0a0a?style=flat-square&logo=keras&logoColor=FFD700) |
| `paladin_context.json`   | ![JSON](https://img.shields.io/badge/Context-Legacy-FFD700?style=flat-square&logo=json&logoColor=941107) | Alternate / legacy context export | ![Legacy](https://img.shields.io/badge/Legacy-v1-941107?style=flat-square) |
| `paladin_contextv2.json` | ![JSON](https://img.shields.io/badge/Context-v2-FFD700?style=flat-square&logo=json&logoColor=941107) | Current v2 context export | ![v2](https://img.shields.io/badge/Context-v2-FFD700?style=flat-square) |
| `paladin.h5`             | ![Keras](https://img.shields.io/badge/Keras-Weights-941107?style=flat-square&logo=keras&logoColor=FFD700) | Keras weights for export pipeline | ![Weights](https://img.shields.io/badge/Weights-h5-FFD700?style=flat-square) |
| `paladin.onnx`           | ![ONNX](https://img.shields.io/badge/ONNX-Graph-FFD700?style=flat-square&logo=onnx&logoColor=941107) | Runtime ONNX graph for `brains.py` | ![ONNX](https://img.shields.io/badge/ONNX-Ready-0a0a0a?style=flat-square) |

### `MODELS/`

| File | Type | Role | Tech/Stats |
|:-----|:-----|:-----|:-----------|
| `brain_model.pkl`   | ![LightGBM](https://img.shields.io/badge/LightGBM-Model-941107?style=flat-square&logo=lightgbm&logoColor=FFD700) | Default LightGBM stack from `brains.py` training | ![ML](https://img.shields.io/badge/ML-Stacked-FFD700?style=flat-square) |
| `paladin_brain.pkl` | ![Fallback](https://img.shields.io/badge/Fallback-Brain-FFD700?style=flat-square&logo=python&logoColor=941107) | Fallback brain if default is missing | ![Backup](https://img.shields.io/badge/Backup-Ready-0a0a0a?style=flat-square) |
| `scaler.pkl`        | ![Scaler](https://img.shields.io/badge/Scaler-Robust-FFD700?style=flat-square&logo=scikit-learn&logoColor=941107) | Fitted `RobustScaler` | ![Scaling](https://img.shields.io/badge/Scaling-Active-FFD700?style=flat-square) |

---
## Prerequisites

- <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/brands/python.svg" width="16" height="16" alt="" /> **Python 3.11** (see `requirements.txt` comments).
- <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/solid/memory.svg" width="16" height="16" alt="" /> **RAM:** 16 GB recommended for interactive ML workloads.
- <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/solid/laptop.svg" width="16" height="16" alt="" /> **OS:** Windows, macOS, or Linux.

```bash
pip install -r requirements.txt
```

Some installs need a system **TA-Lib** library before the Python wheel; see upstream TA-Lib docs for your platform.

---

## Operation

| | Step | Command |
|--:|------|---------|
| <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/solid/desktop.svg" width="16" height="16" alt="" /> | Launch desktop app | `python main.py` |
| <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/solid/screwdriver-wrench.svg" width="16" height="16" alt="" /> | Setup / train / diagnostics | `python setup.py` |
| <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/solid/share-from-square.svg" width="16" height="16" alt="" /> | Export ONNX + context (requires `DATABASE/paladin.h5`) | `python onnx_and_orca.py --export` |
| <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/solid/database.svg" width="16" height="16" alt="" /> | Same export via database script | `python DATABASE/convert_h5_onnx.py` |

---

## Configuration

| | Variable | Meaning |
|--:|----------|---------|
| <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/solid/folder-open.svg" width="16" height="16" alt="" /> | `PALADIN_ORCA_PATH` | Absolute path to a GPT4All-compatible **GGUF** for `humanize.py` (overrides default cache). |

Baseline market data uses **yfinance**; no API key is required for standard Yahoo Finance access.

---

## Regulatory Notice

> [!WARNING]
> **Paladin** outputs analytics only. It is **not** investment advice, a solicitation, or a recommendation to buy or sell any security. Past performance does not guarantee future results. Operators must ensure compliance with applicable law and internal policy. **Red Rook, LLC** disclaims liability for trading losses.


---

## License

© 2025 **Red Rook, LLC.** All rights reserved.

---

<p align="center"><sub><img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/solid/file-lines.svg" width="14" height="14" alt="" /> Document <strong>v1.0</strong> · Last updated <strong>April 20, 2026</strong><br />Icons: <a href="https://fontawesome.com/">Font Awesome</a> 6 Free (CC BY 4.0)</sub></p>
