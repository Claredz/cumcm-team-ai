#!/usr/bin/env python3
"""Compatibility wrapper for the root diagram overlap checker."""
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[3]
runpy.run_path(str(ROOT / "scripts" / "diagrams" / "check_overlap.py"), run_name="__main__")
