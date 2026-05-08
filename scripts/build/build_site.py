#!/usr/bin/env python3
"""Rebuild the data layers that feed the frontend.

Two modes:
  default       -- rebuild mod-derived data (formables, loc, requirements).
                   Fast (<5s). Run this whenever the mod files change.
  --full        -- also rebuild game-derived data (locations index, tile
                   pyramid, basemap recolor, geography, area polygons).
                   Slow (~5 minutes). Run when EU5 itself updates or when
                   the script logic changes.

Each step shells out to its own script so failures localise cleanly.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path


HERE = Path(__file__).resolve().parent
PY = sys.executable


def step(label: str, cmd: list[str]) -> None:
    print(f"\n=== {label} ===", flush=True)
    t0 = time.time()
    res = subprocess.run([PY, str(HERE / cmd[0])] + cmd[1:])
    if res.returncode != 0:
        print(f"\n!!! {label} failed (exit {res.returncode})", file=sys.stderr)
        sys.exit(res.returncode)
    print(f"--- {label} done in {time.time()-t0:.1f}s ---", flush=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true",
                    help="Also rebuild game-derived data (slow)")
    args = ap.parse_args()

    overall = time.time()

    if args.full:
        step("locations index",     ["extract_map.py"])
        step("recoloured basemap",  ["recolor_map.py"])
        step("tile pyramid",        ["tile_map.py"])
        step("geography tree",      ["extract_geography.py"])
        step("area polygons",       ["extract_area_polygons.py"])

    # Mod-derived steps (always run).
    # Note: starters runs before localisation so the loc filter can seed
    # country-name keys for every recommended tag.
    step("formables",               ["parse_formables.py"])
    step("recommended starters",    ["extract_starters.py"])
    step("localisation (filtered)", ["parse_localization.py"])
    step("english requirements",    ["render_requirements.py"])

    print(f"\n=== build_site complete in {time.time()-overall:.1f}s ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
