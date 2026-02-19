"""
Run OCR-only analysis and print/save output so you can inspect before integrating.

Usage:
  From project root:
    python -m vision.run_ocr_demo
    python -m vision.run_ocr_demo path/to/screenshot.png
  From vision/ folder:
    python run_ocr_demo.py
    python run_ocr_demo.py path/to/screenshot.png

If no image path is given, the screen is captured first (minimize this window if you don't want it in the shot).
"""

import json
import sys
from pathlib import Path

# Allow running as script from vision/ or as module from project root
_here = Path(__file__).resolve().parent
_root = _here.parent
if _root not in sys.path:
    sys.path.insert(0, str(_root))

try:
    from vision.vision_ocr import run_ocr_pipeline
    from vision.vision_engine import capture_screen
except ImportError:
    from vision_ocr import run_ocr_pipeline
    from vision_engine import capture_screen

VISION_OUTPUT_DIR = _root / "vision_output"


def main():
    image_path = None
    if len(sys.argv) > 1:
        image_path = Path(sys.argv[1])
        if not image_path.is_file():
            print(f"Error: file not found: {image_path}")
            sys.exit(1)
        print(f"Using image: {image_path}")
    else:
        print("Capturing screen in 2 seconds... (minimize this window to exclude it)")
        import time
        time.sleep(2)
        screenshot_path, ts = capture_screen()
        image_path = screenshot_path
        print(f"Captured: {screenshot_path}")

    print("\nRunning OCR analysis...")
    result = run_ocr_pipeline(image_path=image_path)

    if not result.get("success"):
        print("OCR failed:", result.get("error"))
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(1)

    print("\n" + "=" * 60)
    print("OUTPUT (same shape as Gemini for integration)")
    print("=" * 60)
    a = result.get("analysis", {})
    print("\n--- Summary ---")
    print(a.get("screen_summary", "—"))
    print("\n--- Buttons (short text) ---")
    for b in a.get("detected_buttons", [])[:25]:
        print(f"  • {b.get('label', '')}")
    print("\n--- Options ---")
    for o in a.get("detected_options", [])[:25]:
        print(f"  • {o.get('label', '')}")
    print("\n--- JSON path ---")
    print(result.get("json_path", ""))

    print("\n--- Full JSON (first 2000 chars) ---")
    raw = json.dumps(result, indent=2, ensure_ascii=False)
    print(raw[:2000])
    if len(raw) > 2000:
        print("... (truncated; full JSON saved to file above)")

    print("\nDone. Check vision_output/ for ocr_analysis_*.json")


if __name__ == "__main__":
    main()
