#!/usr/bin/env python3
"""Flatten vanilla and mod localization YAML into a single key->string map.

Paradox loc format:
  l_english:
   KEY: "value"
   OTHER:0 "value with version suffix"

Mod entries override vanilla. Output: dist/data/loc.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

import yaml


def load_config(repo_root: Path) -> dict:
    with open(repo_root / "build.config.yaml") as f:
        return yaml.safe_load(f)


def expand_path(p: str) -> Path:
    return Path(os.path.expanduser(p)).resolve()


# Match a loc line: leading whitespace, KEY: optional-version "value"
# Examples:
#   ALM: "Almohad Caliphate"
#   ALM:0 "Almohad Caliphate"
LOC_LINE = re.compile(r'^\s+([A-Za-z_][A-Za-z0-9_.]*)\s*:\s*\d*\s+"((?:[^"\\]|\\.)*)"')


def parse_loc_file(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (UnicodeDecodeError, OSError) as e:
        print(f"warn: skipping {path.name}: {e}", file=sys.stderr)
        return out
    for line in text.splitlines():
        m = LOC_LINE.match(line)
        if not m:
            continue
        key, val = m.group(1), m.group(2)
        # unescape common sequences
        val = val.replace('\\"', '"').replace("\\n", "\n").replace("\\t", "\t")
        out[key] = val
    return out


def parse_dir(loc_dir: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not loc_dir.exists():
        return out
    for f in sorted(loc_dir.glob("*.yml")):
        out.update(parse_loc_file(f))
    return out


REF_RE = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*)\$")
SHOW_RE = re.compile(
    r"\[Show\w*(?:Name|Adjective)(?:WithNoTooltip)?\(\s*'([^']+)'\s*\)\]"
)


def collect_seed_keys(web_data_dir: Path) -> set[str]:
    needed: set[str] = set()
    formables_path = web_data_dir / "formables.json"
    if formables_path.exists():
        data = json.loads(formables_path.read_text())
        for rec in data.get("formables", []):
            for k in ("tag", "name", "adjective"):
                v = rec.get(k)
                if v:
                    needed.add(v)
                    needed.add(v + "_ADJ")
                    needed.add(v + "_f")
                    needed.add(v + "_f_desc")
            bk = rec.get("block_key")
            if bk:
                needed.add(bk)
                needed.add(bk + "_desc")
                if bk.endswith("_f"):
                    needed.add(bk[:-2])
    geo_path = web_data_dir / "geography.json"
    if geo_path.exists():
        geo = json.loads(geo_path.read_text())
        for level in ("continents", "subregions", "regions", "areas",
                      "provinces", "locations"):
            for name in geo.get(level, {}).keys():
                needed.add(name)
    return needed


def expand_references(loc: dict[str, str], seed: set[str]) -> set[str]:
    """Iteratively pull in any keys referenced from kept values via $REF$
    or [ShowFooName('X')] / [ShowFooAdjective('X')] markup, so the frontend
    can resolve description text without missing pieces."""
    seen = {k for k in seed if k in loc}
    queue = list(seen)
    while queue:
        next_queue: list[str] = []
        for k in queue:
            v = loc.get(k)
            if not v:
                continue
            for m in REF_RE.finditer(v):
                ref = m.group(1)
                if ref in loc and ref not in seen:
                    seen.add(ref)
                    next_queue.append(ref)
            for m in SHOW_RE.finditer(v):
                ref = m.group(1)
                for cand in (ref, ref + "_ADJ"):
                    if cand in loc and cand not in seen:
                        seen.add(cand)
                        next_queue.append(cand)
        queue = next_queue
    return seen


def collect_needed_keys(loc: dict[str, str], web_data_dir: Path) -> set[str]:
    seed = collect_seed_keys(web_data_dir)
    return expand_references(loc, seed)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    ap.add_argument("--full", action="store_true",
                    help="Emit all keys instead of filtering to frontend needs")
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parent.parent.parent
    cfg = load_config(repo_root)
    eu5 = expand_path(cfg["eu5_game_root"])
    mod_root = expand_path(cfg["mod_root"])
    web_data_dir = repo_root / cfg["build"]["web_data_dir"]

    vanilla_dir = eu5 / "main_menu/localization/english"
    mod_dir = mod_root / "main_menu/localization/english"

    print(f"reading vanilla {vanilla_dir} ...")
    loc = parse_dir(vanilla_dir)
    print(f"  {len(loc)} keys")

    print(f"reading mod {mod_dir} ...")
    mod = parse_dir(mod_dir)
    print(f"  {len(mod)} mod keys")
    overlapping = sum(1 for k in mod if k in loc)
    loc.update(mod)
    print(f"  {overlapping} mod keys override vanilla; total now {len(loc)}")

    if not args.full:
        needed = collect_needed_keys(loc, web_data_dir)
        before = len(loc)
        loc = {k: v for k, v in loc.items() if k in needed}
        print(f"  filtered to {len(loc)}/{before} keys "
              f"(seed expanded to {len(needed)} after following $refs/[Show...] markup)")

    out_path = Path(args.out) if args.out else web_data_dir / "loc.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump({"version": 1, "strings": loc}, f)
    print(f"wrote {out_path} ({out_path.stat().st_size/1e6:.2f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
