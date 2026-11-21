#!/usr/bin/env python3
"""Hand the finished front page to the grader.

Only the standard library is used: nothing is installed and there is
no network at grading time, so this just copies the bundled PNG.
"""

import os
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT_DIR = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))

OUT_DIR.mkdir(parents=True, exist_ok=True)
shutil.copyfile(HERE / "entry.png", OUT_DIR / "entry.png")
