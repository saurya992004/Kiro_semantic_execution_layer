"""
Local Vision — OCR-based screen analysis (no cloud).
Output matches the same JSON shape as vision_engine for easy integration later.

Options below are meant to be edited by you (language, engine, thresholds).

Setup:
  pip install pytesseract pillow
  Install Tesseract binary: https://github.com/UB-Mannheim/tesseract/wiki (Windows)
  Optional: set TESSERACT_CMD below if tesseract is not on PATH.
  For EasyOCR: set OCR_ENGINE = "easyocr" and pip install easyocr.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from datetime import datetime

# Common Windows Tesseract path (used if TESSERACT_CMD is not set)
_WINDOWS_TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
]

# -----------------------------------------------------------------------------
# OPTIONS — change these to tune OCR behavior
# -----------------------------------------------------------------------------

# Which OCR engine to use. "tesseract" = pytesseract (needs Tesseract installed).
# "easyocr" = EasyOCR (pip install easyocr; no separate binary).
OCR_ENGINE: str = "tesseract"

# Tesseract: language code(s). Use "+" for multiple: "eng+hin", "eng+fra", etc.
# List: https://tesseract-ocr.github.io/tessdoc/Data-Files-in-different-versions.html
TESSERACT_LANG: str = "eng"

# Path to Tesseract executable. Set if it's not on PATH (e.g. Windows).
# Example: r"C:\Program Files\Tesseract-OCR\tesseract.exe"
TESSERACT_CMD: str | None = None

# Minimum confidence (0–100) for a word to be included. Increase to reduce noise.
OCR_MIN_CONFIDENCE: int = 30

# Short text is treated as button/label; longer as body. Max characters for "button-like".
BUTTON_MAX_CHARS: int = 40

# Max characters for "option" / menu-like text.
OPTION_MAX_CHARS: int = 60

# Max visible_text_regions to return (avoid huge JSON). 0 = no limit.
MAX_TEXT_REGIONS: int = 100

# Max detected_buttons / detected_options to return. 0 = no limit.
MAX_BUTTONS: int = 50
MAX_OPTIONS: int = 50

# EasyOCR: languages (only used if OCR_ENGINE == "easyocr"). e.g. ["en"], ["en", "hi"]
EASYOCR_LANGS: list[str] = ["en"]

# -----------------------------------------------------------------------------
# Implementation
# -----------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VISION_OUTPUT_DIR = PROJECT_ROOT / "vision_output"


def _get_tesseract_cmd() -> str | None:
    """Return Tesseract executable path (user setting or Windows default)."""
    if TESSERACT_CMD and Path(TESSERACT_CMD).is_file():
        return TESSERACT_CMD
    if os.name == "nt":
        for p in _WINDOWS_TESSERACT_PATHS:
            if Path(p).is_file():
                return p
    return TESSERACT_CMD  # may be None; pytesseract will use PATH


def _run_tesseract(image_path: Path) -> list[dict]:
    """Run Tesseract and return list of {text, left, top, width, height, conf, level}."""
    try:
        import pytesseract
        from PIL import Image
    except ImportError as e:
        raise ImportError("Install pytesseract and Pillow: pip install pytesseract pillow") from e

    cmd = _get_tesseract_cmd()
    if cmd:
        pytesseract.pytesseract.tesseract_cmd = cmd

    img = Image.open(image_path)
    if img.mode != "RGB":
        img = img.convert("RGB")

    try:
        data = pytesseract.image_to_data(img, lang=TESSERACT_LANG, output_type=pytesseract.Output.DICT)
    except Exception as e:
        raise RuntimeError(f"Tesseract failed (is Tesseract installed and lang '{TESSERACT_LANG}' available?): {e}") from e

    out = []
    n = len(data.get("text", []))
    for i in range(n):
        text = (data.get("text", [""])[i] or "").strip()
        if not text:
            continue
        conf = int(data.get("conf", [0])[i] or 0)
        if conf < OCR_MIN_CONFIDENCE:
            continue
        out.append({
            "text": text,
            "left": data["left"][i],
            "top": data["top"][i],
            "width": data["width"][i],
            "height": data["height"][i],
            "conf": conf,
            "level": data["level"][i],
        })
    return out


def _run_easyocr(image_path: Path) -> list[dict]:
    """Run EasyOCR and return same-shaped list of detections."""
    try:
        import easyocr
    except ImportError as e:
        raise ImportError("Install easyocr: pip install easyocr") from e

    reader = easyocr.Reader(EASYOCR_LANGS, gpu=False, verbose=False)
    result = reader.readtext(str(image_path))
    out = []
    for (bbox, text, conf) in result:
        # bbox is [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
        xs = [p[0] for p in bbox]
        ys = [p[1] for p in bbox]
        left, right = min(xs), max(xs)
        top, bottom = min(ys), max(ys)
        out.append({
            "text": (text or "").strip(),
            "left": int(left),
            "top": int(top),
            "width": int(right - left),
            "height": int(bottom - top),
            "conf": int(conf * 100) if conf else 0,
            "level": 5,
        })
    return out


def _is_tesseract_unavailable_error(e: Exception) -> bool:
    """True if the exception means Tesseract binary is missing or not on PATH."""
    msg = str(e).lower()
    return (
        "not installed" in msg
        or "not in your path" in msg
        or ("tesseract" in msg and "path" in msg)
        or "no such file" in msg
    )


def _ocr_detect(image_path: Path) -> list[dict]:
    """Run configured OCR engine and return list of text boxes. Falls back to EasyOCR if Tesseract unavailable."""
    if OCR_ENGINE.strip().lower() == "easyocr":
        return _run_easyocr(image_path)
    try:
        return _run_tesseract(image_path)
    except Exception as e:
        if not _is_tesseract_unavailable_error(e):
            raise
        try:
            return _run_easyocr(image_path)
        except ImportError:
            raise RuntimeError(
                "Tesseract is not installed or not in PATH. Either install Tesseract "
                "(https://github.com/UB-Mannheim/tesseract/wiki) or use EasyOCR: pip install easyocr and set OCR_ENGINE = 'easyocr' in vision_ocr.py"
            ) from e


def analyze_screen_ocr(
    image_path: Path | str,
    timestamp_iso: str | None = None,
) -> dict:
    """
    Analyze screenshot with local OCR. Returns the same JSON structure as vision_engine
    (screen_summary, detected_buttons, detected_options, visible_text_regions, etc.)
    so it can be swapped in when you integrate.
    """
    image_path = Path(image_path)
    if not image_path.is_file():
        return {"error": f"Image not found: {image_path}"}

    ts = timestamp_iso or datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        boxes = _ocr_detect(image_path)
    except Exception as e:
        return {"error": str(e), "timestamp_iso": ts}

    # Build text regions (all non-empty detections)
    visible_text_regions = []
    for b in boxes:
        text = (b.get("text") or "").strip()
        if not text:
            continue
        visible_text_regions.append({
            "text": text[:200],
            "role": "label" if len(text) <= BUTTON_MAX_CHARS else "body",
        })
    if MAX_TEXT_REGIONS and len(visible_text_regions) > MAX_TEXT_REGIONS:
        visible_text_regions = visible_text_regions[:MAX_TEXT_REGIONS]

    # Short text → button-like; medium → option-like
    detected_buttons = []
    detected_options = []
    seen = set()
    for b in boxes:
        text = (b.get("text") or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        if len(text) <= BUTTON_MAX_CHARS:
            detected_buttons.append({
                "label": text,
                "context": "detected from OCR",
                "action_hint": "",
            })
        if len(text) <= OPTION_MAX_CHARS and len(text) > 0:
            detected_options.append({
                "label": text,
                "type": "other",
                "context": "detected from OCR",
            })
    if MAX_BUTTONS and len(detected_buttons) > MAX_BUTTONS:
        detected_buttons = detected_buttons[:MAX_BUTTONS]
    if MAX_OPTIONS and len(detected_options) > MAX_OPTIONS:
        detected_options = detected_options[:MAX_OPTIONS]

    # Summary: first few lines of text
    all_text = " ".join(b.get("text", "") or "" for b in boxes).strip()
    summary = all_text[:300] + ("..." if len(all_text) > 300 else "") if all_text else "No text detected."

    return {
        "timestamp_iso": ts,
        "screen_summary": summary,
        "window_title_or_app": "",
        "detected_buttons": detected_buttons,
        "detected_options": detected_options,
        "visible_text_regions": visible_text_regions,
        "possible_errors_or_alerts": [],
        "accessibility_hints": "Local OCR; no semantic labels.",
        "backend": "ocr",
    }


def run_ocr_pipeline(
    image_path: Path | str | None = None,
    timestamp_iso: str | None = None,
) -> dict:
    """
    Run OCR on an image. If image_path is None, capture screen first (uses vision_engine.capture_screen).
    Returns same shape as vision_engine.run_vision_pipeline: success, screenshot_path, json_path, analysis.
    """
    if image_path is None:
        try:
            from .vision_engine import capture_screen
        except ImportError:
            from vision_engine import capture_screen
        screenshot_path, timestamp_iso = capture_screen()
    else:
        screenshot_path = Path(image_path)
        if not timestamp_iso:
            timestamp_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    analysis = analyze_screen_ocr(screenshot_path, timestamp_iso=timestamp_iso)

    if "error" in analysis:
        return {
            "success": False,
            "error": analysis.get("error"),
            "screenshot_path": str(screenshot_path),
            "analysis": analysis,
        }

    # Save to vision_output for comparison
    VISION_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    analysis["screenshot_path"] = str(screenshot_path)
    analysis["screenshot_filename"] = screenshot_path.name
    analysis["analyzed_at_iso"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    ts_file = timestamp_iso.replace(":", "").replace("-", "").split(".")[0]
    json_path = VISION_OUTPUT_DIR / f"ocr_analysis_{ts_file}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)

    return {
        "success": True,
        "screenshot_path": str(screenshot_path),
        "json_path": str(json_path),
        "analysis": analysis,
    }
