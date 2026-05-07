#!/usr/bin/env python3
"""Recolor locations.png into a political-style basemap.

Classifies each location (sea / lake / wasteland / land) via topography in
location_templates.txt, then paints the bitmap by class with subtle borders
between adjacent provinces. Sea-sea borders are suppressed for clean ocean.

Output: data/basemap.png (same dimensions as input).
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
from pathlib import Path

import numpy as np
import yaml
from PIL import Image


SEA_TOPO = {
    "coastal_ocean", "ocean", "inland_sea", "narrows",
    "deep_ocean", "ocean_wasteland",
}
LAKE_TOPO = {"lakes", "high_lakes"}
WASTE_TOPO = {
    "mountain_wasteland", "hills_wasteland", "flatland_wasteland",
    "dune_wasteland", "plateau_wasteland", "wetlands_wasteland",
    "mesa_wasteland", "salt_pans",
}
# Everything else with a topography (flatland, hills, mountains, plateau,
# wetlands, atoll) is treated as land.

CLASS_LAND = 0
CLASS_SEA = 1
CLASS_LAKE = 2
CLASS_WASTE = 3
CLASS_UNKNOWN = 4

# Palette: warm political-map look, low saturation so highlights pop on top
PALETTE = np.array([
    [217, 201, 167],  # land: warm tan
    [ 70,  98, 124],  # sea: muted steel blue
    [110, 150, 175],  # lake: lighter blue
    [165, 152, 130],  # wasteland: muted khaki
    [ 40,  40,  44],  # unknown: near-black
], dtype=np.uint8)
BORDER_RGB = np.array([54, 44, 36], dtype=np.uint8)     # dark warm brown
COAST_RGB  = np.array([34, 30, 28], dtype=np.uint8)     # near-black for coasts


HEX_LINE = re.compile(r"^\s*([a-zA-Z0-9_]+)\s*=\s*([0-9a-fA-F]+)\s*(?:#.*)?$")
TEMPLATE_LINE = re.compile(
    r"^\s*([a-zA-Z0-9_]+)\s*=\s*\{(.*?)\}\s*$"
)


def load_config(repo_root: Path) -> dict:
    with open(repo_root / "build.config.yaml") as f:
        return yaml.safe_load(f)


def expand_path(p: str) -> Path:
    return Path(os.path.expanduser(p)).resolve()


def parse_named_locations(path: Path) -> dict[str, int]:
    out: dict[str, int] = {}
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
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
                continue
            if 0 <= color_int <= 0xFFFFFF:
                out[name] = color_int
    return out


def parse_location_templates(path: Path) -> dict[str, str]:
    """Return name -> topography string."""
    out: dict[str, str] = {}
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            m = TEMPLATE_LINE.match(line)
            if not m:
                continue
            name, body = m.group(1), m.group(2)
            tm = re.search(r"topography\s*=\s*([a-z_]+)", body)
            if tm:
                out[name] = tm.group(1)
    return out


def classify(topo: str | None) -> int:
    if topo is None:
        return CLASS_UNKNOWN
    if topo in SEA_TOPO:
        return CLASS_SEA
    if topo in LAKE_TOPO:
        return CLASS_LAKE
    if topo in WASTE_TOPO:
        return CLASS_WASTE
    return CLASS_LAND


def build_color_class_lut(
    name_to_color: dict[str, int],
    name_to_topo: dict[str, str],
) -> tuple[np.ndarray, np.ndarray]:
    """Return (sorted_colors, class_per_color)."""
    seen: dict[int, int] = {}
    for name, color_int in name_to_color.items():
        cls = classify(name_to_topo.get(name))
        # Same color appearing under multiple names: sea wins, then lake,
        # then waste, then land. Unknown is overridden by anything.
        prev = seen.get(color_int, CLASS_UNKNOWN)
        prio = {CLASS_UNKNOWN: 0, CLASS_LAND: 1, CLASS_WASTE: 2,
                CLASS_LAKE: 3, CLASS_SEA: 4}
        if prio[cls] > prio[prev]:
            seen[color_int] = cls
        elif color_int not in seen:
            seen[color_int] = cls
    colors = np.fromiter(sorted(seen.keys()), dtype=np.uint32)
    classes = np.fromiter((seen[c] for c in colors.tolist()), dtype=np.uint8)
    return colors, classes


def recolor(
    img: np.ndarray,
    colors_sorted: np.ndarray,
    class_per_color: np.ndarray,
) -> np.ndarray:
    h, w, _ = img.shape
    print(f"  packing {w}x{h} ...", flush=True)
    t0 = time.time()
    packed = (
        (img[:, :, 0].astype(np.uint32) << 16)
        | (img[:, :, 1].astype(np.uint32) << 8)
        | img[:, :, 2].astype(np.uint32)
    )
    print(f"  packed in {time.time()-t0:.1f}s", flush=True)

    print("  classifying pixels ...", flush=True)
    t0 = time.time()
    idx = np.searchsorted(colors_sorted, packed)
    idx_clamped = np.minimum(idx, len(colors_sorted) - 1)
    valid = colors_sorted[idx_clamped] == packed
    class_map = np.full(packed.shape, CLASS_UNKNOWN, dtype=np.uint8)
    class_map[valid] = class_per_color[idx_clamped[valid]]
    print(f"  classified in {time.time()-t0:.1f}s", flush=True)

    print("  detecting boundaries ...", flush=True)
    t0 = time.time()
    color_diff = np.zeros(packed.shape, dtype=bool)
    class_diff = np.zeros(packed.shape, dtype=bool)
    for shift, axis in [(1, 0), (-1, 0), (1, 1), (-1, 1)]:
        color_diff |= packed != np.roll(packed, shift, axis=axis)
        class_diff |= class_map != np.roll(class_map, shift, axis=axis)
    # Edges of the bitmap are not real borders for y; for x we wrap (wrap_x)
    color_diff[0, :] = False
    color_diff[-1, :] = False
    class_diff[0, :] = False
    class_diff[-1, :] = False
    print(f"  boundaries in {time.time()-t0:.1f}s", flush=True)

    print("  painting output ...", flush=True)
    t0 = time.time()
    out = PALETTE[class_map]  # (H, W, 3)

    # A pixel is fully-internal sea if every 4-neighbor is sea: skip border there.
    sea_mask = class_map == CLASS_SEA
    not_sea = ~sea_mask
    has_non_sea_neighbor = np.zeros(packed.shape, dtype=bool)
    for shift, axis in [(1, 0), (-1, 0), (1, 1), (-1, 1)]:
        has_non_sea_neighbor |= np.roll(not_sea, shift, axis=axis)

    # Province border (subtle): color differs and we're not deep in the ocean.
    province_border = color_diff & (not_sea | has_non_sea_neighbor)
    out[province_border] = BORDER_RGB
    # Coast (stronger): class differs (land/lake meets sea, etc.).
    out[class_diff] = COAST_RGB
    print(f"  painted in {time.time()-t0:.1f}s", flush=True)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parent.parent.parent
    cfg = load_config(repo_root)
    eu5 = expand_path(cfg["eu5_game_root"])
    png_path = eu5 / cfg["paths"]["locations_png"]
    named_path = eu5 / cfg["paths"]["named_locations"]
    templates_path = eu5 / "in_game/map_data/location_templates.txt"

    for p in [png_path, named_path, templates_path]:
        if not p.exists():
            print(f"error: {p} not found", file=sys.stderr)
            return 1

    print(f"loading named_locations ...")
    name_to_color = parse_named_locations(named_path)
    print(f"  {len(name_to_color)} entries")

    print(f"loading location_templates ...")
    name_to_topo = parse_location_templates(templates_path)
    print(f"  {len(name_to_topo)} entries with topography")

    colors_sorted, class_per_color = build_color_class_lut(
        name_to_color, name_to_topo
    )
    counts = np.bincount(class_per_color, minlength=5)
    print(
        f"  classes: land={counts[0]} sea={counts[1]} lake={counts[2]} "
        f"waste={counts[3]} unknown={counts[4]}"
    )

    print(f"loading {png_path} ...")
    Image.MAX_IMAGE_PIXELS = None
    img = np.asarray(Image.open(png_path).convert("RGB"))
    print(f"  {img.shape}, {img.nbytes/1e6:.0f} MB")

    out = recolor(img, colors_sorted, class_per_color)

    out_path = Path(args.out) if args.out else repo_root / cfg["build"]["data_dir"] / "basemap.png"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"writing {out_path} ...")
    Image.fromarray(out).save(out_path, optimize=True)
    print(f"  {out_path.stat().st_size/1e6:.1f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
