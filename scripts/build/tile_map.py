#!/usr/bin/env python3
"""Slice locations.png into an XYZ tile pyramid for Leaflet.

Strategy: load full image once, then for each zoom level from max down to 0,
slice the current image into 256x256 tiles and downsample by 2x for the
next level. This avoids redundantly downsampling the full image N times.

Map is 16384x8192 (2:1). We pad to 16384x16384 so the standard XYZ scheme
(2^z tiles per side) works cleanly. The bottom half is blank and we skip
writing those tiles -- Leaflet will just show empty.

Output: dist/tiles/{z}/{x}/{y}.png
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import numpy as np
import yaml
from PIL import Image


TILE_SIZE = 256


def load_config(repo_root: Path) -> dict:
    with open(repo_root / "build.config.yaml") as f:
        return yaml.safe_load(f)


def expand_path(p: str) -> Path:
    return Path(os.path.expanduser(p)).resolve()


RESAMPLERS = {
    "nearest": Image.NEAREST,
    "bilinear": Image.BILINEAR,
    "lanczos": Image.LANCZOS,
}


def make_pyramid(
    img: Image.Image,
    max_zoom: int,
    out_root: Path,
    resampler: int = Image.LANCZOS,
) -> int:
    """Generate tiles from max_zoom down to 0. Returns total tile count."""
    out_root.mkdir(parents=True, exist_ok=True)

    # Pad to square at native zoom so XYZ scheme is regular.
    native_w, native_h = img.size
    side = max(native_w, native_h)
    if native_w != side or native_h != side:
        padded = Image.new("RGB", (side, side), (0, 0, 0))
        padded.paste(img, (0, 0))
        img = padded

    total = 0
    current = img
    for z in range(max_zoom, -1, -1):
        z_dir = out_root / str(z)
        z_dir.mkdir(parents=True, exist_ok=True)
        size = current.size[0]  # square
        tiles_per_side = max(1, size // TILE_SIZE)
        # If current image is smaller than 256, pad up to 256 for z=0
        if size < TILE_SIZE:
            framed = Image.new("RGB", (TILE_SIZE, TILE_SIZE), (0, 0, 0))
            framed.paste(current, (0, 0))
            framed.save(z_dir / "0" / "0.png" if False else str(z_dir / f"0_0.png"))
            # standard layout: {z}/{x}/{y}.png
            (z_dir / "0").mkdir(exist_ok=True)
            framed.save(z_dir / "0" / "0.png")
            total += 1
        else:
            # native_h_at_z is how much of the image is non-padding
            scale = side / native_w  # at native zoom this is 1
            current_native_h = int(native_h * (size / side))
            t0 = time.time()
            written = 0
            for x in range(tiles_per_side):
                col_dir = z_dir / str(x)
                col_dir.mkdir(exist_ok=True)
                for y in range(tiles_per_side):
                    # Skip tiles fully in the padding region.
                    if y * TILE_SIZE >= current_native_h:
                        continue
                    box = (
                        x * TILE_SIZE,
                        y * TILE_SIZE,
                        (x + 1) * TILE_SIZE,
                        (y + 1) * TILE_SIZE,
                    )
                    tile = current.crop(box)
                    tile.save(col_dir / f"{y}.png", optimize=True)
                    written += 1
            print(
                f"  z={z}: {tiles_per_side}x{tiles_per_side} grid, "
                f"{written} tiles written in {time.time()-t0:.1f}s",
                flush=True,
            )
            total += written

        # Downsample for next zoom level
        if z > 0:
            new_size = max(1, current.size[0] // 2)
            current = current.resize((new_size, new_size), resampler)
    return total


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None, help="Output dir (default: dist/tiles)")
    ap.add_argument("--input", default=None,
                    help="Input PNG (default: data/basemap.png if it exists, "
                         "else EU5 locations.png)")
    ap.add_argument("--filter", choices=["nearest", "lanczos", "bilinear"],
                    default="lanczos",
                    help="Downsample filter (default: lanczos for recolored basemap)")
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parent.parent.parent
    cfg = load_config(repo_root)

    if args.input:
        png_path = Path(args.input)
    else:
        recolored = repo_root / cfg["build"]["data_dir"] / "basemap.png"
        if recolored.exists():
            png_path = recolored
        else:
            eu5 = expand_path(cfg["eu5_game_root"])
            png_path = eu5 / cfg["paths"]["locations_png"]
    if not png_path.exists():
        print(f"error: {png_path} not found", file=sys.stderr)
        return 1

    out_root = Path(args.out) if args.out else repo_root / cfg["build"]["dist_dir"] / "tiles"
    max_zoom = int(cfg["map"]["zoom_levels"])

    print(f"loading {png_path} ...")
    Image.MAX_IMAGE_PIXELS = None  # disable decompression bomb warning
    img = Image.open(png_path).convert("RGB")
    print(f"  {img.size}")

    print(f"generating pyramid 0..{max_zoom} into {out_root} (filter={args.filter})")
    t0 = time.time()
    total = make_pyramid(img, max_zoom, out_root, RESAMPLERS[args.filter])
    print(f"done: {total} tiles in {time.time()-t0:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
