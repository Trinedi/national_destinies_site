#!/usr/bin/env python3
"""Parse vanilla and mod formable_countries/*.txt into structured records.

Handles three header forms at top level of each file:
  - TAG_f = { ... }                full definition (vanilla, or mod-new)
  - INJECT:TAG_f = { ... }         add fields to existing vanilla def
  - REPLACE:TAG_f = { ... }        wholesale replace vanilla def

Output: data/formables.json with a list of merged records, each marked with
a `source` field showing whether the mod touches it.
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


# --- Named color resolution ------------------------------------------------

NAMED_COLOR_RE = re.compile(
    r"\b([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(rgb|hsv360|hsv)\s*\{\s*"
    r"([\d.]+)\s+([\d.]+)\s+([\d.]+)\s*\}"
)


def _hsv_to_rgb(h: float, s: float, v: float) -> tuple[int, int, int]:
    # h: 0-360, s/v: 0-100 (game uses hsv360 with 0-100 percent)
    import colorsys
    r, g, b = colorsys.hsv_to_rgb((h % 360) / 360.0, s / 100.0, v / 100.0)
    return (round(r * 255), round(g * 255), round(b * 255))


def parse_named_colors(*color_dirs: Path) -> dict[str, tuple[int, int, int]]:
    """Parse `colors = { name = rgb {...} }` blocks from every file in the dirs.

    Later directories override earlier ones (mod overrides vanilla).
    """
    out: dict[str, tuple[int, int, int]] = {}
    for d in color_dirs:
        if not d.exists():
            continue
        for path in sorted(d.glob("*.txt")):
            text = strip_comments(path.read_text(encoding="utf-8-sig"))
            for m in NAMED_COLOR_RE.finditer(text):
                name, kind, a, b, c = m.groups()
                fa, fb, fc = float(a), float(b), float(c)
                if kind == "rgb":
                    out[name] = (int(fa), int(fb), int(fc))
                else:  # hsv / hsv360
                    out[name] = _hsv_to_rgb(fa, fb, fc)
    return out


def _tag_hash(s: str) -> int:
    # FNV-1a 32-bit, deterministic across Python runs
    h = 0x811C9DC5
    for ch in s.encode("utf-8"):
        h ^= ch
        h = (h * 0x01000193) & 0xFFFFFFFF
    return h


def _rgb_to_hsl(r: int, g: int, b: int) -> tuple[float, float, float]:
    import colorsys
    h, l, s = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
    return (h * 360.0, s * 100.0, l * 100.0)


def _hsl_to_hex(h: float, s: float, l: float) -> str:
    import colorsys
    r, g, b = colorsys.hls_to_rgb((h % 360) / 360.0, max(0, min(1, l / 100.0)), max(0, min(1, s / 100.0)))
    return "#{:02x}{:02x}{:02x}".format(round(r * 255), round(g * 255), round(b * 255))


def resolve_color(color_name: str | None, tag: str | None,
                  named: dict[str, tuple[int, int, int]]) -> str | None:
    """Resolve a formable's color to a hex string with a small per-tag nudge.

    The base RGB comes from the named color (matching the in-game tint).
    A deterministic per-tag hash shifts hue by ~±4 degrees and lightness
    by ~±4 percent so multiple formables sharing one named color stay
    visually distinguishable while remaining clearly the same family.
    """
    if not color_name:
        return None
    rgb = named.get(color_name)
    if rgb is None:
        return None
    if not tag:
        return "#{:02x}{:02x}{:02x}".format(*rgb)
    h, s, l = _rgb_to_hsl(*rgb)
    th = _tag_hash(tag)
    hue_nudge = ((th & 0xFF) / 255.0 - 0.5) * 8.0          # ±4 deg
    light_nudge = (((th >> 8) & 0xFF) / 255.0 - 0.5) * 8.0  # ±4 percent
    return _hsl_to_hex(h + hue_nudge, s, l + light_nudge)


HEADER_RE = re.compile(
    r"((?:INJECT|REPLACE):)?([A-Za-z_][A-Za-z0-9_]*_f)\s*=\s*\{"
)


def strip_comments(text: str) -> str:
    return re.sub(r"#[^\n]*", "", text)


def find_top_level_blocks(text: str):
    """Yield (mode, block_key, body_text) for each top-level header = { ... } block.

    mode is 'full', 'inject', or 'replace'. block_key is e.g. 'ALM_f' or
    'sweden_f'. body_text is the contents between the outermost braces.
    """
    text = strip_comments(text)
    pos = 0
    while pos < len(text):
        m = HEADER_RE.search(text, pos)
        if not m:
            return
        mode_prefix = m.group(1)  # 'INJECT:' / 'REPLACE:' / None
        block_key = m.group(2)
        if mode_prefix == "INJECT:":
            mode = "inject"
        elif mode_prefix == "REPLACE:":
            mode = "replace"
        else:
            mode = "full"
        body_start = m.end()  # past the '{'
        # Track braces (no quote handling needed inside a comment-stripped script)
        depth = 1
        i = body_start
        while i < len(text) and depth > 0:
            c = text[i]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
            i += 1
        if depth != 0:
            print(f"warn: unclosed block {block_key}", file=sys.stderr)
            return
        body = text[body_start : i - 1]
        yield mode, block_key, body
        pos = i


def find_balanced_block(body: str, key: str) -> str | None:
    """Find `key = { ... }` inside body and return the inner text. None if missing."""
    pat = re.compile(rf"\b{re.escape(key)}\s*=\s*\{{")
    m = pat.search(body)
    if not m:
        return None
    depth = 1
    i = m.end()
    start = i
    while i < len(body) and depth > 0:
        c = body[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        i += 1
    if depth != 0:
        return None
    return body[start : i - 1]


SIMPLE_FIELD_RE = re.compile(
    r"^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([^\s{}#]+)", re.MULTILINE
)


def extract_simple_fields(body: str) -> dict[str, str]:
    """Top-level scalar fields like `level = 3`. Excludes block-valued fields."""
    out: dict[str, str] = {}
    depth = 0
    cur_pos = 0
    # Walk character by character to honor depth, capturing only depth-0 assignments.
    i = 0
    while i < len(body):
        c = body[i]
        if c == "{":
            depth += 1
            i += 1
            continue
        if c == "}":
            depth -= 1
            i += 1
            continue
        if depth == 0:
            m = re.match(r"\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*", body[i:])
            if m:
                key = m.group(1)
                val_start = i + m.end()
                if val_start < len(body) and body[val_start] == "{":
                    # Block value, skip; will be handled by find_balanced_block
                    i = val_start
                    continue
                # Read until whitespace, comment, or end
                val_match = re.match(r"([^\s{}#]+)", body[val_start:])
                if val_match:
                    out[key] = val_match.group(1)
                    i = val_start + val_match.end()
                    continue
        i += 1
    return out


def extract_name_list(block_body: str | None) -> list[str]:
    if block_body is None:
        return []
    return re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", block_body)


def extract_owns(allow_body: str | None) -> list[str]:
    if allow_body is None:
        return []
    return re.findall(r"\bowns\s*=\s*location:([a-zA-Z0-9_]+)", allow_body)


def extract_form_event(form_effect_body: str | None) -> str | None:
    if form_effect_body is None:
        return None
    m = re.search(r"\btrigger_event_non_silently\s*=\s*([a-zA-Z0-9_.]+)", form_effect_body)
    return m.group(1) if m else None


def parse_block(block_key: str, body: str, mode: str, source_file: str) -> dict:
    fields = extract_simple_fields(body)
    regions = extract_name_list(find_balanced_block(body, "regions"))
    areas = extract_name_list(find_balanced_block(body, "areas"))
    locations = extract_name_list(find_balanced_block(body, "locations"))
    provinces = extract_name_list(find_balanced_block(body, "provinces"))
    sub_continents = extract_name_list(find_balanced_block(body, "sub_continents"))
    continents = extract_name_list(find_balanced_block(body, "continents"))
    allow_body = find_balanced_block(body, "allow")
    potential_body = find_balanced_block(body, "potential")
    form_effect_body = find_balanced_block(body, "form_effect")

    record: dict = {
        "block_key": block_key,
        "mode": mode,
        "source_file": source_file,
        "tag": fields.get("tag"),
        "name": fields.get("name"),
        "adjective": fields.get("adjective"),
        "flag": fields.get("flag"),
        "color": fields.get("color"),
        "level": _maybe_int(fields.get("level")),
        "fraction": _maybe_float(fields.get("required_locations_fraction")),
        "rule": fields.get("rule"),
        "content_priority": _maybe_int(fields.get("content_priority")),
        "regions": regions,
        "areas": areas,
        "locations": locations,
        "provinces": provinces,
        "sub_continents": sub_continents,
        "continents": continents,
        "must_own": extract_owns(allow_body),
        "allow_raw": allow_body.strip() if allow_body else None,
        "potential_raw": potential_body.strip() if potential_body else None,
        "form_effect_raw": form_effect_body.strip() if form_effect_body else None,
        "formation_event": extract_form_event(form_effect_body),
    }
    return record


def _maybe_int(s: str | None) -> int | None:
    if s is None:
        return None
    try:
        return int(s)
    except ValueError:
        return None


def _maybe_float(s: str | None) -> float | None:
    if s is None:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def parse_dir(path: Path) -> list[dict]:
    records: list[dict] = []
    if not path.exists():
        return records
    for f in sorted(path.glob("*.txt")):
        if f.name == "readme.txt":
            continue
        text = f.read_text(encoding="utf-8-sig")
        for mode, block_key, body in find_top_level_blocks(text):
            records.append(parse_block(block_key, body, mode, str(f.name)))
    return records


def derive_variant_label(block_key: str, tag: str | None) -> str | None:
    """For LAT_REDUCED_REQUIREMENTS_f or ROM_BYZ_f-style block keys, derive a
    short suffix like 'Reduced Requirements' or 'BYZ' to disambiguate when
    multiple blocks share the same canonical tag."""
    body = block_key[:-2] if block_key.endswith("_f") else block_key
    if tag and body.upper().startswith(tag.upper() + "_"):
        body = body[len(tag) + 1 :]
    elif tag and body.upper() == tag.upper():
        return None
    body = body.replace("_", " ").strip()
    if not body:
        return None
    return body.title()


TERRITORY_FIELDS = (
    "continents", "sub_continents", "regions", "areas",
    "provinces", "locations", "must_own",
)


def apply_territory_overrides(records: list[dict], overrides: dict) -> None:
    if not overrides:
        return
    n = 0
    for r in records:
        tag = r.get("tag")
        if not tag or tag not in overrides:
            continue
        if any(r.get(f) for f in TERRITORY_FIELDS):
            continue  # only fill in when the formable has no territory at all
        patch = overrides[tag]
        for k, v in patch.items():
            if k in TERRITORY_FIELDS and v:
                r[k] = list(v)
        n += 1
    if n:
        print(f"  applied territory overrides to {n} formable(s)")


def annotate_variants(records: list[dict]) -> None:
    by_tag: dict[str, list[dict]] = {}
    for r in records:
        if r.get("tag"):
            by_tag.setdefault(r["tag"], []).append(r)
    for tag, group in by_tag.items():
        if len(group) <= 1:
            for r in group:
                r["variant_label"] = None
            continue
        for r in group:
            r["variant_label"] = derive_variant_label(r["block_key"], tag)


def merge(vanilla: list[dict], mod: list[dict]) -> list[dict]:
    """Merge vanilla + mod definitions by block_key.

    INJECT/REPLACE entries override or supplement vanilla; full mod entries
    that share a block_key with vanilla replace it; new keys are added.
    """
    by_key: dict[str, dict] = {}
    for r in vanilla:
        r = dict(r)
        r["source"] = "vanilla"
        r["mod_overrides"] = False
        by_key[r["block_key"]] = r

    for r in mod:
        key = r["block_key"]
        existing = by_key.get(key)
        if existing is None:
            # Mod-new formable
            r2 = dict(r)
            r2["source"] = "mod_new"
            r2["mod_overrides"] = True
            by_key[key] = r2
            continue
        if r["mode"] == "replace" or r["mode"] == "full":
            r2 = dict(r)
            r2["source"] = "vanilla+mod_replace"
            r2["mod_overrides"] = True
            # Preserve vanilla tag/name if mod doesn't set them
            for k in ("tag", "name", "adjective", "flag", "color"):
                if r2.get(k) is None and existing.get(k) is not None:
                    r2[k] = existing[k]
            by_key[key] = r2
        elif r["mode"] == "inject":
            # INJECT replaces specified fields wholesale (per CLAUDE.md note).
            # We start from vanilla and overlay mod-provided fields.
            merged = dict(existing)
            merged["source"] = "vanilla+mod_inject"
            merged["mod_overrides"] = True
            for k, v in r.items():
                if k in ("block_key", "mode", "source", "source_file", "mod_overrides"):
                    continue
                if v in (None, [], ""):
                    continue
                merged[k] = v
            # Always carry the mod's source_file for reference
            merged["mod_source_file"] = r["source_file"]
            merged["form_effect_raw"] = r["form_effect_raw"] or existing.get("form_effect_raw")
            merged["formation_event"] = r["formation_event"] or existing.get("formation_event")
            by_key[key] = merged
    return list(by_key.values())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parent.parent.parent
    cfg = load_config(repo_root)

    eu5 = expand_path(cfg["eu5_game_root"])
    mod_root = expand_path(cfg["mod_root"])
    vanilla_dir = eu5 / "in_game/common/formable_countries"
    mod_dir = mod_root / "in_game/common/formable_countries"

    print(f"reading vanilla {vanilla_dir} ...")
    vanilla = parse_dir(vanilla_dir)
    print(f"  {len(vanilla)} formables")

    print(f"reading mod {mod_dir} ...")
    mod = parse_dir(mod_dir)
    print(f"  {len(mod)} mod entries (full + INJECT/REPLACE)")

    merged = merge(vanilla, mod)
    apply_territory_overrides(merged, cfg.get("territory_overrides") or {})
    annotate_variants(merged)

    # Resolve in-game named colors to hex with a per-tag nudge so siblings
    # sharing a named color (e.g. several Scandinavian tags) stay distinct.
    named_dirs = [
        eu5 / "main_menu/common/named_colors",
        mod_root / "main_menu/common/named_colors",
    ]
    named_colors = parse_named_colors(*named_dirs)
    print(f"resolved {len(named_colors)} named colors")
    n_resolved = 0
    n_unresolved = 0
    for r in merged:
        rgb_hex = resolve_color(r.get("color"), r.get("tag") or r.get("block_key"), named_colors)
        if rgb_hex:
            r["color_rgb"] = rgb_hex
            n_resolved += 1
        elif r.get("color"):
            n_unresolved += 1
    print(f"  color_rgb assigned to {n_resolved} formables; {n_unresolved} unresolved color refs")
    by_source: dict[str, int] = {}
    for r in merged:
        by_source[r["source"]] = by_source.get(r["source"], 0) + 1
    print("merged:")
    for k, v in sorted(by_source.items()):
        print(f"  {k}: {v}")
    n_variants = sum(1 for r in merged if r.get("variant_label"))
    print(f"  {n_variants} variant labels assigned (alt-path formables)")

    out_path = Path(args.out) if args.out else repo_root / cfg["build"]["web_data_dir"] / "formables.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump({"version": 1, "formables": merged}, f, indent=2)
    print(f"wrote {out_path} ({out_path.stat().st_size/1e6:.2f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
