# forge-ui-components

Reusable UI components for Xolv forge apps — FunScriptForge, SyncPlayer, forgegen, and beyond.

## Architecture

```
forge-ui-components/
├── forge_ui_components/
│   ├── funscript_chart/     ← Plotly charts (monochrome + vibrant)
│   ├── file_picker/         ← Upload with guard, clear, stats
│   ├── beat_bar/            ← Wraps videoflow AudioBeatMap
│   ├── project_status/      ← Read-only sidebar dashboard
│   ├── transform_editor/    ← Slider UI, before/after (stub)
│   └── tone_selector/       ← 6 tone cards, sliders (stub)
└── tests/                   ← 37 tests
```

Each component has two layers:

- **`core.py`** — Framework-agnostic Python logic (data prep, state, algorithms). Zero UI imports. Testable without Streamlit.
- **`streamlit.py`** — Thin render layer that calls core and renders with Streamlit widgets. No business logic.

This separation keeps components portable to React/Tauri v2 later — only the render layer changes.

### Dependency graph

```
FunScriptForge / SyncPlayer / forgegen
        │
        ▼
forge-ui-components          ← this repo (UI components)
        │
        ├── videoflow        ← beat analysis, scene detection (xolvco/videoflow)
        └── plotly           ← charting
```

## Components

### funscript_chart (extracted)

Monochrome and vibrant Plotly funscript visualizations.

| Function | Replaces | Used by |
|---|---|---|
| `monochrome_figure()` | `_funscript_chart`, `_plot_device`, `_plot_funscript` | Project, Device, Tone tabs |
| `vibrant_figure()` | `FunscriptChart._build_figure` | Viewer, Export, Phrase Detail panels |
| `funscript_stats()` | `forge.funscript.funscript_stats` | Project tab stats row |
| `compute_chart_data()` | `chart_data.compute_chart_data` | Vibrant chart data pipeline |
| `compute_annotation_bands()` | `chart_data.compute_annotation_bands` | Phrase bounding boxes |

Core includes: `PointSeries`, `AnnotationBand`, color interpolation (velocity/amplitude), time axis helpers, series slicing.

```python
# Monochrome (fast, no assessment)
from forge_ui_components.funscript_chart.streamlit import render_monochrome
render_monochrome(actions, caption="my_file.funscript")

# Vibrant (color-coded, post-assessment)
from forge_ui_components.funscript_chart.core import compute_chart_data, vibrant_figure
series = compute_chart_data(actions)
fig = vibrant_figure(series, bands, view_state=vs, height=380)
```

### file_picker (extracted)

Drag+drop file upload with processed guard, clear button, and stats display.

| Config | Extensions | Used by |
|---|---|---|
| `FUNSCRIPT_PICKER` | `.funscript` | Project tab |
| `VIDEO_PICKER` | `.mp4, .mov, .avi, .mkv` | Project tab |
| `AUDIO_PICKER` | `.mp3, .wav, .flac, .ogg` | Project tab |
| `CAPTIONS_PICKER` | `.srt, .vtt, .ass` | Project tab |

Context-specific behavior (downstream reset, project storage, disk space checks) is handled via `on_upload` / `on_clear` callbacks.

```python
from forge_ui_components.file_picker.streamlit import render_upload
from forge_ui_components.file_picker import VIDEO_PICKER, resolve_file_path

video_path = resolve_file_path(VIDEO_PICKER, st.session_state, project_path=existing)
render_upload(VIDEO_PICKER, version=v, on_upload=my_handler, current_path=video_path)
```

### beat_bar (extracted, wraps videoflow)

Beat analysis visualization. All librosa logic lives in [videoflow](https://github.com/xolvco/videoflow) — this component provides the Plotly visualization and Streamlit render layer.

```python
from forge_ui_components.beat_bar.core import analyze_beats, save_beats, load_cached_beats

# Analyze (delegates to videoflow.audio.analyze_beats)
beat_map = analyze_beats("audio.mp3")  # returns AudioBeatMap
save_beats(beat_map, "output/_beat_data.json")

# Render
from forge_ui_components.beat_bar.streamlit import render_beat_bar
render_beat_bar(beat_map)  # energy-scaled bar chart + stats
```

### project_status (extracted)

Read-only sidebar dashboard. Collects all display data into a `ProjectStatus` snapshot — render code never touches session state.

```python
from forge_ui_components.project_status.core import ProjectStatus
from forge_ui_components.project_status.streamlit import render_full_sidebar_status

status = ProjectStatus(
    project_name="My Project",
    funscript_name="scene.funscript",
    tabs_completed={"Project": True, "Device": True},
    phrase_count=12, bpm_avg=120.0,
)
render_full_sidebar_status(status)
```

### transform_editor (stub)

Slider UI with before/after preview, accept/cancel. Already shared in FunScriptForge via `transform_picker.py` — extraction pending.

### tone_selector (stub)

6 tone cards, variable sliders per tone, impact slider, dual suggestions. Extraction pending.

## Install

```bash
# Core only (Plotly charts, file picker, project status)
pip install -e ../forge-ui-components

# With Streamlit render layer
pip install -e "../forge-ui-components[streamlit]"

# With beat detection (pulls in videoflow + librosa)
pip install -e "../forge-ui-components[beats]"

# Development
pip install -e "../forge-ui-components[dev]"
```

## Testing

```bash
pytest tests/ -v    # 37 tests, <1s
```

## License

MIT — © 2026 Liquid Releasing
