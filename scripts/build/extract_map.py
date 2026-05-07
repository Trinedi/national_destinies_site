#!/usr/bin/env python3
"""Extract per-location centroids and bounding boxes from EU5's locations.png.

Reads:
  - <eu5>/in_game/map_data/named_locations/00_default.txt  (name -> hex color)
  - <eu5>/in_game/map_data/locations.png                   (color bitmap)

Writes:
  - data/locations_index.json with per-location centroid, bbox, pixel_count.

Polygon extraction is a follow-up; this script gives us pins + the data spine.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

import numpy as np
import yaml
from PIL import Image


def load_config(repo_root: Path) -> dict:
    with open(repo_root / "build.config.yaml") as f:
        return yaml.safe_load(f)


def expand_path(p: str) -> Path:
    return Path(os.path.expanduser(p)).resolve()


HEX_LINE = re.compile(r"^\s*([a-zA-Z0-9_]+)\s*=\s*([0-9a-fA-F]+)\s*(?:#.*)?$")


def parse_named_locations(path: Path) -> dict[str, int]:
    """Parse `name = hexcolor` lines. Hex is variable length, zero-pad to 6 chars."""
    name_to_color: dict[str, int] = {}
    with open(path, encoding="utf-8-sig") as f:
        for lineno, line in enumerate(f, 1):
            line = line.split("#", 1)[0].rstrip()
            if not line.strip():
                continue
            m = HEX_LINE.match(line)
            if not m:
                continue
            name, hex_str = m.group(1), m.group(2)
            try:
                color_int = int(hex_str, 16)
            except ValueError:
                print(f"warn: bad hex on line {lineno}: {line}", file=sys.stderr)
                continue
            if color_int > 0xFFFFFF:
                print(f"warn: oversize color {hex_str} on line {lineno}", file=sys.stderr)
                continue
            name_to_color[name] = color_int
    return name_to_color


def extract_locations(png_path: Path, named: dict[str, int]) -> dict[str, dict]:
    """For each named color, compute centroid, bbox, pixel count from the bitmap.

    Strategy: pack RGB into uint32, compute unique colors and their pixel positions
    in one pass, then look up each named color's stats.
    """
    print(f"loading {png_path} ...", flush=True)
    t0 = time.time()
    img = np.asarray(Image.open(png_path).convert("RGB"))  # (H, W, 3) uint8
    h, w, _ = img.shape
    print(f"  {w}x{h}, {img.nbytes / 1e6:.0f} MB, loaded in {time.time()-t0:.1f}s", flush=True)

    print("packing pixels ...", flush=True)
    t0 = time.time()
    packed = (
        (img[:, :, 0].astype(np.uint32) << 16)
        | (img[:, :, 1].astype(np.uint32) << 8)
        | img[:, :, 2].astype(np.uint32)
    )
    del img
    print(f"  packed in {time.time()-t0:.1f}s", flush=True)

    print("finding unique colors ...", flush=True)
    t0 = time.time()
    flat = packed.ravel()
    # argsort lets us group by color in one pass
    order = np.argsort(flat, kind="stable")
    sorted_colors = flat[order]
    # boundaries between color runs
    diff = np.diff(sorted_colors)
    boundaries = np.concatenate(
        ([0], np.flatnonzero(diff) + 1, [len(sorted_colors)])
    )
    print(
        f"  {len(boundaries)-1} unique colors in {time.time()-t0:.1f}s",
        flush=True,
    )

    # Map color_int -> (start, end) into the sorted order array
    color_runs: dict[int, tuple[int, int]] = {}
    for i in range(len(boundaries) - 1):
        s, e = boundaries[i], boundaries[i + 1]
        color_runs[int(sorted_colors[s])] = (s, e)

    print(f"computing stats for {len(named)} named locations ...", flush=True)
    t0 = time.time()
    out: dict[str, dict] = {}
    missing = 0
    for name, color_int in named.items():
        run = color_runs.get(color_int)
        if run is None:
            missing += 1
            continue
        s, e = run
        flat_idx = order[s:e]  # 1-d indices into packed
        ys, xs = np.divmod(flat_idx, w)
        out[name] = {
            "centroid": [float(xs.mean()), float(ys.mean())],
            "bbox": [
                int(xs.min()),
                int(ys.min()),
                int(xs.max()),
                int(ys.max()),
            ],
            "pixels": int(e - s),
            "color": int(color_int),
        }
    print(
        f"  {len(out)} resolved, {missing} missing in {time.time()-t0:.1f}s",
        flush=True,
    )
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=None, help="Path to build.config.yaml")
    ap.add_argument("--out", default=None, help="Output JSON (default: data/locations_index.json)")
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parent.parent.parent
    cfg_path = Path(args.config) if args.config else repo_root / "build.config.yaml"
    cfg = load_config(cfg_path.parent)

    eu5 = expand_path(cfg["eu5_game_root"])
    named_path = eu5 / cfg["paths"]["named_locations"]
    png_path = eu5 / cfg["paths"]["locations_png"]

    if not named_path.exists():
        print(f"error: named_locations not found at {named_path}", file=sys.stderr)
        return 1
    if not png_path.exists():
        print(f"error: locations.png not found at {png_path}", file=sys.stderr)
        return 1

    print(f"reading {named_path} ...")
    named = parse_named_locations(named_path)
    print(f"  parsed {len(named)} named locations")

    locations = extract_locations(png_path, named)

    out_path = Path(args.out) if args.out else repo_root / cfg["build"]["data_dir"] / "locations_index.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump({"version": 1, "locations": locations}, f)
    print(f"wrote {out_path} ({out_path.stat().st_size / 1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
