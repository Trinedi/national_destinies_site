#!/usr/bin/env python3
"""Extract per-area polygon outlines from locations.png as GeoJSON.

For each area in geography.json, build the union of pixels from its member
locations, find contours via scikit-image, simplify with shapely, and emit
as a GeoJSON FeatureCollection. Disconnected areas become MultiPolygons.

Coordinates are EU5 native pixel space: x in [0, 16384], y in [0, 8192],
origin top-left. The frontend converts to Leaflet's flipped CRS.Simple.

Output: dist/data/areas.geojson
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
from skimage import measure
from shapely.geometry import MultiPolygon, Polygon, mapping
from shapely.validation import make_valid


def load_config(repo_root: Path) -> dict:
    with open(repo_root / "build.config.yaml") as f:
        return yaml.safe_load(f)


def expand_path(p: str) -> Path:
    return Path(os.path.expanduser(p)).resolve()


HEX_LINE = re.compile(r"^\s*([a-zA-Z0-9_]+)\s*=\s*([0-9a-fA-F]+)\s*(?:#.*)?$")
TEMPLATE_LINE = re.compile(r"^\s*([a-zA-Z0-9_]+)\s*=\s*\{(.*?)\}\s*$")

# Topographies that should NOT contribute to area polygons (sea zones leak
# into adjacent areas otherwise, since EU5 "areas" group land and the
# coastal sea zones around them).
NON_LAND_TOPO = {
    "coastal_ocean", "ocean", "inland_sea", "narrows",
    "deep_ocean", "ocean_wasteland",
    "lakes", "high_lakes",
}


def parse_location_templates(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            m = TEMPLATE_LINE.match(line)
            if not m:
                continue
            tm = re.search(r"topography\s*=\s*([a-z_]+)", m.group(2))
            if tm:
                out[m.group(1)] = tm.group(1)
    return out


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
            try:
                color_int = int(m.group(2), 16)
            except ValueError:
                continue
            if 0 <= color_int <= 0xFFFFFF:
                out[m.group(1)] = color_int
    return out


def build_area_id_map(
    packed: np.ndarray,
    name_to_color: dict[str, int],
    geography: dict,
    name_to_topo: dict[str, str],
) -> tuple[np.ndarray, list[str]]:
    """Map every pixel to an area index (0 = not-in-any-area).

    Sea, lake, and ocean locations are excluded so polygons hug the
    coastline instead of leaking into adjacent water tiles.
    """
    # Build location -> area lookup, then color -> area_id.
    loc_to_area: dict[str, str] = {}
    skipped_water = 0
    for prov_name, prov in geography["provinces"].items():
        area = prov.get("area")
        if not area:
            continue
        for loc in prov["locations"]:
            topo = name_to_topo.get(loc)
            if topo in NON_LAND_TOPO:
                skipped_water += 1
                continue
            loc_to_area[loc] = area
    print(f"  skipped {skipped_water} water/lake locations", flush=True)

    # Stable area ordering for deterministic IDs.
    area_names_sorted = [""] + sorted(set(loc_to_area.values()))
    area_index = {name: i for i, name in enumerate(area_names_sorted)}

    # color_int -> area_id
    color_to_area: dict[int, int] = {}
    for loc_name, color in name_to_color.items():
        area = loc_to_area.get(loc_name)
        if area is None:
            continue
        color_to_area[color] = area_index[area]

    # Build sorted-color LUT for vectorised lookup.
    colors_sorted = np.fromiter(sorted(color_to_area.keys()), dtype=np.uint32)
    aids = np.fromiter(
        (color_to_area[c] for c in colors_sorted.tolist()), dtype=np.int32
    )

    print(f"  resolving {len(color_to_area)} color->area mappings ...", flush=True)
    t0 = time.time()
    idx = np.searchsorted(colors_sorted, packed)
    idx_clamped = np.minimum(idx, len(colors_sorted) - 1)
    valid = colors_sorted[idx_clamped] == packed
    out = np.zeros(packed.shape, dtype=np.int32)
    out[valid] = aids[idx_clamped[valid]]
    print(f"    done in {time.time()-t0:.1f}s", flush=True)
    return out, area_names_sorted


def extract_area_polygon(
    area_id_map: np.ndarray,
    area_idx: int,
    bbox_pad: int = 2,
    simplify_tolerance: float = 6.0,
) -> dict | None:
    """Return GeoJSON geometry (Polygon or MultiPolygon) for one area, or None."""
    ys, xs = np.where(area_id_map == area_idx)
    if len(ys) == 0:
        return None
    y0, y1 = max(0, ys.min() - bbox_pad), min(area_id_map.shape[0], ys.max() + bbox_pad + 1)
    x0, x1 = max(0, xs.min() - bbox_pad), min(area_id_map.shape[1], xs.max() + bbox_pad + 1)
    sub = area_id_map[y0:y1, x0:x1] == area_idx
    if not sub.any():
        return None

    # find_contours expects float and operates between pixels at level=0.5
    contours = measure.find_contours(sub.astype(np.uint8), 0.5)
    polys: list[Polygon] = []
    # find_contours returns (row, col) pairs. Sort by length so largest is
    # treated as the exterior; smaller ones as holes if topologically inside.
    rings: list[np.ndarray] = []
    for c in contours:
        if len(c) < 4:
            continue
        # convert (row, col) -> (x, y) absolute
        ring = np.column_stack(((c[:, 1] + x0), (c[:, 0] + y0)))
        rings.append(ring)
    if not rings:
        return None

    # Build polygons. Treat any ring as its own polygon for now; holes are
    # rare in our case and shapely's make_valid will fix overlaps.
    for ring in rings:
        try:
            p = Polygon(ring)
            if not p.is_valid:
                p = make_valid(p)
            if p.is_empty:
                continue
            if p.geom_type == "Polygon":
                polys.append(p)
            elif p.geom_type == "MultiPolygon":
                polys.extend(list(p.geoms))
        except Exception:
            continue

    if not polys:
        return None

    geom = MultiPolygon(polys) if len(polys) > 1 else polys[0]
    geom = geom.simplify(simplify_tolerance, preserve_topology=True)
    if geom.is_empty:
        return None
    return mapping(geom)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--simplify", type=float, default=6.0,
                    help="Douglas-Peucker tolerance in pixels (default: 6.0)")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parent.parent.parent
    cfg = load_config(repo_root)
    eu5 = expand_path(cfg["eu5_game_root"])
    web_data_dir = repo_root / cfg["build"]["web_data_dir"]

    png_path = eu5 / cfg["paths"]["locations_png"]
    named_path = eu5 / cfg["paths"]["named_locations"]
    templates_path = eu5 / "in_game/map_data/location_templates.txt"
    geo_path = web_data_dir / "geography.json"
    for p in [png_path, named_path, templates_path, geo_path]:
        if not p.exists():
            print(f"error: {p} not found", file=sys.stderr)
            return 1

    print("loading geography ...")
    geography = json.loads(geo_path.read_text())
    print(f"  {len(geography['areas'])} areas, {len(geography['provinces'])} provinces")

    print("loading named_locations ...")
    name_to_color = parse_named_locations(named_path)
    print(f"  {len(name_to_color)} entries")

    print("loading location_templates ...")
    name_to_topo = parse_location_templates(templates_path)
    print(f"  {len(name_to_topo)} entries with topography")

    print(f"loading {png_path} ...")
    Image.MAX_IMAGE_PIXELS = None
    img = np.asarray(Image.open(png_path).convert("RGB"))
    h, w, _ = img.shape
    print(f"  {w}x{h}, {img.nbytes/1e6:.0f} MB")
    packed = (
        (img[:, :, 0].astype(np.uint32) << 16)
        | (img[:, :, 1].astype(np.uint32) << 8)
        | img[:, :, 2].astype(np.uint32)
    )
    del img

    print("building area id map ...")
    area_id_map, area_names = build_area_id_map(
        packed, name_to_color, geography, name_to_topo
    )
    del packed

    print(f"extracting polygons (simplify={args.simplify}px) ...")
    features: list[dict] = []
    skipped = 0
    t0 = time.time()
    last_log = t0
    for i, area_name in enumerate(area_names):
        if i == 0:
            continue  # sentinel "no area"
        geom = extract_area_polygon(area_id_map, i, simplify_tolerance=args.simplify)
        if geom is None:
            skipped += 1
            continue
        meta = geography["areas"].get(area_name, {})
        features.append({
            "type": "Feature",
            "id": area_name,
            "properties": {
                "name": area_name,
                "region": meta.get("region"),
                "subregion": meta.get("subregion"),
                "continent": meta.get("continent"),
            },
            "geometry": geom,
        })
        if time.time() - last_log > 5:
            done = i
            elapsed = time.time() - t0
            print(f"  {done}/{len(area_names)-1} done, {elapsed:.0f}s elapsed", flush=True)
            last_log = time.time()
    print(f"  {len(features)} features, {skipped} empty in {time.time()-t0:.1f}s")

    fc = {"type": "FeatureCollection", "features": features}
    out_path = Path(args.out) if args.out else web_data_dir / "areas.geojson"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(fc, f, separators=(",", ":"))
    print(f"wrote {out_path} ({out_path.stat().st_size/1e6:.2f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
