# forge-ui-components

Reusable UI components for Xolv forge apps — FunScriptForge, SyncPlayer, forgegen, and beyond.

## Architecture

Each component has two layers:

- **`core.py`** — Framework-agnostic Python logic (data prep, state, algorithms). No UI imports.
- **`streamlit.py`** — Thin render layer that calls core and renders with Streamlit widgets.

This separation keeps components portable to React/Tauri v2 later — only the render layer changes.

## Components

| Component | Description |
|---|---|
| `funscript_chart` | Monochrome (fast, blue) and vibrant (color-coded, post-assessment) Plotly charts |
| `file_picker` | Drag+drop upload with clear button and file stats |
| `transform_editor` | Slider UI with before/after preview, accept/cancel — shared by Phrases and Patterns |
| `beat_bar` | Librosa beat detection, caching, and timeline visualization |
| `project_status` | Read-only sidebar dashboard showing workflow progress |
| `tone_selector` | 6 tone cards, variable sliders per tone, impact slider, suggestions |

## Install

```bash
# From FunScriptForge or other consumer app
pip install -e ../forge-ui-components

# With Streamlit render layer
pip install -e "../forge-ui-components[streamlit]"

# With beat detection
pip install -e "../forge-ui-components[beats]"
```

## Usage

```python
# Core logic (no Streamlit needed)
from forge_ui_components.funscript_chart import prepare_chart_data, monochrome_figure

# Streamlit render
from forge_ui_components.funscript_chart.streamlit import render_monochrome
```

## License

MIT
