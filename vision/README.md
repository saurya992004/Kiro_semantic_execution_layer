# Vision Intelligence Engine (Phase 9)

Screen capture + Gemini Vision analysis. Output is **JSON** in `vision_output/` for use in the TROUBLESHOOTER phase.

## Quick start

1. Install deps: `pip install -r requirements.txt`
2. Set `GEMINI_API_KEY1` in `.env`
3. Run the widget: **`python run_vision_widget.py`**

In the widget: type a query (e.g. *What's on my screen?*), click **Capture & Analyze**. Screenshot and analysis JSON are saved under `vision_output/`.

## Output layout

- **vision_output/screenshots/** — PNG screenshots (`screen_YYYYMMDD_HHMMSS.png`)
- **vision_output/analysis_*.json** — Structured analysis (summary, buttons, options, errors, etc.)

## JSON schema (example)

- `screen_summary` — Short description of the screen
- `detected_buttons` — List of `{ label, context, action_hint }`
- `detected_options` — List of `{ label, type, context }` (menu, checkbox, radio, link, tab)
- `visible_text_regions`, `possible_errors_or_alerts`, `accessibility_hints`

## Programmatic use

```python
from vision.vision_engine import run_vision_pipeline

result = run_vision_pipeline("What buttons are on screen?")
# result["success"], result["screenshot_path"], result["json_path"], result["analysis"]
```

## Model

Uses **gemini-2.5-flash** for vision. Override with `analyze_screen(..., model="...")` if needed.
