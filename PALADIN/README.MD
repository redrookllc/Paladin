<!-- Icons: Font Awesome 6.5.1 Free — solid (`fas`) + brands (`fab`) SVGs via jsDelivr (FortAwesome/Font-Awesome) -->

<div align="center">

# <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/solid/shield-halved.svg" width="28" height="28" alt="Paladin" /> Paladin

**Trading Intelligence Application**

*Desktop market analytics and signal generation for institutional-style workflows*

[![Python](https://img.shields.io/badge/python-3.11-941107?style=flat-square&logo=python&logoColor=f5f5f5&labelColor=0a0a0a)](https://www.python.org/downloads/)
[![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-941107?style=flat-square&labelColor=0a0a0a)](https://pypi.org/project/PyQt5/)
[![License](https://img.shields.io/badge/License-Proprietary-941107?style=flat-square&labelColor=0a0a0a)](#license)

<br/>

</div>

---

## <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/solid/bullseye.svg" width="20" height="20" alt="" /> Purpose

> [!NOTE]
> This document inventories the deliverable source tree for **operators, integrators, and internal engineering**.

**Paladin** is a proprietary trading intelligence application by **Red Rook, LLC.** It provides a PyQt5 workstation for charting, multi-timeframe market data, and machine-learning-assisted directional signals: a calibrated **LightGBM** ensemble, optional **ONNX** transformer inference, and engineered technical features over **Yahoo Finance** data via `yfinance`.

---

## <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/solid/diagram-project.svg" width="20" height="20" alt="" /> Repository layout

### <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/solid/folder-tree.svg" width="18" height="18" alt="" /> Application source (project root)

| | File | Role |
|--:|------|------|
| <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/brands/python.svg" width="16" height="16" alt="" /> | `main.py` | PyQt5 shell: onboarding, charting, signal engine integration. |
| <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/solid/brain.svg" width="16" height="16" alt="" /> | `brains.py` | `get_brain_v2()` brain, features, ONNX Runtime when `DATABASE/paladin.onnx` exists, LightGBM fallback, `MODELS/` persistence. |
| <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/solid/comments.svg" width="16" height="16" alt="" /> | `humanize.py` | Optional GPT4All-compatible conversational layer; set `PALADIN_ORCA_PATH` to your GGUF. |
| <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/solid/gears.svg" width="16" height="16" alt="" /> | `onnx_and_orca.py` | Keras → ONNX export, knowledge flattening from `DATABASE/general_info.py`, optional CLI chat. |
| <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/solid/language.svg" width="16" height="16" alt="" /> | `translator.py` | GUI translation hooks. |
| <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/solid/screwdriver-wrench.svg" width="16" height="16" alt="" /> | `setup.py` | Dependency checks, training bootstrap from `data4.json`, diagnostics. |
| <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/solid/file-code.svg" width="16" height="16" alt="" /> | `data4.json` | Brain metadata for setup/training. |
| <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/solid/list-ul.svg" width="16" height="16" alt="" /> | `requirements.txt` | Python dependencies. |

### <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/solid/database.svg" width="18" height="18" alt="" /> `DATABASE/`

| | File | Role |
|--:|------|------|
| <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/brands/python.svg" width="16" height="16" alt="" /> | `general_info.py` | `SYSTEM_PROMPT_JSON` for export and conversational pipelines. |
| <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/solid/arrow-right-arrow-left.svg" width="16" height="16" alt="" /> | `convert_h5_onnx.py` | Load `paladin.h5`, emit `paladin.onnx`, refresh `paladin_contextv2.json`. |
| <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/solid/file-code.svg" width="16" height="16" alt="" /> | `paladin_context.json` | Alternate / legacy context export. |
| <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/solid/file-code.svg" width="16" height="16" alt="" /> | `paladin_contextv2.json` | Current v2 context export. |
| <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/solid/cube.svg" width="16" height="16" alt="" /> | `paladin.h5` | Keras weights for export pipeline (when supplied). |
| <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/solid/network-wired.svg" width="16" height="16" alt="" /> | `paladin.onnx` | Runtime ONNX graph for `brains.py` when present. |

Additional preview assets may ship in this folder.

### <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/solid/box-archive.svg" width="18" height="18" alt="" /> `MODELS/`

| | File | Role |
|--:|------|------|
| <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/solid/floppy-disk.svg" width="16" height="16" alt="" /> | `brain_model.pkl` | Default LightGBM stack from `brains.py` training. |
| <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/solid/floppy-disk.svg" width="16" height="16" alt="" /> | `paladin_brain.pkl` | Fallback brain if default is missing. |
| <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/solid/floppy-disk.svg" width="16" height="16" alt="" /> | `scaler.pkl` | Fitted `RobustScaler`. |

### <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/solid/code.svg" width="18" height="18" alt="" /> `.vscode/`

Optional editor settings (e.g. `settings.json`); no runtime effect.

### <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/brands/python.svg" width="18" height="18" alt="" /> `paladin/` (optional)

Project-local Python virtual environment (`Lib/site-packages`, etc.). Not application source; prefer isolated envs in production.

---

## <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/solid/list-check.svg" width="20" height="20" alt="" /> Prerequisites

- <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/brands/python.svg" width="16" height="16" alt="" /> **Python 3.11** (see `requirements.txt` comments).
- <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/solid/memory.svg" width="16" height="16" alt="" /> **RAM:** 16 GB recommended for interactive ML workloads.
- <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/solid/laptop.svg" width="16" height="16" alt="" /> **OS:** Windows, macOS, or Linux.

```bash
pip install -r requirements.txt
```

Some installs need a system **TA-Lib** library before the Python wheel; see upstream TA-Lib docs for your platform.

---

## <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/solid/terminal.svg" width="20" height="20" alt="" /> Operation

| | Step | Command |
|--:|------|---------|
| <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/solid/desktop.svg" width="16" height="16" alt="" /> | Launch desktop app | `python main.py` |
| <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/solid/screwdriver-wrench.svg" width="16" height="16" alt="" /> | Setup / train / diagnostics | `python setup.py` |
| <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/solid/share-from-square.svg" width="16" height="16" alt="" /> | Export ONNX + context (requires `DATABASE/paladin.h5`) | `python onnx_and_orca.py --export` |
| <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/solid/database.svg" width="16" height="16" alt="" /> | Same export via database script | `python DATABASE/convert_h5_onnx.py` |

---

## <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/solid/sliders.svg" width="20" height="20" alt="" /> Configuration

| | Variable | Meaning |
|--:|----------|---------|
| <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/solid/folder-open.svg" width="16" height="16" alt="" /> | `PALADIN_ORCA_PATH` | Absolute path to a GPT4All-compatible **GGUF** for `humanize.py` (overrides default cache). |

Baseline market data uses **yfinance**; no API key is required for standard Yahoo Finance access.

---

## <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/solid/triangle-exclamation.svg" width="20" height="20" alt="" /> Regulatory notice

> [!WARNING]
> **Paladin** outputs analytics only. It is **not** investment advice, a solicitation, or a recommendation to buy or sell any security. Past performance does not guarantee future results. Operators must ensure compliance with applicable law and internal policy. **Red Rook, LLC** disclaims liability for trading losses.

---

## <img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/solid/scale-balanced.svg" width="20" height="20" alt="" /> License

© 2026 **Red Rook, LLC.** All rights reserved.

---

<p align="center"><sub><img src="https://cdn.jsdelivr.net/gh/FortAwesome/Font-Awesome@6.5.1/svgs/solid/file-lines.svg" width="14" height="14" alt="" /> Document <strong>v1.0</strong> · Last updated <strong>April 17, 2026</strong><br />Icons: <a href="https://fontawesome.com/">Font Awesome</a> 6 Free (CC BY 4.0)</sub></p>
