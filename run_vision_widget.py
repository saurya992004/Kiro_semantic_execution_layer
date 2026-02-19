#!/usr/bin/env python3
"""
Launch the Vision Intelligence widget from project root:
    python run_vision_widget.py
"""
import sys
from pathlib import Path

# Ensure project root is on path
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from vision.vision_widget import main

if __name__ == "__main__":
    main()
