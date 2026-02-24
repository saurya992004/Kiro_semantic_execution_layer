"""
Vision Intelligence Engine — Phase 9
Captures screen, analyzes with Gemini Vision, outputs structured JSON.
Output saved to vision_output/ for later use (e.g. TROUBLESHOOTER phase).
"""

import os
import json
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# Default output folder (project root / vision_output)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
VISION_OUTPUT_DIR = PROJECT_ROOT / "vision_output"
SCREENSHOTS_DIR = VISION_OUTPUT_DIR / "screenshots"

# Vision analysis prompt — structured JSON output
VISION_SYSTEM_PROMPT = """You are a screen analysis assistant. Analyze the provided screenshot and return a single valid JSON object (no markdown, no code fence) with this exact structure:

{
  "timestamp_iso": "<ISO datetime when screenshot was taken>",
  "screen_summary": "<1-2 sentence summary of what is on screen>",
  "window_title_or_app": "<best guess of app/window title if visible>",
  "detected_buttons": [
    { "label": "<button text>", "context": "<where it appears>", "action_hint": "<what it likely does>" }
  ],
  "detected_options": [
    { "label": "<option/menu text>", "type": "menu|checkbox|radio|link|tab|other", "context": "<where it appears>" }
  ],
  "visible_text_regions": [
    { "text": "<short excerpt>", "role": "heading|body|label|error|other" }
  ],
  "possible_errors_or_alerts": [
    { "text": "<message>", "severity": "error|warning|info|unknown" }
  ],
  "accessibility_hints": "<any notable UI elements for automation: dialogs, modals, focus areas>"
}

If a list has no items, use []. Be concise. Preserve exact button/option labels when visible."""


def ensure_output_dirs() -> None:
    """Create vision_output and screenshots folders if missing."""
    VISION_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)


def capture_screen() -> tuple[Path, str]:
    """
    Capture full screen and save as PNG.
    The entire screen image is captured and later sent to Gemini as-is.
    Caller should minimize/hide any overlay windows before calling so they are not in the shot.
    Returns (path_to_png, timestamp_iso).
    """
    try:
        import mss
        import mss.tools
    except ImportError:
        raise ImportError("Install mss: pip install mss")

    ensure_output_dirs()
    timestamp = datetime.utcnow()
    ts_str = timestamp.strftime("%Y%m%d_%H%M%S")
    ts_iso = timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
    filename = f"screen_{ts_str}.png"
    path = SCREENSHOTS_DIR / filename

    with mss.mss() as sct:
        # Monitor 0 = all monitors combined; full image is sent to Gemini
        mon = sct.monitors[0]
        screenshot = sct.grab(mon)
        png_bytes = mss.tools.to_png(screenshot.rgb, screenshot.size)
    path.write_bytes(png_bytes)
    return path, ts_iso


def analyze_screen(
    image_path: Path,
    user_query: str = "What is on this screen? List all buttons and options.",
    api_key: str | None = None,
    model: str = "gemini-2.5-flash",
) -> dict:
    """
    Send screenshot to Gemini Vision and return structured JSON analysis.
    """
    api_key = api_key or os.getenv("GEMINI_API_KEY1")
    if not api_key:
        raise ValueError("Permission denied")

    with open(image_path, "rb") as f:
        image_bytes = f.read()
    # Full screenshot (whole screen) is sent to Gemini Vision
    client = genai.Client(api_key=api_key)
    prompt = user_query.strip() or "What is on this screen? List all buttons and options."
    full_prompt = f"{VISION_SYSTEM_PROMPT}\n\nUser request: {prompt}"

    response = client.models.generate_content(
        model=model,
        contents=[
            types.Part.from_text(text=full_prompt),
            types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
        ],
    )

    text = (response.text or "").strip()
    # Extract JSON from response (handle optional markdown wrapper)
    if "```json" in text:
        start = text.find("```json") + 7
        end = text.find("```", start)
        text = text[start:end] if end > start else text
    elif "```" in text:
        start = text.find("```") + 3
        end = text.find("```", start)
        text = text[start:end] if end > start else text
    if not text:
        return {"error": "Empty vision response", "raw": getattr(response, "text", "")}

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON from vision: {e}", "raw": text}

    if not isinstance(data, dict):
        return {"error": "Vision response is not a JSON object", "raw": text}

    return data


def save_vision_result(
    result: dict,
    screenshot_path: Path,
    timestamp_iso: str,
) -> Path:
    """Write analysis JSON to vision_output with reference to screenshot."""
    ensure_output_dirs()
    result["screenshot_path"] = str(screenshot_path)
    result["screenshot_filename"] = screenshot_path.name
    result["analyzed_at_iso"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    if "timestamp_iso" not in result:
        result["timestamp_iso"] = timestamp_iso

    ts_file = timestamp_iso.replace(":", "").replace("-", "").split(".")[0]
    json_path = VISION_OUTPUT_DIR / f"analysis_{ts_file}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    return json_path


def run_vision_pipeline(
    user_query: str = "What is on my screen? List buttons and options.",
    api_key: str | None = None,
) -> dict:
    """
    Full pipeline: capture screen → analyze with vision → save JSON.
    Returns the analysis dict and paths for caller to use.
    """
    screenshot_path, timestamp_iso = capture_screen()
    analysis = analyze_screen(screenshot_path, user_query=user_query, api_key=api_key)

    if "error" in analysis:
        return {
            "success": False,
            "error": analysis.get("error"),
            "screenshot_path": str(screenshot_path),
            "analysis": analysis,
        }

    json_path = save_vision_result(analysis, screenshot_path, timestamp_iso)
    return {
        "success": True,
        "screenshot_path": str(screenshot_path),
        "json_path": str(json_path),
        "analysis": analysis,
    }
