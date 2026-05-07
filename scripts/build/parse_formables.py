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
    by_source: dict[str, int] = {}
    for r in merged:
        by_source[r["source"]] = by_source.get(r["source"], 0) + 1
    print("merged:")
    for k, v in sorted(by_source.items()):
        print(f"  {k}: {v}")

    out_path = Path(args.out) if args.out else repo_root / cfg["build"]["data_dir"] / "formables.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump({"version": 1, "formables": merged}, f, indent=2)
    print(f"wrote {out_path} ({out_path.stat().st_size/1e6:.2f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
